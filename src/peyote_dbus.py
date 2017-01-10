#!/usr/bin/python
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
                                    
import dbus.service
from Queue import Queue, Empty
from threading import Semaphore

dbus_path = "net.sourceforge.peyote"
PASS         = 0
PLAYPAUSE    = 1
NEXTTRACK    = 2
NEWPANEL     = 3
CD           = 4
TAB          = 5
PREV_PANEL   = 6 
NEXT_PANEL   = 7
CLOSE_PANEL  = 8
REDRAW       = 9
ENTER        = 0x0a
LEFT         = 0x0b
RIGHT        = 0x0c
UP           = 0x0d
DOWN         = 0x0e
HOME         = 0x0f
END          = 0x10
PAGEUP       = 0x11
PAGEDOWN     = 0x12
INSERT       = 0x13
GOTO         = 0x14
SAVE         = 0x15
INC_PANEL_WIDTH = 0x16
DEC_PANEL_WIDTH = 0x17
PLAY          = 0x18
CD_AND_PLAY  = 0x19


ARTIST       = 0x100
ALBUM        = 0x101
TITLE        = 0x102
DATE         = 0x103
STATUS       = 0x104
def dbus_path_init():
    return
    global dbus_path
    bus = dbus.SessionBus()

    try:
        remote_object = bus.get_object(dbus_path, "/Mescaline")
        remote_object.Pass(dbus_interface = dbus_path)
    except dbus.DBusException:
        return
    i = 1
    while True:
        dbus_path = "net.sourceforge.peyote.%i", i
        try:
            remote_object = bus.get_object(dbus_path, "/Mescaline")
            remote_object.Pass(dbus_interface = dbus_path)
        except dbus.DBusException:
            return
        i += 1
        

class PeyoteDbus(dbus.service.Object):
    def __init__ (s, bus, name):
        dbus.service.Object.__init__(s, bus, name)
        s.q = Queue()
        s.iq = Queue()
        s.oq = Queue()
    def exit(s):
        for q in [ s.q, s.iq, s.oq ]:
            while not q.empty():
                q.get()
                q.task_done()
            q.join()
        pass
    def __del__ (s):
        while s.get_command():
            pass
        del s.q
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Ping(s):
        pass
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def PrevPanel(s):
        s.q.put( [PREV_PANEL] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def NextPanel(s):
        s.q.put( [NEXT_PANEL] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def ClosePanel(s):
        s.q.put( [CLOSE_PANEL] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Redraw(s):
        s.q.put( [REDRAW] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Enter(s):
        s.q.put( [ENTER] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Left(s):
        s.q.put( [LEFT] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Right(s):
        s.q.put( [RIGHT] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Up(s):
        s.q.put( [UP] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Down(s):
        s.q.put( [DOWN] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Home(s):
        s.q.put( [HOME] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def End(s):
        s.q.put( [END] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def PageUp(s):
        s.q.put( [PAGEUP] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def PageDown(s):
        s.q.put( [PAGEDOWN] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Insert(s):
        s.q.put( [INSERT] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def GoTo(s):
        s.q.put( [GOTO] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Save(s):
        s.q.put( [SAVE] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def IncPanelWidth(s):
        s.q.put( [INC_PANEL_WIDTH] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def DecPanelWidth(s):
        s.q.put( [DEC_PANEL_WIDTH] )

    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def PlayPause(s):
        s.q.put( [PLAYPAUSE] )
    
    @dbus.service.method(dbus_path, in_signature='s', out_signature='')
    def CD(s, location):
        s.q.put( [ CD, location ] )

    @dbus.service.method(dbus_path, in_signature='s', out_signature='')
    def CdAndPlay( s, location):
        s.q.put( [ CD_AND_PLAY, location ] )

    @dbus.service.method(dbus_path, in_signature='s', out_signature='')
    def NewTab(s, location):
        s.q.put( [ NEWPANEL, location ] )

    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def NextTrack(s):
        s.q.put( [NEXTTRACK] )

    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Tab(s):
        s.q.put( [TAB] )

    @dbus.service.method(dbus_path, in_signature='', out_signature='')
    def Play(s):
        s.q.put( [PLAY] )
    @dbus.service.method(dbus_path, in_signature='', out_signature='s')
    def GetArtist(s):
        task = [ARTIST]
        s.iq.put (task)
        try:
            rc = s.oq.get()
        except Empty:
            pass
        else:
            s.oq.task_done()
            return rc
        return ""

    @dbus.service.method(dbus_path, in_signature='', out_signature='s')
    def GetAlbum(s):
        task = [ALBUM]
        s.iq.put (task)
        try:
            rc = s.oq.get()
        except Empty:
            pass
        else:
            s.oq.task_done()
            return rc
        return ""

    @dbus.service.method(dbus_path, in_signature='', out_signature='s')
    def GetTitle(s):
        task = [TITLE]
        s.iq.put (task)
        try:
            rc = s.oq.get()
        except Empty:
            pass
        else:
            s.oq.task_done()
            return rc
        return ""
    @dbus.service.method(dbus_path, in_signature='', out_signature='s')
    def GetStatus(s):
        task = [STATUS]
        s.iq.put (task)
        try:
            rc = s.oq.get()
        except Empty:
            pass
        else:
            s.oq.task_done()
            return rc
        return ""


    def response(s, arg):
        s.oq.put(arg)
    
    def get_command(s):
        try:
            command = s.q.get_nowait()
        except Empty:
            return None
        else:
            s.q.task_done()
            return command
    def get_command2(s):
        try:
            command = s.iq.get()
        except Empty:
            return None
        else:
            s.iq.task_done()
            return command
    def stop(s):
        s.iq.put(None)



