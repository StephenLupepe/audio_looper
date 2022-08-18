import math
import PySimpleGUI as sg
import pygame
import time
from pathlib import Path
from PIL import Image
from pydub import AudioSegment
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#Function for creating the window
def create_window(theme):

    sg.theme(theme)

    #menu layout for additional themes
    menu_layout = [
    ['File', ['Open', 'Load Loop Timing', 'Save Loop Timings', 'Export Loop']],
    theme_menu
    ]

    buttons_col = sg.Column([
        [sg.Checkbox('Loop Full', key='-LOOPFULL-')],
        [sg.Checkbox('Loop Section', key='-LOOPSECTION-')],
        [sg.Text('Loop:'), sg.Input('1', size=(5,1), key='-NUMBERLOOPS-'), sg.Text('time(s)')]
])

    timings_col = sg.Column([
        [sg.Text('Start:'), sg.Push(), sg.Button(image_filename='buttons/8px_back.png', p=0, mouseover_colors=None, key='-DECLOOPSTART-'), sg.Input(size=(15,1), default_text='00:00:00:00', key='-LOOPSTARTINPUT-'), sg.Button(image_filename='buttons/8px_forward.png', p=0, mouseover_colors=None, key='-INCLOOPSTART-')],
        [sg.Text('End:'), sg.Push(), sg.Button(image_filename='buttons/8px_back.png', p=0, mouseover_colors=None, key='-DECLOOPEND-'), sg.Input(size=(15,1), default_text='00:00:00:00', key='-LOOPENDINPUT-'), sg.Button(image_filename='buttons/8px_forward.png', p=0, mouseover_colors=None, key='-INCLOOPEND-')],
        [sg.Push(),sg.Button('Apply Loop', key='-APPLYLOOP-'), sg.Button('Reset Settings', key='-RESETLOOP-'), sg.Push()]
    ])


    layout = [
    [sg.Menu(menu_layout)],
    [sg.Text('', key='-TRACKNAME-'), sg.Push(), sg.Text('', font=('Helvetica', 14, 'bold'), text_color='red', key='-ERRORMSG-')],
    [sg.Push(), sg.Graph(canvas_size=(810, 100), graph_bottom_left=(0,0), graph_top_right=(3000,1), background_color='black', key='-SCOPE-'), sg.Push()],
    [sg.Text(text='00:00:00:00', size=(10,1), key='-CURRENTTIME-'), sg.Slider(range=(0,3000), orientation='h', size=(84, 20), enable_events=True, disable_number_display=True, key='-PLAYBACK-'), sg.Text(text='00:00:00:00', size=(10,1), key='-SONGLENGTH-')],
    [sg.Text(text='Loop Start:', size=(10,1)), sg.Slider(range=(0,3000), orientation='h', size=(84, 6), disable_number_display=True,key='-LOOPSTART-'), sg.Text(text='00:00:00:00', size=(10,1), key='-STARTTIMEDISPLAY-')],
    [sg.Text(text='Loop End:', size=(10,1)), sg.Slider(range=(0,3000), orientation='h', size=(84, 6), disable_number_display=True, default_value=3000, key='-LOOPEND-'), sg.Text(text='00:00:00:00', size=(10,1), key='-ENDTIMEDISPLAY-')],
    [   
        sg.Column(layout=[[sg.Text(text="Volume:")],[sg.Slider(range=(0,100), resolution=5, orientation='h', size=(20,20), default_value=15, key="-VOLUME-")]]),
        sg.Push(),
        sg.Button('', image_filename='buttons/rw.png', p=0, mouseover_colors=None, key='-RW3-'), 
        sg.Button('', image_filename='buttons/play.png',p=0, mouseover_colors=None, key='-PLAY/PAUSE-'), 
        sg.Button('', image_filename='buttons/stop.png',p=0, mouseover_colors=None, key='-STOP-'),
        sg.Button('', image_filename='buttons/ff.png', p=0, mouseover_colors=None, key='-FF3-'),
        sg.Push(),
        sg.Frame('Loop Controls', layout=[
            [buttons_col, sg.VerticalSeparator(), timings_col]
            ])
    ]]

    return sg.Window('Audio Looper', layout, font=('Hevetica', 14))

#Set flags for song status
global song_loaded, paused, start_time, current_time, saved_time
song_loaded, paused, start_time, current_time, saved_time = False, True, 0, 0, 0

global seek_bar, loop_full, loop_section, is_seeking
seek_bar, loop_full, loop_section, is_seeking = 0, False, False, False

#define theme menu
theme_menu = ['Themes', ['LightGrey1','LightBrown11', 'Dark', 'Darkamber', 'DarkTeal7']]

