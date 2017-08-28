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

import curses
c = curses
from nc_panel.semaphores import curses_lock, curses_unlock
import gettext
from useful import localise
from sets import config
_ = localise

class Button:
    def __init__(s, name, keys):
        s.name = name
        s.keys = keys
        s.button_txt = s.keys[0][0] + '[' + name + ']'
        if len(s.keys) > 1:
            s.button_txt += s.keys[1][0]
        s.length = len(s.button_txt) + 1
    def mouse(s, x):
        if x>0:
            if x <= len(s.keys[0][0]) + 2 + len(s.name):
                return s.keys[0][1]
            elif len(s.keys) > 1:
                return s.keys[1][1]
        return None
    def pprint(s):
        print  s.button_txt
    def cprint(s, pos, win, colors):
        p = pos

        curses_lock()
        try:
            win.addstr(0, pos, ' ')
        except:
            pass
        curses_unlock()

        p+=1

        curses_lock()
        try:
            win.addstr(0, p, s.keys[0][0].encode('utf-8'), c.color_pair(colors['button key'].get_pair_no())|colors['button key'].get_args())
        except:
            pass
        curses_unlock()

        p+= len(s.keys[0][0])

        curses_lock()
        try:
            win.addstr(0, p, (u'[' + s.name + u']').encode('utf-8'), c.color_pair(colors['button'].get_pair_no())|colors['button'].get_args())
        except:
            pass
        curses_unlock()

        p += len(s.name) + 2
        if len(s.keys) > 1:
            curses_lock()
            try:
                win.addstr(0, p, s.keys[1][0].encode('utf-8'), c.color_pair(colors['button key'].get_pair_no())|colors['button key'].get_args())
            except:
                pass
            curses_unlock()

            p += len(s.keys[1][0])

        return p

