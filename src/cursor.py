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

import random
from media_fs import is_cue_file
from threading import Semaphore
from useful import get_id, is_track, is_track2
from sets import config

def is_cue(entry):
    if entry['type'] in ['cue']:
        return True
    return False

class Cursor:
    def __init__(s, pc, trackno, storage, image=config.audio_player_cursors[0]):
        s.pc = pc
        s.pos = trackno
        s.image = image
        s.storage = storage

    def get_type(s):
        return 0 if s.pc.ctrack == s else 1

    def get_track(s):
        try:
            track = s.storage.elements[s.pos]
            if not is_track(track):
                return None
            return track
        except:
            return None

    def destroy(s):
        try:
            s.pc.on_cursor_destroy(s)
        except:
            pass
    

class PlayerCursor:
    def __init__(s, player):
        s.ctrack = None #current track
        s.ntrack = None #next track
        s.history = [] #played tracks
        s.player = player
        #s.repeat  = player.repeat
        #s.shuffle = player.shuffle
        s.player.cursor = s
        s.sm = Semaphore(1)
    def lock(s):
        s.sm.acquire()

    def unlock(s):
        s.sm.release()

    def on_cursor_destroy(s, cursor):
        s.lock()
        if s.ctrack == cursor:
            s.ctrack = None
        elif s.ntrack == cursor:
            s.ntrack = None
        s.unlock()

    def disconnect_cursor(s, cursor):
        cursor.storage.disconnect_cursor(cursor)
        cursor.pc = None
        cursor.storage = None
        if cursor == s.ctrack:
            del s.ctrack
            s.ctrack = None
        elif cursor == s.ntrack:
            del s.ntrack
            s.ntrack = None

    def play(s, storage, pos):
        s.lock()
        if s.ctrack != None:
            s.disconnect_cursor(s.ctrack)

        s.ctrack = Cursor(s, pos, storage, config.audio_player_cursors[0])
        storage.cursors.append(s.ctrack)
        s.unlock()
    
    def set_current(s, storage, addr):
        s.lock()
        if s.ctrack != None:
            s.unlock()
            return
        for n,e in enumerate(storage.elements):
            if is_track(e) and e.get('addr', '') == addr:
                s.ctrack = Cursor(s, n, storage, config.audio_player_cursors[0])
                storage.cursors.append(s.ctrack)
                break
        s.unlock()

    def set_next(s, storage, addr):
        s.lock()
        if s.ntrack != None:
            s.unlock()
            return
        for n,e in enumerate(storage.elements):
            if is_track(e) and e.get('addr', '') == addr:
                s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                storage.cursors.append(s.ntrack)
                s.player.on_next_track(storage[n])
                break
        s.unlock()

    def set_next_track(s, storage, pos):
        s.lock()
        try:
            if is_track(storage.elements[pos]):
                if s.ntrack != None:
                    s.disconnect_cursor(s.ntrack)
                s.ntrack = Cursor(s, pos, storage, config.audio_player_cursors[1])
                storage.cursors.append(s.ntrack)
                storage.pcursorup()
                s.player.on_next_track(storage[pos])
                s.unlock()
                return True
        except:
            pass
        s.unlock()
        return False
    
    def get_addrs_by_storage(s, storage):
        s.lock()
        c = None
        n = None

        if s.ctrack and s.ctrack.storage == storage:
            track = s.ctrack.get_track()
            if track:
                c = get_id(track)
        if s.ntrack and s.ntrack.storage == storage:
            track = s.ntrack.get_track()
            if track:
                n = get_id(track)
            
        s.unlock()
        return (c,n)
    def set_cursors(s, storage, addrs):
        s.lock()
        try:
            if not s.ctrack and addrs[0]:
                for n,e in enumerate(storage.elements):
                    if is_track(e) and e.get('addr', '') == addrs[0]:
                        s.ctrack = Cursor(s, n, storage, config.audio_player_cursors[0])
                        storage.cursors.append(s.ctrack)
                        break

            if not s.ntrack and addrs[1]:
                for n,e in enumerate(storage.elements):
                    if is_track(e) and e.get('addr', '') == addrs[1]:
                        s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                        storage.cursors.append(s.ntrack)
                        s.player.on_next_track(storage[n])
                        break
        except:
            pass
        s.unlock()
    
    def calculate_next_by_storage(s, storage, path = None):
        s.lock()
        numbers = []
        direction = s.get_direction()

        if path:
            if is_cue_file(path):
                for n,track in enumerate(storage.elements):
                    if is_cue(track) and path in track.get('addr', "") > 0:
                        numbers.append(n)
            else:
                for n,track in enumerate(storage.elements):
                    if is_track2(track) and path in track.get('addr', ""):
                        numbers.append(n)
                if numbers == []:
                    for n,track in enumerate(storage.elements):
                        if is_cue(track) and path in track.get('file', ""):
                            numbers.append(n)
            if numbers != []:
                if s.ntrack != None:
                    s.disconnect_cursor(s.ntrack)

        elif s.ctrack != None and s.ctrack.storage == storage:
            if s.ntrack != None:
                s.disconnect_cursor(s.ntrack)
            s.calculate_next()
            s.unlock()
            return

        elif s.player.repeat:
            for n,track in enumerate(storage.elements):
                if is_track2(track):
                    numbers.append(n)
        else:
            for n,track in enumerate(storage.elements):
                if is_track2(track) and track.get('playback_num',0) == 0:
                    numbers.append(n)

        if numbers == []:
            s.unlock()
            return

        if s.ntrack != None:
            s.disconnect_cursor(s.ntrack)

        if s.player.shuffle:
                s.ntrack = Cursor(s, random.choice(numbers), storage, config.audio_player_cursors[1])
                storage.cursors.append(s.ntrack)
                s.unlock()
                return
        if direction == 0:
            s.ntrack = Cursor(s, numbers[0], storage, config.audio_player_cursors[1])
        else:
            s.ntrack = Cursor(s, numbers[-1], storage, config.audio_player_cursors[1])
        storage.cursors.append(s.ntrack)
        s.unlock()


    def get_direction(s):
        direction = s.player.direction
        if direction == 2:
            direction = 0 if s.player.zigzag else 1
            s.player.zigzag = 1 - s.player.zigzag
        return direction

    def calculate_next(s, ctrack=None, direction = None):
        if s.ctrack == None:
            if ctrack == None:
                return
        elif ctrack == None:
            ctrack = s.ctrack

        if s.ntrack != None:
            return
        storage = ctrack.storage
        if not storage.nol:
            return
        if direction == None:
            direction = s.get_direction()
        pos = ctrack.pos
        if s.player.shuffle == False:

            if direction == 3: #one track
                s.ntrack = Cursor(s, pos, storage, config.audio_player_cursors[2])
                storage.cursors.append(s.ntrack)
            elif s.player.repeat == True: # repeat
                if direction == 0: 
                    for n,track in enumerate(storage.elements[pos+1:]):
                        n += pos + 1
                        if is_track2(track):
                            s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                            storage.cursors.append(s.ntrack)
                            break
                    if s.ntrack == None:
                        for n,track in enumerate(storage.elements):
                            if is_track2(track):
                                s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                                storage.cursors.append(s.ntrack)
                                break
                else:
                    for n in  reversed(range(pos)):
                        track = storage.elements[n]
                        if is_track2(track):
                            s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                            storage.cursors.append(s.ntrack)
                            break
                    if s.ntrack == None:
                        for n in reversed(range(storage.nol)):
                            track = storage.elements[n]
                            if is_track2(track):
                                s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                                storage.cursors.append(s.ntrack)
                                break
            else: #don't repeat
                if direction == 0:
                    for n,track in enumerate(storage.elements[pos+1:]):
                        n += pos + 1
                        if is_track2(track) and not track.get('playback_num',0):
                            s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                            storage.cursors.append(s.ntrack)
                            return
                    if pos == 0:
                        return
                    for n,track in enumerate(storage.elements[:pos]):
                        if is_track2(track) and not track.get('playback_num',0):
                            s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                            storage.cursors.append(s.ntrack)
                            return
                else:
                    for n in  reversed(range(pos)):
                        track = storage.elements[n]
                        if is_track2(track) and not track.get('playback_num',0):
                            s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                            storage.cursors.append(s.ntrack)
                            break
                    if s.ntrack == None:
                        for n in reversed(range(storage.nol)):
                            track = storage.elements[n]
                            if is_track2(track) and not track.get('playback_num',0):
                                s.ntrack = Cursor(s, n, storage, config.audio_player_cursors[1])
                                storage.cursors.append(s.ntrack)
                                break
            return
        else: #Shuffle
            numbers = []
            if s.player.repeat:
                for n,track in enumerate(storage.elements):
                    if is_track2(track):
                        numbers.append(n)
            else:
                for n,track in enumerate(storage.elements):
                    if is_track2(track) and track.get('playback_num',0) == 0:
                        numbers.append(n)
            if numbers:
                s.ntrack = Cursor(s, random.choice(numbers), storage, config.audio_player_cursors[1])
                storage.cursors.append(s.ntrack)
    
            
    def reshufle(s):
        s.lock()
        if s.ctrack:
            if s.ntrack:
                if s.ntrack.storage != s.ctrack.storage:
                    s.unlock()
                    return
                s.ntrack.storage.cursors.remove(s.ntrack)
                s.ntrack = None
                #s.ntrack.destroy()
            s.calculate_next()
            s.ctrack.storage.pcursorup()
            if s.ntrack and s.ntrack.storage:
                s.player.on_next_track(s.ntrack.storage[s.ntrack.pos])
        s.unlock()


        
    def deactive(s):
        s.lock()
        s.ntrack.storage.cursors.remove(s.ntrack)
        s.ntrack.storage.pcursorup()
        s.ntrack = None
        s.ctrack.storage.cursors.remove(s.ctrack)
        s.ctrack.storage.pcursorup()
        s.ctrack = None
        s.unlock()


    def prev_track(s):
        pass

    def next_track(s, p=True):
        s.lock()
        if s.ctrack == None:
            if s.ntrack == None:
                s.unlock()
                return None
            s.ntrack.image = config.audio_player_cursors[0]
            s.ctrack = s.ntrack
            s.ntrack = None
        else:
            s.disconnect_cursor(s.ctrack)
            if s.ntrack == None:
                s.unlock()
                return None
            s.ntrack.image = config.audio_player_cursors[0]
            s.ctrack = s.ntrack
            s.ntrack = None

        track =  s.ctrack.get_track()
        if track:
            if p:
                s.player.play_track(track)
            track['playback_num'] = track.get('playback_num', 0) + 1
            s.ctrack.storage.reshort_no(s.ctrack.pos)
            
        s.calculate_next()
        if s.ntrack:
            s.player.on_next_track(s.ntrack.storage[s.ntrack.pos])
        s.ctrack.storage.pcursorup()
        s.unlock()

