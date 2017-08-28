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

class Mixer:
    def __init__(s):
        s.mixer = None
    def restart(s):
        try:
            if s.mixer:
                s.mixer.set_state ( Gst.State.NULL )
        except:
            pass
        s.mixer = None
        try:
            s.mixer = Gst.ElementFactory.make( config.mixer['plugin'] )
            for p,v in config.mixer['properties']:
                s.mixer.set_property(p, v)

            s.mixer.set_state(Gst.State.READY)
        except:
            s.mixer = None
    def get_labels(s):
        ret = []
        if s.mixer:
            try:
                for n,track in enumerate ( s.mixer.list_tracks() ):
                    if s.mixer.get_volume(track) != ():
                        ret.append( (n, unicode2 ( track.label ) ) )
            except:
                return []
        return ret

    def get_label(s, no=None):
        try:
            if no == None:
                no = config.mixer [ 'track_no' ]
            return unicode2 ( s.mixer.list_tracks()[no].label )
        except:
            return 'None'
    
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
            try:
                track,pv = s._trpv()
                return s.mixer.get_volume(track)[0]*pv
            except:
                return 0
    
    def increase_volume(s, ppstep = 1.):
        try:
            track,pv = s._trpv()
            vol = []
            for n,v in enumerate ( s.mixer.get_volume(track) ):
                dv = int(ppstep/pv)
                if dv == 0:
                    dv = 1 if ppstep > 0 else -1
                v += dv
                if v < track.min_volume:
                    v = track.min_volume
                elif  v > track.max_volume:
                    v = track.max_volume
                vol.append( int(v) )
            s.mixer.set_volume( track, tuple(vol) )
        except:
            pass

    def decrease_volume(s, ppstep = 1. ):
        s.increase_volume( - ppstep )

if __name__ == '__main__':
    class Co:
        def __init__(s):
            s.mixer = {}
            s.mixer [ 'plugin' ] = 'oss4mixer'
            s.mixer [ 'properties' ] = [ ( 'device', '/dev/mixer0' ) ]
            s.mixer [ 'track_no' ] = 0
    config = Co()
                    
    mix = Mixer()
    mix.restart()
    print mix.get_labels()
    print mix.get_volume_pp()
    mix.increase_volume()
    print mix.get_volume_pp()
    # BasicPlayer
    default_mixer = "oss4mixer"
    gst_mixer = Gst.ElementFactory.make(default_mixer)
    gst_mixer.set_state(Gst.State.READY)
    tracks = gst_mixer.list_tracks()
    for track in tracks:
        print track.label, track.min_volume, track.max_volume, track.num_channels, gst_mixer.get_volume(track)
    print dir( tracks[0] )
    print dir ( gst_mixer.get_volume )
