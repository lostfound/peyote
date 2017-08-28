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

from subprocess import Popen, PIPE
from useful import get_human_readable, unicode2, localise
import os, statvfs
import gettext
import fs.auto
import codecs
from thread_system.thread_polls import polls
from sets import config

_ = localise

def get_fsstat(path):
        try:
            osstat = os.statvfs(path)
        except:
            return (None,None)

        total = osstat[statvfs.F_BSIZE] * osstat[statvfs.F_BLOCKS]
        free  = osstat[statvfs.F_BSIZE] * osstat[statvfs.F_BAVAIL]
        return (get_human_readable(free), get_human_readable(total))
def mp_to_dict(path):
    sts = get_fsstat(path)

    if sts != (None, None):
        return {'type': 'system_location' , 'path': path, 'free': sts[0], 'total' : sts[1] }
    else:
        return {'type': 'system_location' , 'path': path}

def get_home():
    home_path = unicode2(os.getenv('HOME'))
    sts = get_fsstat(home_path)
    if sts == (None, None):
        return {'type': 'system_location' , 'path': home_path, 'free': sts[0], 'total' : sts[1] , 'name' : _("Home") }
    else:
        return {'type': 'system_location' , 'path': home_path, 'name' : _("Home") }

def blacklist():
    try:
        with codecs.open(config.locations_bad_file, 'r', encoding='utf-8') as f:
            bl = map( lambda x: x.rstrip(), f.readlines() )
        return bl
    except:
        return []

def save_blacklist(lst):
    bl = set( blacklist () )
    for e in lst:
        bl.add(e)
    try:
        with codecs.open(config.locations_bad_file, 'w', encoding='utf-8') as f:
            for e in bl:
                f.write(e+u'\n')
    except:
        pass
    

def get_mount_points():
    exc = Popen('mount', stdout=PIPE, shell=True)
    exc.wait()
    black_list = blacklist()
    points = map(lambda l: unicode2(l.split(' on ')[1].strip().split()[0]), exc.stdout.readlines())
    mount_points = filter(lambda l: l.split('/')[1] not in ['', 'usr', 'var', 'tmp', 'live', 'proc', 'lib', 'dev', 'sys', 'tmp'], points)
    mount_points = filter(lambda l: l not in black_list, mount_points)
    return map( lambda d: mp_to_dict(d), mount_points ) 

def _read_user_specific_locations_file(panel):
    locations = []
    if not os.path.exists(config.locations_file):
        with codecs.open(config.locations_file, 'w', encoding='utf-8') as f:
            f.write(config.default_playlist + '\n')
            f.write(_('Default playlist\n'))

    with codecs.open(config.locations_file, 'r', encoding='utf-8') as f:
        n=2
        while True:
            path = unicode2(f.readline().rstrip('\n'))
            if not path:
                break
            name = unicode2(f.readline().rstrip('\n'))
            locations.append( {'type' : 'user_location', 'path' : path, 'name' : name } )
            if name == '':
                del locations[-1]['name']
            if path.lower().startswith('http://'):
                pass
            elif fs.auto.isdir(path):
                sts = get_fsstat(path)
                if sts != (None,None):
                    locations[-1]['free'] = sts[0]
                    locations[-1]['total'] = sts[1]
            elif not fs.auto.isfile(path):
                del locations[-1]
            panel.progress.update_progress(0, n)
            panel.refresh()
            n = (n+1)%10

    return locations

def _element_to_location(e):
    path = e['path'] if e.has_key('path') else e['addr']
    name = os.path.basename(path)
    loc = {'type' : 'user_location', 'path' : path, 'name' : name}

    if path[:7].lower() == 'http://':
        loc['name'] += ' on %s' % path[7:].split('/',1)[0]
        #loc['server'] = path[:7].split('/',1)[0]
    else:
        sts = get_fsstat(path)
        if sts != (None,None):
            loc['free'] = sts[0]
            loc['total'] = sts[1]
    return loc



    
