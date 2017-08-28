#!/usr/bin/python
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

try:
    from pyinotify import *
    from threading import Event, Semaphore
    from os.path import dirname, basename, isdir
    from Queue import Queue, Empty
    from media_fs import is_audio_file, is_cue_file
    from useful import unicode2
    from os import getenv
    lock = Semaphore(1)
    subscribers = {}
    notifier = None
    wm = WatchManager()
    q = Queue()
    mask = IN_DELETE | IN_CREATE | IN_MOVED_FROM | IN_MOVED_TO | IN_UNMOUNT | IN_MODIFY
    inotify_support = True
except:
    inotify_support = False    

def conv_dir(p):
    if p[-1] != '/':
        return unicode2( p )
    return unicode2( p[:-1] )

def parent_dir(p):
    if p[-1] != '/':
        return dirname(p)
    return dirname( p[:-1] )

class EventHandler(ProcessEvent):
    def process_IN_CREATE(s, event):
        s.process(event)
    def process_IN_DELETE(s, event):
        s.process(event)
    def process_IN_MOVED_FROM(s, event):
        s.process(event, skip_hiden=False)
    def process_IN_MOVED_TO(s, event):
        s.process(event, skip_hiden=False)
    def process_IN_UNMOUNT(s, event):
        q.put( conv_dir(event.pathname) )
    def process_IN_MODIFY(s, event):
        bn = basename ( unicode2( event.pathname ) )
        if is_cue_file(bn) or is_audio_file(bn):
            s.process(event)
    def process(s, event, skip_hiden=True):
        pathname = unicode2(event.pathname)
        if skip_hiden and basename( pathname ).startswith('.'):
            return
        bd = parent_dir(pathname)
        q.put ( bd )

def start():
    global notifier
    notifier = ThreadedNotifier(wm, EventHandler())
    notifier.start()

def stop():
    notifier.stop()
    while not q.empty():
        q.get()
        q.task_done()
    q.join()

def get_events():
    paths = set()
    while not q.empty():
        paths.add( q.get() )
        q.task_done()
    if paths == set():
        return set()

    ret = []
    lock.acquire()
    for path in paths:
        for a in subscribers.get( path, (None, []) )[1]:
            ret.append( [a, path] )
    lock.release()
    return ret

def subscribe(path, arg):
    if not isdir( path ):
        return
    lock.acquire()
    try:
        if not subscribers.has_key(path):
            wmm = wm.add_watch( path, mask, rec=False )
            subscribers[path] = (wmm, set( [arg] ) )
        else:
            subscribers[path][1].add(arg)
    except Exception, e:
        pass
    lock.release()

def unsubscribe(arg, path = None):
    lock.acquire()
    try:
        if path:
            if subscribers.has_key(path):
                subscribers[path][1].discard(arg)
                if subscribers[path][1] == set():
                    wm.rm_watch(subscribers[path][0].values())
                    del subscribers[path]
        else:
            for path in subscribers.keys():
                subscribers[path][1].discard(arg)
                if subscribers[path][1] == set():
                    wm.rm_watch(subscribers[path][0].values())
                    del subscribers[path]
    except:
        pass
    lock.release()

