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
def printScore(beat_loc, beat_error, level): 

    # level vs error threshold
    if level == 1: 
        error_thres = 0.10 # expert
    elif level == 2:
        error_thres = 0.15 # normal
    else:
        error_thres = 0.20 # easy
    
    # beginning
    string_print_0 = "  "
    string_print_1 = "| "
    string_print_2 = "| "
    string_print_3 = "| "
    string_print_4 = "  "


    for n in range(8):
        
        # top row
        string_print_0 += str(n%4+1)+" . . . "
        
        # beat notation
        print_index = beat_loc[4*n] + 2*beat_loc[1+4*n] + 4*beat_loc[2+4*n] + 8*beat_loc[3+4*n]
        string_print_1 += string_beat_1[print_index]
        string_print_2 += string_beat_2[print_index]
        string_print_3 += string_beat_3[print_index]
    
        
        for m in range(4):
            if beat_loc[m+4*n] == 1:
                if beat_error[m+4*n] > -error_thres and beat_error[m+4*n] < error_thres:
                    string_print_4 += "C "
                elif beat_error[m+4*n] < -error_thres:
                    string_print_4 += "E "
                elif beat_error[m+4*n] > error_thres:
                    string_print_4 += "L "
            else:
                string_print_4 += "  "
        
        # middle
        if n==3:
            string_print_0 += "   "
            string_print_1 += " | "
            string_print_2 += " | "
            string_print_3 += " | "
            string_print_4 += "   "
            
    # ending
    string_print_0 += "  "
    string_print_1 += " |"
    string_print_2 += " |"
    string_print_3 += " |"
    string_print_4 += "  "
    
    print string_print_0
    print string_print_1
    print string_print_2
    print string_print_3
    print string_print_4
    
    return [string_print_0+"\n"+string_print_1+"\n"+string_print_2+"\n"+string_print_3, string_print_4]

# -------------------------------------------
# get default (empty) score
# -------------------------------------------
def getDefaultScore():

    # beginning
    string_print_0 = "  "
    string_print_1 = "| "
    string_print_2 = "| "
    string_print_3 = "| "
    string_print_4 = "  "
    
    for n in range(8):
        string_print_0 += str(n%4+1)+" . . . "
        string_print_1 += "        "
        string_print_2 += "        "
        string_print_3 += "        "
        string_print_4 += "        "
        # middle
        if n==3:
            string_print_0 += "   "
            string_print_1 += " | "
            string_print_2 += " | "
            string_print_3 += " | "
            string_print_4 += "   "
    
    # ending
    string_print_0 += "  "
    string_print_1 += " |"
    string_print_2 += " |"
    string_print_3 += " |"
    string_print_4 += "  "
    
    return [string_print_0+"\n"+string_print_1+"\n"+string_print_2+"\n"+string_print_3, string_print_4]

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






    