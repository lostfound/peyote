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


from __future__ import with_statement
from useful import *
import os.path, fs.auto
import media_fs
from panel_fs import PFS
from thread_system.thread_polls import polls
from time import time
import cue
from vk import vk_api

import gettext
_ = localise

class PPlaylistThread:
    def pl_progress_maximum(s, m):
        s.panel.process.set_progress(m, _("Tracks"))
        #s.panel.progress.set_progress(0, m, _("Tracks"))

    def pl_progress_up(s, n):
        s.panel.process.increment()
        #try:
        #    s.panel.progress.update_progress(0, int(n))
        #except Exception,e:
        #    pass


    def thread_vksearch_tracks( s, artist, title, accurate = False ):
        s.busy.set()
        try:
            s.panel.process.print_text_message(_(u"Please, wait ..."))
            s.panel.refresh()
            vk = vk_api()
            ret = vk.audio_search(artist, title, accurate)
            if ret != None:
                s.storage.append( ret )
            else:
                err = vk.get_error()
                errs = [ err ]
                while len(errs[-1]) >= s.width - 4:
                    err0 = errs[-1][:s.width - 4]
                    err1 = errs[-1][s.width - 4:]
                    errs[-1] = err0
                    errs.append( err1 )
                s.panel.run_yesno(_(u" error "), errs, [_(u"<Let It Be>")])
                s.question = True
                s.cmd = "error"
        except Exception,e:
            pass
        s.update_total_time()
        try:
            s.panel.head(s.location)
            s.print_info()
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()

    def thread_search_tracks( s, wanted, locations ):
        s.busy.set()
        try:
            s.panel.process.print_text_message(_(u"Please, wait ..."))
            s.panel.refresh()
            for location in locations:
                media_fs.search_track(location, wanted, s)
        except Exception,e:
            pass
        s.update_total_time()
        try:
            s.panel.head(s.location)
            s.print_info()
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()

    def thread_add_tracks_to_playlist( s, elements, copymode ):
        s.busy.set()
        try:
            #s.panel.run_progress(_(" add "), [["", _("Songs are being added"), u"", u""]])
            s.panel.process.print_text_message(_("Songs are being added"))

            tocopy=[]
            for elm in elements:
                if type(elm) == dict and is_track(elm):
                    tocopy.append(elm)
                elif type(elm) == dict and elm['type'] in ['dir']:
                    tracks = media_fs.list_dir(elm['path'])
                    tocopy += tracks

            for e in tocopy:
                if e.has_key('depth'):
                    del e['depth']

            tocopy = filter(is_track2, tocopy)
            tm = time()
            for track in tocopy:
                track['timestamp'] = tm
                tm += 0.00001
            
            if copymode == 1:
                s.storage.insert(tocopy, s.panel.pos)
                s.panel.redraw()
                s.panel.refresh()
            elif copymode == 0:
                for elm in tocopy:
                    s.storage.append([elm])
        except:
            pass
        s.update_total_time()
        try:
            s.print_info()
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()
        
    def thread_open_playlist(s, pos_id = None):
        s.busy.set()
        try:
            s.storage.fill([])
            #s.panel.run_progress(_(" open the playlist "), [["", _("Playlist is being opened"), u"", u""]])
            s.panel.process.print_text_message( _(" open the playlist ") )
            try:
                s.playlist.open_playlist(s.location, s)
            except Exception,e:
                pass
            marks = []
            pos = 0
            if s.played_songs != [] or s.marked_entries != []:
                for i, song in enumerate(s.playlist.tracks):
                    if song.get('addr',"") in s.played_songs:
                        song['playback_num'] = 1
                        s.played_songs.remove(song.get('addr',""))
                    if song.get('addr',"") in s.marked_entries:
                        marks.append(i)
                        s.marked_entries.remove(song.get('addr',""))
                    if pos_id and get_id(song) == pos_id:
                        pos = i
                        pos_id = None
                    if s.played_songs == [] and s.marked_entries == [] and not pos_id:
                        break
            tm = time()
            for track in s.playlist.tracks:
                if not track.get('timestamp'):
                    track['timestamp'] = tm
                tm += 0.00001

            s.storage.fill(s.playlist.tracks)
            s.panel.pos = pos
            s.played_songs = []
            s.marked_entries = []
            for i in marks:
                s.storage.marked_elements[i] = 1
        except:
            pass
        s.update_total_time()
        try:
            s.print_info()
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()
    

