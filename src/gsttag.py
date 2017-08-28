#!/usr/bin/env python
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

import time
from threading import Semaphore

from useful import quote_http, quote

class GstDetect:
    
    def __init__(self):
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        self.player.set_property("audio-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.sem = Semaphore(0)
        self.time_format = Gst.Format.TIME
        
    def get_duration(self, filepath):
        try:
            del self.sem
            self.sem = Semaphore(0)
            if filepath.find('://') == -1:
                self.player.set_property("uri", "file://" + quote(filepath) )
            else:
                if len(filepath) > 7 and filepath.lower()[:7] == 'http://':
                    filepath = quote_http(filepath)
                self.player.set_property("uri", filepath)
            self.err = False
            self.player.set_state(Gst.State.PAUSED)
            self.sem.acquire()
            if self.err == True:
                self.player.set_state(Gst.State.NULL)
                return None
            while True:
                try:
                    duration = self.player.query_duration(self.time_format)[1]
                except:
                    time.sleep(.05)
                else:
                    break
            duration = self.player.query_duration(self.time_format)[1]
            duration /= 1000000000.
            self.player.set_state(Gst.State.NULL)
        except:
            try:
                self.player.set_state(Gst.State.NULL)
            except:
                pass
            return None
        else:
            return duration

    def get_tags(self, filepath):
        try:
            self.tag = {}
            del self.sem
            self.sem = Semaphore(0)
            if filepath.find('://') == -1:
                self.player.set_property("uri", "file://" + filepath)
            else:
                if len(filepath) > 7 and filepath.lower()[:7] == 'http://':
                    filepath = quote_http(filepath)
                self.player.set_property("uri", filepath)
            self.err = False
            self.player.set_state(Gst.State.PAUSED)
            self.sem.acquire()
            if self.err == True:
                self.player.set_state(Gst.State.NULL)
                return None
            while True:
                try:
                    duration = self.player.query_duration(self.time_format)[1]
                except:
                    time.sleep(.05)
                else:
                    break
            duration = self.player.query_duration(self.time_format)[1]
            duration /= 1000000000.
            self.player.set_state(Gst.State.NULL)
        except:
            try:
                self.player.set_state(Gst.State.NULL)
            except:
                pass
            return None
        else:
            
            self.tag['duration'] = duration
            return self.tag

        
                        
    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.sem.release()
        elif t == Gst.MessageType.ERROR:
            self.err = True
            self.sem.release()
        elif t == Gst.MessageType.TAG:
            try:
                taglist = message.parse_tag()
                for k in taglist.keys():
                    if not self.tag.has_key(k):
                        self.tag[k] = taglist[k]
            except:
                pass
        #elif t == Gst.MessageType.DURATION:
        #    self.sem.release()
        elif t == Gst.MessageType.STATE_CHANGED:
            src = message.src.get_name()
            if src == "player":
                os = None
                ns = None
                pn = None
                #_from = message.parent
                os,ns,pn = message.parse_state_changed()#os, ns, pn)
                if os == Gst.State.READY and ns == Gst.State.PAUSED:
                    self.sem.release()

if __name__ == "__main__":
    from threading import Thread
    GObject.threads_init()
    Gst.init(None)
    dt = GstDetect()
    def test_gsttags():
        import time
        time.sleep(1)
        path="/home/hippy/love/lossless/Donovan/2004 - Beat Cafe/02-Donovan-Poormans_Sunshine.flac"
        print dt.get_duration(path)
        print dt.get_tags(path)

    thr = Thread(target=test_gsttags)
    thr.start()
    loop = GObject.MainLoop()
    loop.run()
