#!/usr/bin/python2
# -*- coding: utf-8 -*-

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

import sys, os.path
import dbus, getopt
dbus_path = "net.sourceforge.peyote"

def usage():
    print "Usage: %s [--print-artist ] [ --print-album ] [--print-title] [--print-status]" % sys.argv[0]
    print "       %s [ --playpayse ] [--pause] [--resume] [--play]" % (" "*len(sys.argv[0]) )
    print "       %s [--next] [--new-panel location] [--cd location] [--tab] [--cd-and-play audiofile|location|playlist]" % (" "*len(sys.argv[0]) )
    print "       %s directory|audio_file|cuefile" % sys.argv[0]
    print "       %s --help" % sys.argv[0]

def parse_commandline():
    #    gopts = ['help', 'encoding=', 'gst-sink=', 'scheme=']
    if '--help' in sys.argv[1:]:
        usage()
        sys.exit(1)
    try:
        bus = dbus.SessionBus()
    except:
        #print "Run the peyote first!"
        sys.exit(0)

    gopts = [ 'print-artist', 'print-album', 'print-title', 'playpause', "pause", "resume", 'next', 'print-status', 'new-panel=', 'cd=', 'tab', "play", "cd-and-play=" ]
    try:
        optlist, args = getopt.getopt(sys.argv[1:], '', gopts)
    except getopt.GetoptError, err:
        usage()
        sys.exit(1)
    if sys.argv[1][:2] != "--":
        optlist=[ [ '--cd-and-play', os.path.abspath(sys.argv[1]) ] ]
    

    for val,arg in optlist:
        try:
            if val == '--print-artist':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.GetArtist(dbus_interface = dbus_path)
                print rc.encode('utf-8')
            elif val == '--print-album':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.GetAlbum(dbus_interface = dbus_path)
                print rc.encode('utf-8')

            elif val == '--print-title':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.GetTitle(dbus_interface = dbus_path)
                print rc.encode('utf-8')
            elif val == '--print-status':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.GetStatus(dbus_interface = dbus_path)
                print rc.encode('utf-8')

            elif val == '--playpause':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.PlayPause(dbus_interface = dbus_path)
            elif val == '--pause':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.Pause(dbus_interface = dbus_path)
            elif val == '--resume':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.Resume(dbus_interface = dbus_path)

            elif val == '--tab':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.Tab(dbus_interface = dbus_path)

            elif val == '--next':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.NextTrack(dbus_interface = dbus_path)
            elif val == '--new-panel':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.NewTab(arg, dbus_interface = dbus_path)
            elif val == '--cd':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.CD(arg, dbus_interface = dbus_path)
            elif val == '--cd-and-play':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.CdAndPlay(arg, dbus_interface = dbus_path)
            elif val == '--play':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.Play(dbus_interface = dbus_path)
            elif val == '--dec-lpw':
                remote_object = bus.get_object(dbus_path, "/Mescaline")
                rc = remote_object.DecPanelWidth(dbus_interface = dbus_path)
                
        except dbus.DBusException:
            #print "Run the peyote first!"
            sys.exit(1)




if __name__ == '__main__':
    if len(sys.argv) == 1:
        usage()
        sys.exit(0)
    parse_commandline()
