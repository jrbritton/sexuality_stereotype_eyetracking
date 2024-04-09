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
import pandas as pd
import pylink as pl
import os
import random

### DIALOGUE BOX ROUTINE ###

exp_info = {'participant': 0, 'subgroup': 0, 'version': 0, 'rotation': ''}
dlg = DlgFromDict(exp_info)

### DIALOGUE BOX ROUTINE END ###

# If pressed Cancel, abort!
if not dlg.OK:
    quit()
else:
    # Quit when experiment info is not filled in or if invalid subgroup/version
    if not exp_info['participant']:
        quit()
    if exp_info['subgroup'] > 2 or exp_info['version'] > 2:
        quit()
    if exp_info['subgroup'] < 1 or exp_info['version'] < 1:
        quit()
    else:  # Start the experiment!
        print(f'''Started experiment for participant {exp_info['participant']},
                 subgroup {exp_info['subgroup']},
                    version {exp_info['version']}''')
                 

# Set the rotation type (male or female)
rotation_type = exp_info['rotation']

# Make subgroup and version strings for concatenation and saving
subgroup = str(exp_info['subgroup'])
version = str(exp_info['version'])
part = str(exp_info['participant'])

session_info = (f"{part}_sub{subgroup}_ver{version}")

### EYE TRACKER SETUP ###

# Eye tracker to use ('mouse', 'eyelink', 'gazepoint', or 'tobii')
TRACKER = 'eyelink'
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

win = visual.Window((1920, 1080),
                    units='pix',
                    fullscr=False,
                    allowGUI=False,
                    colorSpace='rgb255',
                    monitor='sls_Dell',
                    color=BACKGROUND_COLOR,
                    screen=0
                    )
                    
io = launchHubServer(window=win, 
                    **devices_config, 
                    experiment_code='Gender Stereotypes',
                    session_code=session_info)
                
# Specify the iohub .hdf5 file to process. None will prompt for file selection when script is run.
#IOHUB_DATA_FILE = session_code
# Specify which event type to save. Setting to None will prompt to select an event table
SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent'  # 'MonocularEyeSampleEvent'
# Specify which event fields to save. Setting to None will save all event fields.
SAVE_EVENT_FIELDS = None  # ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START = 'trial.start' #'text.started' #  'target.started'
TRIAL_END = 'trial.end' #'fix_end_stim.started' #  'fix_end_stim.started'

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

# Setup paths to subgroup stims files
subgroup1version1_F = 'subgroup1version1_F.csv'
subgroup1version1_M = 'subgroup1version1_M.csv'
# Create pandas dataframes
subgroup1version1_F = pd.read_csv(subgroup1version1_F)
subgroup1version1_M = pd.read_csv(subgroup1version1_M)
# Shuffle rows in the stims file using pandas sample (frac=1 is 100% of rows)
subgroup1version1_F = subgroup1version1_F.sample(frac = 1).reset_index()
subgroup1version1_M = subgroup1version1_M.sample(frac = 1).reset_index()

# Create trial lists by passing a dataframe or a dictionary
# These are iterated over in the main experiment loop

# Practice trials
# Extract values to list for each column for male and female sets

# Main trials
# Extract values to list for each column for male and female sets
section_list_F = subgroup1version1_F['Section'].tolist()
section_list_M = subgroup1version1_M['Section'].tolist()
id_list_F = subgroup1version1_F['ID'].tolist()
id_list_M = subgroup1version1_M['ID'].tolist()
prime_list_F = subgroup1version1_F['Prime'].tolist()
prime_list_M = subgroup1version1_M['Prime'].tolist()
target_list_F = subgroup1version1_F['Target'].tolist()
target_listM = subgroup1version1_M['Target'].tolist()
question_list_F = subgroup1version1_F['Question'].tolist()
question_list_M = subgroup1version1_M['Question'].tolist()

# Create trial handler from the pandas dataframe
#trials = data.TrialHandler(trialList=stims_file.to_dict('records'), nReps=1, method='sequential')

