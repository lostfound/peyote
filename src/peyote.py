#!/usr/bin/python2
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
import sys, os, signal
import curses
import locale, gettext
import select
import traceback
import buttons
import pickle
from time import sleep
from peyote_exec import background

from sets import config,get_performer_alias,get_album_alias, VERSION


from threading import Thread
from useful import unicode2, localise
c = curses

#Globals
dbus_enabled = True
crutch = True

pipes = []
bttons = None
panels = None
nop = 4
colors = None
pair = None
lp = None
cp = None
sp = None
rp = None
w  = None
ap = None
mixer = None
parent_pid = None
player_cursor = None

is_started = True
_ = localise

def init_pairs():
    c.start_color()

def sighandler(signum, frame):
    global w,c
    if signum == signal.SIGWINCH:
        curses_lock()
        try:
            c.endwin()
        except:
            pass
        else:
            if is_started:
                w = c.initscr()
        curses_unlock()
        redraw()
        try:
            if not autopanel():
                redraw()
        except:
            pass

def print_buttons():
    global panels, bttons, cp, lp, rp
    spanel = None if get_opm() else  panels[lp if cp != lp else rp]
    bttons.print_buttons(panels[cp], spanel )

def redraw():
    global panels, pair,colors, nop, cplayer, lp,rp,w, bttons,ap
    for i in range(0, nop):
        if i != lp and i != rp:
            panels[i].redraw()
    #cplayer.parent = w
    cplayer.genwin()

    bttons.genwin(w)
    print_buttons()
    try:
        cplayer.print_shuffle(ap.shuffle)
        cplayer.print_repeat(ap.repeat)
        cplayer.print_direction(ap.direction)
        cplayer.print_equalizer(ap.hold_equalizer)
    except:
        pass
    cplayer.refresh()
    if lp == cp:
        panels[rp].redraw()
        panels[lp].redraw()
    else:
        panels[lp].redraw()
        panels[rp].redraw()
        

def psi_thread():
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, ap
    while True:
        try:
            panels[rp].psi_redraw()
            panels[lp].psi_redraw()
        except:
            pass
        time.sleep(.2)

def autopanel():
    global w
    if not config.autopanel:
        return False

    Y,X = w.getmaxyx()
    
    if X < config.autopanel_width:
        onepanel_mode = True
    else:
        onepanel_mode = False
    if get_opm() != onepanel_mode:
        switch_panel_mode()
        return True
    else:
        return False

def switch_panel_mode():
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, sp
    opm = sw_opm()
    if opm:
        if cp == lp:
            sp = rp
        else:
            sp = lp
    else:
        if sp == cp:
            sp = cp + 1
        if sp >= nop:
            sp = 0
        if cp == rp:
            lp = sp
        else:
            rp = sp
    for n in range ( nop ):
        if opm:
            if n != cp:
                panels[n].show( force = True )
                panels[n].hide()
        else:

            pos = "left" if cp == lp else "right"
            if n == lp:
                panels[n].show(position="left", force = True)
            elif n == rp:
                panels[n].show(position="right", force = True)
            else:
                panels[n].show(position=pos, force = True)
                panels[n].hide()
            if n != cp:
                panels[n].chfocus(False)
    panels[cp].show(force = True, position = "left" if cp == lp else "right")
    panels[cp].chfocus()
    
    print_buttons()

def prev_panel(destroy=False):
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, sp
    if get_opm():
        np = cp - 1 
        if np < 0:
            np = np = nop -1


    else:
        np = cp
        while np == lp or np == rp:
            if np == 0:    np = nop -1
            else:        np -= 1

    panels[cp].hide()
    if destroy:
        panels[cp].destroy()
    if cp == lp:
        panels[np].show()
        lp = np
    else:
        panels[np].show(position="right")
        rp = np
    cp = np
    panels[np].chfocus()
    print_buttons()
    #bttons.print_buttons(panels[cp], panels[lp if cp != lp else rp])

def next_panel():
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w
    if get_opm():
        np = cp + 1
        if np >= nop: 
            np = 0
    else:
        np = cp
        while np == lp or np == rp:
            if np < nop - 1:    np += 1
            else:            np = 0

    panels[cp].hide()
    if cp == lp:
        panels[np].show()
        lp = np
    else:
        panels[np].show(position="right")
        rp = np
    cp = np
    panels[np].chfocus()
    print_buttons()

def new_panel(current_path='locations://'):
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, callback
    panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
    np = nop
    nop += 1
    panels[cp].hide()
    if cp == lp:
        panels[np].show()
        lp = np
    else:
        panels[np].show(position="right")
        rp = np
    panels[np].chfocus()
    cp = np
    print_buttons()

