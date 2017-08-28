#!/usr/bin/env python2
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
                                    

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.oggflac import OggFLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.wavpack import WavPack
import sys, os, thread, time, threading
import time
from threading import Semaphore, Thread, Event
import cue
import pickle
from useful import quote_http, quote
from sets import config, EncoderProfile, get_performer_alias, get_album_alias
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from equalizer import *


cue_time_to_ns = cue.cue_time_to_ns

def convert_ns(time_int):
    time_int = time_int / 1000000000
    time_str = ""
    if time_int >= 3600:
        _hours = time_int / 3600
        time_int = time_int - (_hours * 3600)
        time_str = str(_hours) + ":"
    if time_int >= 600:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + str(_mins) + ":"
    elif time_int >= 60:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + "0" + str(_mins) + ":"
    else:
        time_str = time_str + "00:"
    if time_int > 9:
        time_str = time_str + str(time_int)
    else:
        time_str = time_str + "0" + str(time_int)
        
    return time_str

class GstPipelineHelper:
    def __init__(s):
        s.reset()
    def reset(s):
        s.time_format = gst.Format.TIME
        s.state = None
        s.eof = False
        s.sem = Semaphore(0)
        s.error = False
        s.error_desc = u""
        s.the_end = Event()
        s.the_end.clear()
        s.start_time = None
        s.stop_time = None
        s.duration = None
        s.pipeline_name = s.pipeline.get_property("name")
    def on_message(s, bus, message):
        t = message.type
        src = message.src.get_name()

        if t == Gst.MessageType.STATE_CHANGED and s.state != None:
            if src == s.pipeline_name:
                os = None
                ns = None
                pn = None
                os,ns,pn = message.parse_state_changed()#os, ns, pn)
                if ns == s.state:
                    s.state = None
                    s.sem.release()
        elif t == Gst.MessageType.EOS and src == s.pipeline_name:
            s.eof = True
            s.sem.release()
            s.the_end.set()
        elif t == Gst.MessageType.ERROR:
            s.error = True
            err, s.error_desc = message.parse_error()
            s.sem.release()
            s.the_end.set()
    def get_error(s):
        return s.error_desc
    
    def get_splited_error(s, w):
        ret = []
        for tail in s.error_desc.split('\n'):
            while len(tail) > w:
                ret.append(tail[:w])
                tail = tail[w:]
            ret.append(tail)
        return ret
    
    def get_dur_time(s):
        try:
            pos = s.pipeline.query_position(s.time_format)[1]
            if s.start_time != None:
                pos -= s.start_time
            if s.duration != None:
                duration = s.duration
            else:
                duration = 0
        except Exception,e:
            return None
        return duration, pos

    def set_state(s, state):
        s.state = state
        s.pipeline.set_state(state)
        s.sem.acquire()
        if s.error or s.state != None:
            return False
        return True

    def wait_for_finish(s):
        s.sem.acquire()
        if s.eof:
            return True
        return False

    def wff(s, timeout, fx):
        while not s.the_end.is_set():
            time.sleep(timeout)
            dn = s.get_dur_time()
            if dn:
                fx(dn)
        return s.wait_for_finish()

class Decoder(GstPipelineHelper):
    def __init__(s):
        s.dest_file = os.tempnam("/tmp","peyenc")

        s.pipeline = Gst.ElementFactory.make("playbin")

        fakesink = Gst.ElementFactory.make("fakesink")
        filesink = Gst.ElementFactory.make("filesink")
        filesink.set_property("location", s.dest_file)
        s.sink = filesink

        s.pipeline.set_property("video-sink", fakesink)
        s.pipeline.set_property("audio-sink", filesink)

        bus = s.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", s.on_message)
            

    def decode(s, source, start_time=None, stop_time=None):
        s.reset()
        if not s.pipeline.set_state(Gst.State.NULL):
            return False
        s.pipeline.set_property("uri",  source)
        if not s.set_state(Gst.State.PAUSED):
            s.pipeline.set_state( Gst.State.NULL )
            return False

        s.caps = s.sink.get_pad("sink").get_negotiated_caps()

        s.start_time = start_time
        s.stop_time = stop_time
        if start_time != None:
            if stop_time:
                rc = s.pipeline.seek(
                1.0, s.time_format, Gst.SeekFlags.FLUSH ,
                Gst.SeekType.SET, start_time, 
                Gst.SeekType.SET, stop_time)
                s.duration = stop_time - start_time 
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
                try:
                    s.duration = s.pipeline.query_duration(s.time_format)[1] - start_time 
                except:
                    pass
        else:
            try:
                s.duration = s.pipeline.query_duration(s.time_format)[1]
            except:
                pass


        if not s.set_state(Gst.State.PLAYING):
            s.pipeline.set_state( Gst.State.NULL )
            return False
        return True
                
    def remove_temp(s):
        try:
            os.unlink(s.dest_file)
        except:
            pass

    def __del__(s):
        try:
            os.unlink(s.dest_file)
        except:
            pass

