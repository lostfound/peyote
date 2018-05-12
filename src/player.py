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
import sys, os, time, threading
import time
import cue
import pickle
from useful import quote_http, quote
from sets import config, get_performer_alias, get_album_alias
from thread_system.thread_polls import polls
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)

from equalizer import *
from threading import Semaphore, Event, Thread
from Queue import Queue, Empty, Full
try:
    import pylast
except:
    pylast = None

PITCH_STEP=0.005
SOFTVOL_STEP=0.02

cue_time_to_ns = cue.cue_time_to_ns
workers = None
def Initialize(task_workers):
    global workers, lastfm
    workers = task_workers
    Thread(target=lastfm.thread).start()


class LastFm:
    def __init__(s):
        s.timestamp = None
        s.track = None
        s.key = u"8cf011776844b1adc62538bd3636cd0c"
        s.secret = u"3b6b31e2c4551cc84d67257eec804f4d"
        s.net = None
        s.ss = threading.Semaphore(1)
        s.q = Queue()
        s.ex = False
        s.RECONNECT = 1
        s.START = 2
        s.STOP = 3
    def thread(s): #reconnect - 1, exit - None, start =2 , stop =3
        s.connect()
        while True:
            task,args = s.q.get()
            if not task:
                s.q.task_done()
                return
            try:
                if task == 1:
                    s.connect()
                elif task == 2:
                    s._start(*args)
                elif task == 3:
                    s._stop(*args)
            except:
                pass
            s.q.task_done()
                
    def exit(s):
        if s.ex:
            return
        try: s.q.put( (None,None) )
        except: pass
        s.ex = True
    

    def reconnect(s):
        try: s.q.put( (s.RECONNECT,[]) )
        except: pass

    def connect(s):
        try:
            if pylast and config.lastfm_scrobbler and config.lastfm_user and config.lastfm_md5:
                s.net = pylast.LastFMNetwork(api_key=s.key, 
                        api_secret=s.secret, 
                        username=config.lastfm_user, 
                        password_hash = config.lastfm_md5)
            else:
                s.net = None
        except:
            s.net = None
        
    def _start(s, track):
        artist = get_performer_alias(track.get("performer", ""), 7)
        album = get_album_alias(track.get("album", ""), 7)
        title=track.get("title", "")
        if track.get('type') == 'stream':
            duration = 600
        else:
            duration = int(track.get('time', 0))
        if track.get('type') == 'stream' and not config.lastfm_scrobble_radio:
            return
        if s.net and title and artist:
            s.net.update_now_playing(artist=artist
                    , album=album
                    , title=track.get("title", "")
                    , duration = duration
                    )

    def _stop(s, timestamp, track, cbu = None):
        artist = get_performer_alias(track.get("performer", ""), 7)
        album = get_album_alias(track.get("album", ""), 7)
        title = track.get("title", "")
        if s.net and title and artist:
            ltrack = {   "artist": artist
                   , "title": title
                   , "timestamp": timestamp
                   , "album": album
                 #  , "chosenByUser": "0"
                 }
            if cbu:
                track["chosenByUser"] = "0"
            if track.get('id'):
                ltrack["track_number"] = track.get('id')
            s.net.scrobble_many( [ltrack] )

    def start(s, track, cbu = None):
        if not s.net or not config.lastfm_scrobbler:
            return
        s.ss.acquire()
        try:
            s.timestamp = int(time.time())
            s.track = dict(track)
            if track.get('type') == 'stream': # radio
                if cbu: 
                    # radio TAG
                    if s.track.has_key('performer') and s.track.has_key('title'):
                        try: s.q.put((s.START, [dict(s.track)]))
                        except : pass
                    else: #start to listen radio
                        s.track = None
            else: # song
                if s.track.has_key('performer') and s.track.has_key('title'):
                    try: s.q.put((s.START, [dict(s.track)]))
                    except : pass
        except:
            pass
        s.ss.release()

    def stop(s):
        if not s.track:
            return
        if not s.net or not config.lastfm_scrobbler:
            s.track = None
            return
        s.ss.acquire()
        try:
            difftime = time.time() - s.timestamp
            duration = int(s.track.get('time', 0))

            if s.track.get('type') == 'stream' and config.lastfm_scrobble_radio:
                if difftime > 60:
                    try: s.q.put((s.STOP, [s.timestamp, dict(s.track), True]))
                    except: pass
            else:
                if duration >= 30 and difftime >= min(240, duration/2):
                    try: s.q.put((s.STOP, [s.timestamp, dict(s.track)]))
                    except : pass
        except:
            pass
        s.track = None
        s.ss.release()

lastfm = LastFm()


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


class PlayingOrders:
    repeat = False
    shuffle = False
    direction = 0
    zigzag = 0
    hold_equalizer = False

    def switch_shuffle(s):
        s.shuffle = not s.shuffle
        s.gui.print_shuffle(s.shuffle)
        s.cursor.reshufle()

    def switch_repeat(s):
        s.repeat = not s.repeat
        s.gui.print_repeat(s.repeat)
        s.cursor.reshufle()

    def switch_direction(s):
        s.direction = ( s.direction + 1 )%4
        s.gui.print_direction(s.direction)
        s.cursor.reshufle()
    
    def switch_hold_equalizer(s):
        s.hold_equalizer = not s.hold_equalizer
        s.gui.print_equalizer(s.hold_equalizer)

class Subscribers:
    subssem = threading.Semaphore(1)
    subscribers = []
    def subscribe(s, fx):
        s.subssem.acquire()
        s.subscribers.append(fx)
        s.subssem.release()

    def unsubscribe(s, fx):
        s.subssem.acquire()
        s.subscribers.remove(fx)
        s.subssem.release()

    def inform_all(s, track, equalizer):
        s.subssem.acquire()
        for subscriber in s.subscribers:
            subscriber(track, equalizer)
        s.subssem.release()
    