# Audio directories
prime_folder = '../primes'
target_folder = '../targets'

# Instructions

instructions = '''In this experiment, you will hear the first part of a sentence, then there will be a pause before the final word is played.
Your task is to combine the two parts together in your head to form a sentence. 

In some trials you will be asked a yes or no question after hearing both parts.
Please use the left and right arrow keys to answer the question.

There will now be a short practice. Please press 'enter' to continue.
'''
# True or false question text
true_false_text1 = '左 = 不是    |    右 = 是的'
true_false_text2 = '左 = 是的    |    右 = 不是'

# Thank you text
thankYou = '''The experiment is complete. Thank you for taking part!
Please press ‘enter’ to end the experiment.'''

### START BODY OF EXPERIMENT ###

# Set up all of the display text except the question stims (in main trial loop)
welcome_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', units='norm', text="Welcome to this experiment!")
instruct_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', units='norm',text=instructions, alignText='center')

true_false_stim1 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=true_false_text1, alignText='center', pos=(0, -0.2))
true_false_stim2 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', units='norm', text=true_false_text2, alignText='center', pos=(0, -0.2))

thankYou_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', units='norm', text=thankYou, alignText='left')
fixation = TextStim(win, color=(0.8,1.0,0.5), units='norm', font='Calibri', text="+")

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

### SENTENCE ROUTINE ###

# Iterate over the trials in trial handler
if rotation_type == 'f':
    for index, (ID, Prime, Target, Question) in enumerate(zip(id_list_F, prime_list_F, target_list_F, question_list_F)):
        trial_num = str(index)
        io.clearEvents()
        tracker.setRecordingState(True)
        #prime = trial['prime']
        #target = trial['target']
        #question = trial['question']
        # draw the fixation
        io.sendMessageEvent(text='fixationtask_start', category=trial_num)
        fixation.draw()
        win.flip()
        core.wait(1.5)
        win.flip()
        clock.reset()
        # Get the latest gaze position in display coord space.
        gpos = tracker.getLastGazePosition()
        # Create a file path to the audio by concatenating audio_folder and intro
        # Play the sentence prime
        io.sendMessageEvent(text=TRIAL_START, category=trial_num)
        current_prime = os.path.join(prime_folder, Prime)
        prime_stim = sound.Sound(current_prime)
        prime_stim.play()
        core.wait(prime_stim.getDuration())
        trial_clock.reset()
        # Play the target audio
        fixation.draw()
        win.flip()
        core.wait(1.5)
        win.flip()
        current_target = os.path.join(target_folder, Target)
        target_stim = sound.Sound(current_target)
        target_stim.play()
        core.wait(target_stim.getDuration())
        trial_clock.reset()
        # Set up question
        current_question = Question
        #question_txt = TextStim(win, text=current_question, units='norm', pos=(0, 0))
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
                keys = event.waitKeys(keyList=["left", "right"])
                if "left" in keys:
                    subgroup1version1_F.loc[index, "Response"] = "FALSE"
                elif "right" in keys:
                    subgroup1version1_F.loc[index, "Response"] = "TRUE"
            else:
                true_false_stim2.draw()
                win.flip()
                keys = event.waitKeys(keyList=["left", "right"])
                if "left" in keys:
                    subgroup1version1_F.loc[index, "Response"] = "TRUE"
                elif "right" in keys:
                    subgroup1version1_F.loc[index, "Response"] = "FALSE"
        io.sendMessageEvent(text=TRIAL_END, category=trial_num)
        tracker.setRecordingState(False)
        

### SENTENCE ROUTINE END ###

# Save stims_file to csv
subgroup1version1_F.to_csv('../results/subgroup'+subgroup+'_version'+version+'/'+\
part+'_sub'+subgroup+'ver'+version+'_results.csv', encoding='utf_8_sig')

# Save hdf5 file
#hdf5FilePath=IOHUB_DATA_FILE
if __name__ == '__main__':
    result = saveEventReport(eventType=SAVE_EVENT_TYPE,
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