class AudioEncoder(GstPipelineHelper):
    def __init__(s, profile):
        s.decoder = Decoder()
        s.profile = EncoderProfile()
        s.profile.Load(profile.Save())


        s.pipeline = Gst.Pipeline()
        elements = []

        s.filesrc = Gst.ElementFactory.make("filesrc")
        s.filesrc.set_property("location", s.decoder.dest_file )
        elements.append(s.filesrc)

        s.capsfilter = Gst.ElementFactory.make("capsfilter")
        elements.append(s.capsfilter)

        for fname, status, params in s.profile.filters:
            if not status:
                continue
            try:
                af = Gst.ElementFactory.make ( fname )
                for p,v in params:
                    af.set_property(p, v)
            except:
                continue
            elements.append ( Gst.ElementFactory.make("audioconvert") )
            elements.append ( af )

        s.audioconvert = Gst.ElementFactory.make("audioconvert")
        elements.append(s.audioconvert)

        enc = Gst.ElementFactory.make( s.profile.encoder )
        elements.append(enc)

        for o,v in s.profile.encoder_opts:
            enc.set_property(o, v)

        if profile.muxer:
            muxer = Gst.ElementFactory.make(s.profile.muxer)
            elements.append(muxer)
            
            for o,v in s.profile.muxer_opts:
                muxer.set_property(o, v)

        s.filesink = Gst.ElementFactory.make("filesink")
        elements.append(s.filesink)

        s.pipeline.add(*elements)
        gst.element_link_many(*elements)



        s.elements = elements

        bus = s.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", s.on_message)

    
    def prepare_track(s, track, pwd):
        s.pipeline.set_state(Gst.State.NULL)
        src_file = track.get('file')
        if src_file:
            s.URI = 'file://' + quote(src_file)
        else:
            n = track.get('addr').find('://')
            s.URI = track.get('addr')[:n+3] + quote( track.get('addr')[n+3:] )

        s.dest = os.path.join(pwd, s.profile.get_file_path(track))
        try:
            os.makedirs(os.path.dirname(s.dest), 0755)
        except:
            pass

        s.filesink.set_property("location", s.dest.encode('utf8'))
        s.tag_dest = s.dest
        s.tag_track = track
        s.track_length = None

        s.start = None
        s.stop = None

        if track.has_key("begin"):
            s.start = cue_time_to_ns(track['begin'])

            if track.has_key('end'):
                s.stop = cue_time_to_ns(track['end'])

        elif track.has_key('end'):
            s.start = 0.
            s.stop = cue_time_to_ns(track['end'])

        return True

    def decode(s):
        return s.decoder.decode(s.URI, s.start, s.stop)


    def encode(s):
        s.reset()
        if not s.pipeline.set_state(Gst.State.NULL):
            return False
        s.capsfilter.set_property('caps', s.decoder.caps)

        if not s.set_state(Gst.State.PAUSED):
            s.pipeline.set_state( Gst.State.NULL )
            return False

        if not s.set_state(Gst.State.PLAYING):
            s.pipeline.set_state( Gst.State.NULL )
            return False

        s.duration = s.decoder.duration
        return True

    def to_null(s):
        s.pipeline.set_state(Gst.State.NULL)

    def finalize(s):
        s.pipeline.set_state(Gst.State.NULL)

        if s.profile.tag_type == 'flac':
            tag = FLAC(s.dest)

        elif s.profile.tag_type == 'oggflac':
            tag = OggFLAC(s.dest)

        elif s.profile.tag_type == 'oggvorbis':
            tag = OggVorbis(s.dest)

        elif s.profile.tag_type == 'id3':
            tag = EasyID3()
            tag.filename = s.tag_dest

        elif s.profile.tag_type == 'wavpack':
            tag = WavPack(s.dest)

        else:
            return

        if s.tag_track.has_key('performer'):
            tag['artist'] = [ get_performer_alias( s.tag_track.get('performer', ''), 4 ) ]

        if s.tag_track.has_key('album'):
            tag['album']  = [ get_album_alias( s.tag_track.get('album', ''), 4 ) ]

        if s.tag_track.has_key('title'):
            tag['title']  = [ s.tag_track.get('title', '') ]

        if s.tag_track.has_key('date'):
            tag['date'] = [ s.tag_track.get('date', '') ]

        if s.tag_track.has_key('id'):
            tag['tracknumber'] =  [ unicode(s.tag_track.get('id', '')) ]
        #tag['length'] = [ '1000' ]
        tag.save()


