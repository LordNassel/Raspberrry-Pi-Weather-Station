#!/usr/bin/env python2

import RPi.GPIO as GPIO
from random import randrange
import time
import pyaudio
import wave
from scipy.signal import butter, lfilter, freqz
import matplotlib
#matplotlib.use("GTK") #uncomment when plotting
import matplotlib.pyplot as plt
import numpy as np
import sys

# How many bytes of audio to read at a time
CHUNK = 512

class LedController:
    def __init__(self, pin_nums):
        # pin_nums is an R, G, B tuple

        # Initial setup of GPIO pins
        GPIO.setmode(GPIO.BCM)

        # Set each pin as an output and create a pwm
        # instance
        self.pins = []
        for p in pin_nums:
            GPIO.setup(p, GPIO.OUT)
            # Create a pwm instance for the pin at a
            # frequency of 200Hz
            self.pins.append(GPIO.PWM(p, 200))
            # Set each pin to a random brightness to
            # begin with
            self.pins[-1].start(randrange(0, 100))

    def set_colour(self, colour_tuple):
        # Takes a colour tuple in the form (R, G, B)
        # where the values are from 0 to 255 > 255 is
        # capped

        for i in range(0, 3):
            # Scale 0 to 255 to a percentage
            scaled = int(colour_tuple[i] * 
                         (100.0/255.0))

            # Ensure we are giving correct values
            if scaled < 0:
                scaled = 0.0
            elif scaled > 100:
                scaled = 100.0

            #print "{0}: {1}".format(i ,scaled)
            self.pins[i].ChangeDutyCycle(scaled)

    def test(self):
        # Change to a random colour
        while True:
            r = randrange(0, 256)
            g = randrange(0, 256)
            b = randrange(0, 256)
            self.set_colour((r, g, b))
            time.sleep(1)

class FreqAnalyser:
    # Filtering based on
    # http://wiki.scipy.org/Cookbook/ButterworthBandpass
    
    def __init__(self, channels, sample_rate, leds=None):
        self.leds = leds # Not needed if just plotting
        self.channels = channels
        self.sample_rate = sample_rate
        self.nyquist = float(sample_rate) / 2

        # Filter order - higher the order the sharper
        # the curve
        order = 3

        # Cut off frequencies:
        # Low pass filter
        cutoff = 200 / self.nyquist
        # Numerator (b) and denominator (a)
        # polynomials of the filter. 
        b, a = butter(order, cutoff, btype='lowpass')
        self.low_b = b
        self.low_a = a

        # High pass filter
        cutoff = 4000 / self.nyquist
        b, a = butter(order, cutoff, btype='highpass')
        self.high_b = b
        self.high_a = a
        
        # Keep track of max brightness for each
        # colour
        self.max = [0.0, 0.0, 0.0]
        # Make different frequencies fall faster
        # bass needs to be punchy.
        self.fall = [15.0, 2.5, 5.0]
    
    def filter(self, data):
        # Apply low filter
        self.low_data = lfilter(self.low_b,
                                self.low_a,
                                data)

        # Apply high filter
        self.high_data = lfilter(self.high_b,
                                 self.high_a,
                                 data)
 
        # Get mid data by doing signal - (low + high)
        self.mid_data = np.subtract(data,
                        np.add(self.low_data,
                               self.high_data))

    @staticmethod
    def rms(data):
        # Return root mean square of data set
        # (i.e. average amplitude)
        return np.sqrt(np.mean(np.square(data)))

    def change_leds(self):
        # Get average amplitude
        l = []
        l.append(self.rms(self.low_data))
        l.append(self.rms(self.mid_data))
        l.append(self.rms(self.high_data))

        # These values are floating point from 0 to 1
        # and our led values go to 255 
        divval = 1.0/255

        for i in range(0, 3):
            l[i] = l[i] / divval
        
        # Do any number fudging to make it look better
        # here - probably want to avoid high values of
        # all because it will be white
        l[0] *= 2 # Emphasise bass
        l[1] /= 2 # Reduce mids
        l[2] *= 5 # Emphasise treble
        #print l

        for i in range(0, 3):
            # First cap all at 255
            if l[i] > 255.0:
                l[i] = 255.0

            # Use new val if > previous max
            if l[i] > self.max[i]:
                self.max[i] = l[i]
            else:
                # Otherwise, decrement max and use that
                # Gives colour falling effect
                self.max[i] -= self.fall[i]
                if self.max[i] < 0:
                    self.max[i] = 0
                l[i] = self.max[i]

        self.leds.set_colour(l)

    def plot_response(self):
        # Frequency response of low and high pass
        # filters. Borrowed from
        # http://wiki.scipy.org/Cookbook/ButterworthBandpass
        plt.figure(1)
        plt.clf()
        w, h = freqz(self.low_b,
                     self.low_a,
                     worN=20000)
        plt.plot((self.nyquist / np.pi) * w,
                 abs(h), label="Low Pass")

        w, h = freqz(self.high_b,
                     self.high_a,
                     worN=20000)
        plt.plot((self.nyquist / np.pi) * w,
                 abs(h), label="High Pass")

        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Gain')
        plt.grid(True)
        plt.legend(loc='best')
        plt.xscale('log')
        plt.show()
        # Exit at after showing the plot. Only to
        # verify frequency response
        sys.exit()

