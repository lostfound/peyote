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
from  threading import Semaphore
import gettext
from useful import *
import os,fs.auto, time, random
import peyote_exec
import gettext
import httplib
import media_fs
import shutil, stat, httplib, signal
from panel_locations import PLocations
from thread_system.thread_polls import polls
import player
from encoder import ReEncoder
from sets import config

exists = fs.auto.exists
_ = localise

def chmoduw(fl):
    try:
        fldir = os.path.split(fl)[0]
        os.chmod( fl, os.stat(fl).st_mode|stat.S_IWRITE)
        os.chmod( fldir, os.stat(fldir).st_mode|stat.S_IWRITE )
    except:
        pass

class PFS:
    def execute(s):
        s.panel.run_yesno(_(" Command execution "), [_("Please enter a command"), [""], ""], 
            [_("<Run>"), _("<Background>"), _("<Cancel>")])
        s.question = True
        s.cmd = "execute"
    def on_delete(s):
        if s.type == "fs":
            s.thread_elements = s.storage.get_marked_elements()
            if s.thread_elements == [] and s.panel.pos > 0 and s.panel.pos < s.storage.nol:
                s.thread_elements = [ s.storage.elements[s.panel.pos] ]

            if s.thread_elements != []:
                s.stop_thread_flag = False
                s.AddTask(s.delete_thread)
        return False
    
    def dirsize(s):
        elements = s.storage.get_marked_elements()
        s.thread_elements = []
        for elm in elements:
            if elm['type'] == 'dir':
                s.thread_elements.append(elm)

        if s.thread_elements == []:
            del s.thread_elements
        else:
            s.stop_thread_flag = False
            s.AddTask(s.dirsize_thread)
        

    def rename(s):
        #stop inotify
        s.callback.inotify_unsubscribe(s)
        paths = set()
        if s.storage.marked_elements.count(True) > 1:
            marked_elements = s.storage.get_marked_elements()

            name = os.path.basename( marked_elements[0].get('path', "") )
            before = name
            after = name
            bodies = []
            for elm in marked_elements[1:]:
                if elm.has_key('path'):
                    name = os.path.basename( elm['path'] )
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

            for elm in marked_elements:
                if elm.has_key('path'):
                    name = os.path.basename ( elm['path'] )
                    name = name[len(before):]
                    if len(after) > 0:
                        name = name[:-len(after)]
                    bodies.append((name, elm))


            if  bodies != []:
                mask = s.panel.rename(before + '*' + after)
                if mask != None and mask.count('*') == 1:
                    
                    before = mask[:mask.find('*')]
                    after  = mask[mask.find('*') + 1:]
                    for name,elm in bodies:
                        paths.add( fs.auto.parentdir(elm['path']) )
                        try:
                            os.rename(elm['path'], os.path.join(fs.auto.parentdir(elm['path']), before + name + after ) )
                        except OSError,e:
                            s.panel.run_yesno(_(u" error "), [unicode2(e[1]), ""], [_(u"<Let It Be>")])
                            s.question = True
                            s.cmd = "error"
                            break
        else:
            if s.storage.marked_elements.count(True) == 1:
                elm = s.storage.get_marked_elements()[0]
            else:
                elm = s.storage.elements[s.panel.pos]

            if elm.has_key('path'):
                new_name = s.panel.rename(os.path.basename(elm['path']))
                if new_name != None:
                    try:
                        filepath = os.path.join( fs.auto.parentdir(elm['path']), new_name)
                        os.rename(elm['path'], filepath )
                    except OSError,e:
                        s.panel.run_yesno(_(u" error "), [unicode2(e[1]), ""], [_(u"<Let It Be>")])
                        s.question = True
                        s.cmd = "error"
                    except:
                        s.panel.run_yesno(_(u" error "), [_("can't rename"), ""], [_(u"<Let It Be>")])
                        s.question = True
                        s.cmd = "error"
                    else:
                        s.fs_refresh(filepath = filepath, path = fs.auto.parentdir(filepath) )
        #start inotify
        s.callback.inotify_subscribe(s)
        for p in reversed( sorted(paths) ):
            s.fs_refresh(path=p)

    def question_enter(s):
            if s.cmd == "delete":
                rc = s.panel.yesno.enter()
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False

                s.panel.redraw()
                s.panel.refresh()
                if rc == 2:
                    rc = random.randint(0,1)
                if rc == 0:
                        s.on_delete()
                s.cmd = None


            elif s.cmd == "move":
                rc = s.panel.yesno.enter()
                destination = s.panel.yesno.inputs[0][1]

                s.cmd =  None
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False

                if rc == 0:
                    s.on_fsmove(destination)
                else:
                    s.panel.redraw()
                    s.panel.refresh()

            elif s.cmd == "newelement":
                rc = s.panel.yesno.enter()
                del s.panel.yesno
                s.panel.yesno = None

                if rc == 2:
                    s.question = False
                    s.panel.redraw()
                    s.panel.refresh()
                elif rc == 1:
                    s.new_playlist()
                elif rc == 0:
                    s.new_directory()

            elif s.cmd == "newdirectory":
                rc = s.panel.yesno.enter()
                directory_name = s.panel.yesno.inputs[0][1]
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                if rc == 0 and len(directory_name) > 0: #create playlist
                    #stop inotify
                    s.callback.inotify_unsubscribe(s)
                    if directory_name[0] != '/':
                        directory_path = os.path.abspath( os.path.join(s.location, directory_name) )
                    else:
                        directory_path = directory_name
                    if exists(directory_path):
                        s.panel.run_yesno(_(u" error "), [_(u"File exists"), ""], [_(u"<Let It Be>")])
                        s.question = True
                        s.cmd = "error"
                    else:
                        try:
                            os.makedirs(directory_path)
                        except OSError,e:
                            s.panel.run_yesno(_(u" error "), [unicode2(e[1]), ""], [_(u"<Let It Be>")])
                            s.question = True
                            s.cmd = "error"
                        except:
                            s.panel.run_yesno(_(u" error "), [_("Can't create a Directory"), ""], [_(u"<Let It Be>")])
                            s.question = True
                            s.cmd = "error"
                        else:
                            s.fs_refresh(filepath = directory_path,  path = fs.auto.parentdir( directory_path ) )
                    #start inotify
                    s.callback.inotify_subscribe(s)
                s.panel.redraw()
                s.panel.refresh()

            elif s.cmd == "newplaylist":
                rc = s.panel.yesno.enter()
                playlist_name = s.panel.yesno.inputs[0][1]
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False

                if rc == 0 and len(playlist_name) > 0: #create playlist
                    #stop inotify
                    s.callback.inotify_unsubscribe(s)
                    if playlist_name[0] != '/':
                        playlist_path = os.path.abspath( os.path.join(s.location, playlist_name) )
                    else:
                        playlist_path = playlist_name
                    if exists(playlist_path):
                        s.panel.run_yesno(_(u" error "), [_(u"File exists."), ""], [_(u"<Let It Be>")])
                        s.question = True
                        s.cmd = "error"
                    else:
                        try:
                            f = open(playlist_path, "w")
                            f.close()
                        except IOError,e:
                            s.panel.run_yesno(_(u" error "), [unicode2(e[1]), ""], [_(u"<Let It Be>")])
                            s.question = True
                            s.cmd = "error"
                        except Exception,e:
                            s.panel.run_yesno(_(u" error "), [_("Can't create a playlist"), ""], [_(u"<Let It Be>")])
                            s.question = True
                            s.cmd = "error"
                        else:
                            s.fs_refresh(filepath = playlist_path, path = fs.auto.parentdir( playlist_path ) )
                    #start inotify
                    s.callback.inotify_subscribe(s)

                s.panel.redraw()
                s.panel.refresh()

            elif s.cmd == "select-encoder":
                rc = s.panel.yesno.enter()
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                s.panel.redraw()
                s.panel.refresh()
                if rc == 0:
                    return
                rc -= 1
                profile = config.encoder_profiles[config.encoder_profiles.keys()[rc]]
                try:
                    s.encoder = ReEncoder(profile)
                except Exception, e:
                    s.panel.run_yesno(_(u" error "), [_("Can't initialize encoder!"), repr(e), ""], [_(u"<Let It Be>")])
                    s.question = True
                    s.cmd = "error"
                else:
                    s.AddTask(s.encode_thread)

            elif s.cmd == "thread-error":
                s.tes.release()
                
            elif s.cmd == "error":
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                s.panel.redraw()
                s.panel.refresh()

            elif s.cmd == "audioselect":
                rc = s.panel.yesno.enter()
                title = s.panel.yesno.inputs[0][1]
                artist = s.panel.yesno.inputs[1][1]
                album = s.panel.yesno.inputs[2][1]

                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                s.panel.redraw()
                s.panel.refresh()

                if rc == 0:
                    wanted = dict()
                    if title != "":
                        wanted['title'] = title.lower().split()
                    if artist != "":
                        wanted['performer'] = artist.lower().split()
                    if album != "":
                        wanted['album'] = album.lower().split()
                    if wanted != dict():
                        for n,elm in enumerate (s.storage.elements):
                            tst = True
                            if is_track(elm) and not s.storage.marked_elements[n]:
                                try:
                                    if wanted.get('title', []) != []:
                                        sss = elm.get('title', u'').lower()
                                        for part in wanted.get('title', []):
                                            if part not in sss:
                                                tst = False
                                                break

                                    if wanted.get('album', []) != []:
                                        sss = elm.get('album', u'').lower()
                                        for part in wanted.get('album', []):
                                            if part not in sss:
                                                tst = False
                                                break

                                    if wanted.get('performer', []) != []:
                                        sss = elm.get('performer', u'').lower()
                                        for part in wanted.get('performer', []):
                                            if part not in sss:
                                                tst = False
                                                break

                                    if tst:
                                        s.storage.marked_elements[n] = True
                                        s.storage.reshort_no(n)
                                except:
                                    pass
                        s.panel.redraw()
                        s.panel.refresh()
                else:
                    pass
                    

            elif s.cmd == "execute":
                rc = s.panel.yesno.enter()
                command = s.panel.yesno.inputs[0][1]
                #password= s.panel.yesno.inputs[1][1]
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                pwd = s._get_target_dir()
                if command != u"" and rc !=2 : #Execute
                    if rc == 1:
                        peyote_exec.background(command, pwd = pwd )
                    else:
                        s.busy.set()
                        s.stop_thread_flag = False
                        s.command = command
                        s.AddTask(s.execute_thread)
                    pass
                s.panel.redraw()
                s.panel.refresh()
            elif s.cmd == "kill":
                s.kill_semaphore.acquire()
                if s.question == False: #
                    s.kill_semaphore.release()
                    return
                rc = s.panel.yesno.enter()
                #cpid = peyote_exec.get_shell_child(s.exc.pid)
                cpid = s.exc.pid
                if cpid != None:
                    try:
                        os.kill(cpid, signal.SIGTERM if rc == 0 else signal.SIGKILL)
                    except:
                        pass
                s.kill_semaphore.release()

    def _open_location_thread(s, parent_entry, played_songs, marked_entries, opened_dirs = None, pos_id = None):
        s.busy.set()
        try:
            s.marked_size = 0
            #s.panel.run_progress(_(" Open "), [[_("Please, wait ..."), u""]])
            #s.panel.progress.set_progress(0, 10, "")
            s.panel.process.print_text_message(_(u"Please, wait ..."))
            #s.panel.refresh()

            #s.panel.progress.update_progress(0, 6);
            #s.panel.refresh()
            s.fs.open_dir(s.location)

            s.storage.fill(s.fs.get_elements())
            #s.panel.progress.update_progress(0, 10);
            #s.panel.refresh()
            if opened_dirs and opened_dirs != []:
                s.panel.process.set_progress(len(opened_dirs))
                for od in opened_dirs:
                    for n,elm in enumerate( s.storage.elements ):
                        if elm.get('type') == 'dir' and elm.get('path') == od:
                            s.fs_open_subdir(n)
                            s.panel.process.increment()
                            break

            if parent_entry:
                n = s.storage.search_keyval('name', parent_entry)
                if n >= 0:
                    s.panel.select(n)

            if played_songs  or marked_entries:
                for i, song in enumerate(s.storage.elements):
                    if song.get('addr',"") in played_songs:
                        song['playback_num'] = 1
                        played_songs.remove(song.get('addr',""))
                    if song.get('addr',"") in marked_entries:
                        s.storage.marked_elements[i] = 1
                        marked_entries.remove(song.get('addr',""))
                    #set cursor position
                    if pos_id and get_id(song) == pos_id:
                        s.panel.pos = i
                        pos_id = None
                    if played_songs == [] and marked_entries == [] and not pos_id :
                        break

                s.marked_size =  media_fs.get_elm_size(s.storage.get_marked_elements())

        except Exception, e:
            pass
        try: s.storage.reshort()
        except: pass
        try: s.panel.redraw()
        except: pass
        try: s.panel.refresh()
        except: pass
        try: s.update_total_time()
        except: pass
        try: s.print_info()
        except: pass

        #start inotify
        s.callback.inotify_unsubscribe(s)
        s.callback.inotify_subscribe(s)
        s.busy.clear()


    def open_location(s, parent_entry=None, played_songs = None, marked_entries = None, opened_dirs = None, pos_id = None ):
        s.panel.head(s.location)
        s.AddTask( s._open_location_thread, args = [ parent_entry, played_songs, marked_entries, opened_dirs, pos_id] )

    def enter(s):
        if s.question:
            PFS.question_enter(s)
            return

        item = s.panel.get_current_item()
        if type(item) == dict:
            if item['type'] in  ['dir', 'playlist']:
                parent_entry = None
                if item['name'] == u"/..":
                    split_location = os.path.split(s.location)
                    parent_entry = u"/" + split_location[1]
                    s.set_location(split_location[0])
                else:
                    parent_entry = None
                    s.set_location( item['path'] )

                if len(s.location) > 1 and s.location[1] == '/' and s.location[0] == '/':
                    s.location = s.location[1:]

                if item['type'] == 'playlist':
                    s.type  = 'playlist'
                else:
                    s.type = "fs"

                if s.type == "fs":
                    PFS.open_location(s, parent_entry)

                elif s.type == "playlist":
                    s.open_playlist()


            elif is_track(item):
                s.callback.play_track(item)

            elif item['type'] == 'fsfile':
                peyote_exec.execute(item, s.location)

    def tree_back(s):
        s.storage.remember_cursors()
        selected_path = s.location
        s.fs.back(s.storage.elements)
        s.location = s.fs.path
        s.panel.head(s.location)
        elements = s.fs.unzip(s.fs.get_elements())
        s.storage.fill(elements)
        for n,e in enumerate(elements):
            if e.get('type') == 'dir' and e.get('path') == selected_path:
                s.panel.select(n)
                break
        
        s.storage.restore_cursors()
        s.panel.print_playercursor()
        s.callback.inotify_subscribe(s)

    def back(s):
        if  s.storage[s.panel.pos]['type'] == 'dir' and s.storage[s.panel.pos].get('opened'):
            s.fs_close_subdir()
        elif s.tree_mode and s.storage[s.panel.pos]['type'] == 'dir' and s.storage[s.panel.pos].get('name') in ['/..', '~..']:
            s.tree_back()
        elif s.storage[s.panel.pos].get('depth'):
            depth = s.storage[s.panel.pos].get('depth')
            for n in reversed( range(s.panel.pos) ):
                if s.storage[n].get('depth',0) == depth - 1:
                    s.panel.pos = n
                    s.panel.redraw()
                    s.panel.refresh()
                    s.update_total_time()
                    s.print_info()
                    break
        elif s.fs.has_parent():
            split_location = os.path.split(s.location)
            parent_entry = u"/" + split_location[1]
            s.set_location ( split_location[0] )
            PFS.open_location(s, parent_entry)
        else:
            s.set_location('locations://')
            s.change_location()

    def tree_right(s):
        if not s.storage[s.panel.pos].get('opened'):
            s.fs_open_subdir()
        else:
            depth = s.storage[s.panel.pos].get('depth', 0)
            for n in range(s.panel.pos+1, s.storage.nol ):
                if s.storage[n].get('depth',0) <= depth:
                    s.panel.pos = n
                    s.panel.redraw()
                    s.panel.refresh()
                    s.update_total_time()
                    s.print_info()
                    return
            s.panel.pos = s.storage.nol - 1
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()

    def on_copy(s, elements, source_location, copymode=0):
        s.thread_elements = []
        if copymode == 2:
            s.thread_elements = []
            for elm in elements:
                if is_track2(elm):
                    s.thread_elements.append(elm)
                elif type(elm) == dict and elm['type'] in ['dir']:
                    tracks = media_fs.list_dir(elm['path'])
                    s.thread_elements += tracks
            if s.thread_elements != []:
                encoders = ["<Cancel>" ] + map ( lambda e: u"<" + e +">", config.encoder_profiles.keys() )
                s.panel.run_yesno(_(u" encode "), [_("Select encoder")], encoders )
                s.cmd = "select-encoder"
                s.question = True

            return

        cue_files = set()
        audio_files = set()
        for elm in elements:
            if elm['type'] in ['http']:
                s.thread_elements.append(elm)
            elif elm.has_key('path'):
                s.thread_elements.append(elm)
            elif elm['type'] == 'cue':
                try:
                    cue_file = {'type' : 'file', 
                        'path' : elm['addr'].split('cue://',1)[1].rsplit('#',1)[0] }
                    if cue_file == '':
                        continue
                except:
                    continue

                audio_file = {'type' : 'file', 'path' : elm['file'] }
                if cue_file['path'] not in cue_files:
                    cue_files.add(cue_file['path'])
                    s.thread_elements.append(cue_file)
                if audio_file['path'] not in audio_files:
                    audio_files.add(audio_file['path'])
                    s.thread_elements.append(audio_file)
                
        if s.thread_elements != []:
            s.stop_thread_flag = False
            if source_location and len(source_location) > 1 and source_location[-1] == '/':
                s.source_location = source_location[:-1]
            else:
                s.source_location = source_location
            s.AddTask(s.copy_thread, [copymode])
        return
            
    def fsmove(s, destdir):
        s.panel.run_yesno(_(u" move "), [_("Move files and directories to"), [destdir]], [_("<Yes>"), _("<No>")])
        s.cmd = "move"
        s.question = True

    def on_fsmove(s, destdir):
        s.move_thread_destdir = destdir
        s.move_thread_melements = [] #те что на одной файловой системе
        s.move_thread_celements = [] #которые находятся на разных файловых системах
        
        #Подготовим тред
        destmp = media_fs.get_mount_point(destdir)
        for elm in s.storage.get_marked_elements() if s.storage.marked_elements.count(True) > 0 else [s.storage.elements[s.panel.pos]]:
            if elm.has_key('path'):
                if destmp == media_fs.get_mount_point(elm['path']):
                    s.move_thread_melements.append(elm)
                else:
                    s.move_thread_celements.append(elm)
        if s.move_thread_melements == [] and s.move_thread_celements == []:
            #если нет того что перемещать
            del s.move_thread_destdir
            del s.move_thread_melements
            del s.move_thread_celements
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()
        else:
            #если есть, то запустим трэд
            s.stop_thread_flag = False
            s.AddTask(s.move_thread)
            
    def update_fs(s, path=None):
        if not s.busy.is_set() and not s.question and s.type == 'fs':
            s.fs_refresh(path=path)
            
    def fs_refresh(s, filepath=None, path=None):
        N = 0
        if path and path != s.location:
            parent = None
            for n,e in enumerate(s.storage.elements):
                if e.get('path') == path and e.get('type') == 'dir':
                    parent = e['owner'].children.get(path)
                    N = n
                    break
            if not parent:
                return
            try:
                relms,nelms = parent.update()
            except:
                return
        else:
            parent = s.fs
            try:
                relms,nelms = s.fs.update()
            except:
                return
        #remove relms
        for re in relms:
            reid = get_id(re)
            for n,e in enumerate(s.storage.elements):
                if get_id(e) == reid:
                    if e['type'] == 'dir' and e.get('opened'):
                        depth = e.get('depth', 0)
                        children = []
                        for i in range(n+1, s.storage.nol):
                            if s.storage[i].get('depth', 0) <= depth:
                                break
                            children.append(i)
                        for i in reversed(children):
                            s.storage.remove(i)
                    s.storage.remove(n)
                    break
        #add new elements
        elements = parent.get_elements()
        while nelms != []:
            for e in nelms:
                idx = elements.index(e)
                if idx == 0:
                    s.storage.insert([e], N)
                    nelms.remove(e)
                    break
                else:
                    prev = elements[idx-1]
                    try:
                        n = s.storage.elements.index(prev) 
                    except:
                        continue
                    depth = e.get('depth', 0)
                    if n+1 < s.storage.nol:
                        i = n + 1
                        for i in range(n+1, s.storage.nol):
                            if depth >= s.storage[i].get('depth', 0):
                                n = i - 1
                                break
                        else:
                            n = s.storage.nol - 1
                    s.storage.insert([e], n)
                    nelms.remove(e)
                    break
                
        s.storage.append(nelms)

        pos = s.panel.pos
        s.panel.head(s.location)
        if pos != None and pos >=0 and filepath==None:
            if pos < s.storage.nol:
                s.panel.pos = pos
            else:
                s.panel.pos = s.storage.nol - 1
            s.panel.select(s.panel.pos)
        elif filepath:
            for n,elm in enumerate (s.storage.elements):
                if elm.get('path','') == filepath:
                    s.panel.select(n)
                    break
        s.storage.reshort()
        s.panel.redraw()
        s.panel.refresh()
        s.update_total_time()
        s.print_info()

    def switch_tree_mode(s):
        if not s.question and not s.busy.is_set() and s.type == 'fs':
            s.tree_mode = not s.tree_mode
            if not s.storage.nol:
                return

            s.storage.remember_cursors()
            if not s.tree_mode:
                pos_id = None
                for n in reversed( range(s.panel.pos + 1) ):
                    e = s.storage[n]
                    if e.get( 'depth', 0 ) == 0:
                        pos_id = get_id(e)
                        break
                s.callback.inotify_unsubscribe(s)
                s.fs.close_subdirs()
                s.storage.fill( s.fs.get_elements() )
                s.callback.inotify_subscribe(s)

                pos = 0
                if pos_id != None:
                    for n,e in enumerate(s.storage.elements):
                        if get_id(e) == pos_id:
                            pos = n
                            break
                s.panel.pos = pos
            else:
                s.storage.reshort()
            s.storage.restore_cursors()
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()
    def fs_subdir(s):
        pos = s.panel.pos
        if pos != None and s.storage[pos]['type'] == 'dir':
            if not s.storage[pos].has_key('opened'):
                s.fs_open_subdir()
            else:
                s.fs_close_subdir()
    def fs_open_subdir(s, pos=None):
        if pos == None:
            pos = s.panel.pos
        if pos != None and s.storage[pos]['type'] == 'dir' and not s.storage[pos].has_key('opened'):
            m = s.storage[pos]['owner']
            elements = m.open_subdir(s.storage[pos])
            s.storage.insert(elements, pos)
            s.storage.reshort_no(pos)
            s.callback.inotify_subscribe(s, s.storage[pos]['path'] )
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()

    def fs_close_subdir(s):
        pos = s.panel.pos
        if pos != None and s.storage[pos]['type'] == 'dir' and s.storage[pos].has_key('opened'):
            depth = s.storage[pos].get( 'depth', 0 )
            m = s.storage[pos]['owner']
            pos += 1
            while pos != s.storage.nol and s.storage[pos].get( 'depth', 0 ) > depth:
                s.storage.remove(pos)
            m.close_subdir( s.storage[s.panel.pos] )
            s.storage.reshort_no(s.panel.pos)
            #unsubscribe
            s.callback.inotify_unsubscribe(s, s.storage[s.panel.pos]['path'])
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()
                

    def fs_files(s):
        if s.fs.fsmode%2 == 0: #Hide files
            current_item = None
            if s.panel.pos != None:
                for pos in reversed ( range(s.panel.pos + 1) ):
                    if s.storage[pos]['type'] != 'fsfile':
                        current_item = s.storage[pos]
                        break

            for i in reversed( range(s.storage.nol)):
                if s.storage[i]['type'] == 'fsfile':
                    s.storage.remove(i)
            if s.storage.nol:
                if current_item:
                    s.panel.pos = s.storage.elements.index(current_item)
                else:
                    s.panel.pos = 0
            else:
                s.panel.pos = None
            s.panel.redraw()
            s.panel.refresh()
            s.update_total_time()
            s.print_info()

        else: #show files
            subdirs = []
            for n,e in enumerate( s.storage.elements ) :
                if e['type'] == 'dir' and e.get('opened'):
                    subdirs.append(n)

            for n in reversed( subdirs ):
                END=n
                depth = s.storage[n].get('depth', 0)
                try:
                    m = s.storage[n]['owner'].children[s.storage[n]['path']]
                except:
                    continue

                for i in range( n + 1, s.storage.nol ):
                    if s.storage[i].get('depth',0) <= depth:
                        END = i - 1
                        break
                else:
                    END = s.storage.nol - 1
                s.storage.insert( m.get_files(), END )
                    
            s.storage.append(s.fs.get_files())

    def delete(s):
        s.panel.run_yesno(_(u" delete "), [_(u"Delete "), _(u"files and directories?"), ""], [_(u"<Yes>"), _(u"<No>"), _(u"<Random>")])
        s.question = True
        s.cmd = "delete"

    def new_directory(s):
        s.panel.run_yesno(_(' Create a new Directory '), [_('Please, Enter Directory Name:'), ["folder"], ""], [_('<Okey>'), _('<Cancel>')])
        s.cmd = "newdirectory"
        s.panel.redraw()
        s.panel.refresh()

    def new_playlist(s):
        s.panel.run_yesno(_(' Create a new Playlist '), [_('Please, Enter playlist name:'), ["playlist.xspf"], ""], [_('<Okey>'), _(u'<Cancel>')])
        s.cmd = "newplaylist"
        s.panel.redraw()
        s.panel.refresh()


