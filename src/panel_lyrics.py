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

from useful import unicode2, is_track, localise
from threading import Semaphore
import gettext
from lyrics.lyrics import search_lyrics
from thread_system.thread_polls import polls
from sets import config, get_performer_alias

_ = localise

lyrics_sem = Semaphore(1)
class PLyrics:
    def lyrics_init(s):
        s.follow_the_player = True
        s.storage.clear()
        s.panel.redraw()
        s.artist = u""
        s.title =  u""
        track = s.callback.get_current_track()
        if track:
            s.show_lyrics(track)
        s.callback.subscribe(s.on_next_track)
    def lyrics_deinit(s):
        s.callback.unsubscribe(s.on_next_track)

    def _load_lyrics_thread(s, track):
        s.busy.set()
        lyrics_sem.acquire()
        try:
            #s.panel.run_progress(_(" Getting lyrics "), [[_("Please, wait ...")]])
            s.panel.process.print_text_message(_("Please, wait ..."))
            s.panel.refresh()
            artist = get_performer_alias( track.get('performer', 'nobody'), 3 )
            title  = track.get('title', '')
            lyrics = search_lyrics(artist, title)
            if lyrics:
                lyrics_entries = unicode2(lyrics).split('\n')
                s.storage.fill(lyrics_entries)
            else:
                lyrics_entries = [ _(u'Not Found') ]
            s.artist = artist
            s.title  = title
            #s.panel.del_progress()

            s.storage.fill( [ {'type': 'lyrics', 'artist' : s.artist, 'title': s.title}, u"" ] + lyrics_entries )
        except:
            pass
        lyrics_sem.release()
        try: s.print_info()
        except: pass
        try: s.panel.redraw()
        except: pass
        try: s.panel.refresh()
        except: pass
        s.busy.clear()

    def on_next_track(s, track, equalizer):
        if s.admittance() and s.follow_the_player:
            s.show_lyrics(track)

    def show_lyrics(s, track):
        s.AddTask(s._load_lyrics_thread, [track] )

    def on_copy(s, elements, source_location, copymode=0):
        for e in elements:
            if is_track(e):
                s.show_lyrics(e)
                break

    def back(s):
        pass