def close_panel():
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, callback, sp
    if nop == 2 or not panels[cp].admittance():
        return
    dp = cp
    prev_panel(destroy=True)

    if lp > dp:
        lp -= 1
    if rp > dp:
        rp -= 1
    if cp > dp:
        cp -= 1
    if get_opm() and sp > dp:
        sp -= 1
        print_buttons()
    nop-=1

    panel=panels.pop(dp)
    del panel

class Callback:
    def restart(s):
        global ap, player_cursor
        tp = 'crossfade' if config.audio_player['crossfade'] else 'standart'
        if ap.type() == tp:
            ap.restart()
            return
        status = ap.get_status()
        #eq = ap.get_eqlzr2()
    
        orders = [ ap.repeat, ap.shuffle, ap.direction, ap.hold_equalizer]
        ssn = ap.store_session()
        subscribers =  ap.subscribers
        ap.exit()
        ap = None
        if tp == 'crossfade':
            ap = player.AudioCrossFadePlayer( 0 )
        else:
            ap = player.AudioPlayer( )
        ap.gui = cplayer
        player_cursor.player = ap
        ap.cursor = player_cursor
        ap.subscribers = subscribers
        ap.restore_session(ssn)
        if tp == 'crossfade':
            if player_cursor.ntrack:
                ap.on_next_track( player_cursor.ntrack.get_track() )
        ap.repeat = orders[0]
        ap.shuffle = orders[1]
        ap.direction = orders[2]
        ap.hold_equalizer = orders[3]
        #for n,e in enumerate(eq):
        #    ap.set_eqlzr( ( n,e ) )

        ap.start()
        if status == 'Playing':
            ap.playpause()

        #ap.restore_session(r)

    def get_equalizer(s):
        return ap.get_equalizer()

    def play_track(s, track):
        return ap.play_track(track)
    
    def get_current_track(s):
        return ap.get_current_track()
    
    def subscribe(s, fx):
        return ap.subscribe(fx)
    
    def unsubscribe(s, fx):
        return ap.unsubscribe(fx)
    def get_cursors_by_storage(s, storage):
        return player_cursor.get_addrs_by_storage(storage)
    def set_cursors(s, storage, cursors):
        player_cursor.set_cursors(storage, cursors)
    def inotify_subscribe(s, panel, path = None):
        if fs_events.inotify_support:
            if path == None:
                fs_events.subscribe(panel.location, panel)
                for e in panel.storage.elements:
                    if e['type'] == 'dir' and e.get('opened'):
                        fs_events.subscribe(e['path'], panel)
            else:
                fs_events.subscribe(path, panel)
    def inotify_unsubscribe(s, panel, path = None):
        if fs_events.inotify_support:
            fs_events.unsubscribe(panel, path)

    def restart_mixer(s):
        mixer.restart()

    def get_mixer_label(s):
        return mixer.get_label()
    
    def mixers(s):
        return mixer.get_labels()
    
    def redraw(s):
        redraw()

callback = Callback()
def notify(track, eq):
    if not config.do_notify:
        return
    try:
        NS = unicode(config.notification_string).replace("%title", track.get('title', ''))
        NS = NS.replace("%artist", track.get('performer', '')).replace("%album", track.get('album', ''))
        NS = NS.replace("%path", track.get('file', track.get('addr','')))
        background(NS)
    except:
        pass

def dbus_responser_thread():
    while is_started:
        command = object.get_command2()
        if not is_started:
            break
        if ap == None:
            object.response ( "" )
        if command[0] == ARTIST:
            try:
                ct = callback.get_current_track()
                if ct:
                    response = get_performer_alias(ct.get('performer', ""), 5 )
                else:
                    response = ""
            except:
                response = ""

            object.response ( response )

        elif command[0] == ALBUM:
            try:
                ct = callback.get_current_track()
                if ct:
                    response = get_album_alias( ct.get('album', ""), 5 )
                else:
                    response = ""
            except:
                response = ""
            object.response ( response )

        elif command[0] == TITLE:
            try:
                if callback.get_current_track():
                    response = callback.get_current_track().get('title', "")
                else:
                    response = ""
            except:
                response = ""

            object.response ( response )

        elif command[0] == STATUS:
            try:
                #response = ap.get_status()
                pass
            except:
                response = ""
    object.exit()


def save_pitch():
    global ap, config
    pitch = ap.get_pitch()
    if pitch == None:
        return
    #find pitch plug
    for e in reversed( config.audio_player['pre_sinks'] ):
        if e[0] == 'pitch' and e[1] == True:
            for n,prop in enumerate(e[2]):
                if prop[0] == 'pitch':
                    e[2][n] = ('pitch', pitch )
                    config.Save()
                    break
            break