class Buttons:
    def __init__(s, colors, f="fspl"):
        s.win = None
        s.colors = colors
        s.get_buttons()
    def get_buttons(s):
        s.buttons = [None]*12

        main_btns = [
            Button(_('tag'), [ (u'ins', c.KEY_IC ), (u'*', ord('*') ) ])

            ,Button(_(u'next ♫'), [(u'n', ord('n'))])
            ,Button(_('move'), [ (u'⇑↑', 337 ), (u'⇑↓', 336 ) ])
            ,Button(_('tabs'), [ (u'<', ord('<') ), (u'>', ord('>') ) ])
            ,Button(_('cd'), [(u'c', ord('c'))])
            ,Button(_('+-10s'), [ (u'⇑←', c.KEY_SLEFT ), (u'⇑→', c.KEY_SRIGHT ) ])
            ,Button(_('border'), [ (u'1', ord('1') ), (u'2', ord('2') ) ])
            ,Button(_('1/2'), [(u'p', ord('p'))])
            ,Button(_('new panel'), [(u't', ord('t'))])
            ,Button(_('close panel'), [(u'y', ord('y'))])
            ,Button(_('redraw'), [(u'w', ord('w'))])
            ,Button(_('volume'), [ (u'9', ord('9') ), (u'0', ord('0') ) ])
            ,Button(_('pitch'), [ (u'7', ord('7') ), (u'8', ord('8') ) ])
            ,Button(_('crossfade'), [(u'3', ord('3')), (u'4', ord('4')) ] )
            ,Button(_('go to tag'), [(u'i', ord('i')), ('I',ord('I'))])
            ,Button(_('quit'), [(u'q', ord('q'))])
        ]
        s.buttons[0] = main_btns
        s.buttons[1] = [ #[FS] vs ??
                Button(_('new'), [(u'F7', c.KEY_F7)])
                ,Button(_('remove'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
                ,Button(_('rename'), [(u'F9', c.KEY_F9)])
                ,Button(_('tree'), [(u'\\', ord('\\')), (u'|', ord('|'))])
                ,Button(_('mode'), [(u'm', ord('m'))])
                ,Button(_('show files'), [(u'f', ord('f'))])
                ,Button(_('search'), [(u'?', ord('?'))])
                ,Button(_('quick search'), [(u'/', ord('/'))])
                ,Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)]) 
                ,Button(_('go to tag'), [(u'i', ord('i')), ('I',ord('I'))])
                ,Button(_('size'), [(u'd', ord('d'))])
                ,Button(u'☐', [(u'u', ord('u'))])
                ,Button(u'☒', [(u'U', ord('U'))])
                ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
                ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ]
        s.buttons[2] = [ #[FS] vs PL
                 Button(_('add'), [(u'F4', c.KEY_F4)])
                ,Button(_('append'), [(u'F5', c.KEY_F5)])
                ,Button(_('new'), [(u'F7', c.KEY_F7)])
                ,Button(_('remove'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
                ,Button(_('rename'), [(u'F9', c.KEY_F9)])
                ,Button(_('tree'), [(u'\\', ord('\\')), (u'|', ord('|'))])
                ,Button(_('mode'), [(u'm', ord('m'))])
                ,Button(_('show files'), [(u'f', ord('f'))])
                ,Button(_('search'), [(u'?', ord('?'))])
                ,Button(_('quick search'), [(u'/', ord('/'))])
                ,Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)]) 
                ,Button(_('size'), [(u'd', ord('d'))])
                ,Button(u'☐', [(u'u', ord('u'))])
                ,Button(u'☒', [(u'U', ord('U'))])
                ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
                ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
                
            ]
        s.buttons[3] = [ #[FS] vs FS
                 Button(_('copy'), [(u'F5', c.KEY_F5), (u'F4', c.KEY_F4)])
                ,Button(_('move'), [(u'F6', c.KEY_F6)])
                ,Button(_('new'), [(u'F7', c.KEY_F7)])
                ,Button(_('remove'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
                ,Button(_('rename'), [(u'F9', c.KEY_F9)])
                ,Button(_('tree'), [(u'\\', ord('\\')), (u'|', ord('|'))])
                ,Button(_('mode'), [(u'm', ord('m'))])
                ,Button(_('show files'), [(u'f', ord('f'))])
                ,Button(_('search'), [(u'?', ord('?'))])
                ,Button(_('quick search'), [(u'/', ord('/'))])
                ,Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)]) 
                ,Button(_('size'), [(u'd', ord('d'))])
                ,Button(u'☐', [(u'u', ord('u'))])
                ,Button(u'☒', [(u'U', ord('U'))])
                ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
                ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ]
        s.buttons[4] = [ #[FS] vs Locations
                 Button(_('new'), [(u'F7', c.KEY_F7)])
                ,Button(_('copy'), [(u'F5', c.KEY_F5), (u'F4', c.KEY_F4)])
                ,Button(_('remove'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
                ,Button(_('rename'), [(u'F9', c.KEY_F9)])
                ,Button(_('tree'), [(u'\\', ord('\\')), (u'|', ord('|'))])
                ,Button(_('mode'), [(u'm', ord('m'))])
                ,Button(_('show files'), [(u'f', ord('f'))])
                ,Button(_('search'), [(u'?', ord('?'))])
                ,Button(_('quick search'), [(u'/', ord('/'))])
                ,Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)]) 
                ,Button(_('size'), [(u'd', ord('d'))])
                ,Button(u'☐', [(u'u', ord('u'))])
                ,Button(u'☒', [(u'U', ord('U'))])
                ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
                ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ]
        s.buttons[5] = [ #[Pl] vs ??
             Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)])
            ,Button(_('mode'), [(u'm', ord('m'))])
            ,Button(_('save'), [(u'F2', c.KEY_F2)])
            ,Button(_('edit'), [(u'F9', c.KEY_F9)])
            ,Button(_('add song'), [(u'F7', c.KEY_F7)])
            ,Button(_('delete'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
            ,Button(_('quick search'), [(u'/', ord('/'))])
            ,Button(u'☐', [(u'u', ord('u'))])
            ,Button(u'☒', [(u'U', ord('U'))])
            ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
            ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ,Button( _(u'sort'), [ (u']', ord(']') ) ] )
            ,Button( _(u'shuffle'), [ (u'}', ord('}') ) ] )
            ,Button( _(u'chronology'), [ (u'{', ord('{') ) ] )
            ]
        s.buttons[6] = [ #[Pl] vs FS
             Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)])
            ,Button(_('mode'), [(u'm', ord('m'))])
            ,Button(_('save'), [(u'F2', c.KEY_F2)])
            ,Button(_('edit'), [(u'F9', c.KEY_F9)])
            ,Button(_('copy'), [(u'F5', c.KEY_F5), (u'F4', c.KEY_F4)])
            ,Button(_('add song'), [(u'F7', c.KEY_F7)])
            ,Button(_('delete'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])    
            ,Button(_('quick search'), [(u'/', ord('/'))])
            ,Button(u'☐', [(u'u', ord('u'))])
            ,Button(u'☒', [(u'U', ord('U'))])
            ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
            ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ,Button( _(u'sort'), [ (u']', ord(']') ) ] )
            ,Button( _(u'shuffle'), [ (u'}', ord('}') ) ] )
            ,Button( _(u'chronology'), [ (u'{', ord('{') ) ] )
            ]

        s.buttons[7] = [ #[Pl] vs PL
             Button(_('go to'), [(u'bspace', c.KEY_BACKSPACE)])
            ,Button(_('mode'), [(u'm', ord('m'))])
            ,Button(_('edit'), [(u'F9', c.KEY_F9)])
            ,Button(_('save'), [(u'F2', c.KEY_F2)])
            ,Button(_('add'), [(u'F4', c.KEY_F4)])
            ,Button(_('append'), [(u'F5', c.KEY_F5)])
            ,Button(_('add song'), [(u'F7', c.KEY_F7)])
            ,Button(_('delete'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
            ,Button(_('quick search'), [(u'/', ord('/'))])
            ,Button(u'☐', [(u'u', ord('u'))])
            ,Button(u'☒', [(u'U', ord('U'))])
            ,Button(u'(un)curse', [(u'k', ord('k')), ( u'K', ord('K') ) ])
            ,Button(_('tag') + u' ☒', [(u'_', ord('_'))])
            ,Button( _(u'sort'), [ (u']', ord(']') ) ] )
            ,Button( _(u'shuffle'), [ (u'}', ord('}') ) ] )
            ,Button( _(u'chronology'), [ (u'{', ord('{') ) ] )
            ]

        s.buttons[8] = [ # equalizer://
            Button(_('save'), [(u'F2', c.KEY_F2)])
            ,Button(_('bands'), [(u'F6', c.KEY_F6)])
            ,Button(_('show/hide tags'), [(u'f', ord('f'))])
            ,Button(_('0 Db'), [(u']', ord(']'))])
            ]

        s.buttons[9] = [ # locations://
             Button(_('new'), [(u'F7', c.KEY_F7)])
            ,Button(_('delete'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
            ,Button(_('rename'), [(u'F9', c.KEY_F9)])
            ]
        s.buttons[10] = [ # config://
            Button(_('delete'), [(u'F8', c.KEY_F8), (u'del', c.KEY_DC)])
            ]
        s.buttons[11] = [ # radio://
             Button(_('copy'), [(u'F5', c.KEY_F5), (u'F4', c.KEY_F4)])
            ]
        s.Z = False
            
    def genwin(s, pw):
        if config.hide_keybar:
            return
        s.parent = pw

        s.start = map ( lambda x: [0,0], s.buttons )
        size_yx = s.parent.getmaxyx()
        s.x = size_yx[1]
        if s.win != None:
            s.win = None

        curses_lock()
        try:
            s.win = s.parent.subwin(1, size_yx[1], size_yx[0]-1, 0 )
            s.win.bkgdset(' ', c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
            s.win.bkgd(' ', c.color_pair(s.colors['player body'].get_pair_no())|s.colors['player body'].get_args())
        except:
            pass
        curses_unlock()
        
    def print_buttons(s, cp = None, sp = None):
        if config.hide_keybar:
            return
        bline = u''
        N = 0
        if cp == None:
            N = s.N
            s.start[N][0] = s.start[N][1]

        elif cp.type == 'fs':
            N = 1
            if not sp:
                pass
            elif sp.type == 'playlist':
                N = 2
            elif sp.type == 'fs':
                N = 3
            elif sp.type == 'locations':
                N = 4
        elif cp.type == 'playlist':
            N = 5
            if not sp:
                pass
            elif sp.type == 'fs':
                N = 6
            elif sp.type == 'playlist':
                N = 7
        elif cp.type == 'equalizer':
            N = 8
        elif cp.type == 'locations':
            N = 9
        elif cp.type == 'config':
            N = 10
        elif cp.type == 'radio':
            N = 11

        pos = 3
        s.N = N

        curses_lock()
        try:
            s.win.erase()

            if s.Z:
                s.start[0][0] = s.start[0][1]
                N = 0
                s.win.addstr(0,0,'☚☟☛')
            else:
                s.win.addstr(0,0,'☚☝☛')
        except:
            pass
        curses_unlock()
        
        s.positions = []
        for button in s.buttons[N][s.start[N][0]:] + s.buttons[N][:s.start[N][0]]:
            if pos + button.length >= s.x:
                s.start[N][1] = s.buttons[N].index(button)
                break
            try:
                rpos = button.cprint(pos, s.win, s.colors)
            except:
                s.start[N][1] = s.buttons[N].index(button)
                break
            s.positions.append((pos,rpos,button))
            pos = rpos

        curses_lock()
        try:
            s.win.refresh()
        except:
            pass
        curses_unlock()

    def mouse(s, x):
        if config.hide_keybar:
            return None
        if x < 3:
            if x == 0:
                s.start[0 if s.Z else s.N] = [0,0]
            elif x == 1:
                s.Z = False if s.Z else True
            s.print_buttons()
            return None
        for pos in s.positions:
            if pos[1] > x > pos[0]:
                return pos[2].mouse(x-pos[0])
        return None

