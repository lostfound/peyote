#!/usr/bin/env python
# -*- coding: utf8 -*-

#
# Copyright (C) 2010-2011  Platon Peacel☮ve <platonny@ngs.ru>
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
                                    
import curses, os, random, sys
from nc_panel.semaphores import curses_lock, curses_unlock
from threading import Semaphore
from time import time
from sets import config,get_performer_alias,get_album_alias,Dice

PAIR_PLAYER = 5
c = curses
workers = None
def Initialize(task_workers):
    global workers
    workers = task_workers

class PlayerCursesGUI:
    def __init__(s, parent, colors):
        s.parent = parent
        s.win = None
        s.x = None
        s.colors = colors

        s.genwin()

        s.x11 = True if os.getenv('DISPLAY') else False

        s.reset_xtheader()

        s.track = None
        s.playing_bar = None
        s.aux_sem = Semaphore(1)
        s.aux_time = None
    def genwin(s):
        curses_lock()
        try:
            size_yx = s.parent.getmaxyx()
            s.x = size_yx[1]
            if s.win != None:
                del s.win
            s.win = s.parent.subwin(2, size_yx[1], size_yx[0]-3+int(config.hide_keybar), 0 )
            s.win.bkgdset(' ', c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
            s.win.bkgd(' ', c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
        except:
            pass
        curses_unlock()

        try:
            if s.track != None:
                s.update_track(s.track)
            else:
                curses_lock()
                try:
                    s.win.erase()
                except:
                    pass
                curses_unlock()
                s.refresh()
        except:
            pass

    def hide_aux_task(s, fx = None):
        s.aux_sem.acquire()
        try:
            difftime = s.aux_time - time()
            if difftime > 0:
                workers.add_timed_task(s.hide_aux_task, [fx], delay = difftime )
            else:
                s.aux_time = None

                curses_lock()
                s.win.addstr(1, 55, ' '*10, c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
                curses_unlock()

                try:
                    if fx != None:
                        fx()
                except:
                    pass
                s.aux_sem.release()
                s.refresh()
                return
        except:
            pass
        s.aux_sem.release()

    def print_aux(s, info, delay = 2, fx = None):
        curses_lock()
        try:
            s.win.addstr(1, 55, ' '*10, c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
            s.win.addstr(1, 55, info[:10].encode('utf-8'), c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
        except:
            pass
        curses_unlock()
        s.aux_sem.acquire()
        if s.aux_time:
            s.aux_time = time() + delay
        else:
            s.aux_time = time() + delay
            workers.add_timed_task(s.hide_aux_task, [fx], delay = delay )
        s.aux_sem.release()
        s.refresh()

    def update_times(s, pos, duration, pos_ns, duration_ns):
        if duration_ns <= 0:
            timestr = unicode(pos) + " [ stream ] "
            s.playing_bar = None
            tstr_len = len(timestr)
            playing_bar = " "*(45 - tstr_len)
        else:
            timestr = unicode(pos) + "/" + unicode(duration) + " "
            tstr_len = len(timestr)
            s.playing_bar = [ tstr_len + 1, 46 ]
            pp = float(pos_ns)/float(duration_ns)
            pb_len = (45 - tstr_len)

            playing_bar = config.playing_bar_chars[0]*int(float(pb_len*pp) )
            playing_bar += config.playing_bar_chars[1]*( 45 - tstr_len - len(playing_bar) )
        playing_bar = playing_bar[:45-tstr_len]

        curses_lock()
        try:
            s.win.addstr(1, 1, timestr.encode('utf-8'),c.color_pair(s.colors['player time'].get_pair_no())|s.colors['player body'].get_args())
            s.win.addstr(1, 1 + tstr_len, playing_bar.encode('utf-8'),c.color_pair(s.colors['player time'].get_pair_no())|s.colors['player body'].get_args())
        except:
            pass
        curses_unlock()

        s.refresh()

    def refresh(s):
        curses_lock()
        try:
            s.win.refresh()
        except:
            pass
        curses_unlock()

    def update_track(s, track):
        if type(track) == dict:
            X = s.x - 1
            s.track = track
            first_line = u''
            #title|performer|album
            tdl = config.playing_track_left.print_song(track)
            tdl_len = len(tdl)
            if tdl_len + 2 >= X:
                first_line = tdl
            else:
                tdr = config.playing_track_right.print_song(track)
                tdr_len = len(tdr)
                if tdl_len == 0:
                    first_line = tdl
                elif tdr_len + 2 + tdl_len <= X:
                    spaces_len = X - tdl_len - tdr_len
                    first_line = tdl + spaces_len*u' ' + tdr
                else:
                    first_line = tdl + u'  ' + tdr[ tdr_len + tdl_len + 2 - X:]

            curses_lock()
            try:
                s.win.erase()
                s.win.addstr(0, 1, first_line[:X].encode('utf-8'), c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
            except:
                pass
            curses_unlock()
            if X - 56 > 3:
                Xb = X - 55
                tdb = config.playing_track_bottom.print_song(track)
                tdb_len = len(tdb)
                if tdb_len != 0:
                    if Xb > tdb_len:
                        line = (Xb-tdb_len)*u' ' + tdb
                    else:
                        line = tdb[-Xb:]
                    curses_lock()
                    try:
                        s.win.addstr(1,56, line[:Xb].encode('utf-8'))
                    except:
                        pass
            curses_unlock()

            s.print_xtheader(track)
            s.refresh()
    def on_pause(s, track):
        try:
            track_name = track.get('title', '') + ' | ' + track.get('performer')

            if s.x11:
                curses_lock()
                try:
                    sys.stdout.write('\033]0;' + '|| ' + track_name + ' \007')
                except:
                    pass
                curses_unlock()

            s.refresh()
        except:
            pass

    def reset_xtheader(s):
        curses_lock()
        try:
            if s.x11:
                sys.stdout.write('\033]0;' + '(: peyote :)' + ' \007')
            s.win.addstr(1, 1, " "*47, c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
            s.playing_bar = None
        except:
            pass
        curses_unlock()
        s.refresh()

    def print_xtheader(s, track):
        try:
            track_name = track.get('title', '') + ' | ' + track.get('performer')
            if s.x11:
                curses_lock()
                try:
                    sys.stdout.write('\033]0;' + '|> ' + track_name + ' \007')
                except:
                    pass
                curses_unlock()
            s.refresh()
        except:
            pass
        
    def print_shuffle(s, shuffle):
        if shuffle:
            s.win.addstr(1, 48, (Dice() + ' ').encode('utf-8'))
        else:
            s.win.addstr( 1, 48, (config.repeat_char[0] + u" ").encode('utf-8') )

        s.refresh()

    def print_repeat(s, repeat):
        if repeat:
            s.win.addstr(1,50, (u"%s " % config.track_status_chars[0]).encode('utf-8'))
        else:
            s.win.addstr(1,50, (u"%s " % config.track_status_chars[1]).encode('utf-8'))
        s.refresh()

    def print_direction(s, direction_no):
        curses_lock()
        try:
            s.win.addstr(1,52, (config.direction_chars[direction_no]+' ').encode('utf-8'))
        except:
            pass
        curses_unlock()

        s.refresh()
    
    def print_equalizer(s, hold):
        sym = config.equalizer_holding_chars[1] if hold else config.equalizer_holding_chars[0]
        curses_lock()
        try:
            s.win.addstr(1,54, sym.encode('utf-8'))
        except:
            pass
        curses_unlock()

        s.refresh()
        

    def mouse_click(s, x, y):
        if y == 1:
            if s.playing_bar and s.playing_bar[0] <= x < s.playing_bar[1]:
                return float(x - s.playing_bar[0])/float(s.playing_bar[1] - s.playing_bar[0])
            if  48 <= x < 50:
                return "shuffle"
            elif 50<= x <52:
                return "repeat"
            elif 52<= x <54:
                return "direction"
            elif 54<= x <56:
                return "equalizer"
        return "playpause"
            
