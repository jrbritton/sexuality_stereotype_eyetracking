from psychopy.gui import DlgFromDict
from psychopy.visual import Window, TextStim, ImageStim
from psychopy.core import Clock, quit, wait
from psychopy.event import Mouse
from psychopy.hardware.keyboard import Keyboard
from psychopy import prefs, sound, core, event
from psychopy.iohub import launchHubServer, util, client
import pandas as pd
import os
import pylink
import random

### DIALOGUE BOX ROUTINE ###
exp_info = {'participant': '', 'subgroup': '', 'version': ''}
dlg = DlgFromDict(exp_info)

# iohub config file
iohub_config = 'iohub_config.yaml'
# Import config file
io_config = util.readConfig(iohub_config)

# If pressed Cancel, abort!
if not dlg.OK:
    quit()
else:
    # Quit when either the participant number or age is not filled in
    if not exp_info['participant'] or not exp_info['age']:
        quit()

    # Also quit in case of invalid participant nr or age
    if exp_info['participant'] > 99 or int(exp_info['age']) < 18:
        quit()
    else:  # let's start the experiment!
        print(f"Started experiment for participant {exp_info['participant']} "
                 f"with age {exp_info['age']}.")
                 

# Initialize a fullscreen window with correct monitor (check monitor centre)
win = Window(size=(1920, 1080), fullscr=False, monitor='ThinkPadX1C9')

# Also initialize a mouse, for later
# We'll set it to invisible for now
mouse = Mouse(visible=False)

# Initialize a (global) clock
clock = Clock()

# Initialize a (trial) clock
trial_clock = Clock()

# Initialize Keyboard
kb = Keyboard()

### EYE TRACKER SETUP ###

# Connect to the tracker (ip 100.1.1.1)
tk = pylink.EyeLink(None) # Use 'None' when not connected to eye-link
# Open EDF file
tk.openDataFile('genste2.edf')
# Set sample rate
tk.sendCommand("sample_rate 1000")

### CALIBRATION ###
#pylink.openGraphics()
#tk.doTrackerSetup()
#pylink.closeGraphics()

### EYE TRACKER SETUP END ###

# Path to audio stims file
stims_file = 'stims_file.csv'
# Create pandas dataframe
stims_file = pd.read_csv(stims_file)
# Shuffle rows in the stims file using pandas sample (frac=1 is 100% of rows)
stims_file = stims_file.sample(frac = 1).reset_index()

# Audio directories
prime_folder = '../primes'
target_folder = '../targets'

# Extract values to list for each column
trial_list = stims_file['trial'].tolist()
prime_list = stims_file['prime'].tolist()
target_list = stims_file['target'].tolist()
question_list = stims_file['question'].tolist()

# Instructions

instructions = '''In this experiment, you will hear the first part of a sentence, then there will be a pause before the final word is played.
Your task is to combine the two parts together in your head to form a sentence. 

In some trials you will be asked a yes or no question after hearing both parts.
Please use the left and right arrow keys to answer the question.

There will now be a short practice. PLease press 'enter' to continue.
'''
# True or false question text
true_false_text1 = '左 = 不是    |    右 = 是的'
true_false_text2 = '左 = 是的    |    右 = 不是'

# Thank you text
thankYou = '''The experiment is complete. Thank you for taking part!
Please press ‘enter’ to end the experiment.'''

### START BODY OF EXPERIMENT ###

# Set up all of the display text except the question stims (in main trial loop)
welcome_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', text="Welcome to this experiment!")
instruct_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', text=instructions, alignText='center')

true_false_stim1 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', text=true_false_text1, alignText='center', pos=(0, -0.2))
true_false_stim2 = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', text=true_false_text2, alignText='center', pos=(0, -0.2))

thankYou_txt_stim = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', text=thankYou, alignText='left')
fixation = TextStim(win, color=(0.8,1.0,0.5), font='Calibri', text="+")



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

# Start the eye tracker recording
#tk.startRecording(1, 1, 1, 1)

# The zip function combines the two iterable lists
# The first element of each list is played before moving to the next

for trial, prime, target, question in zip(trial_list, prime_list, target_list, question_list):
    #tk.sendMessage(f'Trial: {trial}')
    # draw the fixation
    fixation.draw()
    win.flip()
    core.wait(1.5)
    win.flip()
    clock.reset()
    # Create a file path to the audio by concatenating audio_folder and intro
    # Play the sentence prime
    current_prime = os.path.join(prime_folder, prime)
    prime_stim = sound.Sound(current_prime)
    prime_stim.play()
    core.wait(prime_stim.getDuration())
    trial_clock.reset()
    # Play the target audio
    #tk.sendMessage(f'Target: {trial}')
    fixation.draw()
    win.flip()
    core.wait(1.5)
    win.flip()
    current_target = os.path.join(target_folder, target)
    target_stim = sound.Sound(current_target)
    target_stim.play()
    core.wait(target_stim.getDuration())
    trial_clock.reset()
    # Set up question
    current_question = question
    question_txt = TextStim(win, text=current_question, pos=(0, 0))
    # Create 1/3 chance of question
    # This checks whether the random number is 2 (show question)
    question_num = random.randint(1,3)
    if question_num == 2:
        question_stim = TextStim(win, color=(0.8,1.0,0.5), font='SimSun', text=question, alignText='center')
        question_stim.draw()
        true_false_num = random.randint(1,2)
        if true_false_num == 1:
            true_false_stim1.draw()
            win.flip()
            # Check which key was pressed and record response
            ansKey = event.waitKeys()
            keys = kb.getKeys(["left", "right"])
            if ansKey == "left":
                stims_file.loc[trial, "response"] = "NO"
            else:
                stims_file.loc[trial, "response"] = "YES"
        else:
            true_false_stim2.draw()
            win.flip()
            ansKey = event.waitKeys()
            keys = kb.getKeys(["left", "right"])
            if ansKey == "left":
                stims_file.loc[trial, "response"] = "YES"
            else:
                stims_file.loc[trial, "response"] = "NO"

# Stop the eye tracker recording
#tk.stopRecording()

### SENTENCE ROUTINE END ###

# Save stims_file to csv
stims_file.to_csv('results.csv')

### THANK YOU ROUTINE ###

while True:
    thankYou_txt_stim.draw()
    win.flip()
    keys = kb.getKeys()
    contKey = event.waitKeys()
    if 'return' in contKey:
        break

### END THANK YOU ROUTINE ###