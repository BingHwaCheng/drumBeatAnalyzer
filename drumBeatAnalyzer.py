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
is_capture_active = 0
raw_sample_buffer = []
rd_ptr            = 0
wr_ptr            = 0
score_text        = ""

# -------------------------------------------------
# beat tracking start
# -------------------------------------------------
def startAudio(bpm, sensitivity):

    global is_capture_active, raw_sample_buffer, rd_ptr, wr_ptr, score_text
    
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

    # initialize audio proc
    ap = audioProcessing(bpm, sensitivity/100.0)
    
    # initialize capture parameters
    raw_sample_buffer = []
    wr_ptr = 0
    rd_ptr = 0
    
    # clear text field
    score_text = getDefaultScore()
    var_1.set(score_text)
    label_1.update_idletasks()
    
    # start audio processing thread
    thread.start_new_thread(audioProcThread, (ap,))
    
    # start playing and recording
    frames = []
    rec_wav = numpy.array([])
    is_capture_active = 1
    
    for n in range(sampling_rate*total_num_beats*60/bpm/block_size):

        # write metronome samples to audio output
        temp=metro.get_samples()
        data_out = ''.join(struct.pack('h', samp) for samp in temp)
        stream.write(data_out, block_size)
     
        # read audio input
        data = stream.read(block_size)
        
        # skip the beginning
        if n<sampling_rate*3.5*60/bpm/block_size:
            continue
        
        temp_data = numpy.fromstring(data, 'Int16');
        rec_wav = numpy.concatenate([rec_wav, temp_data]);
        frames.append(data)
        
        for m in range(block_size):
            raw_sample_buffer.append(temp_data[m])
        wr_ptr = wr_ptr + 1
        
        var_1.set(score_text)
        label_1.update_idletasks()
        
    
    # ends capture
    is_capture_active = 0

    # final update
    var_1.set(score_text)
    label_1.update()
        
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
    global is_capture_active, raw_sample_buffer, rd_ptr, wr_ptr, score_text

    num_peak_detected = 0
    while is_capture_active == 1:
        if rd_ptr != wr_ptr:
            temp_data = []
            for n in range(block_size):
                temp_data.append(raw_sample_buffer[n + rd_ptr*block_size])
            peak_found = ap.audioSampleProcessing(temp_data)
            rd_ptr = rd_ptr + 1
        
            if peak_found == 1:
                beat_loc_float = ap.getBeatLoc()
                beat_error = ap.getBeatError()
                energy_type = ap.getEnergyTypeArr()
                score_text = printScore(beat_loc_float, beat_error)
            
    print "audio processing thread terminated"
    
# -------------------------------------------------
# GUI handler function for start beat tracking
# -------------------------------------------------
def startAudioGUI():
    print "start audio playing/recording!!!" ;
    print "sens = " + str(var_sens.get())+ ", bpm = " + str(var_bpm.get())
    startAudio(var_bpm.get(), var_sens.get())
    
# -------------------------------------------------
# GUI handler function for audio replay
# -------------------------------------------------
def replayAudio():
    print "replay audio!!!";
    playWavFile(sampling_rate, block_size)

# -------------------------------------------------
# GUI main function
# -------------------------------------------------
root = Tk()

# top frame: score text
topframe = Frame(root)
topframe.pack()
var_1 = StringVar()
var_1.set(getDefaultScore())
label_1 = Label(topframe, textvariable=var_1, width=80, height=7, font="Menlo 18 bold", relief=RAISED, justify=LEFT)
label_1.grid(row=0, column=1)

# bottom frame: buttons and scales
bottomframe = Frame(root)
bottomframe.pack()

# BPM
var_bpm = IntVar()
var_bpm.set(90)
scale_bpm=Scale(bottomframe, label="BPM", variable=var_bpm, orient=HORIZONTAL, from_=60, to=140)
scale_bpm.grid(row=0, column=0)

# sensitivity
var_sens = IntVar()
var_sens.set(5)
scale_sens=Scale(bottomframe, label="SENSITIVITY", variable=var_sens, orient=HORIZONTAL, from_=0, to=10)
scale_sens.grid(row=0, column=1)

# start
button_start = Button(bottomframe, text="START", width=6, command=startAudioGUI)
button_start.grid(row=0, column=2)

# replay
button_replay = Button(bottomframe, text="REPLAY", width=6, command=replayAudio)
button_replay.grid(row=0, column=3)

root.mainloop()


