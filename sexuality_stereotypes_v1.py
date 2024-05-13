from psychopy.gui import DlgFromDict
from psychopy.visual import Window, TextStim, ImageStim
from psychopy.core import Clock, quit, wait
from psychopy.event import Mouse
from psychopy.hardware.keyboard import Keyboard
from psychopy import prefs, sound, core, event, data, visual, iohub
from psychopy.iohub.client.eyetracker.validation import TargetStim
from psychopy.iohub.client import launchHubServer, ioHubConnection, yload, yLoader
from psychopy.iohub.util import hideWindow, showWindow
from psychopy.iohub.datastore.util import saveEventReport
from psychopy.visual.textbox import TextBox
import pandas as pd
import pylink as pl
import os
import random
import csv

# Set audio prefs
prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo', 'pygame']

### DIALOGUE BOX ROUTINE ###

exp_info = {'participant': 0, 
            'subgroup': 0, 
            'version': 0, 
            'rotation': '',
            'tracker (mouse/eyelink)': ''}
dlg = DlgFromDict(exp_info, title='Experiment Setup', sortKeys=False)

### DIALOGUE BOX ROUTINE END ###

# If pressed Cancel, abort!
if not dlg.OK:
    quit()
else:
    # Quit when experiment info is not filled in or if invalid subgroup/version
    if not exp_info['participant']:
        quit()
    if exp_info['subgroup'] > 2 or exp_info['version'] > 2:
        print("Error: Invalid subgroup or version. Please select '1' or '2'.")
        quit()
    if exp_info['subgroup'] < 1 or exp_info['version'] < 1:
        print("Error: Invalid subgroup or version. Please select '1' or '2'.")
        quit()
    else:  # Start the experiment!
        print(f'''Started experiment for participant {exp_info['participant']},
                 subgroup {exp_info['subgroup']},
                    version {exp_info['version']}''')
                 

# Set the rotation type (male or female)
rotation_type = exp_info['rotation']

# Make subgroup and version strings for concatenation and saving
part = str(exp_info['participant'])
subgroup = str(exp_info['subgroup'])
version = str(exp_info['version'])
rotation = str(exp_info['rotation'])
session_info = (f"{part}_sub{subgroup}_ver{version}_{rotation}")
tracker_info = str(exp_info['tracker (mouse/eyelink)'])

### EYE TRACKER SETUP ###

# Eye tracker to use ('mouse', 'eyelink', 'gazepoint', or 'tobii')
TRACKER = tracker_info
BACKGROUND_COLOR = [128, 128, 128]

devices_config = dict()
eyetracker_config = dict(name='tracker')
if TRACKER == 'mouse':
    eyetracker_config['calibration'] = dict(screen_background_color=BACKGROUND_COLOR)
    devices_config['eyetracker.hw.mouse.EyeTracker'] = eyetracker_config
elif TRACKER == 'eyelink':
    eyetracker_config['model_name'] = 'EYELINK 1000 DESKTOP'
    eyetracker_config['runtime_settings'] = dict(sampling_rate=1000, track_eyes=' ')
    eyetracker_config['calibration'] = dict(screen_background_color=BACKGROUND_COLOR)
    devices_config['eyetracker.hw.sr_research.eyelink.EyeTracker'] = eyetracker_config
elif TRACKER == 'gazepoint':
    eyetracker_config['calibration'] = dict(use_builtin=False, screen_background_color=BACKGROUND_COLOR)
    devices_config['eyetracker.hw.gazepoint.gp3.EyeTracker'] = eyetracker_config
elif TRACKER == 'tobii':
    eyetracker_config['calibration'] = dict(screen_background_color=BACKGROUND_COLOR)
    devices_config['eyetracker.hw.tobii.EyeTracker'] = eyetracker_config
else:
    print("{} is not a valid TRACKER name; please use 'mouse', 'eyelink', 'gazepoint', or 'tobii'.".format(TRACKER))
    core.quit()

win = visual.Window((1280, 1024),
                    units='pix',
                    fullscr=True,
                    allowGUI=False,
                    colorSpace='rgb255',
                    monitor='sls_Dell',
                    color=BACKGROUND_COLOR,
                    screen=0
                    )

                    
io = launchHubServer(window=win, 
                    **devices_config, 
                    experiment_code='sex_stereo',
                    session_code=session_info)
                
# Specify the iohub .hdf5 file to process. None will prompt for file selection when script is run.
IOHUB_DATA_FILE = session_info+'.hdf5'
# Specify which event type to save. Setting to None will prompt to select an event table
SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent' # 'MonocularEyeSampleEvent'
# Specify which event fields to save. Setting to None will save all event fields.
SAVE_EVENT_FIELDS = None # ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START = 'trial_start' #'text.started' #  'target.started'
TRIAL_END = 'trial_end' #'fix_end_stim.started' #  'fix_end_stim.started'

