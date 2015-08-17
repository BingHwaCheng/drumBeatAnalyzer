# utility: provides supporting functions to drumBeatAnalyzer

# Copyright (c) 2015 Bing Hwa Cheng

import numpy
import wave
import struct
import pyaudio
import sys
import math

# global parameters
string_beat_1 = ["        ", "_       ", "  _     ", "___     ", "    _   ", "_____   ", "  ___   ", "_____   ", 
                 "      _ ", "_______ ", "  _____ ", "_______ ", "    ___ ", "_______ ", "  _____ ", "_______ "]
                  
string_beat_2 = ["        ", "|       ", "  |     ", "| |     ", "    |   ", "|   |   ", "  | |   ", "| | |   ", 
                 "      | ", "|     | ", "  |   | ", "| |   | ", "    | | ", "|   | | ", "  | | | ", "| | | | "]
                  
                  
string_beat_3 = ["        ", "o       ", "  o     ", "o o     ", "    o   ", "o   o   ", "  o o   ", "o o o   ",
                 "      o ", "o     o ", "  o   o ", "o o   o ", "    o o ", "o   o o ", "  o o o ", "o o o o "]

# -------------------------------------------
# print drum beat score
# -------------------------------------------
def printScore(beat_loc_float, beat_error): 
    max_len = int(numpy.amax(beat_loc_float))

    beat_loc = []
    for n in range(len(beat_loc_float)):
        beat_loc.append(int(beat_loc_float[n]))
    
    # print snare
    beat_snare = []
    for n in range(((max_len+3)/4)*4):
        beat_snare.append(0)

    for n in beat_loc:
        beat_snare[n-1] = 1

    string_print_0 = ""
    string_print_1 = ""
    string_print_2 = ""
    string_print_3 = ""
    string_print_4 = ""

    for n in range(8):
        string_print_0 += ".       "
    
    for n in range((max_len+3)/4):
        print_index = beat_snare[4*n] + 2*beat_snare[1+4*n] + 4*beat_snare[2+4*n] + 8*beat_snare[3+4*n]
        string_print_1 += string_beat_1[print_index]
        string_print_2 += string_beat_2[print_index]
        string_print_3 += string_beat_3[print_index]

    
    snare_cnt = 0
    for n in range(((max_len+3)/4)*4):
        if beat_snare[n] == 1:
            if beat_error[snare_cnt] > -0.25 and beat_error[snare_cnt] < 0.25:
                string_print_4 += "C "
            elif beat_error[snare_cnt] < -0.25:
                string_print_4 += "E "
            elif beat_error[snare_cnt] > 0.25:
                string_print_4 += "L "
            snare_cnt = snare_cnt + 1
        else:
            string_print_4 += "  "
    
    print string_print_0
    print string_print_1
    print string_print_2
    print string_print_3
    print string_print_4
    
    return string_print_0+"\n"+string_print_1+"\n"+string_print_2+"\n"+string_print_3+"\n"+string_print_4

# -------------------------------------------
# get default (empty) score
# -------------------------------------------
def getDefaultScore():

    string_print_0 = ""
    string_print_1 = ""
    string_print_2 = ""
    string_print_3 = ""
    string_print_4 = ""
    for n in range(8):
        string_print_0 += ".       "
    
    return string_print_0+"\n"+string_print_1+"\n"+string_print_2+"\n"+string_print_3+"\n"+string_print_4

# -------------------------------------------
# save the recording into wav file
# -------------------------------------------
def saveWavFile(samp_width, sampling_rate, decoded):
    wf = wave.open("drum_beat_recording.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(samp_width)
    wf.setframerate(sampling_rate)
    temp_out = ''.join(struct.pack('h', samp) for samp in decoded)
    wf.writeframes(temp_out)
    wf.close()
    
# -------------------------------------------
# play the recorded wav file
# -------------------------------------------
def playWavFile(sampling_rate, block_size):
    wf = wave.open("drum_beat_recording.wav", 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sampling_rate,
                    output=True)

    data = wf.readframes(block_size)

    while data != '':
        stream.write(data)
        data = wf.readframes(block_size)

    stream.stop_stream()
    stream.close()

    p.terminate()
    
# -------------------------------------------
# compute Hamming window
# -------------------------------------------
def getHammingWindow(length):
    w = []
    for n in range(length):
        w.append( 0.54 - 0.46*math.cos(2*math.pi*n/length) )
    return w

# -------------------------------------------
# compute low pass filter
# -------------------------------------------
def getLowPassFilter(fc, Fs, N):
    w = getHammingWindow(N)
    wc = 2*math.pi*fc/Fs
    h = []
    for n in range(N):
        if n == N/2:
            h.append( wc/math.pi )
        else:
            h.append( math.sin(wc*(n-N/2))/(math.pi*(n-N/2))*w[n] )
    return h






    