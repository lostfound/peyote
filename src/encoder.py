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

if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)

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
        s.time_format = Gst.Format.TIME
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
        s.time_type = None

    def to_null(s):
        s.pipeline.set_state(Gst.State.NULL)

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
            try:
                s.finalize()
            except: pass
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
            if s.time_type == None:
                if s.start_time and pos < s.start_time:
                    s.time_type = 1
                else:
                    s.time_type = 0
            if s.time_type != 1 and s.start_time:
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
        if s.state == s.pipeline.get_state(Gst.State.NULL)[1]: return True
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


class ReEncoder(GstPipelineHelper):
    def process(s, track, pwd):
        if not s.prepare_track(track, pwd): return False
        if not s.set_state(Gst.State.PLAYING): return False
        return True

    def __init__(s, profile):
        s.pipeline = Gst.ElementFactory.make("playbin")

        fakesink = Gst.ElementFactory.make("fakesink")
        s.filesink = Gst.ElementFactory.make("filesink")

        s.pipeline.set_property("video-sink", fakesink)

        #Encoder
        s.profile = EncoderProfile()
        s.profile.Load(profile.Save())


        elements = []
        if 1:
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

        
        elements.append(s.filesink)

        abin = Gst.Bin()
        for e in elements:
            abin.add( e )

        for e0,e1 in zip(elements[:-1], elements[1:]):
            e0.link(e1)

        sinkpad = elements[0].get_static_pad("sink")
        abin.add_pad(Gst.GhostPad.new('sink', sinkpad))
        s.pipeline.set_property("audio-sink", abin)
        s.elements = elements

        bus = s.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", s.on_message)

    def prepare_track(s, track, pwd):
        s.reset()
        s.pipeline.set_state(Gst.State.NULL)
        src_file = track.get('file')
        if src_file:
            s.URI = 'file://' + quote(src_file)
        else:
            n = track.get('addr').find('://')
            s.URI = track.get('addr')[:n+3] + quote( track.get('addr')[n+3:] )

        s.dest = os.path.join( pwd, s.profile.get_file_path(track) )

        try:
            os.makedirs(os.path.dirname(s.dest), 0755)
        except:
            pass

        s.pipeline.set_property("uri", s.URI)
        s.filesink.set_property("location", s.dest.encode('utf8'))
        s.tag_dest = s.dest
        s.tag_track = track
        s.track_length = None

        start_time = 0
        stop_time = None

        if track.has_key("begin"):
            start_time = cue_time_to_ns(track['begin'])
            s.start_time = start_time

            if track.has_key('end'):
                stop_time = cue_time_to_ns(track['end'])
            else:
                stop_time = None
        else:
            if track.has_key('end'):
                stop_time = cue_time_to_ns(track['end'])
            else:
                stop_time = None
        s.stop_time = stop_time

        if not s.set_state(Gst.State.PAUSED): return False

        #ppp
        s.start_time = start_time
        s.stop_time = stop_time
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
            s.duration = s.pipeline.query_duration(s.time_format)[1] - start_time 

        return True


    def finalize(s):
        s.set_state(Gst.State.NULL)

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
    def __del__(s):
            pass

if __name__ == "__main__":
    enc_profile ={}
    if 1:
        enc_profile['name'] =u"ogg"
        enc_profile['encoder_name'] = u"vorbisenc"
        enc_profile['encoder_args'] = []
        enc_profile['muxer_name'] = u"oggmux"
        enc_profile['muxer_args'] = []
        enc_profile['filters'] = []
        enc_profile['path'] = u"%$n - %$title.ogg"
        enc_profile['tag'] = 'oggvorbis'
    else:
        enc_profile['name'] =u"mp3"
        enc_profile['encoder_name'] = u"lamemp3enc"
        enc_profile['encoder_args'] = [ ('cbr', True), ('target', 1), ('bitrate', 320) ]
        enc_profile['muxer_name'] = None
        enc_profile['muxer_args'] = []
        enc_profile['filters'] = []
        enc_profile['path'] = u"%$n - %$title.mp3"
        enc_profile['tag'] = 'id3'
    default_profile=EncoderProfile()
    default_profile.Load(enc_profile)
    print default_profile.Save()
    track={}
    track["addr"]="/home/hippy/love/lossless/Donovan/2004 - Beat Cafe/01-Donovan-Love_Floats.flac"
    track["title"]="LSD"
    track["performer"]="LSD 25"
    track["album"]="Drugs"
    track["file"]=track["addr"]
    pwd= "/home/hippy/fakeHome/"
    track["id"]="666"
    track["begin"]="1:10.2"
    track["end"]="1:23.2"
    encoder=ReEncoder(default_profile)
    def test_encoder():
        encoder.process(track, pwd)
        print encoder.time_type
        print encoder.duration/1000000000.

    thr = Thread(target=test_encoder)
    thr.start()
    loop = GObject.MainLoop()
    loop.run()