#Pause/Unpause function
def playpause():
    global song_loaded, paused, start_time, saved_time, seek_bar, is_seeking
    if song_loaded == True:
        if is_seeking == False:
            if paused == True:
                seek_time = (seek_bar * song_length) / 3000
                pygame.mixer.music.play(start=seek_time)
                saved_time = seek_time
                paused = False
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/pause.png')
                start_time = time.time()
            else:
                pygame.mixer.music.pause()
                paused = True
                saved_time += current_time
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')
        else:
            if paused == True:
                is_seeking = False
            else:
                pygame.mixer.music.pause()
                paused = True
                saved_time += current_time
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')

#Function for stopping playback and resetting certain parameters 
def stop():
    pygame.mixer.music.stop()
    global paused, saved_time, seek_bar, current_loop
    paused = True
    window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')
    window['-CURRENTTIME-'].update('00:00:00:00')
    window['-PLAYBACK-'].update(0)
    saved_time = 0
    seek_bar = 0
    current_loop = 1

#Function for looping specified sections of the audio
def loop():
    global song_loaded, paused, start_time, current_time, saved_time, seek_bar, current_loop
    pygame.mixer.music.pause()
    paused = True
    seek_time = loop_start
    pygame.mixer.music.play(start=seek_time)
    saved_time = seek_time
    paused = False
    current_time = 0
    start_time = time.time()
    current_loop += 1

#Function for fast forwarding or rewind 3 seconds  
def rwff(backorforward):
    global song_loaded, paused, start_time, saved_time, seek_bar, is_seeking
    if song_loaded == True:
                pygame.mixer.music.pause()
                paused = True
                saved_time += current_time
                seek_time = (seek_bar * song_length) / 3000
                if backorforward == 'back':
                    if seek_time >= 3:
                        seek_time -= 3
                    else:
                        seek_time = 0
                elif backorforward == 'forward':
                    if (seek_time + 3) <= song_length:
                        seek_time += 3
                    else:
                        seek_time = song_length
                pygame.mixer.music.play(start=seek_time)
                saved_time = seek_time
                paused = False
                start_time = time.time()


#Function for adjusting the volume
def set_volume(volume):
    adjusted_volume = volume / 100
    pygame.mixer.music.set_volume(adjusted_volume)

def draw_plot_from_file(sound):
    #get the sample rate
    sample_rate = sound.frame_rate
    #get the number of samples
    n_samples = sound.frame_count()
    #get array of samples
    samples = sound.get_array_of_samples()
    npdata = np.array(samples)
    times = np.linspace(0, int(n_samples/sample_rate), num=len(npdata))

    if len(npdata) > 100000:
        every_nth = math.ceil(len(npdata) / 100000)
        plotdata = npdata[::every_nth]
        plottimes = times[::every_nth]
    else:
        plotdata = npdata
        plottimes = times 

    return create_plot(plottimes, plotdata)