class PLocations:
    def _load_locations_thread(s):
        s.busy.set()
        try:
            s.panel.run_progress(_(" Open "), [[_("Please, wait ..."), u""]])
            s.panel.progress.set_progress(0, 10, "")
            s.panel.refresh()
            locations = get_mount_points() + [ get_home(), {'type': 'system_location', 'path' :'equalizer://', 'name' : _('Equalizer') } ] 
            locations.append({'type': 'system_location', 'path' :'radio://', 'name' : _('Radio') }) 
            locations.append({'type': 'system_location', 'path' :'lyrics://', 'name' : _('Lyrics') }) 
            locations.append({'type': 'system_location', 'path' :'config://', 'name' : _('Config') }) 
            locations.append({'type': 'system_location', 'path' :'help://', 'name' : _('Help') }) 
            s.panel.progress.update_progress(0, 1);
            s.panel.refresh()
            locations += _read_user_specific_locations_file(s.panel)
            s.panel.del_progress()
            s.storage.fill(locations)
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()

    def load_locations(s):
        s.AddTask(s._load_locations_thread, [])

    def enter(s):
        item = s.panel.get_current_item()
        s.set_location(item['path'])
        s.change_location()

    def delete(s):
        marked = s.storage.get_enumerated_marked_elements()
        if marked:
            #marked = filter( lambda ne: ne[1]['type'] == 'user_location', marked )
            system = filter( lambda ne: ne[1]['type'] != 'user_location', marked )
            if system != []:
                save_blacklist( map( lambda x: x[1]['path'], system) )
            if not marked:
                return
            for n,e in reversed(marked):
                s.storage.remove(n)
            s.panel.on_remove()
            s.save_locations()
        elif s.panel.get_current_item()['type'] == 'user_location':
            s.storage.remove(s.panel.pos)
            s.panel.on_remove()
            s.save_locations()
        else:
            save_blacklist([s.storage[s.panel.pos]['path']])
            s.storage.remove(s.panel.pos)
            s.panel.on_remove()
            
            return

    def on_copy(s, elements, source_location, copymode=0):
        s.storage.append( map(_element_to_location, elements) )
        s.save_locations()
    
    def save_locations(s):
        with codecs.open(config.locations_file, 'w', encoding='utf-8') as f:
            for lc in s.storage.elements:
                if lc['type'] == 'user_location':
                    f.write( lc['path'] + '\n')
                    f.write( lc['name'] + '\n')
    def new_element(s):
        s.panel.run_yesno(_(u' Add a new Location '), [_(u'Location Name:'), [""], _(u"Location Path:"), [""], ""], [_('<Okey>'), _('<Cancel>')])
        s.question = True
        s.cmd = "locations:new_element"

    def rename(s):
        location = s.storage.elements[s.panel.pos]
        if location['type'] == 'system_location':
            return
        s.panel.run_yesno(_(u' Rename a Location '), [_(u'Location Name:'), [location["name"]], _(u"Location Path:"), [location["path"]], ""], [_('<Okey>'), _('<Cancel>')])
        s.question = True
        s.cmd = "locations:rename"

    def question_enter(s):
        if s.cmd == "locations:new_element":
            rc = s.panel.yesno.enter()
            path = s.panel.yesno.inputs[1][1]
            name = s.panel.yesno.inputs[0][1]

            del s.panel.yesno
            s.panel.yesno = None
            s.question = False

            if rc == 0:
                location = { 'type' : 'user_location', 'path' : path, 'name' : name}
                if fs.auto.exists( path ) and name:
                    if not fs.auto.isfile( path ):
                        sts = get_fsstat(path)
                        if sts != (None,None):
                            location['free'] = sts[0]
                            location['total'] = sts[1]
                    s.storage.append( [ location ]  )
                    s.save_locations()

            s.panel.redraw()
            s.panel.refresh()

        elif s.cmd == "locations:rename":
            rc = s.panel.yesno.enter()
            path = s.panel.yesno.inputs[1][1]
            name = s.panel.yesno.inputs[0][1]

            del s.panel.yesno
            s.panel.yesno = None
            s.question = False

            if rc == 0:
                location = s.storage.elements[s.panel.pos]
                location['path'] = path
                location['name'] = name
                if fs.auto.exists( path ) and name:
                    if not fs.auto.isfile( path ):
                        sts = get_fsstat(path)
                        if sts != (None,None):
                            location['free'] = sts[0]
                            location['total'] = sts[1]

                    s.storage.reshort_no(s.panel.pos)
                    s.save_locations()

            s.panel.redraw()
            s.panel.refresh()

    def aftermove(s):
        s.save_locations()

