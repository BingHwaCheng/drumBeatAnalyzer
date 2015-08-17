# metronome: provides audio samples for metronome

# Copyright (c) 2015 Bing Hwa Cheng

"""
The metronome class provides audio samples for metronome with specified 
BPM (beat per minute) and sampling rate (44.1 kHz in most cases). The 
method get_samples returns block_size samples each time it is called. 

"""

import math

# -------------------------------------------
# global parameters
# -------------------------------------------
pulse_duration = 512
freq_arr       = [2000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
amp_arr        = [1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5]

freq_arr_start = [2000, 2000, 2000, 2000, 2000, 2000, 2000, 2000]
amp_arr_start  = [1, 0, 1, 0, 1, 1, 1, 1]

class metronome:
    def __init__(self, bpm, sampling_rate, block_size):
        # passed in parameters
        self.bpm = bpm
        self.sampling_rate = sampling_rate
        self.block_size = block_size
        
        # derived parameters
        self.pulse_interval = int(60*sampling_rate/bpm/2)
        
        # initializing state parameters
        self.pulse_active = 0
        self.pulse_sample_cnt = 0
        self.beat_cnt = 0
        self.rd_ptr = 0
    
    def get_samples(self):
        temp = []
        for m in range(self.block_size):
            # check for condition if metronome pulse is active
            if self.rd_ptr >= self.pulse_interval and self.pulse_active == 0:
                self.pulse_active = 1
                self.rd_ptr = 0
                    
            self.rd_ptr = self.rd_ptr+1
            if self.pulse_active == 1:
                # metronome sample is active, prepare audio samples (tone)
                if self.beat_cnt < 8:
                    amp = amp_arr_start[self.beat_cnt%8]
                    freq = freq_arr_start[self.beat_cnt%8]
                elif self.beat_cnt < 24:
                    amp = amp_arr[self.beat_cnt%8]
                    freq = freq_arr[self.beat_cnt%8]
                else:
                    amp = 0
                    freq = freq_arr[self.beat_cnt%8]
                    
                    
                temp.append(int(amp*math.sin(self.pulse_sample_cnt/((self.sampling_rate/freq)/math.pi))*32767))
                self.pulse_sample_cnt = self.pulse_sample_cnt + 1
                if self.pulse_sample_cnt > pulse_duration:
                    self.pulse_sample_cnt = 0
                    self.pulse_active = 0
                    self.beat_cnt = self.beat_cnt + 1
            else:
                # metronome sample is inactive, append zeros
                temp.append(0)
        
        return temp
        
    