KEY_CTRL_IC=532
def main(*args):
    global panels, pair,colors, nop, cplayer, lp,rp,cp, w, bttons,ap, workers, player_cursor, mixer

    player.Initialize(workers)
    player_gui.Initialize(workers)
    mixer = Mixer()
    mixer.restart()
    try:
        if config.audio_player['crossfade']:
            ap = player.AudioCrossFadePlayer( 0 )
        else:
            ap = player.AudioPlayer( )
    except Exception,e:
        #import traceback
        #ex_type, ex, tb = sys.exc_info()
        #traceback.print_tb(tb)
        print "Player initialization failed:", e
        return

    player_cursor = cursor.PlayerCursor(ap)
    panels = []
    ap.subscribe(notify)


    w = c.initscr()
    c.mousemask(0xfffffff)
    c.mousemask(0xff)
    c.meta(1)
    #signal.signal(signal.SIGWINCH, sighandler)
    w.keypad(True)

    c.noecho()
    c.curs_set(False)
    #c.mousemask(3)
    init_pairs()
    c.use_default_colors()
    
    #colors = mc_colors()
    if config.LoadScheme() == False:
        config.SaveScheme()

    colors = config.color_scheme.generate_palette()
    colors = config.color_scheme.generate_colors()
    bttons = buttons.Buttons(colors)
    bttons.genwin(w)

    current_path = os.path.abspath(u".")
    panel_engine.parentw = w
    panel_engine.panel_position('left')
    border = 1

    cplayer = player_gui.PlayerCursesGUI(w, colors)
    ap.gui = cplayer
    opm = False
    #restore an equalizer
    ##for eqband in zip(range(0,10), config.equalizer):
    ##    ap.set_eqlzr(eqband)

    if config.cmd.has_key('locations'):
        #get locations from cmdline
        for loc in config.cmd['locations']:
            panels.append( panel_engine.PEngine( loc, callback, pair, colors, player_cursor) )

        while len(panels) < 2:
            panels.append(panel_engine.PEngine( current_path, callback, pair, colors, player_cursor))

    elif os.path.exists(config.session_file):
        #restore last session
        session = None
        try:
            session = open(config.session_file, 'r')
            firstline = session.readline().rstrip()
            if firstline.count('.') >= 2:
                version = map(lambda x: int(x), firstline.split('.'))
                nop_str = session.readline().rstrip()
            else:
                version = [0, 10, 0]
                nop_str = firstline

            nop = int(nop_str)
            lp = int(session.readline().rstrip())
            rp = int(session.readline().rstrip())
            cp = int(session.readline().rstrip())
            opm = False if session.readline().rstrip() == "False" else True
            border = float(session.readline().rstrip())
            panel_engine.set_pppp(border)
            ap.shuffle = bool(int(session.readline().rstrip()))
            ap.repeat = bool(int(session.readline().rstrip()))
            ap.direction = int(session.readline().rstrip())
            ap.hold_equalizer = bool(int(session.readline().rstrip()))
            if version > [0, 9, 12]:
                ap.zigzag = int(session.readline().rstrip())

            ap.restore_session(session)

            ctrack = pickle.load(session)
            ntrack = pickle.load(session)

            sp = rp if cp == lp else lp
            for i in range(nop):
                panels.append(panel_engine.PEngine( session, callback, pair, colors))
            if ctrack.has_key('panel_id'):
                n = ctrack['panel_id']
                panels[n].set_current_track(player_cursor, ctrack['addr'])
            if ntrack.has_key('panel_id'):
                n = ntrack['panel_id']
                panels[n].set_next_track(player_cursor, ntrack['addr'])
            session.close()
        except Exception,e: #Incorrect session file
            #import debug
            #debug.debug(e)
            #debug.trace()
            opm = False
            if session:
                session.close()
            os.remove( config.session_file )
            panels = []
            cp = None
            panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
            panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
            panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
            panels.append(panel_engine.PEngine( config.default_playlist, callback, pair, colors))

    else:
        panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
        panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
        panels.append(panel_engine.PEngine( current_path, callback, pair, colors))
        panels.append(panel_engine.PEngine( config.DefaultPlaylist(), callback, pair, colors))

    if cp == None:
        nop = len(panels)
        lp = nop - 2
        rp = nop - 1
        cp = lp
        sp = rp
    
    if opm:
        switch_panel_mode()
    else:
        panels[lp].show()
        panels[rp].show(position="right")
        panels[cp].chfocus()
        panels[sp].chfocus(False)
    #bttons.print_buttons(panels[cp], panels[lp if cp != lp else rp])
    print_buttons()

    cplayer.refresh()
    cplayer.print_shuffle(ap.shuffle)
    cplayer.print_repeat(ap.repeat)
    cplayer.print_direction(ap.direction)
    ap.start()


    km = None
    pkl_flag = False
    w.nodelay(1)
    while is_started:
        if km != None:
            #mouse click
            k = km 
            km = None
        elif dbus_enabled:
            command = object.get_command()
            if command: #DBUS HANDLER
                if command[0] == PLAYPAUSE:
                    ap.playpause()
                elif command[0] == NEXTTRACK:
                    ap.next()
                elif command[0] == TAB and not get_opm():
                    sp = cp
                    cp = rp if cp == lp else lp
                    panels[sp].chfocus(False)
                    panels[cp].chfocus()
                    print_buttons()
                    
                elif command[0] == CD:
                    panels[cp].cd( unicode2(command[1]) )
                elif command[0] == CD_AND_PLAY:
                    rc = panels[cp].cd( unicode2(command[1]) )
                    if not rc[1]:
                        panels[cp].play_everything(player_cursor)
                    else:
                        panels[cp].play_path(player_cursor, unicode2(command[1]) )


                elif command[0] == NEWPANEL:
                    new_panel()
                elif command[0] == PREV_PANEL:
                    prev_panel()
                elif command[0] == NEXT_PANEL:
                    next_panel()
                elif command[0] == CLOSE_PANEL:
                    close_panel()
                elif command[0] == REDRAW:
                    curses_lock()
                    try:
                        c.endwin()
                    except:
                        pass
                    else:
                        w = c.initscr()
                    curses_unlock()
                    redraw()
                    
                elif command[0] == ENTER:
                    panels[cp].enter(pc=player_cursor)

                elif command[0] == LEFT:
                    panels[cp].left()
                elif command[0] == RIGHT:
                    panels[cp].right(pc=player_cursor)
                elif command[0] == UP:
                    panels[cp].up()
                elif command[0] == DOWN:
                    panels[cp].down()
                elif command[0] == HOME:
                    panels[cp].home()
                elif command[0] == END:
                    panels[cp].end()
                elif command[0] == PAGEUP:
                    panels[cp].pgup()
                elif command[0] == PAGEDOWN:
                    panels[cp].pgdown()
                elif command[0] == INSERT:
                    panels[cp].mark()
                elif command[0] == GOTO:
                    panels[cp].go_to_player_cursor(pc=player_cursor)
                elif command[0] == SAVE:
                    panels[cp].save()
                elif command[0] == INC_PANEL_WIDTH and not get_opm():
                    panel_engine.left_panel_increase()
                    panels[lp].redraw()
                    panels[rp].redraw()
                elif command[0] == DEC_PANEL_WIDTH and not get_opm():
                    panel_engine.left_panel_decrease()
                    panels[lp].redraw()
                    panels[rp].redraw()
                elif command[0] == PLAY:
                    panels[cp].play_everything(player_cursor)
                continue
            else:
                curses_lock()
                k = w.getch()
                curses_unlock()
        else: # dbus = off
            curses_lock()
            k = w.getch()
            curses_unlock()

        if k == -1:
            sleep(0.04)
            if fs_events.inotify_support:
                fsevents = fs_events.get_events()
                if fsevents != []:
                    for pnl, path in fsevents:
                        pnl.update_fs(path)

        elif k in [ord('q'), ord('Q')]:
            pkl_flag = True
            break
        elif k in [ord('<')]:#prev panel
            if get_opm() or  nop > 2:
                prev_panel()

        elif k in [ord('>')]:#next panel
            if get_opm() or  nop > 2:
                next_panel()

        elif k in [ord('t'), ord('T')]: # new panel
            new_panel()
        elif k in [ord('h'), ord('H')]: # new panel with help
            new_panel('help://')
        elif k in [ord('\\'), ord('|')]: #will be removed
            panels[cp].switch_tree_mode()
        elif k in [ord('y'), ord('Y')]: #close panel
            close_panel()
        elif k in [ord('w'), ord('W')]:    #redraw
            curses_lock()
            try:
                c.endwin()
            except:
                pass
            else:
                w = c.initscr()
            curses_unlock()
            redraw()

        elif k in [ord('c'), ord('C')]:    #CD
            if panels[cp].cd() == True:
                print_buttons()

        elif k in [ord('m'), ord('M')]: #switch fs mode
            panels[cp].switch_mode()
        elif k in [ord('f'), ord('F')]: #show/hide files
            panels[cp].showfiles()
        elif k in [ord('p'), ord('P')]:    #panel mode
            switch_panel_mode()
        elif k in [ord(' ')]: #play/pause
            ap.playpause()
        elif k in [ord('n'), ord('N')]:    #next track
            ap.next()
        elif k in [ord('s'), ord('S')]: #shuffle
            ap.switch_shuffle()
        elif k in [ord('x'), ord('X')]: #direction
            ap.switch_direction()

        elif k in [ord('o'), ord('O')]: #sort/shuffle playlist
            pass
        elif k in [ord('r'), ord('R')]: #repeat
            ap.switch_repeat()
        elif k in [ord('e'), ord('E')]: #hold equalizer
            ap.switch_hold_equalizer()
        elif k in [c.KEY_ENTER, 10]:
            panels[cp].enter(pc=player_cursor)
        elif k in [c.KEY_RIGHT]: #Right
            panels[cp].right(pc=player_cursor)
        elif k in [c.KEY_LEFT]: #Back
            panels[cp].left()
        elif k in [c.KEY_UP]:
            panels[cp].up()
        elif k in [c.KEY_DOWN]:
            panels[cp].down()
        elif k in [c.KEY_HOME]:
            panels[cp].home()
        elif k in [c.KEY_END]:
            panels[cp].end()
        elif k in [c.KEY_PPAGE]: #Page up
            panels[cp].pgup()
        elif k in [c.KEY_NPAGE]: #Page down
            panels[cp].pgdown()
        elif k in [c.KEY_IC]: #insert
            panels[cp].mark()
        elif k in [KEY_CTRL_IC]: #insert
            panels[cp].mark(1)
        elif k in [ord('i'), ord('I')]:
            panels[cp].go_to_mark( k == ord('i') )
        elif k in [ord('*')]:
            panels[cp].mark_all_tracks()
        elif k in [ord('-')]:
            panels[cp].untag_all_tagged_entries()
        elif k in [9]: #tab
            if  get_opm():
                continue
            sp = cp
            cp = rp if cp == lp else lp
            panels[sp].chfocus(False)
            panels[cp].chfocus()
            print_buttons()
        elif k in [c.KEY_F5]:
            if  get_opm():
                continue
            elements = panels[cp].copy()
            if elements != [] and elements != None:
                if panels[cp].type == 'fs':
                    source_location = panels[cp].location
                else:
                    source_location = None
                if panels[sp].type not in ['playlist', 'locations', 'lyrics']:
                    panels[sp].on_copy(elements, source_location )
                    sp = cp
                    cp = rp if cp == lp else lp
                    panels[sp].chfocus(False)
                    panels[cp].chfocus()
                    print_buttons()
                else:
                    panels[sp].on_copy(elements, None, 0)
        elif k in [c.KEY_F4]:
            if  get_opm():
                continue
            elements = panels[cp].copy()
            if elements != [] and elements != None:
                if panels[cp].type == 'fs':
                    source_location = panels[cp].location
                else:
                    source_location = None
                if panels[sp].type not in ['playlist', 'locations']:
                    panels[sp].on_copy(elements, source_location, 1 )
                    sp = cp
                    cp = rp if cp == lp else lp
                    panels[sp].chfocus(False)
                    panels[cp].chfocus()
                    print_buttons()
                else:
                    panels[sp].on_copy(elements, None, 1)

        elif k in [c.KEY_F3]:
            if  get_opm():
                continue
            elements = panels[cp].copy()
            if elements != [] and elements != None:
                if panels[cp].type == 'fs':
                    source_location = panels[cp].location
                else:
                    source_location = None
                if panels[sp].type != 'playlist':
                    panels[sp].on_copy(elements, source_location, 2 )
                    sp = cp
                    cp = rp if cp == lp else lp
                    panels[sp].chfocus(False)
                    panels[cp].chfocus()
                    print_buttons()
                else:
                    panels[sp].on_copy(elements, None, 2)

        elif k in [c.KEY_BACKSPACE, 127]:
            panels[cp].go_to_player_cursor(pc=player_cursor)
        elif k in [c.KEY_F6]:
            if panels[cp].type == 'equalizer':
                panels[cp].resize_equalizer()
            elif not get_opm() and panels[sp].type == 'fs':
                panels[cp].fsmove(panels[sp]._get_target_dir())
        elif k in [c.KEY_F9]:
            panels[cp].rename()
        elif k in [c.KEY_F7]:
            panels[cp].newelement()
        elif k in [c.KEY_F2]:
            panels[cp].save()
        elif k in [c.KEY_F8, c.KEY_DC]:
            panels[cp].delete()
        elif k in [337, 97]: #shift + up
            panels[cp].move("up")
        elif k in [336, 98]: # shift + down 
            panels[cp].move("down")
        elif k in [ord('!')]: #execute
            panels[cp].execute()
        elif k in [27]: #Escape
            panels[cp].cancel()
        elif k in [ord('+')]:
            panels[cp].select()
        elif k in [ord('?')]:
            if panels[cp].type == "playlist":
                pass
                #panels[cp].vpaleve_search()
            else:
                locations = panels[cp].search_tracks()
                if locations:
                    sp = cp
                    cp = rp if cp == lp else lp
                    panels[sp].chfocus(False)
                    panels[cp].chfocus()
                    print_buttons()
                    panels[cp].on_search_tracks(locations)

        elif k in [ord('/')] and panels[cp].type != 'equalizer':
            panels[cp].fast_search()

        elif k in [c.KEY_SRIGHT, ord(')')]:
            ap.seek(10)

        elif k in [c.KEY_SLEFT, ord('(')]:
            ap.seek(-10)

        elif k in [ord('d'), ord('D')]:
            panels[cp].dirsize()
            
        elif k in [ord('1')]:
            panel_engine.left_panel_decrease()
            panels[lp].redraw()
            panels[rp].redraw()
        elif k in [ord('2')]:
            panel_engine.left_panel_increase()
            panels[lp].redraw()
            panels[rp].redraw()
        elif k in [ ord('0') ]:
            mixer.increase_volume()
            vol = mixer.get_volume_pp()
            if vol != None:
                aux = u"[♫ %i" % vol
                aux += "%]"
                cplayer.print_aux(aux)
        elif k in [ ord('9') ]:
            mixer.decrease_volume()
            vol = mixer.get_volume_pp()
            if vol != None:
                aux = u"[♫ %i" % vol
                aux += "%]"
                cplayer.print_aux(aux)
        elif k in [ ord('8') ]:
            ap.increase_pitch()
            pitch = ap.get_pitch()
            if pitch != None:
                aux = u"[☯ %.3f]" % pitch
                cplayer.print_aux(aux, fx = save_pitch)

        elif k in [ ord('7') ]:
            ap.decrease_pitch()
            pitch = ap.get_pitch()
            if pitch != None:
                aux = u"[☯ %.3f]" % pitch
                cplayer.print_aux(aux, fx = save_pitch)

        elif k in [ ord('6') ]:
            ap.increase_softvol()
            softvol = ap.get_softvol()
            if softvol != None:
                aux = u"[♪ %.2f]" % softvol
                cplayer.print_aux(aux)

        elif k in [ ord('5') ]:
            ap.decrease_softvol()
            softvol = ap.get_softvol()
            if softvol != None:
                aux = u"[♪ %.2f]" % softvol
                cplayer.print_aux(aux)
        elif k in [ ord('4') ]: #increase crossfade
            config.audio_player['crossfade_time'] += 0.1
            aux = u"[⋇ %.2f]" % config.audio_player['crossfade_time']
            cplayer.print_aux(aux, fx = config.Save())
        elif k in [ ord('3') ]: #decrease crossfade
            if config.audio_player['crossfade_time'] > 0.1:
                config.audio_player['crossfade_time'] -= 0.1
                aux = u"[⋇ %.2f]" % config.audio_player['crossfade_time']
                cplayer.print_aux(aux, fx = config.Save())
        elif k in [ord('_')]:
            panels[cp].mark_all_played_tracks()
        elif k in [ord('.')]:
            panels[cp].center()
        elif k in [ord('u')]:
            panels[cp].mark_unplayed()
        elif k in [ord('U')]:
            panels[cp].mark_played()

        elif k in [ord('k')]:
            cl = panels[cp].curse()
            if cl != set():
                for pnl in panels:
                    pnl.on_cursebless(cl)

        elif k in [ord('K')]:
            cl = panels[cp].bless()
            if cl != set():
                for pnl in panels:
                    pnl.on_cursebless(cl)
            
        elif k in [ord(']')]:
            if panels[cp].type == 'equalizer':
                panels[cp].set_gain(0.)
            elif panels[cp].type == 'playlist':
                panels[cp].sort()
        elif k in [ord('}')]:
            if panels[cp].type == 'equalizer':
                panels[cp].set_gain(-6.)
            elif panels[cp].type == 'playlist':
                panels[cp].shuffle()
        elif k in [ord('{')]:
            if panels[cp].type == 'playlist':
                panels[cp].chronology()

        elif k in [ord('z'), ord('Z')]:    #play_everything
            panels[cp].play_everything(player_cursor)
        elif k in [ord('~')]:    #random_entry
            panels[cp].random_entry()
        elif k in [c.KEY_MOUSE]:
            x,y, border_x, border_y = panel_engine.panel_position("left")
            try:
                mid, x, y, z, bstate =  c.getmouse()
            except:
                continue

            if y < border_y:
                if bstate in [ c.BUTTON1_RELEASED, c.BUTTON1_CLICKED , c.BUTTON1_DOUBLE_CLICKED, c.BUTTON2_CLICKED ]:
                    opm = get_opm()

                    if not opm and ( ( cp == lp and x >= border_x) or ( cp == rp and x < border_x) ):
                        sp = cp
                        cp = rp if cp == lp else lp
                        panels[sp].chfocus(False)
                        panels[cp].chfocus()
                        print_buttons()

                    if not opm and x >= border_x:
                        x -= border_x
            
                    if y > 0 and y < border_y - 4:
                        if x == 0:
                            panels[cp].mouse_scroll(y-1)
                        elif bstate == c.BUTTON2_CLICKED:
                            panels[cp].mouse_mark(y-1)
                        else:
                            panels[cp].mouse_select(y-1, x)
                            if bstate == c.BUTTON1_DOUBLE_CLICKED and panels[cp].question != True:
                                panels[cp].enter(pc=player_cursor)

                    elif y == 0 and  bstate == c.BUTTON1_CLICKED:
                        panels[cp].move_by_title(x-1)
            elif y == border_y + 2:
                km = bttons.mouse(x)
            else:
                rc = cplayer.mouse_click(x, y-border_y)
                if rc == "playpause":
                    ap.playpause()
                elif rc == "shuffle":
                    ap.switch_shuffle()
                elif rc == "repeat":
                    ap.switch_repeat()
                elif rc == "direction":
                    ap.switch_direction()
                elif rc == "equalizer":
                    ap.switch_hold_equalizer()
                else:
                    ap.seek_pp(rc)
        else:
            pass



    if pkl_flag:
        #store this session
        pfile = open(config.session_file, 'w')
        version_str=""
        for v in VERSION:
            version_str += str(v) + u'.'

        version_str = version_str.rstrip('.')

        pfile.write( version_str + '\n')
        pfile.write( str(nop) + '\n')
        pfile.write( str(lp) + '\n')
        pfile.write( str(rp) + '\n')
        pfile.write( str(cp) + '\n')
        pfile.write( str(get_opm()) + '\n' )
        pfile.write( str(panel_engine.get_pppp()) + '\n')
        pfile.write( str(int(ap.shuffle)) + '\n')
        pfile.write( str(int(ap.repeat)) + '\n')
        pfile.write( str(ap.direction) + '\n')
        pfile.write( str(int(ap.hold_equalizer)) + '\n')
        pfile.write( str(ap.zigzag) + '\n' )

        ap.store_session(pfile)
        ctrack = player_cursor.ctrack
        ntrack = player_cursor.ntrack
        pkl_c = {}
        pkl_n = {}
        if ctrack:
            pkl_c['image'] = ctrack.image
            pkl_c['panel_id'] = panels.index(ctrack.storage.engine)
            pkl_c['addr'] = ctrack.storage.elements[ctrack.pos]['addr']
        if ntrack:
            pkl_n['image'] = ntrack.image
            pkl_n['panel_id'] = panels.index(ntrack.storage.engine)
            pkl_n['addr'] = ntrack.storage.elements[ntrack.pos]['addr']
        pickle.dump(pkl_c,  pfile)
        pickle.dump(pkl_n,  pfile)

        for pnl in panels:
            pnl.save_panel(pfile)
        pfile.close()

    stop_peyote()