# Get some iohub devices for future access.
keyboard = io.getDevice('keyboard')
tracker = io.getDevice('tracker')

# Calibration
# Minimize the PsychoPy window if needed
hideWindow(win)
# Display calibration gfx window and run calibration.
result = tracker.runSetupProcedure()
print("Calibration returned: ", result)
# Maximize the PsychoPy window if needed
showWindow(win)

### EYE TRACKER SETUP END ###

# Initialize a mouse set to invisible
mouse = Mouse(visible=False)
# Initialize a (global) clock
clock = Clock()
# Initialize a (trial) clock
trial_clock = Clock()
# Initialize Keyboard
kb = Keyboard()

# Create trial lists based on session info
def trial_list_reader(subgroup,version,rotation):
    trial_list_path = 'stim_lists/subgroup'+subgroup+'version'+version+'_'+rotation+'.csv'
    trial_list = pd.read_csv(trial_list_path)
    return trial_list
    
trial_list = trial_list_reader(subgroup,version,rotation)

# Shuffle rows in the trial_list using pandas sample (frac=1 is 100% of rows)
trial_list = trial_list.sample(frac = 1)

# Create all possible orders for 1 - 4
# Randomly select one to sort by

orderDict = {'1': [1,2,3,4],
             '2': [1,2,4,3],
             '3': [1,3,2,4],
             '4': [1,3,4,2],
             '5': [1,4,2,3],
             '6': [1,4,3,2],
             '7': [2,1,3,4],
             '8': [2,1,4,3],
             '9': [2,3,1,4],
             '10': [2,3,4,1],
             '11': [2,4,1,3],
             '12': [2,4,3,1],
             '13': [3,1,2,4],
             '14': [3,1,4,2],
             '15': [3,2,1,4],
             '16': [3,2,4,1],
             '17': [3,4,1,2],
             '18': [3,4,2,1],
             '19': [4,1,2,3],
             '20': [4,1,3,2],
             '21': [4,2,1,3],
             '22': [4,2,3,1],
             '23': [4,3,1,2],
             '24': [4,3,2,1]
             }
             
# Select a number from 1 - 24 to use as a key to select an order
orderNum = random.randint(1,24)
# Define order sequence
orderSeq = orderDict[f'{orderNum}']

# Convert Section to categorical and use orderSeq to sort
trial_list['Section'] = pd.Categorical(trial_list['Section'], categories=orderSeq, ordered=True)

# Sort the frame based on Section and reset index
trial_list = trial_list.sort_values(by='Section').reset_index()

# Setup paths to practice files
practice_female = 'stim_lists/practice_female.csv'
practice_male = 'stim_lists/practice_male.csv'

# Practice trials
if rotation == 'f':
    practice_trials = pd.read_csv(practice_female)
if rotation == 'm':
    practice_trials = pd.read_csv(practice_male)
if rotation == 'test':
    practice_trials = pd.read_csv(practice_female)

# Shuffle rows
practice_trials = practice_trials.sample(frac = 1).reset_index()

# Extract values to list for each column for practice
practice_id_list = practice_trials['ID'].tolist()
practice_prime_list = practice_trials['Prime'].tolist()
practice_target_list = practice_trials['Target'].tolist()
practice_question_list = practice_trials['Question'].tolist()

# Main trials
# Extract values to list for each column for trial_list
section_list = trial_list['Section'].tolist()
id_list = trial_list['ID'].tolist()
prime_list = trial_list['Prime'].tolist()
target_list = trial_list['Target'].tolist()
question_list = trial_list['Question'].tolist()

# Audio directories
prime_folder = '../primes'
target_folder = '../targets'

# Instructions

instructions_female = '''
实验开始后你将会听到一系列句子，
你的任务是通过听到的句子内容进\n行判断。在一句话结束后，你可能会\n看见一个关于该句子内容的问题，
你可以通过键盘左右键选择你认为是\n或不是。

请以尽量快的速度准确地做出判断。

请在实验过程中保持专注!

接下来你将会听到一些由以普通话作为\n母语的成年女性说出的语句，请你通\n过听见的内容回答与句子内容相关\n的问题。
'''

instructions_male = '''
实验开始后你将会听到一系列句子，
你的任务是通过听到的句子内容进\n行判断。在一句话结束后，你可能会\n看见一个关于该句子内容的问题，
你可以通过键盘左右键选择你认为是\n或不是。

请以尽量快的速度准确地做出判断。

请在实验过程中保持专注!

接下来你将会听到一些由以普通话作为\n母语的成年男性说出的语句，请你通\n过听见的内容回答与句子内容相关\n的问题。
'''