_linear = lambda x, l: x/l
_second_power = lambda x, l: (x/l)**2
_sqrt        = lambda x, l: (x/l)**0.5

from encoder import GstPipelineHelper
class GstPipelineHelper2:
    # reset
    # _is_HTTP
    # on_message
    # is_eof
    # get_error
    # get_splited_error
    # set_state
    def __init__(s):
        s.reset()

    def _is_HTTP(s):
        try:
            if s.track.get('type') == 'cue':
                if s.track.get('file').lower().startswith('http://'):
                    return True
                else:
                    return False
            else:
                if s.track.get('addr', s.track.get('file')).lower().startswith('http://'):
                    return True
                else:
                    return False
        except:
            return False

    def reset(s):
        s.time_format = Gst.Format.TIME #gst.Format(gst.FORMAT_TIME)
        s.state = None
        s.eof = False
        s.sem = Semaphore(0)
        s.error = False
        s.error_desc = u""
        s.the_end = Event()
        s.the_end.clear()
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
            try:
                workers.add_immediate_task(s.task_eos, [])
            except: pass

        elif t == Gst.MessageType.ERROR:
            s.error = True
            err, s.error_desc = message.parse_error()
            s.sem.release()
            s.the_end.set()
        elif t == Gst.MessageType.TAG:
            try:
                p = s.p
            except:
                p = s
            try:
                if s.track['type'] == 'stream': #or (s.track['type'] != cue and s.track['addr'].startswith('http://')):
                    taglist = message.parse_tag()
                else:
                    return
                b=False
                track = {}
                for k in taglist.keys():
                    if k in ['title']:
                        track['title'] = taglist[k]
                    elif k in ['artist', 'performer']:
                        track['performer'] = taglist[k]
                    elif k in ['album']:
                        track['album'] = taglist[k]
                    elif k in ['date', 'year']:
                        track['date'] = unicode(taglist[k].year)
                        
                if track != {}:
                    if not track.has_key('artist'):
                        spl = map ( lambda x: x.strip().rstrip(), track.get('title','').split('-', 1))
                        if len(spl) == 2 and spl[0] != '' and spl[1] != '':
                            if spl[1].startswith('-'):
                                spl[1] = spl[1:].strip()
                            track['performer'] = spl[0]
                            track['title'] = spl[1]
                    do_update = False
                    if not p.is_crossfade:
                        do_update = True
                    else:
                        try:
                            if p.players[CUR] == s:
                                do_update = True
                        except: pass

                    if do_update:
                        lastfm.stop()
                    for k in track.keys():
                        s.track[k] = track[k]

                    if do_update:
                        lastfm.start(s.track, cbu=True)
                        p.gui.update_track(s.track)
                        p.inform_all(s.track, s.eq)
            except Exception,e:
                pass
    def is_eof(s):
        return s.the_end.is_set()

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
    
    def set_state(s, state):
        s.state = state
        s.pipeline.set_state(state)
        s.sem.acquire()
        if s.error or s.state != None:
            return False
        return True

class CrossfadeParams:
    cf_start_time = .0
    cf_stop_time = .0
    cf_fx = _linear