#Creates the image for the scope
def create_plot(times, samples):
    plt.figure(figsize=(8.25, 1), dpi=100)
    plt.plot(times, samples, color="green", lw=0.5)
    plt.axis('off')
    plt.gca().set_axis_off()
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
             hspace = 0, wspace = 0)
    plt.margins(0,0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.rcParams['savefig.facecolor']='black'
    return plt.savefig('scope_image.png')

#Creates a window with the given theme using the function above
window = create_window('LightGrey1')

#Standard pysimplegui update loop
while True:
    event, values = window.read(timeout=10)

    #Draws the scope
    window['-SCOPE-'].erase()
    scope_image = window['-SCOPE-'].DrawImage(filename='scope_image.png', location=(0,1))
    
    if event == sg.WIN_CLOSED:
        break
    
    #Sets behavior for the open file button. Initializes pygame mixer loads the song and sets appropriate flags
    if event == 'Open':
        file_name = sg.popup_get_file('Open', no_window=True)
        if file_name:
            pygame.init()
            pygame.mixer.init()
            pygame.mixer.music.load(file_name)
            song_loaded = True
            window['-TRACKNAME-'].update(file_name.split('/')[-1])
            song = AudioSegment.from_file(file_name)
            song_length = song.duration_seconds
            window['-SONGLENGTH-'].update(time.strftime('%H:%M:%S', time.gmtime(song_length)) + str(round(song_length%1, 2))[-3:])
            scope_image = draw_plot_from_file(song)

    #Runs the play pause function when the button is pressed
    if event == '-PLAY/PAUSE-':
        playpause()
    
    #Stops the music and resets flags, etc. when stop is pressed
    if event == '-STOP-':
        stop()

    if event == '-PLAYBACK-':
        is_seeking = True
        playpause()

    #Sets the behavior for the skip forward and skip back buttons 
    if event == '-RW3-':
        rwff('back')

    if event == '-FF3-':
        rwff('forward')

    if event == '-DECLOOPSTART-':
        temploopstart = values['-LOOPSTART-']
        if temploopstart > 0:
            temploopstart -= 1
        window['-LOOPSTART-'].update(temploopstart)

    if event == '-INCLOOPSTART-':
        temploopstart = values['-LOOPSTART-']
        if temploopstart < 3000:
            temploopstart += 1
        window['-LOOPSTART-'].update(temploopstart)

    if event == '-DECLOOPEND-':
        temploopend = values['-LOOPEND-']
        if temploopend > 0:
            temploopend -= 1
        window['-LOOPEND-'].update(temploopend)

    if event == '-INCLOOPEND-':
        temploopend = values['-LOOPEND-']
        if temploopend < 3000:
            temploopend += 1
        window['-LOOPEND-'].update(temploopend)

    if event == '-APPLYLOOP-':
        if loop_end <= loop_start:
            window['-ERRORMSG-'].update('ERROR: LOOP START LATER THAN LOOP END!')
        else:
            stop()
            playpause()
            loop_section = values['-LOOPSECTION-']
            current_loop = 1
            song_loops = int(values['-NUMBERLOOPS-'])
            loop_full = values['-LOOPFULL-']
            window['-ERRORMSG-'].update('')

        # if values['-LOOPSECTION-'] == True:
        #     cut_start = int(round(loop_start, 3) * 1000)
        #     cut_end = int(round(loop_end, 3) * 1000)
        #     song_start = song[:cut_start]
        #     song_end = song[cut_end:]
        #     no_end = song[:cut_end]
        #     song_middle = no_end[cut_start:]
        #     song_loops = int(values['-NUMBERLOOPS-'])
        #     current_loop = 1

        #     first_part = song_start + song_middle
        #     if song_loops == 1:
        #         temp_song = first_part
        #     else:
        #         i = 1
        #         while i < song_loops:
        #             temp_song = first_part  + song_middle
        #             i += 1

        #     final_song = temp_song + song_end
            # print("start: " + str(final_song.duration_seconds))
            # print("middle: " + str(final_song.duration_seconds))
            # print("end: " + str(final_song.duration_seconds))

    if event == '-RESETLOOP-':
        stop()
        loop_start = 0
        loop_end = song_length
        window['-LOOPFULL-'].update(False)
        window['-LOOPSECTION-'].update(False)
        window['-NUMBERLOOPS-'].update(1)
        window['-LOOPSTART-'].update(0)
        window['-LOOPEND-'].update(3000)
        window['-ERRORMSG-'].update('')

    #Updates certain params when a song is loaded. Updates additional params when the song starts playing
    if song_loaded == True:
        set_volume(values['-VOLUME-'])
        loop_start = (values['-LOOPSTART-'] / 3000) * song_length
        window['-STARTTIMEDISPLAY-'].update(time.strftime('%H:%M:%S', time.gmtime(loop_start)) + str(loop_start%1)[1:4])
        window['-LOOPSTARTINPUT-'].update(time.strftime('%H:%M:%S', time.gmtime(loop_start)) + str(loop_start%1)[1:4])
        loop_end = (values['-LOOPEND-'] / 3000) * song_length
        window['-ENDTIMEDISPLAY-'].update(time.strftime('%H:%M:%S', time.gmtime(loop_end)) + str(loop_end%1)[1:4])
        window['-LOOPENDINPUT-'].update(time.strftime('%H:%M:%S', time.gmtime(loop_end)) + str(loop_end%1)[1:4])
        loop_start_scope = window['-SCOPE-'].DrawLine((values['-LOOPSTART-'],0), (values['-LOOPSTART-'],1), color='blue', width=3)
        loop_end_scope = window['-SCOPE-'].DrawLine((values['-LOOPEND-'],0), (values['-LOOPEND-'],1), color='blue', width=3)
        scope_line = window['-SCOPE-'].DrawLine((seek_bar,0), (seek_bar,1), color='red', width=3)
        seek_bar = values['-PLAYBACK-']
        if not paused  == True:
            current_time = (time.time() - start_time)
            window['-CURRENTTIME-'].update(time.strftime('%H:%M:%S', time.gmtime(saved_time + current_time)) + str((saved_time + current_time) % 1)[1:4])
            seek_bar = ((saved_time + current_time)/ song_length) * 3000
            window['-PLAYBACK-'].update(seek_bar)
            
            if loop_section == True and current_time + saved_time >= loop_end and current_loop < song_loops:
                loop()

            if current_time + saved_time >= song_length:
                if loop_full == False:
                    print(str(loop_full))
                    stop()
                else:
                    print(str(loop_full))
                    print(str(current_time + saved_time))
                    stop()
                    playpause()

    if event in theme_menu[1]:
        window.close()
        window = create_window(event)
       
window.close()

#TO DO:
#add a table below the player that lets you sort through loop data
#add export for loops
#export for loop data
#export as a .exe