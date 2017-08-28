#!/usr/bin/python2
# -*- coding: utf8 -*-

#
# Copyright (C) 2010-2017  Platon Peacel☮ve <platonny@ngs.ru>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os,sys
#import gst
from threading import Event
import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
child_proxy_get_child_by_index = Gst.ChildProxy.get_child_by_index


class Band:
    def __init__(s, parent, band):
        s.band = band
        s.parent = parent
        s.min_gain = band.get_properties('gain')
        
    def get_name(s):
        return s.band.get_property('name')

    def get_gain(s):
        return s.band.get_property('gain')
    
    def get_freq(s):
        return s.band.get_property('freq')

    def get_bandwidth(s):
        return s.band.get_property('bandwidth')

    def set_bandwidth(s, n):
        s.band.set_property('bandwidth', n)

    def set_freq(s,n):
        s.band.set_property('freq', n)

    def set_gain(s,n):
        s.band.set_property('gain', n)

    def increase(s, step):
        gain = s.band.get_property('gain') + step
        if gain < -24.:
            gain = -24.
        elif gain > 12.:
            gain = 12.
        s.band.set_property('gain', gain )
    
    def substitution(s, band2):
        gain = float( s.get_gain() )
        gain2 = float( band2.get_gain() )
        band2.set_gain ( gain )
        s.set_gain( gain2 )
    
LOWEST_FREQ = 20.0
HIGHEST_FREQ = 20000.0
class Equalizer():
    def __init__(s, num_bands = 33):
        s.eq = Gst.ElementFactory.make('equalizer-nbands')
        s.eqr = Gst.ElementFactory.make('equalizer-nbands')
        s.generate_bands(num_bands)
    
    def __len__(s):
        return len(s.bands)
    
    def __getitem__(s, n):
        return s.bands[n]
    
    def Save(s):
        return map ( lambda b: (b.get_freq(), b.get_bandwidth(), b.get_gain()), s.bands )
    
    def Load(s, el):
        if el == None:
            s.generate_bands()
            return
        if len(el) != s.eq.get_property('num-bands'):
            s.generate_bands( len(el) )

        for i, opt in zip(range( len(el) ), el):
            band = s.bands[i]
            band.set_freq( opt[0] )
            band.set_bandwidth( opt[1] )
            band.set_gain( opt[2] )
            

    def generate_bands(s, numbands = 33):
        s.set_num_bands(numbands)
        s.bands = []
        if numbands == 33:
            freqs = [16, 20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000, 25000]
            width =[4] +  map(lambda n: freqs[n] - freqs[n-1], range(1,33))
            for i, fw in enumerate( zip(freqs, width)):
                f,w = fw
                band = Band( s, child_proxy_get_child_by_index(s.eq, i) )

                band.set_freq( f )
                band.set_bandwidth( w )
                band.set_gain( 0.0)
                s.bands.append(band)
            return

        freq0 = LOWEST_FREQ
        z = (HIGHEST_FREQ/LOWEST_FREQ)**(1./(numbands) )

        for i in range(numbands):
            freq1 = freq0*z
            band = Band( s, child_proxy_get_child_by_index(s.eq, i) )
            band.set_freq( freq0 + ((freq1 - freq0) / 2.0) )
            band.set_bandwidth( freq1-freq0)
            band.set_gain( 0.0)
            s.bands.append(band)
            freq0 = freq1


    def set_num_bands(s, n):
        s.eq.set_property('num-bands', n)
    
        
if __name__ == '__main__':
    eq = Equalizer(10)

    print len(eq.bands)
    for i in range( len(eq) ):
        print i, eq[i].get_freq(), eq.bands[i].get_bandwidth(),  eq[i].get_gain()

