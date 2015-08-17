# audioProcessing: main program for envelop extraction, 
#                  short-time FFT, and peak picking

# Copyright (c) 2015 Bing Hwa Cheng

import math
import numpy
from utility import getHammingWindow
from utility import getLowPassFilter

class audioProcessing:
    # -------------------------------------------
    # class variables shared by all instances
    # -------------------------------------------
    # low pass filter
    fc          = 5;  # in Hz
    N_tap       = 16

    # short time FFT params
    Fs          = 44100.0
    block_size  = 4096
    N_fft       = 2048
    N_step      = 256
    
    # peak picking params
    t2          = 0  # this is dynamic threshould, computed based on neighboring samples
    lambda_peak = 0.4
    t_size      = 40
    t_inp_size  = block_size/N_step

    # -------------------------------------------
    # initialization
    # -------------------------------------------
    def __init__(self, bpm, t1):
    
        # reset number of iteration
        self.iter = 0
        
        # get window for FFT
        self.w_sm = getHammingWindow(self.N_fft)
    
        # get low pass filter tap coefficient
        self.h_lp = getLowPassFilter(self.fc, self.Fs/self.N_step, self.N_tap)
        
        # initialize sample buffers
        self.s_in_buffer = []
        for n in range(4*self.block_size):
            self.s_in_buffer.append(0)    
            
        self.s_env_buffer = []
        for n in range(5*self.t_inp_size):
            self.s_env_buffer.append(0)
            
        self.h_lp_state = []
        for n in range(self.N_tap):
            self.h_lp_state.append(0)

        # compute beat duration (4-th note)
        self.beat_duration = 60.0/bpm/4*self.Fs/self.N_step;
        
        # peak picking params
        self.peak_loc     = []
        self.beat_loc     = []
        self.energy_type  = []
        self.conf_meas    = []
        self.beat_error   = []
        self.t1           = t1 # threshold for peak picking
        self.num_peaks    = 0
        self.peak_loc_raw = 0
        
    # -------------------------------------------
    # audio sample processing
    # -------------------------------------------
    def audioSampleProcessing(self, s):
            
        # increment iteration count
        self.iter = self.iter + 1
        
        # fill s_in_buffer
        for n in range(3*self.block_size):
            self.s_in_buffer[n] = self.s_in_buffer[self.block_size+n]
        for n in range(self.block_size):
            self.s_in_buffer[3*self.block_size+n] = s[n]/32768.0
        
        # wait until buffer is full
        if self.iter < 4:
            return 0 

        # STFT
        s_env = self.getShortTimeFFT()
        
        # low pass filtering
        s_env_lp = self.getLowPassFiltering(s_env)
        
        # fill in s_env_buffer
        for n in range(4*self.t_inp_size):
            self.s_env_buffer[n] = self.s_env_buffer[self.t_inp_size+n]
        for n in range(self.t_inp_size):
            self.s_env_buffer[4*self.t_inp_size+n] = s_env_lp[n]
        
        # wait until buffer is full 
        if self.iter < 5:
            return 0
        
        # peak picking
        peak_found = self.getPeak()
        
        return peak_found
        
    # -------------------------------------------
    # short time FFT
    # -------------------------------------------
    def getShortTimeFFT(self):
        
        s_env = []
        for n in range(self.block_size/self.N_step):
            # apply window
            s_win = []
            for m in range(self.N_fft):
                temp_s = self.s_in_buffer[2*self.block_size + m + n*self.N_step]
                s_win.append( temp_s * self.w_sm[m] )
            # FFT
            s_fft = abs(numpy.fft.fft(s_win))
            
            # get low freq components
            # summation of FFT bins from 0 to 49, 
            # this corresponds to 0 to 1076 Hz with
            # sampling rate of 44.1k and 2048-point FFT 
            temp_accum = 0
            for m in range(50):
                temp_accum = temp_accum + s_fft[m]
            
            s_env.append(temp_accum / self.N_fft)
        
        return s_env
        
    # -------------------------------------------
    # low pass filtering
    # -------------------------------------------
    def getLowPassFiltering(self, s_env):
    
        s_env_lp = []
        for n in range(self.block_size/self.N_step):
            # update filter state
            for m in range(1,self.N_tap):
                self.h_lp_state[self.N_tap-m] = self.h_lp_state[self.N_tap-m-1]
            self.h_lp_state[0] = s_env[n]
            
            # filtering
            temp_accum = 0
            for m in range(self.N_tap):
                temp_accum = temp_accum + self.h_lp[m] * self.h_lp_state[m]
            s_env_lp.append(temp_accum)
        
        return s_env_lp
    
    # -------------------------------------------
    # peak picking
    # -------------------------------------------
    def getPeak(self):
    
        peak_found = 0
        for n in range(3*self.t_inp_size, 4*self.t_inp_size):
            # skip if sample is less than t1
            if (self.s_env_buffer[n] < self.t1):
                continue
            
            # skip if sample is not a peak
            if (self.s_env_buffer[n] < self.s_env_buffer[n-1] or
                self.s_env_buffer[n] < self.s_env_buffer[n+1]):
                continue
            
            # dynamic threshold checking (t2)
            temp_accum = 0
            for m in range(self.t_size):
                temp_accum = temp_accum + self.s_env_buffer[n-self.t_size+m]
            t2 = temp_accum/self.t_size
            
            if self.s_env_buffer[n] < self.t1 + t2*self.lambda_peak:
                continue
            
            # peak found!
            peak_found = 1
            self.peak_loc_raw = n - 3*self.t_inp_size
            self.peak_loc.append(n + self.iter*self.t_inp_size - 112)
            self.num_peaks = self.num_peaks + 1
             
            if self.num_peaks > 1:
                temp_duration = self.peak_loc[self.num_peaks-1] - self.peak_loc[0]
                self.beat_loc.append( round(temp_duration/self.beat_duration) + self.beat_loc[0] ) 
                self.beat_error.append( temp_duration/self.beat_duration - self.beat_loc[self.num_peaks-1] + 1)
            else: 
                self.beat_loc.append(1.0)
                self.beat_error.append(0)
            
            if peak_found == 1:
                print "peak found!!!"
                print self.beat_loc
                self.energy_type.append(1)
                break
        
        return peak_found    
    
    # -------------------------------------------
    # get beat_loc
    # -------------------------------------------
    def getBeatLoc(self):
        return self.beat_loc
    
    # -------------------------------------------
    # get beat_error
    # -------------------------------------------
    def getBeatError(self):
        return self.beat_error
    
    # -------------------------------------------
    # get energy_type array
    # -------------------------------------------
    def getEnergyTypeArr(self):
        return self.energy_type
    

    