class AudioController:
    def __init__(self, filename, leds):
        if filename == 'line-in':
            self.line_in = True
        else:
            self.line_in = False
            self.wf = wave.open(filename)

        self.leds = leds
        self.p = pyaudio.PyAudio()
    
    @staticmethod
    def get_left(data):
        # Return the left channel of stereo audio
        data = np.reshape(data, (CHUNK, 2))
        return data[:, 0]
    
    def more(self):
        if self.line_in:
            try:
                # Return line in data
                return self.stream.read(CHUNK)
            except:
                print "line-in error"
                return 'ab'
        else:
            # Read data from wav file
            return self.wf.readframes(CHUNK)

    def analyse(self, data):
        # Convert to numpy array and filter
        data = np.fromstring(data, dtype=np.int16)

        # If stereo only work on left side
        if self.channels == 2:
            data = self.get_left(data)

        # Convert int16 to float for dsp
        data = np.float32(data/32768.0)

        # Send to filter
        self.analyser.filter(data)

        self.analyser.change_leds()

    def play_setup(self):
        # Assume 16 bit wave file either mono or stereo
        self.channels = self.wf.getnchannels()
        self.sample_rate = self.wf.getframerate()
        self.stream = self.p.open(format = pyaudio.paInt16,
                                  channels = self.channels,
                                  rate = self.sample_rate,
                                  output = True)

    def record_setup(self):
        self.channels = 1
        self.sample_rate = 44100
        self.stream = self.p.open(format = pyaudio.paInt16,
                                  channels = self.channels,
                                  rate = self.sample_rate,
                                  input = True)

    def loop(self):
        # Main processing loop
        # Do appropriate setup depending on line in
        # or not
        if self.line_in:
            self.record_setup()
        else:
            self.play_setup()

        self.analyser = FreqAnalyser(self.channels,
                                     self.sample_rate,
                                     self.leds)

        # Read the first block of audio data 
        data = self.more()

        # While there is still audio left
        while data != '':
            try:
                # If we're playing audio write to stream
                if not self.line_in:
                    self.stream.write(data)

                # Analyse data and change LEDs
                self.analyse(data)

                # Get more audio data
                data = self.more()
            except KeyboardInterrupt:
                break

        # Tidy up
        self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    #f = FreqAnalyser(2, 44100)
    #f.plot_response()

    lc = LedController((20, 21, 16))
    #lc.test()
    ac = AudioController(sys.argv[1], lc)
    ac.loop()