class PThread:
    def _threaderr(s):
        s.tes = Semaphore(0)
        s.cmd = "thread-error"
        s.question = True
        s.tes.acquire()

    def _get_target_dir(s):
        location = s.location
        depth = s.storage[s.panel.pos].get('depth', 0)
        if s.storage[s.panel.pos]['type'] == 'dir' and s.storage[s.panel.pos].get('opened'):
            location = s.storage[s.panel.pos]['path']
        elif depth != 0:
            for i in reversed(range(0, s.panel.pos)):
                d = s.storage[i].get('depth', 0)
                if d < depth and s.storage[i]['type'] == 'dir':
                    location = s.storage[i]['path']
                    break
        return location

    def http_get_length(s, track):
        c= httplib.HTTPConnection(track['server'])
        c.request('GET', track['addr'])
        rq=c.getresponse()
        c.close()

        if rq.status == 200:
            if type(rq.length) == int:
                return rq.length
            else:
                return 0
        else:
            return

    def default_pfs_sets(s):
        s.overwrite_all = False
        s.skip_file_existence = False
        s.skip_symlink_creation = False
        s.skip_open_error = False
        s.try_chmod = False
        s.delete_skip_all = False

    def remove_file(s, dst):
        errno = 0
        while True:
            repeat = False
            if s.stop_thread_flag:
                break

            if s.try_chmod:
                try:
                    os.remove(dst)
                except:
                    chmoduw(dst)
                else:
                    return True
            try:

                os.remove(dst)
    
            except OSError,e:
                if not s.delete_skip_all:
                    errno = e[0]

                    if errno == 13:
                        s.panel.run_yesno(_(u" error "), [_(u"Can't delete file:"), dst[-(s.width - 5):], unicode2(e[1]), ""], 
                            [_(u"<Abort>"), _(u"<Retry>"), _(u"<Skip"), _(u"All>"), _(u"<chmod"), _(u"All>")])

                    else:
                        s.panel.run_yesno(_(u" error "), [_(u"Can't delete file:"), dst[-(s.width - 5):], unicode2(e[1]), ""], 
                            [_(u"<Abort>"), _(u"<Retry>"), _(u"<Skip"), _(u"All>")])

                    s._threaderr()
                else:
                    return False

                s.question = True

            except Exception, e:
                if not s.delete_skip_all:
                    s.panel.run_yesno(_(u" error "), [_(u"Can't delete file:"), unicode2(e)[-(s.width - 5):], dst[-(s.width - 5):], ""], 
                        [_(u"<Abort>"), _(u"<Retry>"), _(u"<Skip>")])
                    s._threaderr()
                else:
                    return False
            else:
                return True

            rc = s.panel.yesno.enter()
            del s.panel.yesno
            s.panel.yesno = None
            s.question = False

            if rc == 0: #abort
                s.stop_thread_flag = True
                return False

            elif rc == 1: #retry
                pass
            elif rc == 2: #skip
                return False

            elif rc == 3: #skip all
                s.delete_skip_all = True
                return False

            elif rc == 4: #chmod
                chmoduw(dst)
    
            elif rc == 5: #chmod all
                s.try_chmod = True
        #remove_file

    
    def make_dir(s, dst):
        if not exists(dst):
            while True:
                if s.stop_thread_flag:
                    return False

                try:
                    os.makedirs( dst )
                except OSError,e:
                    errno = e[0]
                    s.panel.run_yesno(_(u" error "), [_(u"Can't create target directory"), dst[-(s.width - 5):], unicode2(e[1]), ""], 
                        [_(u"<Abort>"), _(u"<Retry>"), _(u"<Skip>")])
                    s._threaderr()
                except:
                    s.panel.run_yesno(_(u" error "), [_("Can't create target directory"), dst[-(s.width - 5):], ""],
                        [_(u"<Abort>"), _(u"<Retry>"), _(u"<Skip>")])
                    s._threaderr()
                else:
                    return True

                rc = s.panel.yesno.enter()
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False

                if rc == 0:
                    s.stop_thread_flag = True
                    return False
                if rc == 2:
                    return False
            return False
        return True
        #make_dir

    def copy_file(s, src, dst, total_count):
        bufsize = 128000

        while True:
            if exists ( dst ):
                if s.skip_file_existence:
                    #skip this file
                    return False
                elif s.overwrite_all:
                    if not os.path.islink(dst) and os.path.isdir(dst):
                        #write me
                        return False
                        pass

                    else:
                        #remove file
                        s.remove_file(dst)
                else:
                    s.panel.run_yesno(_(u" File exists "), [_(u"Target file already exists!"),dst[-(s.width - 5):], ""], 
                        [_(u"<Abort>"), _(u"<Retry>"), _(u"<Overwrite"), _(u"All>"),  _(u"<Skip"), _("All>")])
                    s._threaderr()

                    rc = s.panel.yesno.enter()
                    del s.panel.yesno
                    s.panel.yesno = None
                    s.question = False
                    s.panel.redraw()
                    s.panel.refresh()

                    if rc == 0:
                        #stop copy
                        s.stop_thread_flag = True
                        return False
                    elif rc == 1:
                        #retry
                        pass
                    elif rc == 2:
                        #Overwrite
                        s.remove_file(dst)
                    elif rc == 3:
                        s.overwrite_all = True
                        #Overwrite all
                    elif rc == 4:
                        #Skip
                        return False
                    elif rc == 5:
                        s.skip_file_existence = True
                        #Skip all
                        return False
            else:
                break

        if fs.auto.islink(src):
            while True:
                try:
                    link = os.readlink(src)
                    os.symlink(link, dst)
                except OSError,e:
                    if not s.skip_symlink_creation:
                        s.panel.run_yesno(_(u" symlink error "), [_(u"Unable to create symlink"), dst[-(s.width - 5):], unicode2(e), ""], 
                            [_(u"<Abort>"), _(u"<Retry>"), _("<Skip"), _("All>")])
                        s._threaderr()

                        rc = s.panel.yesno.enter()
                        del s.panel.yesno
                        s.panel.yesno = None
                        s.question = False
                        s.panel.redraw()
                        s.panel.refresh()
                        if rc == 0:
                            #stop a thread
                            s.stop_thread_flag = True
                            return False
                        elif rc == 1:
                            #retry
                            pass
                        elif rc == 2:
                            #Skip
                            return False
                        elif rc == 3:
                            #Skip all
                            s.skip_symlink_creation = True
                            return False
                    
                else:
                    return True
        if not fs.auto.isfile(src):
            #fix me
            return False
            
        
        while True:
            #open a source
            try:
                fr =  fs.auto.open(src, "rb")
            except IOError,e:
                if not s.skip_open_error:
                    s.panel.run_yesno(_(u" file open error "), [_(u"Can't open source file:"),src[-(s.width - 5):], unicode2(e), ""], 
                        [_(u"<Abort>"), _(u"<Retry>"), _("<Skip"), _("All>")])
                    s._threaderr()

                    rc = s.panel.yesno.enter()
                    del s.panel.yesno
                    s.panel.yesno = None
                    s.question = False
                    s.panel.redraw()
                    s.panel.refresh()
                    if rc == 0:
                        #stop a thread
                        s.stop_thread_flag = True
                        return False
                    elif rc == 1:
                        #retry
                        pass
                    elif rc == 2:
                        #Skip
                        return False
                    elif rc == 3:
                        #Skip all
                        s.skip_open_error = True
                        return False
                else:
                    return False
            else:
                break
        while True:
            #open a destination
            try:
                fw =  open(dst, "wb")
            except IOError,e:
                if not s.skip_open_error:
                    s.panel.run_yesno(_(u" file open error "), [_(u"Can't open destination file"),dst[-(s.width - 5):], unicode2(e[1]), ""], 
                        [_(u"<Abort>"), _(u"<Retry>"), _("<Skip"), _("All>")])
                    s._threaderr()

                    rc = s.panel.yesno.enter()
                    del s.panel.yesno
                    s.panel.yesno = None
                    s.question = False
                    s.panel.redraw()
                    s.panel.refresh()
                    if rc == 0:
                        #stop a thread
                        s.stop_thread_flag = True
                        fr.close()
                        return False
                    elif rc == 1:
                        #retry
                        pass
                    elif rc == 2:
                        #Skip
                        fr.close()
                        return False
                    elif rc == 3:
                        #Skip all
                        s.skip_open_error = True
                        fr.close()
                        return False
                else:
                    fr.close()
                    return False
            else:
                break

        while True:
            if s.stop_thread_flag:
                break
            try:
                buf = fr.read(bufsize)
            except IOError, e:
                #read error handler
                s.panel.run_yesno(_(u" file read error "), [_(u"Can't read source file:"),src[-(s.width - 5):], unicode2(e[1]), ""], 
                    [_(u"<Abort>"), _("<Skip>")])
                s._threaderr()

                rc = s.panel.yesno.enter()
                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                s.panel.redraw()
                s.panel.refresh()
                #close fds and remove source
                fr.close()
                fw.close()
                try:
                    os.remove(dst)
                except:
                    pass
                if rc == 0:
                    #stop a thread
                    s.stop_thread_flag = True
                    return False
                elif rc == 1:
                    return False
            if not buf:
                break

            while True:
                try:
                    fw.write(buf)
                except IOError, e:
                    s.panel.run_yesno(_(u" file write error "), [_(u"Can't write destination file:"),dst[-(s.width - 5):], unicode2(e[1]), ""], 
                        [_(u"<Abort>"), _("<Repeat>"), _("<Skip>")])
                    s._threaderr()

                    rc = s.panel.yesno.enter()
                    del s.panel.yesno
                    s.panel.yesno = None
                    s.question = False
                    s.panel.redraw()
                    s.panel.refresh()
                    if rc in [0,2]:
                        fr.close()
                        fw.close()
                        try:
                            os.remove(dst)
                        except:
                            pass
                    if rc == 0:
                        #stop a thread
                        s.stop_thread_flag = True
                        return False
                    elif rc == 1:#repeat
                        pass
                    elif rc == 2: #skip
                        return False
                else:
                    break

            written_bytes = len(buf)
            s.panel.progress.update_progress(0, written_bytes)
            if total_count != 1:
                s.panel.progress.update_progress(1, written_bytes)


        fr.close()
        fw.close()

        if s.stop_thread_flag:
            try:
                os.remove(dst)
            except:
                pass
            return False
        elif src[:7].lower() != 'http://':
            shutil.copystat(src, dst)
        return True
        #copy_file



    def _encode_progress(s, dt ):
        try:
            if len(dt) == 2:
                s.panel.progress.set_progress(0, dt[0]/1000000000, 'Sec')
                s.panel.progress.update_progress(0, dt[1]/1000000000)
        except:
            pass
        s.panel.progress.refresh()
    def encode_thread(s):
        s.busy.set()
        #stop inotify
        s.callback.inotify_unsubscribe(s)
        try:
            size = 0L
            trees=[]
            pp = 0
            files = 0

            s.panel.run_progress(_(" Encode "), [["", "", ""], [""], [""]] )
            s.panel.progress.set_progress(1, len(s.thread_elements), _("Tracks"))
            abort = False
            for elm in s.thread_elements:
                if abort:
                    break
                if is_track2(elm):
                    repeat = True
                    while repeat:
                        repeat = False
                        s.panel.progress.change_str(0, 0, u"".join([_('artist: '), elm.get('performer',"")]) )
                        s.panel.progress.change_str(0, 1, u"".join([_('title: '), elm.get('title',"")]) )
                        s.panel.progress.print_n(0)
                        s.panel.progress.refresh()

                        if not s.encoder.process(elm, s.location):
                            s.panel.run_yesno(_(u" error "), [_(u"Error:") ] + s.encoder.get_splited_error(s.width - 8) + [ ""], 
                                [_(u"<Abort>"), _("<Repeat>"), _("<Skip>")])
                            s._threaderr()

                            rc = s.panel.yesno.enter()
                            del s.panel.yesno
                            s.panel.yesno = None
                            s.question = False
                            s.panel.redraw()
                            s.panel.refresh()
                            if rc == 0:
                                abort = True
                                break
                            elif rc == 1:
                                repeat = True
                                continue
                            else:
                                continue

                        s.encoder.wff( .2, s._encode_progress )
                        s.encoder.to_null()
                        s.panel.progress.update_progress(1, 1)
                        continue

        except Exception, e:
            pass
        s.stop_encode_thread()
        s.busy.clear()

    def stop_encode_thread(s):
        try:
            s.encoder.decoder.remove_temp()
            del s.encoder
        except:
            pass
        try:
            s.panel.del_progress()
        except:
            pass
        try:
            del s.thread_elements
            s.fs_refresh()
        except:
            pass
        #start inotify
        s.callback.inotify_subscribe(s)

    def copy_thread(s, copymode):
        def paths_to_tree(paths, byr = False):
            tree = {}
            root = None
            oth = []
            for p in sorted(paths):
                if not root:
                    root = p
                    continue
                if p.startswith(root):
                    if tree.has_key(root):
                        tree[root][0].append(p)
                    else:
                        tree[root] = ([p], {})
                else:
                    if tree.has_key(root):
                        tree[root] = paths_to_tree(tree[root][0], True)
                    elif byr:
                        oth.append(root)
                    root = p
            if root and tree.has_key(root):
                tree[root] = paths_to_tree(tree[root][0], True)
            elif byr:
                oth.append(root)
            if byr:
                return (oth, tree)
            return tree
        def prepare_path_tree(tree, n = 0):
            sdt = {}
            fakes = sorted(tree.keys())
            for p in tree.keys():
                dest_dir = os.path.basename(p)
                for x in tree[p][0]:
                    sdt[x] = dest_dir

                sfakes,ssdt = prepare_path_tree(tree[p][1], n+1)
                fakes += sfakes
                for x in sorted(ssdt.keys()):
                    sdt[x] = os.path.join(dest_dir, ssdt[x])
            return fakes, sdt
                    

        # Calculate size of elements
        s.busy.set()
        #stop inotify
        s.callback.inotify_unsubscribe(s)
        location = s.location
        if copymode == 1:
            location = s._get_target_dir()

        s._copy_location = location
        try:
            s.panel.run_progress(_(" Copy "), [[_("Generating tree"), u"", ""]])
            s.panel.progress.set_progress(0, 10, "")
            s.default_pfs_sets()
            size = 0L
            trees=[]
            pp = 0
            files = 0
            paths = []
            ptree = {}
            for elm in s.thread_elements:
                addr = elm['path'] if elm.has_key('path') else elm.get('addr')
                if addr:
                    paths.append(addr)
            ptree = paths_to_tree(paths)
            paths = sorted(paths)
            fakes, sdt = prepare_path_tree(ptree)


            for elm in s.thread_elements:
                addr = elm['path'] if elm.has_key('path') else elm.get('addr')
                if addr and addr not in fakes:
                    tree = list(media_fs.get_tree(addr))
                    if sdt.has_key(addr):
                        tree.append(sdt[addr])
                    trees.append(tree)
                    size+=trees[-1][2]
                    files+=len(trees[-1][0])

                s.panel.progress.update_progress(0,1)
                s.panel.refresh()
                pp += 1
            if len(trees) > 0:
                s.size = size
                s.stop_thread_flag = False
            else:
                s.on_stop_copy_thread()
                return

            s.panel.del_progress()
            s.panel.redraw()
            s.panel.refresh()
                
            if files == 1:
                s.panel.run_progress(_("Copy"), [["", "", ""]] )
            else:
                s.panel.run_progress(_("Copy"), [["", "", u""], [""], [""] ] )
                s.panel.progress.set_progress(1, size,"Bytes")
                s.panel.progress.set_progress(2, files, _("Files"))
                s.panel.progress.update_progress(2, 0)
            pp = 0
            prcs_size = 0L
            n = 0

            for tree in trees:
                if s.stop_thread_flag:
                    break
                source_location = tree[3]
                try:
                    dest_dir = tree[4]
                except:
                    dest_dir = None

                if dest_dir:
                    s.make_dir( os.path.join(location, dest_dir) )

                for dr in tree[1]:
                    if s.stop_thread_flag:
                        break
                    if source_location != None:
                        source_location_len = len(source_location) + 1
                        dir_name = dr[source_location_len:]
                        if dest_dir:
                            new_dir = os.path.join ( location, dest_dir, dir_name )
                        else:
                            new_dir = os.path.join ( location, dir_name )
                        s.make_dir(new_dir)

                for fl in tree[0]:
                    if s.stop_thread_flag:
                        break
                    if source_location != None:
                        source_location_len = len(source_location) + 1
                        name = fl[0][source_location_len:]
                        if dest_dir:
                            dest = os.path.join(location, dest_dir, name)
                        else:
                            dest = os.path.join(location, name)
                    else:
                        dest = os.path.join(location,  os.path.basename(fl[0]) )

                    try:
                        s.panel.progress.set_progress(0, os.path.getsize(fl[0]),"Bytes")
                    except:
                        s.panel.progress.set_progress(0, 0, "Bytes")

                    if s.stop_thread_flag:
                        break
                    s.panel.progress.change_str(0, 1, u"".join([_("copying "), "'", os.path.basename(fl[0]), "'" ] ) )
                    s.panel.progress.refresh()
                    rc = s.copy_file(fl[0], dest, files)
                    if files != 1:
                        s.panel.progress.update_progress(2, 1)
            del trees
        except:
            pass

        s.on_stop_copy_thread()
        s.busy.clear()

    def on_stop_copy_thread(s):
        try:
            s.panel.del_progress()
            del s.source_location
            del s.size
            del s.thread_elements
            if s._copy_location == s.location:
                s.fs_refresh()
            else:
                s.fs_refresh(path = s._copy_location)
            del s._copy_location
        except:
            pass
        #start inotify
        s.callback.inotify_subscribe(s)
            

    def move_thread(s):
        s.busy.set()
        try:
            s.default_pfs_sets()

            #сначало сделаем safe-move
            if s.move_thread_melements != []:
                s.panel.run_progress(_(" Move "), [["", u""]])
                s.panel.progress.set_progress(0, len(s.move_thread_melements), _("Files"))
                s.panel.redraw()
                s.panel.refresh()

            for elm in s.move_thread_melements:
                if s.stop_thread_flag:
                    break
                try:
                    os.rename( elm['path'], os.path.join(s.move_thread_destdir, os.path.basename(elm['path'])) )
                except OSError, e:
                    pass
                else:
                    s.panel.progress.change_str(0, 0, u"".join([_("moving "), os.path.basename(elm['path']) ]) )
                    s.panel.progress.print_n(0)
                    s.panel.progress.update_progress(0, 1)
                    s.panel.progress.refresh()

            if s.move_thread_celements != []:
                size = 0L
                trees=[]
                pp = 0
                files = 0
                s.panel.run_progress(_(" Move "), [[_("Generating tree"), u""]])
                s.panel.progress.set_progress(0, 100, "")
                s.default_pfs_sets()
                s.panel.refresh()
                size = 0L
                trees=[]
                pp = 0
                files = 0


                for elm in s.move_thread_celements:
                    if s.stop_thread_flag:
                        break
                    if elm.has_key('path'):
                        trees.append(media_fs.get_tree(elm['path']))
                        size+=trees[-1][2]
                        files+=len(trees[-1][0])

                    s.panel.progress.update_progress(0,1)
                    s.panel.progress.refresh()
                    pp += 1

                if s.stop_thread_flag:
                    s.on_stop_move_thread()
                    return

                s.panel.del_progress()
                s.panel.redraw()
                s.panel.refresh()
                    
                if files == 1:
                    s.panel.run_progress(_(" Move "), [["", "", ""]] )
                else:
                    s.panel.run_progress(_(" Move "), [["", "", u""], [""], [""] ] )
                    s.panel.progress.set_progress(1, size,"Bytes")
                    s.panel.progress.set_progress(2, files, _("Files"))
                    s.panel.progress.update_progress(2, 0)
                pp = 0
                prcs_size = 0L
                n = 0

                #location_len = len(s.location) + 1
                for tree in trees:
                    if s.stop_thread_flag:
                        break

                    root_dir = tree[3]
                    location_len = len(root_dir) + 1
                    for dr in tree[1]:
                        if s.stop_thread_flag:
                            break

                        dir_name = dr[location_len:]
                        new_dir = os.path.join ( s.move_thread_destdir, dir_name )
                        s.make_dir(new_dir)

                    for fl in tree[0]:
                        if s.stop_thread_flag:
                            break

                        name = fl[0][location_len:]
                        dest = os.path.join(s.move_thread_destdir, name)

                        try:
                            s.panel.progress.set_progress(0, os.path.getsize(fl[0]),"Bytes")
                        except:
                            s.panel.progress.set_progress(0, 0, "Bytes")

                        if s.stop_thread_flag:
                            break
                        s.panel.progress.change_str(0, 1, u"".join([_("moving "), fl[0]]) )
                        rc = s.copy_file(fl[0], dest, files)
                        if rc == True:
                            s.remove_file(fl[0])

                        if files != 1:
                            s.panel.progress.update_progress(2, 1)

                    for dir_name  in reversed (tree[1]): #delete all files
                        if s.stop_thread_flag:
                            break
                        try:
                            os.rmdir(dir_name)
                        except:
                            pass

                del trees
        except:
            pass
        s.on_stop_move_thread()
        s.busy.clear()


    def on_stop_move_thread(s):
        try:
            del s.move_thread_destdir
            del s.move_thread_melements
            del s.move_thread_celements
            s.panel.del_progress()
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
    
    def dirsize_thread(s):
        s.busy.set()
        try:
            s.panel.run_progress(_(" Directory Scanning "), [[_(""), u""]])
            s.panel.progress.set_progress(0, len(s.thread_elements), _("Directories"))
            for elm in s.thread_elements:
                if s.stop_thread_flag:
                    break
                s.panel.progress.change_str(0, 0, os.path.basename(elm['path']))
                s.panel.progress.print_n(0)
                s.panel.progress.refresh()

                tree = media_fs.get_tree(elm['path'])
                elm['size'] = tree[2]
                s.panel.progress.update_progress(0, 1)
                s.panel.progress.refresh()
        except:
            pass

        try:
            s.panel.del_progress()
            s.panel.redraw()
            s.panel.refresh()
            del s.thread_elements
            s.marked_size =  media_fs.get_elm_size(s.storage.get_marked_elements())
            s.print_info()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()


    def delete_thread(s):
        s.busy.set()
        #stop inotify
        s.callback.inotify_unsubscribe(s)
        try:
            s.default_pfs_sets()
            s.panel.run_progress(_("Delete"), [[_("Generating tree"), u""]])
            size = 0L
            skip_all = True
            trees=[]
            pp = 0
            files = 0
            chmod_before = False
            cue_files = set()
            audio_files = set()
            for elm in s.thread_elements:
                if elm.has_key('path'):
                    trees.append(media_fs.get_tree(elm['path']))
                    files+=len(trees[-1][0])
                    files+=len(trees[-1][1])
                elif elm['type'] == 'cue':
                    try:
                        cue_file = elm['addr'].split('cue://',1)[1].rsplit('#',1)[0] 
                        if cue_file == '':
                            continue
                    except:
                        continue

                    audio_file = elm['file'] 
                    if cue_file not in cue_files:
                        cue_files.add(cue_file)
                        trees.append( media_fs.get_tree(cue_file) )
                    if audio_file not in audio_files:
                        audio_files.add(audio_file)
                        trees.append( media_fs.get_tree(audio_file) )
            s.panel.del_progress()
            s.panel.redraw()
            s.panel.refresh()
            s.panel.run_progress(_("Delete"), [["", "", ""]] )
            s.panel.progress.set_progress(0, files, _("Files"))

            paths = set()
            for tree in trees:
                if s.stop_thread_flag:
                    break


                for file_name, size  in tree[0]: #delete all files
                    if s.stop_thread_flag:
                        break

                    try:
                        s.panel.progress.change_str(0, 1, u"".join([_("removing "), file_name]) )
                        s.panel.progress.print_n(0)
                        s.panel.progress.refresh()
                    except:
                        pass

                    if s.remove_file(file_name):
                        paths.add(fs.auto.parentdir(file_name))
                        s.panel.progress.update_progress(0, 1)
                    else:
                        pass

                for dir_name  in reversed (tree[1]): #delete all files
                    if s.stop_thread_flag:
                        break
                    try:
                        os.rmdir(dir_name)
                    except:
                        pass
                    else:
                        paths.add(fs.auto.parentdir(dir_name))
                        s.panel.progress.change_str(0, 1, u"".join([_("removing "), dir_name]) )
                        s.panel.progress.print_n(0)
                        s.panel.progress.refresh()
                        s.panel.progress.update_progress(0, 1)
        except Exception, e:
            pass
        s.on_stop_thread()
        for p in reversed( sorted(paths) ):
            try:
                s.fs_refresh(path=p)
            except Exception, e:
                pass
        #start inotify
        s.callback.inotify_subscribe(s)
        try:
            s.redraw()
            try: s.print_info()
            except: pass
            s.refresh()
        except:
            pass
        s.busy.clear()
    
    def on_stop_thread(s):
        try:
            s.panel.del_progress()
            del s.thread_elements
        except:
            pass

    def execute_thread(s):
        s.busy.set()
        try:
            pwd = s._get_target_dir()
            s.exc = peyote_exec.execute_command( s.command, pwd = pwd )
            if s.exc != None:
                s.kill_semaphore = Semaphore(1)
                s.question = True
                s.panel.run_yesno(_(" waiting "), [_("Waiting for the program to finish."), ""], [u"<SIGTERM>", u"<SIGKILL>"])
                s.cmd = "kill"
                s.panel.redraw()
                s.panel.refresh()
                try:
                    s.exc.wait()
                except:
                    pass
                s.kill_semaphore.acquire()

                del s.panel.yesno
                s.panel.yesno = None
                s.question = False
                s.panel.redraw()
                s.panel.refresh()

                s.kill_semaphore.release()
                time.sleep(.01)
                s.kill_semaphore.acquire()
                del s.kill_semaphore
            else:
                s.panel.run_yesno(_(" error "), [_("Unable to execute the command!"), ""], [u"<Let It Be>"])
                s._threaderr()
                s.panel.redraw()
                s.panel.refresh()
        except:
            pass
        s.on_stop_execute_thread()
        s.busy.clear()

    def on_stop_execute_thread(s):
        try:
            del s.command
            if s.exc:
                del s.exc
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass

