import PySimpleGUI as sg
import pygame
from pathlib import Path
from PIL import Image
from pydub import AudioSegment

#Function for creating the window
def create_window(theme):

    sg.theme(theme)

    #menu layout for additional themes (IN PROGRESS)
    menu_layout = [
    ['File', ['Open', 'Save Loop Timings', 'Export Loop']],
    ['Themes', ['LightGrey1', 'Dark', 'Darkamber', 'DarkTeal7']],
    ]

    layout = [
    [sg.Menu([['File', ['Open', 'Save']]])],
    [sg.Text('', key='-TRACKNAME-')],
    [sg.Push(), sg.Graph(canvas_size=(810, 100), graph_bottom_left=(0,0), graph_top_right=(3000,1), background_color='black', key='-SCOPE-'), sg.Push()],
    [sg.Text(text='00:00:00:00', size=(10,1), key='-CURRENTTIME-'), sg.Slider(range=(0,3000), orientation='h', size=(120, 20), key='-PLAYBACK-'), sg.Text(text='00:00:00:00', size=(10,1), key='-SONGLENGTH-')],
    [sg.Text(text='Loop Start:', size=(10,1)), sg.Slider(range=(0,3000), orientation='h', size=(120, 6), key='-LOOPSTART-'), sg.Text(text='00:00:00:00', size=(10,1), key='-STARTTIMEDISPLAY-')],
    [sg.Text(text='Loop End:', size=(10,1)), sg.Slider(range=(0,3000), orientation='h', size=(120, 6), default_value=3000, key='-LOOPEND-'), sg.Text(text='00:00:00:00', size=(10,1), key='-ENDTIMEDISPLAY-')],
    [   
        sg.Column(layout=[[sg.Text(text="Volume:")],[sg.Slider(range=(0,100), resolution=5, orientation='h', size=(20,20), default_value=15, key="-VOLUME-")]]),
        sg.Push(),
        sg.Button('', image_filename='buttons/3back.png', p=0, mouseover_colors=None, key='-3BACK-'), 
        sg.Button('', image_filename='buttons/play.png',p=0, mouseover_colors=None, key='-PLAY/PAUSE-'), 
        sg.Button('', image_filename='buttons/stop.png',p=0, mouseover_colors=None, key='-STOP-'),
        sg.Button('', image_filename='buttons/3forward.png', p=0, mouseover_colors=None, key='-3FORWARD-'),
        sg.Push(),
        sg.Frame('Loop Controls', layout=[
            [sg.Radio('No Loop', 'LOOP', default=True)], 
            [sg.Radio('Loop Full', 'LOOP', default=False)],
            [sg.Radio('Loop Between', 'LOOP', default=False)],
            [sg.Text('Start'), sg.Input(size=(10,1), key='-LOOPSTART-'), sg.Text('End'), sg.Input(size=(10,1), key='-LOOPEND-')]
            ])
    ]]

    return sg.Window('Audio Looper', layout)

#Set flags for song status
global song_loaded, playing, paused
song_loaded, playing, paused = False, False, True

#Pause/Unpause function
def playpause(song_loaded, is_playing, is_paused):
    global playing, paused
    playing, paused = is_playing, is_paused
    if song_loaded == True:
        if playing == False:
            pygame.mixer.music.play()
            window['-PLAY/PAUSE-'].update(image_filename = 'buttons/pause.png')
            playing = True
            paused = False
        else:
            if paused == True:
                pygame.mixer.music.unpause()
                paused = False
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/pause.png')
            else:
                pygame.mixer.music.pause()
                paused = True
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')


#Function for adjusting the volume
def set_volume(volume):
    adjusted_volume = volume / 100
    pygame.mixer.music.set_volume(adjusted_volume)

#Function for converting the time into hours:mins:secs:milli
def clock_time(time):
    milliseconds = int((time - int(time))*100)
    secondsonly = int(time)
    if secondsonly >= 60:
        seconds = int(secondsonly % 60)
        minutesonly = (secondsonly - seconds) / 60
        if minutesonly >= 60:
            minutes = int(minutesonly % 60)
            hours = int((minutesonly - minutes) /60)
        else:
            hours = 0
            minutes = int(minutesonly)
    else:
        hours = 0
        minutes = 0
        seconds = secondsonly

    return f'{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:02}'

#Creates a window with the given theme using the function above
window = create_window('GrayGrayGray')


#Standard pysimplegui update loop
while True:
    event, values = window.read(timeout=10)

    #Draws the scope and lines for the loop start and loop end poiints
    window['-SCOPE-'].erase()
    scope_image = window['-SCOPE-'].DrawImage(filename='scope_image.png', location=(0,1))
    loop_start_scope = window['-SCOPE-'].DrawLine((values['-LOOPSTART-'],0), (values['-LOOPSTART-'],1), color='blue', width=3)
    loop_end_scope = window['-SCOPE-'].DrawLine((values['-LOOPEND-'],0), (values['-LOOPEND-'],1), color='blue', width=3)


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
            window['-SONGLENGTH-'].update(clock_time(song_length))

    #Runs the play pause function when the button is pressed
    if event == '-PLAY/PAUSE-':
        playpause(song_loaded, playing, paused)
    
    #Stops the music and resets flags, etc. when stop is pressed (REWORK INTO A FUNCTION?)
    if event == '-STOP-':
        pygame.mixer.music.stop()
        playing = False
        paused = True
        window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')
        window['-CURRENTTIME-'].update('00:00:00:00')
        window['-PLAYBACK-'].update(0)

    #Sets the behavior for the skip forward and skip back buttons (NOT YET FUNCTIONAL)
    if event == '-3BACK-':
        pass

    if event == '-3FORWARD-':
        pass
    
    #Updates certain params when a song is loaded. Updates additional params when the song starts playing
    if song_loaded == True:
        set_volume(values['-VOLUME-'])
        loop_start = (values['-LOOPSTART-'] / 3000) * song_length
        window['-STARTTIMEDISPLAY-'].update(loop_start)
        loop_end = (values['-LOOPEND-'] / 3000) * song_length
        window['-ENDTIMEDISPLAY-'].update(loop_end)
        if playing == True:
            current_time = pygame.mixer.music.get_pos() / 1000
            window['-CURRENTTIME-'].update(clock_time((current_time)))
            seek_bar = (current_time / song_length) * 3000
            window['-PLAYBACK-'].update(seek_bar)
            scope_line = window['-SCOPE-'].DrawLine((seek_bar,0), (seek_bar,1), color='red', width=3)

            if current_time <= 0:
                playing = False
                paused = True
                window['-PLAY/PAUSE-'].update(image_filename = 'buttons/play.png')
                window['-CURRENTTIME-'].update('00:00:00:00')
            
       
window.close()

#TO DO:
#get seek bar to work
#get skip buttons to work
#get scope working
#cut at loop position and loop song
#set full loop and custom loop settings
#add arrows to more precisely adjust loop time
#resize buttons
#change loop settings layout
#add extra themes
#add export for loops and loop data