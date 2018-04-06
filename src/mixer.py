#!/usr/bin/python
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


import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from useful import unicode2
from sets import config
try:
    import alsaaudio
except: pass

class Mixer:
    def __init__(s):
        s.mixer = None

    def restart(s):
        try:
            s.mixer = alsaaudio.Mixer( alsaaudio.mixers(s.get_card_no())[config.mixer[ 'track_no' ]], cardindex=s.get_card_no())
        except: s.mixer =None

    def get_card_no(s):
        return config.mixer['card_no']

    def get_card_name(s):
        try:
            return alsaaudio.cards()[s.get_card_no()]
        except: ""

    def get_labels(s):
        try:
            return map(lambda n: (n[0], n[1]),  enumerate ( alsaaudio.mixers(s.get_card_no()) ) )
        except:
            return []

    def get_label(s, no=None):
        try:
            if no == None:
                no = config.mixer [ 'track_no' ]
            return unicode2 ( alsaaudio.mixers(s.get_card_no())[no] )
        except:
            return 'None'
    
    def get_cards(s):
        try:
            ret = []
            for i,name in enumerate( alsaaudio.cards() ):
                ret.append((i, name))
            return ret
        except:
            return []
    
    def _trpv(s):
        no = config.mixer [ 'track_no' ]
        track = s.mixer.list_tracks()[no]
        min_v = track.min_volume
        max_v = track.max_volume
        v = max_v - min_v
        pv = 100./v
        return (track, pv)
        
    def get_volume_pp(s):
        if s.mixer:
            try:    return s.mixer.getvolume()[0]
            except: return 0
    
    def increase_volume(s, ppstep = 1.):
        if s.mixer:
            try:
                vol=min(100, s.get_volume_pp() + ppstep)
                s.mixer.setvolume( int(vol) )
                while vol != s.get_volume_pp() and vol != 100:
                    vol=min(100, vol + ppstep)
                    s.mixer.setvolume( int(vol) )
            except: pass

    def decrease_volume(s, ppstep = 1. ):
        if s.mixer:
            try:
                vol=max(0, s.get_volume_pp() - ppstep)
                s.mixer.setvolume( int(vol) )
                while vol != s.get_volume_pp() and vol != 0:
                    vol=max(0, vol - ppstep)
                    s.mixer.setvolume( int(vol) )
            except: pass

if __name__ == '__main__':
    class Co:
        def __init__(s):
            s.mixer = {}
            #s.mixer [ 'plugin' ] = 'oss4mixer'
            #s.mixer [ 'properties' ] = [ ( 'device', '/dev/mixer0' ) ]
            s.mixer [ 'track_no' ] = 0
            s.mixer [ 'card_no' ] = 0
    config = Co()
                    
    mix = Mixer()
    mix.restart()
    print mix.get_card_name()
    print mix.get_cards()
    print mix.get_labels()
    print mix.get_label()
    print mix.get_volume_pp()
    mix.increase_volume()
    print mix.get_volume_pp()
    ## BasicPlayer
    #default_mixer = "oss4mixer"
    #gst_mixer = Gst.ElementFactory.make(default_mixer)
    #gst_mixer.set_state(Gst.State.READY)
    #tracks = gst_mixer.list_tracks()
    #for track in tracks:
    #    print track.label, track.min_volume, track.max_volume, track.num_channels, gst_mixer.get_volume(track)
    #print dir( tracks[0] )
    #print dir ( gst_mixer.get_volume )