def stop_peyote():
    global is_started, workers
    is_started = False
    #stop player
    if fs_events.inotify_support:
        fs_events.stop()
    ap.exit()
    from player import lastfm
    lastfm.stop()

    #stop tasksWorkers
    workers.stop()
    #trop threads
    thread_system.thread_polls.polls.exit()

    #deinit curses library
    curses_lock()
    try:
        c.endwin()
    except:
        pass
    curses_unlock()

    workers.exit()

def peyote():
    try:
        main()
    except Exception, e:
        try:
            with open(config.crash_report_file, 'w') as f:
                traceback.print_exc(file=f)

            stop_peyote()
            #traceback.print_exc(file=sys.stdout)
            print _("Peyote was crashed!")
            print _("Please send this file '") + config.crash_report_file + _("' to me 'platonny@ngs.ru'")
            print ""
            print _("Press enter to continue.")
            sys.stdout.flush()
            sys.stdin.readline()

        except:
            pass
    loop.quit()
    try:
        global object
        object.stop()
    except:
        pass


RESIZE_TIME = 50
RESIZE_AWESOME_WM = False
def wait_for_signal():
    global pipes, c, is_started
    poll = select.poll()
    poll.register(pipes[0], select.POLLIN)
    while is_started:
        rc = poll.poll(RESIZE_TIME)
        if rc:
            rc = os.read(pipes[0], 1)
            if rc == 'C': #Ctrl+C
                is_started = False
            elif RESIZE_AWESOME_WM:
                sighandler(signal.SIGWINCH, 0)
            else:
                while is_started:
                    rc = poll.poll(RESIZE_TIME)
                    if not rc:
                        sighandler(signal.SIGWINCH, 0)
                        break
                    else:
                        rc = os.read(pipes[0], 1)
                        if rc == 'C': #Ctrl+C
                            is_started = False

