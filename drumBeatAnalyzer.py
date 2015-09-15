# drumBeatAnalyzer: main program for drum beat analyzer, including
#                   audio playing (metronome), audio recording, and
#                   GUI for BPM setting and drum beat display

# Copyright (c) 2015 Bing Hwa Cheng

import math
import pyaudio
import wave
import numpy
import struct
import thread
from Tkinter import *
from metronome import *
from audioProcessing import *
from utility import playWavFile
from utility import printScore
from utility import getDefaultScore
from utility import saveWavFile

# -------------------------------------------------
# global variables
# -------------------------------------------------
# constants
sampling_rate = 44100
block_size    = 4096

# shared between functions/threads
is_audio_play_active = 0
is_capture_active    = 0
raw_sample_buffer    = []
rd_ptr               = 0
wr_ptr               = 0
score_text           = ""
result_text          = ""

# -------------------------------------------------
# beat tracking start
# -------------------------------------------------
def startAudio(bpm):

    global is_capture_active, raw_sample_buffer, rd_ptr, wr_ptr, score_text, is_audio_play_active
        
    # system parameters
    total_num_beats = 15 # capture length in number of 4th note
    pyaudio_format = pyaudio.paInt16
    
    # initialize pyaudio
    p = pyaudio.PyAudio()
    stream = p.open(format = pyaudio_format, 
                    channels = 1, 
                    rate = sampling_rate, 
                    input = True,
                    output = True, 
                    frames_per_buffer=block_size)

    # initialize metronome
    metro = metronome(bpm, sampling_rate, block_size)
    
    # start playing and recording
    frames = []
    rec_wav = numpy.array([])
    is_capture_active = 1
    
    #for n in range(sampling_rate*total_num_beats*60/bpm/block_size):
    while is_audio_play_active:
    
        # write metronome samples to audio output
        temp=metro.get_samples()
        data_out = ''.join(struct.pack('h', samp) for samp in temp)
        stream.write(data_out, block_size)
     
        # read audio input
        data = stream.read(block_size)
        
        # skip the beginning
        #if n<sampling_rate*3.5*60/bpm/block_size:
        #    continue
        
        temp_data = numpy.fromstring(data, 'Int16');
        rec_wav = numpy.concatenate([rec_wav, temp_data]);
        frames.append(data)
        
        for m in range(block_size):
            raw_sample_buffer[m + wr_ptr*block_size] = temp_data[m]
        wr_ptr = (wr_ptr + 1)%128
    
    # ends capture
    is_capture_active = 0
        
    # terminate pyaudio
    stream.stop_stream()
    stream.close()
    p.terminate()

    # save recording in wav file
    saveWavFile(p.get_sample_size(pyaudio_format),
                sampling_rate,
                rec_wav)
        
# -------------------------------------------------
# start audio processing thread
# -------------------------------------------------
def audioProcThread(ap):
    global is_capture_active, raw_sample_buffer, rd_ptr, wr_ptr, score_text, result_text

    num_peak_detected = 0
    while is_capture_active == 1:
        if rd_ptr != wr_ptr:
            temp_data = []
            for n in range(block_size):
                temp_data.append(raw_sample_buffer[n + rd_ptr*block_size])
            peak_found = ap.audioSampleProcessing(temp_data)
            rd_ptr = (rd_ptr + 1)%128
        
            # peak detected, update score_text
            if peak_found > 0:
                beat_loc   = ap.getBeatLoc()
                beat_error = ap.getBeatError()
                score_text, result_text = printScore(beat_loc, beat_error, var_level.get())
            
    print "audio processing thread terminated"
    
# -------------------------------------------------
# GUI handler function for start beat tracking
# -------------------------------------------------
def startAudioGUI():
    global is_audio_play_active, score_text, result_text, raw_sample_buffer, rd_ptr, wr_ptr
    print "start audio playing/recording!!!" ;
    print "sens = " + str(var_sens.get())+ ", bpm = " + str(var_bpm.get())
    
    
    if is_audio_play_active == 1: 
        return # return immediately if audio play is already active
    else:    
        is_audio_play_active = 1
    
    
    # initialize raw_sample_buffer and rd/wr ptrs
    raw_sample_buffer = []
    for n in range(128*block_size):
        raw_sample_buffer.append(0)
    rd_ptr = 0
    wr_ptr = 0
    
    # clear text field
    score_text, result_text = getDefaultScore()
    var_1.set(score_text)
    var_2.set(result_text)
    label_1.update_idletasks()

    # start audio thread
    thread.start_new_thread(startAudio, (var_bpm.get(),) )

    # initialize audio proc and start audio processing thread
    ap = audioProcessing(var_bpm.get(), (10-var_sens.get()+1)/100.0)
    thread.start_new_thread(audioProcThread, (ap,))
    