class PPlaylist(PPlaylistThread):

    def on_search_track(s, track):
        if is_track2(track):
            tm = time()
            track['timestamp'] = tm
            s.storage.append( [ track ] )
            s.panel.process.print_text_message(_(u"Please, wait ..."))

    def open_playlist(s, pos_id = None):
        s.panel.head(s.location)
        s.panel.refresh()
        s.stop_thread_flag = False
        s.AddTask(s.thread_open_playlist, [pos_id] )

    def increase_playback(s,no):
        track = s.storage.elements[no]
        track['playback_num'] = 1 + track.get('playback_num', 0)

    
    def enter(s):
        if s.question:
            PPlaylist.question_enter(s)
            return

    def rename(s):
        if s.storage.marked_elements.count(True) > 1:
            marked_elements = s.storage.get_marked_elements()
            marked_numbers = s.storage.get_marks()

            name = marked_elements[0].get('addr', "")
            before = name
            after = name
            bodies = []
            addrs = set( map(lambda x: x['addr'], marked_elements) ) 
            if len(addrs) == 1:
                addr = s.panel.rename(addrs.pop())
                if addr:
                    track = cue.get_track_by_addr(addr, None, None)
                    if track:
                        for elm,no in zip(marked_elements, marked_numbers):
                            track = dict(track)
                            if elm.get('timestamp'):
                                track['timestamp'] = elm.get('timestamp')
                            else:
                                track['timestamp'] = time()
                            s.storage.elements[no] = track
                            s.storage.reshort_no(no)
                        s.panel.redraw()
                        s.panel.refresh()
                return

            for elm in marked_elements[1:]:
                if elm.has_key('addr'):
                    name = elm['addr'] 
                    if before != "":
                        lb = min( len(before), len(name) )
                        for l in reversed( range(lb) + [lb] ):
                            before = before[:l]
                            if before == name[:l]:
                                name = name[l:]
                                break
                    if after != "":
                        la = min ( len(after), len(name) )
                        for l in reversed( range(la) + [la] ):
                            if after == name[-l:]:
                                break
                            after = after[-l+1:]

            for elm,no in zip(marked_elements,marked_numbers ):
                if elm.has_key('addr'):
                    name = elm['addr']
                    name = name[len(before):]
                    if len(after) > 0:
                        name = name[:-len(after)]
                    bodies.append((name, elm, no))


            speeds = dict()
            #########without *
            if  bodies != []:
                mask = s.panel.rename(before + '*' + after)
                if mask != None and mask.count('*') == 1:
                    
                    before = mask[:mask.find('*')]
                    after  = mask[mask.find('*') + 1:]
                    for name,elm,no in bodies:
                        addr = before + name + after
                        #stream check
                        track = cue.get_track_by_addr(addr, None, speeds)
                        if track:
                            if elm.get('timestamp'):
                                track['timestamp'] = elm.get('timestamp')
                            else:
                                track['timestamp'] = time()
                            s.storage.elements[no] = track
                            s.storage.reshort_no(no)
        else:
            pos = s.panel.pos
            elm = s.storage[pos]
            if elm['type'] != 'stream':
                addr = s.panel.rename(elm.get('addr', ''))
                if not addr:
                    return
                track = cue.get_track_by_addr(addr)
                if track:
                    if elm.get('timestamp'):
                        track['timestamp'] = elm.get('timestamp')
                    else:
                        track['timestamp'] = time()
                    s.storage.elements[pos] = track
                    s.storage.reshort_no(pos)
                else:
                    return
            else:
                s.panel.run_yesno( _(' Edit '), \
                    [_(u'Title:'), [ elm.get('station_name', u'') ],\
                    _(u"URL:"), [elm.get('addr', u'')], ""],\
                    [_(u'<Ok>'), _(u'<Cancel>')] )
                s.question = True
                s.cmd = "audioedit"
                pass
                        
            pass
        s.panel.redraw()
        s.panel.refresh()

    def back(s):
        if s.playlist.was_changed(s.storage.elements):
            s.playlist_back_args = None
            s.panel.run_yesno(_(u" quit "), [_("Playlist was modified,"), _("save with exit?"), ""], [_("<Yes>"), _("<No>"), _("<Cancel>")])
            s.question = True
            s.cmd = "playlist_back"
        
        else:
            playlist_name = os.path.basename(s.location)
            split_location = os.path.split(s.location)
            s.set_location ( split_location[0] )
            if s.type == "fs":
                PFS.open_location(s,playlist_name)

    def vpaleve_search(s):
        if s.question or s.busy.is_set():
            return
        s.panel.run_yesno(_(' Search on vk.com '), [_(u'Artist:'),[""], _(u"Title:"), [""]],
            [_(u'<Accurate'), _(u'Search>'), _(u'<Cancel>')])
        s.question = True
        s.cmd = "vk:audiosearch"

    def question_enter(s):
        if s.cmd == "audioselect":
            PFS.question_enter(s)
        elif s.cmd == "playlist_back":
            playlist_name = os.path.basename(s.location)
            rc = s.panel.yesno.enter()
            del s.panel.yesno
            s.panel.yesno = None
            s.question = False

            if rc == 2:
                s.panel.redraw()
                s.panel.refresh()
                return
            elif rc == 0:
                rc = s._save()
                if not rc:
                    return

            if s.playlist_back_args != None:
                s.move_by_title(s.playlist_back_args, False)
                return

            split_location = os.path.split(s.location)
            s.set_location ( split_location[0] )
            if s.type == "fs":
                s.fs.open_dir(s.location)
                s.storage.fill(s.fs.get_elements())
                s.panel.head(s.location)
                for n,elm in enumerate (s.storage.elements):
                    if elm.get('basename','') == playlist_name or elm.get('name','') == playlist_name:
                        s.panel.select(n)
                        break
                s.panel.refresh()
                s.print_info()

        elif s.cmd == "save":
            rc = s.panel.yesno.enter()
            location = fs.auto.abspath ( s.panel.yesno.inputs[0][1], s.location )
            s.panel.yesno = None
            s.panel.redraw()
            s.panel.refresh()
            s.question = False
            if rc == 2:
                return
            if location == s.location:
                location = None
            if rc == 1:
                relative = True
            else:
                relative = False
            rc = s._save(location, relative)
            if rc and location:
                s.location = location
                s.panel.head(s.location)
                s.panel.refresh()

        elif s.cmd == "error":
            s.panel.yesno = None
            s.question = False
            s.panel.redraw()
            s.panel.refresh()
        elif s.cmd == "audioedit":
            rc = s.panel.yesno.enter()
            title = s.panel.yesno.inputs[0][1]
            url = s.panel.yesno.inputs[1][1]

            del s.panel.yesno
            s.panel.yesno = None
            s.question = False
            
            if rc == 0:
                track = s.storage[s.panel.pos]
                track['station_name'] = title
                track['addr'] = url
                s.storage.reshort_no(s.panel.pos)
            s.panel.redraw()
            s.panel.refresh()

        elif s.cmd == "audiosearch":
            rc = s.panel.yesno.enter()
            title = s.panel.yesno.inputs[0][1]
            artist = s.panel.yesno.inputs[1][1]
            album = s.panel.yesno.inputs[2][1]

            del s.panel.yesno
            s.panel.yesno = None
            s.question = False
            s.panel.redraw()
            s.panel.refresh()
            locations = s.cmd_args
            del s.cmd_args

            if rc == 0 or rc == 1 and (s.type == 'playlist'):
                wanted = dict()
                if title != "":
                    wanted['title'] = title.split()
                if artist != "":
                    wanted['performer'] = artist.split()
                if album != "":
                    wanted['album'] = album.split()
                if wanted != dict():
                    location = s.location
                    if rc == 0:
                        s.set_location( os.path.join('/', "#SEARCH"), tp = "playlist" )
                        s.storage.fill([])
                        s.playlist.blank_playlist()

                    s.stop_thread_flag = False
                    s.AddTask(s.thread_search_tracks, [wanted, locations])
            else:
                pass
        elif s.cmd == "vk:audiosearch":
            rc = s.panel.yesno.enter()
            artist = s.panel.yesno.inputs[0][1]
            title = s.panel.yesno.inputs[1][1]

            del s.panel.yesno
            s.panel.yesno = None
            s.question = False
            s.panel.redraw()
            s.panel.refresh()
            if rc != 2 and ( title != "" or artist != "" ):
                accurate = False if rc == 1 else True
                s.stop_thread_flag = False
                s.AddTask(s.thread_vksearch_tracks, [artist, title, accurate])
                

    def _save(s, location = None, relative = False):
        if not location:
            location = s.location
        s.playlist.tracks = []
        for e in s.storage:
            s.playlist.tracks.append(e)

        #backup first!
        try:
            with fs.auto.open(location, 'r') as f:
                backup = f.read()
        except Exception,e:
            backup = None

        try:
            s.playlist.save_playlist(location, relative)
        except Exception, e:
            if backup != None:
                try:
                    with fs.auto.open(location, 'w') as f:
                        f.write(unicode2(backup))
                except:
                    pass
            try:
                message = unicode2(e)
            except:
                try:
                    message = unicode2(e[1])
                except:
                    message = _("error")
            s.panel.run_yesno(_(" error "), [message[-(s.width - 5):], ""], [_("<Let It Be>")])
            s.question = True
            s.cmd = "error"
            return False
        return True


    def delete(s):
        if s.storage.marked_elements.count(True) != 0:
            s.storage.remove_marked()
        else:
            s.storage.remove(s.panel.pos)
        s.panel.on_remove()
        s.update_total_time()
        s.print_info()
        s.panel.refresh()


    def save(s):
        s.panel.run_yesno(_(" save playlist as "), [_("Playlist Path"), [s.location], ""], 
            [_("<Save>"), _("<Relative paths>"), _("<Cancel>")])
        s.question = True
        s.cmd = "save"

    def on_copy(s, elements, source_location, copymode=0):
        s.AddTask(s.thread_add_tracks_to_playlist, [ elements,copymode ] )
        return True