# Break text
break_text = '''请休息一下。

当您准备好继续时，请按`enter'。'''

# True or false question text
true_false_text1 = '左 = 不是    |    右 = 是的'
true_false_text2 = '左 = 是的    |    右 = 不是'

# Practice end text
practiceEnd = '''练习块已经完成。

如果您准备好开始主要实验，请按"enter"。'''

# Thank you text
thankYou = '''The experiment is complete. 
Thank you for taking part!
Please press 'enter' to end the experiment.'''

### START BODY OF EXPERIMENT ###

# Set up all of the display text except the question stims (in main trial loop)
welcome_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', units='norm', text="Welcome to this experiment!")

if rotation == 'f':
    instruct_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm',text=instructions_female, alignText='center')
if rotation == 'm':
    instruct_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm',text=instructions_male, alignText='center')
if rotation == 'test':
    instruct_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm',text=instructions_female, alignText='center')
    
true_false_stim1 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=true_false_text1, alignText='center', pos=(0, -0.2))
true_false_stim2 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=true_false_text2, alignText='center', pos=(0, -0.2))

practice_end_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=practiceEnd, alignText='center')
thankYou_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', units='norm', text=thankYou, alignText='center')
fixation = TextStim(win, color=(0.8,1.0,0.5), units='norm', font='Calibri', text="+")

fixation_cross = visual.ShapeStim(
    win=win, name='polygon', vertices='cross',
    size=(30, 30),
    ori=0.0, pos=(0, 0), anchor='center',
    lineWidth=1.0, colorSpace='rgb', lineColor='white', fillColor='white',
    opacity=None, depth=0.0, interpolate=True)

# Welcome window
welcome_txt_stim.draw()
win.flip()
wait(3)

### INSTRUCTIONS ROUTINE ###

while True:
    instruct_txt_stim.draw()
    win.flip()
    keys = kb.getKeys()
    contKey = event.waitKeys()
    if 'return' in contKey:
        break

### INSTRUCTIONS ROUTINE END ###

### PRACTICE ROUTINE ###

# Iterate over the trials based on rotation
practice = enumerate(zip(practice_id_list, practice_prime_list, practice_target_list, practice_question_list))

for index, (ID, Prime, Target, Question) in practice:
    interest_region = visual.Circle(win, lineColor=None, radius=200, units='pix')
    io.clearEvents()
    tracker.setRecordingState(True)
    # draw the fixation
    fixation_cross.draw()
    win.flip()
    clock.reset()
    # Get the latest gaze position
    gpos = tracker.getLastGazePosition()
    tracker.getLastSample()
    # Set up stim
    current_prime = os.path.join(prime_folder, Prime)
    prime_stim = sound.Sound(current_prime)
    prime_stim.play()
    core.wait(prime_stim.getDuration())
    trial_clock.reset()
    # Play the target audio
    core.wait(1.5)
    current_target = os.path.join(target_folder, Target)
    target_stim = sound.Sound(current_target)
    target_stim.play()
    core.wait(target_stim.getDuration())
    core.wait(2.7)
    trial_clock.reset()
    # Get pupil and other info
    tracker.getLastSample()
    tracker.setRecordingState(False)
    win.flip()
    core.wait(1)
    # Set up question
    current_question = Question
    # Create 1/3 chance of question
    # This checks whether the random number is 2 (show question)
    question_num = random.randint(1,3)
    if question_num == 2:
        question_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=Question, alignText='center')
        question_stim.draw()
        true_false_num = random.randint(1,2)
        if true_false_num == 1:
            true_false_stim1.draw()
            win.flip()
            # Check which key was pressed and record response
            keys = event.waitKeys(keyList=["left", "right", "q"])
            if "left" in keys:
                practice_trials.loc[index, "Response"] = "FALSE"
            elif "right" in keys:
                practice_trials.loc[index, "Response"] = "TRUE"
            elif "q" in keys:
                core.quit()
        else:
            true_false_stim2.draw()
            win.flip()
            keys = event.waitKeys(keyList=["left", "right", "q"])
            if "left" in keys:
                practice_trials.loc[index, "Response"] = "TRUE"
            elif "right" in keys:
                practice_trials.loc[index, "Response"] = "FALSE"
            elif "q" in keys:
                core.quit()
    win.flip()
    core.wait(1)
    
tracker.setConnectionState(False)
    
while True:
    practice_end_stim.draw()
    win.flip()
    keys = kb.getKeys()
    contKey = event.waitKeys()
    if 'return' in contKey:
        # Continue to main trials
        break