class BasicPlayer(CrossfadeParams, GstPipelineHelper2):
    position = None
    playlist = None
    prev_pitch = None
    track = None
    stop_time = None
    start_time = 0
    duration_str = ""
    eq = None
    bands = {}

    def __init__(s, no, p = None):
        player_config = config.audio_player
        s.p = p
        s.pitch = None
        s.softvol = None
        s.player_name = "player-%i" % no
        s.no = no
        s.pipeline = Gst.ElementFactory.make("playbin", "player-%i" % no )
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink-%i" % no )
        if not s.eq:
            s.eq = Equalizer()
        s.fakesink = fakesink
        s.equalizer = s.eq.eq

        abin = Gst.Bin()
        asink = Gst.ElementFactory.make( player_config['audio_sink'] )
        for p,v in player_config['audio_sink_params']:
            asink.set_property(p,v)
        s.queue = Gst.ElementFactory.make("queue2", "aqueue-%i" % no)

        s.asink = asink
        if True: #PORTING
            s.volume = Gst.ElementFactory.make('volume')
        else:
            try:
                s.asink.get_properties('volume')
                s.volume = s.asink
            except:
                s.volume = Gst.ElementFactory.make('volume')


        for p,v in player_config['audio_sink_params']:
            asink.set_property(p,v)


        pre_sinks = []
        for ps in player_config['pre_sinks']:
            if ps[1]:
                pre_sinks.append( Gst.ElementFactory.make('audioconvert') )
                pre_sinks.append(Gst.ElementFactory.make(ps[0]))
                for p,v in ps[2]:
                    pre_sinks[-1].set_property(p,v)
                if ps[0] == 'pitch':
                    s.pitch = pre_sinks[-1]
                if ps[0] == 'volume':
                    s.softvol = pre_sinks[-1]
        if s.pitch:
            pidx = pre_sinks.index(s.pitch)
            pitch_graph = [ pre_sinks.pop(pidx) , pre_sinks.pop(pidx-1) ]
        else:
            pitch_graph = []

        if s.softvol:
            pidx = pre_sinks.index(s.softvol)
            sv_graph = [ pre_sinks.pop(pidx) , pre_sinks.pop(pidx-1) ]
        else:
            sv_graph = []


        #elements = pre_sinks + [s.queue, Gst.ElementFactory.make('audioconvert'), s.equalizer, s.volume, asink]
        if s.volume == asink:
            elements = pre_sinks + [s.queue] + pitch_graph + sv_graph + [ Gst.ElementFactory.make('audioconvert'), s.equalizer, asink]
        else:
            elements = pre_sinks + [s.queue] + pitch_graph + sv_graph + [ Gst.ElementFactory.make('audioconvert'), s.equalizer, s.volume, asink]
        s.pre_sinks = pre_sinks
        #elements = [s.queue, s.equalizer, asink]
        try:
            #abin.add(*elements)
            for e in elements:
                abin.add(e)

            #gst.element_link_many(*elements)
            for e0,e1 in zip(elements[:-1], elements[1:]):
                e0.link(e1)
        except Exception,e:
            elements = [s.queue, s.equalizer, s.volume, asink]
            for e in elements:
                abin.add(e)
            #gst.element_link_many(*elements)
            for e0,e1 in zip(elements[:-1], elements[1:]):
                e0.link(e1)

        sinkpad = elements[0].get_static_pad("sink")
        s.sinkpad = sinkpad
        abin.add_pad(Gst.GhostPad.new('sink', sinkpad))
        s.pipeline.set_property("audio-sink", abin)
        s.abin = abin
        s.pipeline.set_property("video-sink", fakesink)
        #s.time_format = gst.Format(gst.FORMAT_TIME)
        s.time_format = Gst.Format.TIME #gst.Format(gst.FORMAT_TIME)
        
        bus = s.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", s.on_message)
        s.bus = bus
        s.state = "stopped"#"plating", "paused"
        s.gui = None
        s.life = True

    def prepare_file(s, location, start_time = None, stop_time = None ):
        s.reset()
        s.pipeline.set_state(Gst.State.NULL);
        s.stop_time = stop_time

        is_HTTP = False
        if location[:7] == "file://":
            s.pipeline.set_property("uri",  "file://" + quote(location[7:]) )
        elif location[:7].lower() == 'http://':
            location = quote_http(location)
            s.pipeline.set_property("uri",  location)
            is_HTTP = True
        else:
            s.pipeline.set_property("uri", u"file://" + quote(location) )

        if not s.set_state(Gst.State.PAUSED):
            return

        try:
            s.duration = s.pipeline.query_duration(s.time_format)[1]
        except Exception, e:
            pass


        #calculate duration
        if stop_time == None:
            if s.start_time == None:
                s.duration_ns = s.duration
            else:
                s.duration_ns = s.duration - s.start_time
        else:
            if s.start_time == None:
                s.duration_ns = s.stop_time
            else:
                s.duration_ns = s.stop_time - s.start_time
        s.duration_str = convert_ns(s.duration_ns)

        #seek
        if s.position != None:
            if stop_time != None:
                if is_HTTP or 1:
                    s.pipeline.seek_simple(s.time_format, 
                        Gst.SeekFlags.FLUSH,
                        s.position)
                else:
                    s.pipeline.seek(
                        1.0, s.time_format, Gst.SeekFlags.FLUSH,
                        Gst.SeekType.SET, s.position, 
                        Gst.SeekType.SET, stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    s.position)
            s.position = None
                
        elif start_time != None:
            if stop_time != None:
                if is_HTTP or 1:
                    s.pipeline.seek_simple(s.time_format, 
                        Gst.SeekFlags.FLUSH,
                        start_time)
                else:
                    s.pipeline.seek(
                        1.0, s.time_format, Gst.SeekFlags.FLUSH,
                        Gst.SeekType.SET, start_time, 
                        Gst.SeekType.SET, stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
        return True

    def prepare_track(s, track = None):
        if track == None:
            track = s.track
        else:
            s.position = None

        if type(track) == dict:
            s.track = track
            #pitch aerostat
            if config.aerostat_cheat:
                try:
                    if s.track['performer'] == u'БГ':
                        if s.prev_pitch == None:
                            s.prev_pitch = s.get_pitch()
                        s.set_pitch(config.aerostat_pitch)
                    else:
                        if s.prev_pitch != None:
                            s.set_pitch(s.prev_pitch)
                            s.prev_pitch = None
                except Exception,e:
                    pass
            if track.has_key("begin"):
                start_time = cue_time_to_ns(track['begin'])
                s.start_time = start_time

                if track.has_key('end'):
                    stop_time = cue_time_to_ns(track['end'])
                else:
                    stop_time = None

                return s.prepare_file(track['file'], start_time, stop_time)
            else:
                start_time = None
                s.start_time = 0
                if track.has_key('end'):
                    stop_time = cue_time_to_ns(track['end'])
                else:
                    stop_time = None
                return s.prepare_file(track['addr'], start_time, stop_time)

    def play_track(s, track = None):
        s.prepare_track(track)
        if s.set_state(Gst.State.PLAYING):
            return True

    def stop(s):
        s.pipeline.set_state(Gst.State.NULL)
        return

    def restart(s, v=False):
        status = s.get_state()
        r = False
        b = False
        if v:
            if status == Gst.State.PLAYING:
                s.playpause()
                while s.get_state() == Gst.State.PLAYING:
                    time.sleep(0.03)
                r = True
            elif status == Gst.State.PAUSED:
                track = s.track
                s.stop()
                b = True
                while s.get_state() != Gst.State.NULL:
                    time.sleep(0.03)
        else:
            s.stop()
            while s.get_state() != Gst.State.NULL:
                time.sleep(0.03)
        
        del s.queue
        del s.asink
        del s.bus
        del s.abin
        del s.fakesink
        del s.pre_sinks
        del s.sinkpad
        del s.pipeline
        del s.pitch
        del s.softvol
        s.__init__(s.no)
        if r:
            s.playpause()
        elif b and track:
            s.prepare_track(track)
        #s.start()
    def get_state(s):
        return s.pipeline.get_state(Gst.State.NULL)[1]

    def get_status(s):
        status = s.pipeline.get_state(Gst.State.NULL)[1]
        if status == Gst.State.PLAYING:
            return "Playing"
        elif status == Gst.State.NULL and s.track != None and s.position != None:
            return "Paused"
        else:
            return "Stopped"

    def get_current_ns(s):
        try:
            pos = s.pipeline.query_position(s.time_format)[1]
        except Exception,e:
            pos = None
        return pos

    def set_vol(s, volume):
        s.volume.set_property("volume", volume)

    #def play(s):
    #    status = s.pipeline.get_state(Gst.State.NULL)[1]
    #    if status == Gst.State.PAUSED:
    #        s.set_state(Gst.State.PLAYING)
    
    def get_equalizer(s):
        return s.eq

    def pause(s):
        if s.get_status() == "Playing":
            s.playpause()
    def play(s):
        if s.get_status() != "Playing":
            s.playpause()

    def playpause(s):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            try:
                s.position = s.pipeline.query_position(s.time_format)[1]
                s.pipeline.set_state(Gst.State.NULL);
            except:
                pass
            return True
        elif s.track != None:
            s.play_track()
            s.position = None
            return False
    def seek_pp(s, pp):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            start_time = int(s.duration_ns*pp)
            if s.start_time:
                start_time += s.start_time
            s.set_state(Gst.State.PAUSED)
            is_HTTP = s._is_HTTP()
            if s.stop_time != None and not is_HTTP and 0:
                s.pipeline.seek(
                    1.0, s.time_format, Gst.SeekFlags.FLUSH,
                    Gst.SeekType.SET, start_time, 
                    Gst.SeekType.SET, s.stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
            s.set_state(Gst.State.PLAYING)

    def seek(s, offset):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            start_time = s.get_current_ns()
            if start_time != None:
                start_time += offset*1000000000L
            else:
                return
            if start_time < 0:
                start_time = 0L
            if s.stop_time == None:
                stop_time = s.duration
            else:
                stop_time = s.stop_time
            if start_time > stop_time:
                return
            s.set_state(Gst.State.PAUSED)
            is_HTTP = s._is_HTTP()
            if s.stop_time != None and not is_HTTP and 0:
                s.pipeline.seek(
                    1.0, s.time_format, Gst.SeekFlags.FLUSH,
                    Gst.SeekType.SET, start_time, 
                    Gst.SeekType.SET, s.stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
            s.set_state(Gst.State.PLAYING)
            try:
                pos = s.get_current_ns()
                spos = convert_ns(pos-s.start_time)
            except:
                pass

    def get_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
        except:
            pass
        else:
            return sv

    def increase_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
            sv += SOFTVOL_STEP
            s.softvol.set_property('volume', sv)
        except:
            pass

    def decrease_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
            sv -= SOFTVOL_STEP
            if sv < 0:
                sv = 0
            s.softvol.set_property('volume', sv)
        except:
            pass

    def get_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
        except:
            pass
        else:
            return pitch

    def set_pitch(s, pitch):
        s.pitch.set_property('pitch', pitch)

    def increase_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
            pitch += PITCH_STEP
            s.pitch.set_property('pitch', pitch)
        except:
            pass
    def decrease_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
            pitch -= PITCH_STEP
            s.pitch.set_property('pitch', pitch)
        except:
            pass


class AudioPlayer( PlayingOrders, Subscribers, GstPipelineHelper2 ):
    # FUNCTIONS:
    # get_current_track
    # type
    # restart
    # task_eos
    # get_equalizer
    # increase_volume
    # decrease_volume
    # start
    # exit
    # get_status
    # playpause
    # play_track
    # seek_pp
    # seek
    # play_file
    # on_next_track
    # get_current_ns
    # on_next_track
    # next
    # prev
    # reset_xtheader_task
    # add_playing_task
    # update_time_task
    # playing_task
    # store_session
    # restore_session
    # get_softvol
    # increase_softvol
    # decrease_softvol
    # get_pitch
    # increase_pitch
    # decrease_pitch
    # set_pitch

    is_crossfade = False
    history = []
    position = None
    gui = None
    playlist = None
    track = None
    stop_time = None
    start_time = 0
    equalizer = Equalizer()
    duration_str = ""
    prev_pitch = None

    def __init__(s):
        player_config = config.audio_player
        s.pitch = None
        s.softvol = None

        s.pipeline = Gst.ElementFactory.make("playbin3", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        
        abin = Gst.Bin()
        asink = Gst.ElementFactory.make( player_config['audio_sink'] )
        for p,v in player_config['audio_sink_params']:
            asink.set_property(p,v)
        s.queue = Gst.ElementFactory.make("queue2", "aqueue")

        pre_sinks = []
        for ps in player_config['pre_sinks']:
            if ps[1]:
                pre_sinks.append( Gst.ElementFactory.make('audioconvert') )
                pre_sinks.append(Gst.ElementFactory.make(ps[0]))
                for p,v in ps[2]:
                    pre_sinks[-1].set_property(p,v)
                if ps[0] == 'pitch':
                    s.pitch = pre_sinks[-1]
                if ps[0] == 'volume':
                    s.softvol = pre_sinks[-1]
        if s.pitch:
            pidx = pre_sinks.index(s.pitch)
            pitch_graph = [ pre_sinks.pop(pidx) , pre_sinks.pop(pidx-1) ]
        else:
            pitch_graph = []

        if s.softvol:
            pidx = pre_sinks.index(s.softvol)
            sv_graph = [ pre_sinks.pop(pidx) , pre_sinks.pop(pidx-1) ]
        else:
            sv_graph = []


        elements = pre_sinks + [s.queue] + pitch_graph + sv_graph + [ Gst.ElementFactory.make('audioconvert'), s.equalizer.eq, asink]
        try:
            #abin.add(*elements)
            for e in elements:
                abin.add(e)

            #gst.element_link_many(*elements)
            for e0,e1 in zip(elements[:-1], elements[1:]):
                e0.link(e1)

        except Exception,e:
            elements = [s.queue, s.equalizer, s.volume, asink]
            for e in elements:
                abin.add(e)
            #gst.element_link_many(*elements)
            for e0,e1 in zip(elements[:-1], elements[1:]):
                e0.link(e1)

        sinkpad = elements[0].get_static_pad("sink")
        abin.add_pad(Gst.GhostPad.new('sink', sinkpad))

        s.pipeline.set_property("audio-sink", abin)
        s.pipeline.set_property("video-sink", fakesink)
        s.time_format = Gst.Format.TIME
        s.asink = asink
        
        bus = s.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", s.on_message)
        s.bus = bus
        s.abin = abin
        s.state = "stopped"#"plating", "paused"
        s.life = True
        s.volume = 1.0
        s.fakesink = fakesink
        s.asink = asink
        s.pre_sinks = pre_sinks
        s.sinkpad = sinkpad
        try:
            s.prev_pitch = s.get_pitch()
        except:
            pass

    def get_current_track(s):
        return s.track

    def type(s):
        return "standart"

    def restart(s):
        status = s.get_status()
        if status == "Playing":
            s.playpause()
            while s.get_status() == "Playing":
                time.sleep(0.03)
        s.life = False
        time.sleep(0.6)
        del s.queue
        del s.asink
        del s.bus
        del s.abin
        del s.fakesink
        del s.pre_sinks
        del s.sinkpad
        del s.pipeline
        del s.pitch
        del s.softvol
        s.__init__()
        s.start()
        if status == "Playing":
            s.playpause()

    def task_eos(s):
        if s.life:
            s.next()

    def get_equalizer(s):
        return s.equalizer
    
    def increase_volume(s):
        pass
    def decrease_volume(s):
        pass

    def start(s):
        s.add_playing_task()

    def exit(s):
        s.life = False
        s.pipeline.set_state(Gst.State.NULL);
        del s.queue
        del s.asink
        del s.bus
        del s.abin
        del s.fakesink
        del s.pre_sinks
        del s.sinkpad
        del s.pipeline


    def get_status(s):
        status = s.pipeline.get_state(Gst.State.NULL)[1]
        if status == Gst.State.PLAYING:
            return "Playing"
        elif status == Gst.State.NULL and s.track != None and s.position != None:
            return "Paused"
        else:
            return "Stopped"

    def pause(s):
        if s.get_status() == "Playing":
            s.playpause()

    def play(s):
        if s.get_status() != "Playing":
            s.playpause()

    def playpause(s):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            try:
                s.position = s.pipeline.query_position(s.time_format)[1]
                s.pipeline.set_state(Gst.State.NULL);
                if s.gui != None:
                    s.gui.on_pause(s.track)
                
            except:
                pass
        elif s.track != None:
            s.play_track()
            s.position = None
            if s.gui != None:
                s.gui.print_xtheader(s.track)

            
            
    def play_track(s, track = None):
        if track == None:
            track = s.track
        else:
            lastfm.stop()
            s.position = None
            lastfm.start(track)

        if type(track) != dict:
            return

        s.track = track
        if config.aerostat_cheat:
            try:
                if s.track['performer'] == u'БГ':
                    if s.prev_pitch == None:
                        s.prev_pitch = s.get_pitch()
                    s.set_pitch(config.aerostat_pitch)
                else:
                    if s.prev_pitch != None:
                        s.set_pitch(s.prev_pitch)
                        s.prev_pitch = None
            except Exception,e:
                pass

        if not s.hold_equalizer:
            s.equalizer.Load( config.GetEqualizer(s.track) )

        if track.has_key("begin"):
            start_time = cue_time_to_ns(track['begin'])
            s.start_time = start_time

            if track.has_key('end'):
                stop_time = cue_time_to_ns(track['end'])
            else:
                stop_time = None

            s.play_file(track['file'], start_time, stop_time)
        else:
            start_time = None
            s.start_time = 0
            if track.has_key('end'):
                stop_time = cue_time_to_ns(track['end'])
            else:
                stop_time = None
            s.play_file(track['addr'], start_time, stop_time)

        if s.gui != None:
            s.gui.update_track(track)
            s.gui.print_shuffle(s.shuffle)
            s.gui.print_repeat(s.repeat)
            s.gui.print_direction(s.direction)
            s.gui.print_equalizer(s.hold_equalizer)
        s.inform_all(track, s.equalizer)

    
    def seek_pp(s, pp):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            start_time = int(s.duration_ns*pp)
            if s.start_time:
                start_time += s.start_time
            s.set_state(Gst.State.PAUSED)
            is_HTTP = s._is_HTTP()
            if s.stop_time != None and not is_HTTP and 0:
                s.pipeline.seek(
                    1.0, s.time_format, Gst.SeekFlags.FLUSH,
                    Gst.SeekType.SET, start_time, 
                    Gst.SeekType.SET, s.stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
            s.set_state(Gst.State.PLAYING)

    def seek(s, offset):
        if s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING:
            start_time = s.get_current_ns()
            if start_time != None:
                start_time += offset*1000000000L
            else:
                return
            if start_time < 0:
                start_time = 0L
            if s.stop_time == None:
                stop_time = s.duration
            else:
                stop_time = s.stop_time
            if start_time > stop_time:
                return
            s.set_state(Gst.State.PAUSED)
            is_HTTP = s._is_HTTP()
            if s.stop_time != None and not is_HTTP and 0:
                s.pipeline.seek(
                    1.0, s.time_format, Gst.SeekFlags.FLUSH,
                    Gst.SeekType.SET, start_time, 
                    Gst.SeekType.SET, s.stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
            s.set_state(Gst.State.PLAYING)
            try:
                pos = s.get_current_ns()
                spos = convert_ns(pos-s.start_time)
                s.gui.update_times(spos, s.duration_str, pos, s.duration_ns)
            except Exception, e:
                pass


    def play_file(s, location, start_time = None, stop_time = None ):
        s.reset()
        s.pipeline.set_state(Gst.State.NULL);
        s.stop_time = stop_time

        is_HTTP = False
        if location[:7] == "file://":
            s.pipeline.set_property("uri",  "file://" + quote(location[7:]) )
        elif location[:7].lower() == 'http://':
            location = quote_http(location)
            s.pipeline.set_property("uri",  location)
            is_HTTP = True
        else:
            s.pipeline.set_property("uri", u"file://" + quote(location) )

        if not s.set_state(Gst.State.PAUSED):
            return

        try:
            s.duration = s.pipeline.query_duration(s.time_format)[1]
        except:
            s.duration = 0

        #calculate duration
        if stop_time == None:
            if s.start_time == None:
                s.duration_ns = s.duration
            else:
                s.duration_ns = s.duration - s.start_time
        else:
            if s.start_time == None:
                s.duration_ns = s.stop_time
            else:
                s.duration_ns = s.stop_time - s.start_time
        s.duration_str = convert_ns(s.duration_ns)

        #seek
        if s.position != None:
            if stop_time != None:
                if is_HTTP or 1:
                    s.pipeline.seek_simple(s.time_format, 
                        Gst.SeekFlags.FLUSH,
                        s.position)
                else:
                    s.pipeline.seek(
                        1.0, s.time_format, Gst.SeekFlags.FLUSH,
                        Gst.SeekType.SET, s.position, 
                        Gst.SeekType.SET, stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    s.position)
            s.position = None
                
        elif start_time != None:
            if stop_time != None:
                if is_HTTP or 1:
                    s.pipeline.seek_simple(s.time_format, 
                        Gst.SeekFlags.FLUSH,
                        start_time)
                else:
                    s.pipeline.seek(
                    1.0, s.time_format, Gst.SeekFlags.FLUSH,
                    Gst.SeekType.SET, start_time, 
                    Gst.SeekType.SET, stop_time)
            else:
                s.pipeline.seek_simple(s.time_format, 
                    Gst.SeekFlags.FLUSH,
                    start_time)
        #play
        s.set_state(Gst.State.PLAYING)

    def on_next_track(s, track):
        pass

    def get_current_ns(s):
        try:
            pos = s.pipeline.query_position(s.time_format)[1]
        except:
            pos = None
        return pos
    
    def prev(s):
        try:
            s.pipeline.set_state(Gst.State.NULL);
            s.cursor.prev_track()
        except:
            pass
    def next(s):
        try:
            workers.add_immediate_task(s.reset_xtheader_task, [])
            s.pipeline.set_state(Gst.State.NULL);
            lastfm.stop()
            s.cursor.next_track()
            s.playlist.play_next()
        except:
            pass

    def reset_xtheader_task(s):
        if s.gui != None:
            s.gui.reset_xtheader()
    
    def add_playing_task(s):
        s.prev_pos = -1
        s.stop_counter = 0
        s.playing_task_delay = 0.2
        s.playing_task_counter = 0
        workers.add_immediate_task(s.playing_task, [])

    def update_time_task(s, pos):
        if not s.life:
            return
        if s.gui != None:
            if s.start_time != None:
                spos = convert_ns(pos-s.start_time)
            else:
                spos = convert_ns(pos)
            s.gui.update_times(spos, s.duration_str, pos-s.start_time, s.duration_ns)

        
    def playing_task(s):
        if not s.life:
            return

        try:
            is_state_playing = s.pipeline.get_state(Gst.State.NULL)[1] == Gst.State.PLAYING
        except:
            pass
        else:
            if is_state_playing:
                try:
                    pos = s.get_current_ns()
                    workers.add_immediate_task(s.update_time_task, [pos])
                    
                    if s.stop_time != None and pos > s.stop_time:
                        s.prev_pos = -1
                        s.next()
                    elif pos == s.prev_pos:
                        if s.stop_counter >= 5:
                            s.stop_counter=0
                            s.prev_pos = -1
                            s.next()
                        else:
                            s.stop_counter += 1
                    else:
                        s.stop_counter = 0
                        s.prev_pos = pos

                except:
                    pass
            else:
                s.prev_pos = -1
                
                
        s.playing_task_counter += 1
        workers.add_timed_task(s.playing_task, [], delay = s.playing_task_delay )
            
    def store_session(s, pfile=None):
        player_last_status = {}
        stus = s.get_status()
        if stus == "Playing":
            s.playpause()
            stus = "Paused"

        if stus == "Paused":
            player_last_status['addr'] = s.track['addr']
            player_last_status['position'] = s.position
        
        if pfile:
            pickle.dump(player_last_status,  pfile)
        else:
            return player_last_status

    def restore_session(s, pfile):
        s.reset()
        if type(pfile) == file:
            player_status = pickle.load(pfile)
        else:
            player_status = pfile

        if player_status.has_key('addr'):
            try:
                song = cue.addr_to_track(player_status['addr'])
            except:
                song = None

            if song:
                s.track = song
                s.position = player_status['position']
                s.equalizer.Load( config.GetEqualizer(s.track) )
                try:
                    s.gui.update_track(song)
                    s.gui.on_pause(song)
                except:
                    pass

    def get_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
        except:
            pass
        else:
            return sv

    def increase_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
            sv += SOFTVOL_STEP
            s.softvol.set_property('volume', sv)
        except:
            pass

    def decrease_softvol(s):
        try:
            sv = s.softvol.get_property('volume')
            sv -= SOFTVOL_STEP
            if sv < 0:
                sv = 0
            s.softvol.set_property('volume', sv)
        except:
            pass

    def get_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
        except:
            pass
        else:
            return pitch

    def increase_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
            pitch += PITCH_STEP
            s.pitch.set_property('pitch', pitch)
        except:
            pass
    def decrease_pitch(s):
        try:
            pitch = s.pitch.get_property('pitch')
            pitch -= PITCH_STEP
            s.pitch.set_property('pitch', pitch)
        except:
            pass

    def set_pitch(s, pitch):
        s.pitch.set_property('pitch', pitch)


PREV=0
CUR=1
NEXT=2
class AudioCrossFadePlayer ( PlayingOrders, Subscribers ):
    is_crossfade = True
    life = threading.Event()
    gui = None
    def __init__(s, no):
        s.players_sem = threading.Semaphore(1)
        s.players = [ BasicPlayer(no, s), BasicPlayer(no+1, s), BasicPlayer(no+2, s) ]
        s.fade_sem = threading.Semaphore(1)
        s.prev_pitch = 0.0

        s.next_p = 1
        s.current_p = 0
        s.tid = 0
        s.life.clear()
        polls.Run(s.fade_thread)
        s.fade_in = _linear
        s.fade_out=_linear

        s.start_time = None
        s.stop_time = None
        s.fade_counter = 0 
        s.track = None
    def type(s):
        return "crossfade"

    def flock(s):
        s.fade_sem.acquire()
    def funlock(s):
        s.fade_sem.release()
    def plock(s):
        s.players_sem.acquire()

    def punlock(s):
        s.players_sem.release()

    def crossfade(s, p = True):
        lastfm.stop()
        s.flock()
        if s.players[PREV].get_state() != Gst.State.NULL:
            s.players[PREV].stop()
        s.plock()
        s.players = [ s.players[CUR], s.players[NEXT], s.players[PREV] ]
        s.punlock()
        s.fade_counter += 1

        tm = time.time()
        if s.players[PREV].get_state() == Gst.State.PLAYING:
            s.start_time = s.players[PREV].get_current_ns()
            s.stop_time = s.start_time + config.audio_player['crossfade_time']*1000000000
            try:
                if s.stop_time > s.players[PREV].duration:
                    s.stop_time = s.players[PREV].duration
            except:
                pass
        else:
            s.start_time = None
            s.stop_time = None

        if s.players[CUR].get_state() == Gst.State.PAUSED:
            if s.start_time != None:
                s.players[CUR].set_vol(0.0)
            else:
                s.players[CUR].set_vol(1.0)

            if s.hold_equalizer:
                s.players[CUR].eq.Load( s.players[PREV].eq.Save() )
            else:
                s.players[CUR].eq.Load ( config.GetEqualizer(s.players[CUR].track) )
                

            s.players[CUR].playpause()
        else:
            pass

        track = s.players[CUR].track
        eq = s.players[CUR].get_equalizer()
        s.track = track
        lastfm.start(track)
        s.funlock()
        try:
            if s.gui != None:
                s.gui.reset_xtheader()
            if p:
                polls.Run(s.next_thread)
        except:
            pass
        s.new_track(track, eq)

    def new_track(s, track, eq):
        if s.gui != None:
            s.gui.update_track(track)
            s.gui.print_shuffle(s.shuffle)
            s.gui.print_repeat(s.repeat)
            s.gui.print_direction(s.direction)
            s.gui.print_equalizer(s.hold_equalizer)
        s.inform_all(track, eq)

    def next_thread(s):
        s.cursor.next_track(False)
    def fade_thread(s):
        prev_counter = 0
        prev_time =None
        utime = 0
        while not s.life.is_set():
            s.life.wait(0.07)
            if s.life.is_set():
                return
            s.flock()

            prev_time = s.players[CUR].get_current_ns()
            if prev_counter == s.fade_counter and s.players[CUR].get_state() == Gst.State.PLAYING:
                if s.players[CUR].duration <= 0:
                    s.funlock()
                    try:
                        s.update_time_task()
                    except Exception, e:
                        pass
                    continue
                stop_time = filter(None, [s.players[CUR].stop_time, s.players[CUR].duration]) [0]
                if s.players[CUR].get_current_ns() == prev_time and stop_time - prev_time < 100000000:
                    s.funlock()
                    s.crossfade()
                    continue
                else:
                    if stop_time - s.players[CUR].get_current_ns() <= config.audio_player['crossfade_time'] * 1000000000:
                        s.funlock()
                        s.crossfade()
                        continue
            if s.start_time != None:
                curtime = s.players[PREV].get_current_ns()
                if curtime >= s.stop_time or config.audio_player['crossfade_time'] == 0:
                    s.start_time = None
                    s.stop_time = None
                    s.funlock()
                    s.players[CUR].set_vol(1.0)
                    prev_counter = s.fade_counter
                    s.players[PREV].stop()
                    continue

                try:
                    difftime = float( s.players[PREV].get_current_ns() - s.start_time )
                except:
                    difftime = -1
                if difftime < 0 or s.players[PREV].is_eof():
                    s.start_time = None
                    s.stop_time = None
                    s.funlock()
                    s.players[CUR].set_vol(1.0)
                    s.players[PREV].stop()
                    prev_counter = s.fade_counter
                    continue

                pp = (difftime/config.audio_player['crossfade_time'])/1000000000.
                if s.players[PREV].get_state() == Gst.State.PLAYING:
                    s.players[PREV].set_vol(1 - pp )
                    s.players[CUR].set_vol(pp)
            else:
                prev_counter = s.fade_counter

            tm = time.time()
            if tm - utime > 0.5:
                utime = tm
                try:
                    s.update_time_task()
                except Exception, e:
                    pass
                
            s.funlock()
    def update_time_task(s):
        if s.life.is_set():
            return
        if s.players[CUR].get_state() != Gst.State.PLAYING:
            return
        pos = s.players[CUR].get_current_ns()
        if s.gui != None:
            try:
                if s.players[CUR].start_time != None:
                    spos = convert_ns(pos-s.players[CUR].start_time)
                else:
                    spos = convert_ns(pos)
            except Exception, e:
                pass
            try:
                s.gui.update_times(spos, s.players[CUR].duration_str, pos-s.players[CUR].start_time, s.players[CUR].duration_ns)
            except Exception,e:
                pass

    def restart(s):
        s.flock()
        s.plock()
        s.players[CUR].restart(True)
        s.players[NEXT].restart(True)
        s.players[PREV].restart()
        s.start_time = None
        s.stop_time = None
        s.punlock()
        s.funlock()
    
    def get_equalizer(s):
        return s.players[CUR].get_equalizer()
    
    def get_softvol(s):
        return s.players[CUR].get_softvol()

    def increase_softvol(s):
        s.players[0].increase_softvol()
        s.players[1].increase_softvol()
        s.players[2].increase_softvol()

    def decrease_softvol(s):
        s.players[0].decrease_softvol()
        s.players[1].decrease_softvol()
        s.players[2].decrease_softvol()

    def get_pitch(s):
        return s.players[CUR].get_pitch()

    def set_pitch(s, pitch):
        for i in range(3):
            s.players[0].set_pitch(pitch)

    def increase_pitch(s):
        s.players[0].increase_pitch()
        s.players[1].increase_pitch()
        s.players[2].increase_pitch()

    def decrease_pitch(s):
        s.players[0].decrease_pitch()
        s.players[1].decrease_pitch()
        s.players[2].decrease_pitch()

    
    def start(s):
        pass

    def exit(s):
        s.life.set()
        try:
            s.lastfm.start(s.players[CUR].track)
        except:
            pass
        s.players[PREV].stop()
        s.players[CUR].stop()
        s.players[NEXT].stop()
        del s.players

    def get_status(s):
        try:
            return s.players[CUR].get_status()
        except:
            return "Stopped"
    
    def pause(s):
        if s.get_status() == "Playing":
            s.playpause()

    def play(s):
        if s.get_status() != "Playing":
            s.playpause()

    def playpause(s):
        s.flock()
        s.plock()
        s.players[PREV].stop()
        rc = s.players[CUR].playpause()
        s.start_time = None
        s.stop_time = None
        s.players[CUR].set_vol(1.0)
        if s.gui != None:
            if rc:
                s.gui.on_pause(s.players[CUR].track)
            else:
                s.gui.print_xtheader(s.players[CUR].track)

        s.punlock()
        s.funlock()
    
    def play_track(s, track = None):
        if track:
            s._set_next(track)
            s.crossfade(False)

    def get_current_ns(s):
        pass

    def seek(s, offset):
        s.flock()
        try:
            s.players[PREV].stop()
            s.players[CUR].seek(offset)
        except:
            pass
        s.funlock()
        
    def seek_pp(s, pp):
        s.flock()
        try:
            s.players[PREV].stop()
            s.players[CUR].seek_pp(pp)
        except:
            pass
        s.funlock()

    def on_next_track(s, track):
        s._set_next(track)


    def _set_next(s, track):
        s.plock()
        s.players[NEXT].prepare_track(track)
        s.punlock()

    def next(s):
        s.crossfade()

    def store_session(s, pfile=None):
        s.flock()
        player_last_status = {}
        stus = s.players[CUR].get_status()
        if stus == "Playing":
            s.players[CUR].playpause()
            stus = "Paused"

        if stus == "Paused":
            player_last_status['addr'] = s.players[CUR].track['addr']
            player_last_status['position'] = s.players[CUR].position

        s.funlock()
        if pfile:
            pickle.dump(player_last_status,  pfile)
        else:
            return player_last_status

    def restore_session(s, pfile):
        if type(pfile) == file:
            player_status = pickle.load(pfile)
        else:
            player_status = pfile
        s.flock()

        if player_status.has_key('addr'):
            try:
                song = cue.addr_to_track(player_status['addr'])
            except:
                song = None
            pass
            if song:
                s.players[CUR].track = song
                s.players[CUR].position = player_status['position']
                try:
                    s.players[CUR].get_equalizer().Load( config.GetEqualizer(s.players[CUR].track) )
                    s.inform_all(s.players[CUR].track, s.players[CUR].get_equalizer())
                except:
                    pass
                s.track = song
                try:
                    s.gui.update_track(song)
                    s.gui.on_pause(song)
                except:
                    pass
        s.funlock()
    def get_current_track(s):
        return s.track

if __name__ == "__main__":
    from thread_system.task_workers import TaskWorkers
    config.Load()
    config.LoadEqualizers()
    workers = TaskWorkers(3)
    Initialize(workers)
    #bs = BasicPlayer(1)
    #bs = AudioPlayer()
    bs = AudioCrossFadePlayer(1)
    track={}
    track["addr"]="/home/hippy/love/lossless/Donovan/2004 - Beat Cafe/01-Donovan-Love_Floats.flac"
    track["file"]=track["addr"]
    track["begin"]="1:10.2"
    track["end"]="1:23.2"
    def test_player():
        #bs.add_playing_task()
        bs.play_track(track)
        track['addr']="/home/hippy/love/lossless/Donovan/2004 - Beat Cafe/02-Donovan-Poormans_Sunshine.flac"
        track["file"]=track["addr"]
        track["begin"]="0:30.0"
        time.sleep(8)
        bs.play_track(track)
    thr = Thread(target=test_player)
    thr.start()
    loop = GObject.MainLoop()
    loop.run()