# -------------------------------------------------
# GUI handler function for stop audio
# -------------------------------------------------
def stopAudioGUI():
    global is_audio_play_active
    print "stop audio!!!";
    is_audio_play_active = 0

def pull_score_text():
    global score_text, result_text
    var_1.set(score_text)
    label_1.update_idletasks()
    
    var_2.set(result_text)
    label_2.update_idletasks()
    
    label_1.after(100, pull_score_text)
    

# -------------------------------------------------
# GUI main function
# -------------------------------------------------
root = Tk()    
root.title("drumBeatAnalyzer");

# -------------------------------------------------
# top, middle and bottom frames
# -------------------------------------------------
topframe = Frame(root)
topframe.pack()
middleframe = Frame(root)
middleframe.pack()
bottomframe = Frame(root)
bottomframe.pack()

# -------------------------------------------------
# top frame: score text
# -------------------------------------------------
score_text, result_text = getDefaultScore()

var_1 = StringVar()
var_1.set(score_text)
label_1 = Label(topframe, textvariable=var_1, width=75, height=4, font="Menlo 18 bold", relief=RIDGE, justify=LEFT, bg="grey")
label_1.grid(row=0, column=0, padx=10, pady=6, ipady=5)

# clear text field
var_1.set(score_text)
label_1.update_idletasks()

# -------------------------------------------------
# mid frame: result
# -------------------------------------------------
var_2 = StringVar()
var_2.set(result_text)
label_2 = Label(middleframe, textvariable=var_2, width=75, height=1, font="Menlo 18 bold", relief=RIDGE, justify=LEFT, bg="grey")
label_2.grid(row=0, column=0, padx=10)


# -------------------------------------------------
# bottom left: BPM and sensitivity slide bars
# -------------------------------------------------
bottomLeft = Frame(bottomframe)
bottomLeft.grid(row=0, column=0)

# BPM
var_bpm = IntVar()
var_bpm.set(90)
scale_bpm=Scale(bottomLeft, label="BPM", variable=var_bpm, orient=HORIZONTAL, from_=60, to=140, font="Menlo 16 bold", activebackground="white")
scale_bpm.grid(row=0, column=0, padx=20, pady=4, ipadx=20)

# sensitivity
var_sens = IntVar()
var_sens.set(8)
scale_sens=Scale(bottomLeft, label="SENSITIVITY", variable=var_sens, orient=HORIZONTAL, from_=0, to=10, font="Menlo 16 bold", activebackground="white")
scale_sens.grid(row=0, column=1, padx=20, pady=4, ipadx=10)


# -------------------------------------------------
# bottom mid: Levels
# -------------------------------------------------
bottomMid = Frame(bottomframe)
bottomMid.grid(row=0, column=1)

# level
message_level = Message(bottomMid, text="LEVEL", font="Menlo 16 bold", width=100);
message_level.grid(row=0, column=0, ipadx=30);

var_level = IntVar()
var_level.set(2)
rbutton_level_expert = Radiobutton(bottomMid, text="EXPERT", variable=var_level, value=1, font="Menlo 14", anchor=W, selectcolor="green")
rbutton_level_normal = Radiobutton(bottomMid, text="NORMAL", variable=var_level, value=2, font="Menlo 14", anchor=W)
rbutton_level_easy = Radiobutton(bottomMid, text="EASY", variable=var_level, value=3, font="Menlo 14", anchor=W)

rbutton_level_expert.grid(row=1, column=0)
rbutton_level_normal.grid(row=1, column=1)
rbutton_level_easy.grid(row=1, column=2, padx=20)

# -------------------------------------------------
# bottom right: start and stop
# -------------------------------------------------
bottomRight = Frame(bottomframe)
bottomRight.grid(row=0, column=2)

# start
button_start = Button(bottomRight, text="START", width=6, command=startAudioGUI, font="Menlo 20 bold", fg="green")
button_start.grid(row=0, column=0, ipadx=4, ipady=7, padx=8, pady=10)

# stop
button_stop = Button(bottomRight, text="STOP", width=6, command=stopAudioGUI, font="Menlo 20 bold", fg="red")
button_stop.grid(row=0, column=1, ipadx=4, ipady=7, padx=8, pady=10)


# -------------------------------------------------
# pull score text
# -------------------------------------------------
pull_score_text()
        
root.mainloop()