### PRACTICE ROUTINE END ###

### MAIN EXPERIMENT ROUTINE ###

# Set break numbers by trial counter for main and test runs

if rotation == 'f' or rotation == 'm':
    break1 = 26
    break2 = 51
    break3 = 76
if rotation == 'test':
    break1 = 4
    break2 = 7
    break3 = 10

# Iterate over the trials based on rotation
trials = enumerate(zip(section_list, id_list, prime_list, target_list, question_list))
trial = 0

for index, (ID, Section, Prime, Target, Question) in trials:
    interest_region = visual.Circle(win, lineColor=None, radius=200, units='pix')
    trial_num = str(index)
    trial += 1
    print(f"this is trial {trial}")
    trial_list.loc[index, "Trial"] = trial
    io.clearEvents()
    contKey = []
    if trial == break1 or trial == break2 or trial == break3 and 'return' not in contKey:
        break_message = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=break_text, alignText='center')
        break_message.draw()
        win.flip()
        contKey = event.waitKeys()
    # Run calibration again if a break has occurred
    if 'return' in contKey:
        # Minimize the PsychoPy window if needed
        hideWindow(win)
        # Display calibration gfx window and run calibration.
        result = tracker.runSetupProcedure()
        print("Calibration returned: ", result)
        # Maximize the PsychoPy window
        showWindow(win)
        win.flip()
        core.wait(1)
    tracker.setRecordingState(True)
    # draw the fixation
    io.sendMessageEvent(text='fixationtask_start', category=trial_num)
    fixation_cross.draw()
    win.flip()
    clock.reset()
    io.sendMessageEvent(text=TRIAL_START, category=trial_num)
    # Get the latest gaze position
    gpos = tracker.getLastGazePosition()
    tracker.getLastSample()
    # Set up stim
    current_prime = os.path.join(prime_folder, Prime)
    prime_stim = sound.Sound(current_prime)
    prime_stim.play()
    core.wait(prime_stim.getDuration())
    trial_clock.reset()
    # Play the target audio
    core.wait(1.5)
    current_target = os.path.join(target_folder, Target)
    target_stim = sound.Sound(current_target)
    target_stim.play()
    core.wait(target_stim.getDuration())
    core.wait(2.7)
    trial_clock.reset()
    # Get pupil and other info
    tracker.getLastSample()
    io.sendMessageEvent(text=TRIAL_END, category=trial_num)
    tracker.setRecordingState(False)
    win.flip()
    core.wait(1)
    # Set up question
    current_question = Question
    # Create 1/3 chance of question
    # This checks whether the random number is 2 (show question)
    question_num = random.randint(1,3)
    if question_num == 2:
        question_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=Question, alignText='center')
        question_stim.draw()
        true_false_num = random.randint(1,2)
        if true_false_num == 1:
            true_false_stim1.draw()
            win.flip()
            # Check which key was pressed and record response
            keys = event.waitKeys(keyList=["left", "right", "q"])
            if "left" in keys:
                trial_list.loc[index, "Response"] = "FALSE"
            elif "right" in keys:
                trial_list.loc[index, "Response"] = "TRUE"
            elif "q" in keys:
                break
        else:
            true_false_stim2.draw()
            win.flip()
            keys = event.waitKeys(keyList=["left", "right", "q"])
            if "left" in keys:
                trial_list.loc[index, "Response"] = "TRUE"
            elif "right" in keys:
                trial_list.loc[index, "Response"] = "FALSE"
            elif "q" in keys:
                break
    win.flip()
    core.wait(1)
    
### MAIN EXPERIMENT ROUTINE END ###

# Save trial_list to csv
trial_list.to_csv('../results/subgroup'+subgroup+'_version'+version+'/'+\
session_info+'_results.csv', encoding='utf_8_sig')

# Save hdf5 file
if __name__ == '__main__':
    result = saveEventReport(hdf5FilePath=IOHUB_DATA_FILE,
                             eventType=SAVE_EVENT_TYPE,
                             eventFields=SAVE_EVENT_FIELDS,
                             trialStart=TRIAL_START,
                             trialStop=TRIAL_END)
    if result:
        file_saved, events_saved = result
        print("Saved %d events to %s." % (events_saved, file_saved))
    else:
        raise RuntimeError("saveEventReport failed.")

### THANK YOU ROUTINE ###

while True:
    thankYou_txt_stim.draw()
    win.flip()
    keys = kb.getKeys()
    contKey = event.waitKeys()
    if 'return' in contKey:
        # End experiment
        win.close()
        tracker.setConnectionState(False)
        core.quit()

### END THANK YOU ROUTINE ###