def fork_sighandler(s,unuse):
    global pipes
    if s == signal.SIGWINCH:
        os.write(pipes[1], 'w')
    elif s == signal.SIGINT:
        os.write(pipes[1], 'C')
    elif s == signal.SIGTERM:
        sys.exit()

def peyote_sighandler(signo, unuse):
    if signo in [ signal.SIGINT, signal.SIGTERM ]:
        global is_started
        is_started = False
    else:
        sighandler(signal.SIGWINCH, 0)

#Underline will be replaced by ./configure script. Don't edit it!
LOCALE_DIR="/usr/local/share/locale"

if __name__ == "__main__":
    gettext.bindtextdomain('peyote', LOCALE_DIR)
    gettext.textdomain('peyote')
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    config.Load()
    config.LoadEqualizers()
    config.parse_commandline()
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GObject, Gst
    GObject.threads_init()
    Gst.init(None)

    import panel_config
    import cursor
    import time, player, player_gui
    import playlist
    import nc_panel.panel
    import lyrics.local_library
    lyrics.local_library.initialize(config)
    import panel
    nc_panel.panel.initialize(config)
    import cue,media_fs
    from thread_system.task_workers import TaskWorkers
    from nc_panel.semaphores import CURSES_SEM, curses_lock, curses_unlock
    if dbus_enabled:
        from peyote_dbus import *
        import dbus, dbus.service, dbus.mainloop.glib
    import fs.auto
    import thread_system.thread_polls
    import peyote_exec
    from mixer import Mixer
    from panel import sw_opm, get_opm
    fs.auto.Init(config)

    panel_engine = panel


    #I must to fork a process before gtk.main() because sighandler + gtk.main() + SIGWINCH = 100% cpu usage
    #parent process will wait SIGWINCH
    #child process will be notified by pipe

    pipes = os.pipe()
    parent_pid = os.getpid()
    if crutch:
        rc = os.fork()
        if rc != 0:
            signal.signal(signal.SIGWINCH, fork_sighandler)
            signal.signal(signal.SIGTERM, fork_sighandler)
            signal.signal(signal.SIGINT, fork_sighandler)
            while True:
                time.sleep(1)
    else:
        signal.signal(signal.SIGWINCH, peyote_sighandler)
        #signal.signal(signal.SIGTERM, peyote_sighandler)
        signal.signal(signal.SIGINT, peyote_sighandler)

    import fs_events
    if fs_events.inotify_support:
        fs_events.start()

    #Initialize TaskWorkers
    workers = TaskWorkers(3)

    if dbus_enabled:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        dbus_path_init()

        try:
            session_bus = dbus.SessionBus()
        except:
            dbus_enabled = False
        else:
            name = dbus.service.BusName(dbus_path, session_bus)
            object = PeyoteDbus(session_bus, '/Mescaline')
            Thread(target=dbus_responser_thread).start()

    loop = GObject.MainLoop()

    if crutch:
        signal.signal(signal.SIGINT, lambda a,b: None)
        sigthread = Thread( target = wait_for_signal )
        sigthread.start()

    GObject.timeout_add( 5000, peyote_exec.check_programs )
    Thread(target=peyote).start()
    loop.run()
    peyote_exec.stop()


    try:
        c.endwin()
    except:
        pass

    if crutch:
        os.write(pipes[1], 'C')
        sigthread.join()
        try:
            os.kill(parent_pid, signal.SIGTERM)
        except:
            pass
    time.sleep(0.6)
    signal.signal(signal.SIGINT, lambda a,b: None)
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep(1.5)
    os.kill(os.getpid(), signal.SIGKILL)

