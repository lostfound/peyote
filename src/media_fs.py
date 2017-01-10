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
                                    
import os, statvfs
import stat
import cue
import fs.auto
from sorts import *
from sets import config
from useful import get_id
cue_extensions3 = [".cue"]
plst_extensions3 = [".pls", ".m3u"]
plst_extensions4 = [".xspf"]

autofs = fs.auto

EXT = 1
NAME = 2
c = cue

def is_audio_file(path):
    n = path.rfind('.')
    if n > 0:
        ext = path[n+1:].lower()
        if ext in config.GetAudioExtensions():
            if ext == 'wv' and path.lower().endswith('.iso.wv'):
                return False
            return True

    return False

def is_cue_file(path):
    if path[-4:].lower() in cue_extensions3:
        return True

def unicode2(s):
    if type(s) == str:
        return unicode(s.decode('utf-8'))
    else:
        return s

def convert_dir(dirnfo,pwd):
    element = dict()
    element['type'] = 'dir'
    element['name'] = u'/' + dirnfo[0]
    element['path'] = autofs.abspath(dirnfo[0], pwd)
    element['islink'] = dirnfo[2] == 'S'
    return element

def convert_pls(plsname, pwd):
    element = dict()
    element['type'] = 'playlist'
    element['name'] = plsname
    element['path'] = fs.auto.abspath(plsname, pwd)
    element['islink'] = os.path.islink(element['path'])
    return element

def convert_file(name, pwd):
    element = dict()
    element['type'] = 'fsfile'
    element['name'] = name[0]
    element['path'] = autofs.abspath( name[0], pwd )
    element['islink'] = autofs.is_entry_link(name)
    element['ext'] = c.get_file_type(name[0])
    element['size']= autofs.get_entry_size(name)
    return element

def convert_file2(path):
    element = dict()

    element['type']   = 'fsfile'
    element['name']   = os.path.basename(path)
    element['path']   = path
    element['islink'] = os.path.islink(path)
    element['ext']    = c.get_file_type(element['name'])
    try:
        element['size']   = os.path.getsize(path)
    except:
        element['size']   = 0

    return element
        
def get_tree(path, r=False):
    if path[:7].lower() == 'http://':
        return get_tree2(path, r=r)
    files = []
    directories = []
    size = 0L
    if path[-2:] == u"..":
        return ([],[],0, '')
    path = fs.auto.abspath(path)
    root_dir = os.path.dirname( fs.auto.abspath(path) )

    st = os.stat( path )
    mode =st[stat.ST_MODE]
    if os.path.islink(path):
        files.append( (path, 0) )
    elif stat.S_ISREG(mode):
        files.append( (path, st.st_size) )
        size +=st.st_size
    elif stat.S_ISDIR(mode):
        if r==False:
            directories.append(path)
        entries = os.listdir(path)
        for entry in entries:
            try:
                entry_path = os.path.join(path,entry)
                if os.path.islink(entry_path):
                    files.append( (entry_path, 0) )
                    continue
                st = os.stat( entry_path )
                mode = st[stat.ST_MODE]
                if stat.S_ISREG(mode):
                    files.append( (entry_path, st.st_size) )
                    size +=st.st_size
                elif stat.S_ISDIR(mode):
                    if not stat.S_ISLNK(mode):
                        directories.append(entry_path)
                else:
                    files.append( (entry_path, 0) )
            except:
                pass
        subdirs = []
        for dr in directories[1:] if not r else directories:
                subdirs.append(dr)

        for d in subdirs:
            F,D,S,R = get_tree(d,True)
            files=files + F
            size+=S
            directories += D
    else:
        files.append( (path, 0) )
    

    return (files, directories, size, root_dir)

def get_tree2(path, r=False):
    files = []
    directories = []
    size = 0L
    if path[-2:] == u"..":
        return ([],[],0, '')
    path = fs.auto.abspath(path)
    root_dir = os.path.dirname( fs.auto.abspath(path) )

    if fs.auto.islink(path):
        files.append( ( path, 0 ) )
    elif fs.auto.isfile(path):
        fsize = fs.auto.get_size(path)
        files.append( ( path, fsize ) )
        size += fsize
    elif fs.auto.isdir(path):
        if r==False:
            directories.append(path)
        entries = fs.auto.list_dir(path)
        for entry in entries:
                entry_path = os.path.join(path, entry[0])
                if fs.auto.islink(entry_path):
                    files.append( (entry_path, 0) )
                elif fs.auto.isfile(entry_path):
                    fsize = fs.auto.get_size(entry_path)
                    files.append( ( entry_path, fsize ) )
                    size += fsize
                elif fs.auto.isdir(entry_path):
                    directories.append(entry_path)
        subdirs = []
        for dr in directories[1:] if not r else directories:
            subdirs.append(dr)


        for d in subdirs:
            F,D,S,R = get_tree2(d,True)
            files=files + F
            size+=S
            directories += D
    else:
        files.append( (path, 0) )
    

    return (files, directories, size, root_dir)

def get_hardabs(path):
    hardpath = u""
    if not os.path.isdir(path):
        curpath = os.path.split(path)[0]
    else:
        curpath = path

    while curpath != '/':
        if os.path.islink(curpath):
            curpath = os.readlink(curpath)
        curpath, dirname = os.path.split(curpath)
        hardpath = os.path.join(dirname, hardpath)
    hardpath = os.path.join('/', hardpath)
    return hardpath



        
def get_mount_point(path):
    hardpath = get_hardabs (path)
    while hardpath != '/':
        if os.path.ismount(hardpath):
            return hardpath
        hardpath = os.path.split(hardpath)[0]
    return '/'
    

def get_human_readable(b):
    if b > 10737418240:
        _bytes = unicode(b//1073741824)
        scale = "GB"
    elif b > 10485760:
        _bytes = unicode(b//1048576)
        scale = "MB"
    elif b > 10240:
        _bytes = unicode(b//1024)
        scale = "KB"
    else:
        _bytes = unicode(b)
        scale = "B"
    return unicode(_bytes) + ' ' + scale
    
class media_fs:
    def __init__(s, parent=None):
        s.sort_order = EXT
        s.path = None
        s.dirs = None
        s.files = None
        s.hidden_dirs = None
        s.hidden_files = None
        s.media_files = None
        s.cue_files = None
        s.cues = None
        s.medias = None
        s.playlists = None
        s.tracks = None
        s.dir_entries = None
        s.others = None
        s.bad_cuefiles =None
        s.filesize = None
        s.fsmode = 0
        s.total = 0
        s.free = 0
        s.disc_space = ""
        s.children = {}
        s.parent = parent
        s.depth = 0
        if parent:
            s.depth = s.parent.depth + 1


    def __del__(s):
        s._free()
        for k in s.children.keys():
            del s.children[k]

    def get_fsstat(s):
        try:
            try: osstat = os.statvfs(s.path)
            except UnicodeEncodeError: osstat = os.statvfs( str( s.path.encode('utf-8') ) )
        except:
            s.total = 0
            s.free  = 0
            s.disc_space = ""
        else:
            s.total = osstat[statvfs.F_BSIZE] * osstat[statvfs.F_BLOCKS]
            s.free  = osstat[statvfs.F_BSIZE] * osstat[statvfs.F_BAVAIL]
            s.disc_space = get_human_readable(s.free) + '/' + get_human_readable(s.total)

    def has_parent(s):
        if s.path:
            return autofs.has_parent(s.path)
        return False
    def back(s, elements):
        slave = media_fs(s)
        for e in elements:
            if  e.get('depth', 0 ) == 0:
                e['owner'] = slave
            e['depth'] = e.get('depth', 0 ) + 1
        parent_dir = fs.auto.abspath(os.path.join(s.path, '..'))
        slave_path = s.path

        slave.sort_order = s.sort_order
        slave.path = slave_path
        slave.dirs = s.dirs
        slave.files = s.files
        slave.hidden_dirs = s.hidden_dirs
        slave.hidden_files = s.hidden_files
        slave.media_files = s.media_files
        slave.cue_files = s.cue_files
        slave.cues = s.cues
        slave.medias = s.medias
        slave.playlists = s.playlists
        slave.tracks = s.tracks
        slave.dir_entries = s.dir_entries
        slave.others = s.others
        slave.bad_cuefiles = s.bad_cuefiles
        slave.filesize = s.filesize
        slave.fsmode = s.fsmode
        slave.total = s.total
        slave.free = s.free
        slave.disc_space = s.disc_space
        slave.children = s.children
        for k in slave.children.keys():
            v = slave.children[k]
            v.increase_depth()
        s.children = dict()
        s.open_dir(parent_dir, do_back = True)
        s.children[slave.path] = slave
        for dr in s.dir_entries:
            if dr['path'] == slave_path:
                dr['opened'] = True
                dr['children'] = filter(lambda e: e.get('name') not in ['/..', '~..'] and e['depth'] == 1, elements )
                break

    def increase_depth(s):
        s.depth += 1
        for k in s.children.keys():
            v = s.children[k]
            v.increase_depth()

    def update(s):
        path = s.path
        try:
            entries = autofs.list_dir(path)
        except:
            s._free()
            s.path = path
            return
        others = []
        #TODO: move to autofs!!!
        s.get_fsstat()
        prev_dirs      = [] + s.dir_entries
        prev_tracks    = [] + s.tracks
        prev_playlists = [] + s.playlists
        prev_others    = [] + s.others


        s.dirs = []
        s.files = []
        s.hidden_dirs = []
        s.hidden_files = []
        s.media_files = []
        s.cues = []
        s.cue_files = []
        s.medias = []
        s.playlists = []
        s.tracks = []
        s.dir_entries = []
        s.others = []
        s.bad_cuefiles = []
        s.filesize = dict()
        s.total = 0
        s.free = 0

        for entry in entries:
            try:
                #st = os.stat(s.path + "/" + entry )[stat.ST_MODE]
                if entry[1] == 'D':
                    if entry[0][0] == '.':
                        s.hidden_dirs.append(entry)
                    else:
                        s.dirs.append(entry)
                else:
                    if entry[0][0] == '.':
                        s.hidden_files.append(entry)
                    else:
                        #s.filesize[entry] = 0

                        s.files.append(entry)
                        if is_audio_file(entry[0]):
                            s.media_files.append(entry)
                        elif is_cue_file(entry[0]):
                            s.cue_files.append(entry)
                            cue_file = fs.auto.abspath( entry[0], path )
                            s.cue_parser(cue_file)
                        elif entry[0][-4:].lower() in plst_extensions3:
                            s.playlists.append(entry)
                        elif entry[0][-5:].lower() in plst_extensions4:
                            s.playlists.append(entry)
                        else:
                            others.append(entry)
                    pass
            except:
                pass

        s.media_files = sorted2(s.media_files)
        if s.sort_order == EXT:
            others = ext_sort(others)
        else:
            others = sorted2(others)
        s.others = map(lambda x: convert_file(x, s.path), others)

        s.dirs = sorted2(s.dirs)
        s.playlists = sorted2(s.playlists)

        plses = []
        for pls in s.playlists:
            plsdict = convert_pls(pls[0], s.path)
            plsdict['size'] = pls[3]
            plses.append(plsdict)

        s.playlists = plses

        s.dir_entries = []
        for dirname in s.dirs:
            cdir = convert_dir(dirname,s.path)
            cdir['owner'] = s
            s.dir_entries.append(cdir)

        if s.depth == 0 and autofs.has_parent(path):
            s.dir_entries.insert(0, convert_dir([u'..', 'D', ' '],s.path))

        s.analyse()
        idt = dict()
        for e in s.dir_entries + s.tracks + s.playlists + s.others:
            idt[get_id(e)] = e
            e['depth'] = s.depth
        nels = set( idt.keys() )
        removed_elements = []
        olds = []
        fsmode= s.get_fsmode()%2
        for oe in prev_dirs + prev_tracks + prev_playlists + prev_others:
            di = get_id(oe)
            nels.discard(di)
            if idt.has_key(di):
                e = idt[di]
                oek = oe.keys()
                for key in oek:
                    if key not in [ 'playback_num', 'children', 'opened' ]:
                        del oe[key]
                for key in e.keys():
                    oe[key] = e[key]
                oet = oe['type']
                if oet== 'dir':
                    idx = s.dir_entries.index(e)
                    s.dir_entries[idx] = oe
                elif oet == 'fsfile':
                    idx = s.others.index(e)
                    s.others[idx] = oe
                elif oet == 'playlist':
                    idx = s.playlists.index(e)
                    s.playlists[idx] = oe
                else:
                    idx = s.tracks.index(e)
                    s.tracks[idx] = oe
            else:
                if oe['type'] == 'fsfile':
                    if fsmode:
                        removed_elements.append(oe)
                else:
                    removed_elements.append(oe)


        new_elements = []
        for k in nels:
            e = idt[k]
            if e['type'] == 'fsfile':
                if fsmode:
                    new_elements.append(e)
            else:
                new_elements.append(e)

        return removed_elements, new_elements
        
    def open_dir(s, path, do_back = False):
        s._free(do_back)
        new_path = unicode2(path)

        s.path = new_path
        try:
            entries = autofs.list_dir(path)
        except:
            entries = []

        others = []
        #TODO: move to autofs!!!
        s.get_fsstat()

        for entry in entries:
            try:
                #st = os.stat(s.path + "/" + entry )[stat.ST_MODE]
                if entry[1] == 'D':
                    if entry[0][0] == '.':
                        s.hidden_dirs.append(entry)
                    else:
                        s.dirs.append(entry)
                else:
                    if entry[0][0] == '.':
                        s.hidden_files.append(entry)
                    else:
                        #s.filesize[entry] = 0

                        s.files.append(entry)
                        if is_audio_file(entry[0]):
                            s.media_files.append(entry)
                        elif is_cue_file(entry[0]):
                            s.cue_files.append(entry)
                            cue_file = fs.auto.abspath( entry[0], path )
                            s.cue_parser(cue_file)
                        elif entry[0][-4:].lower() in plst_extensions3:
                            s.playlists.append(entry)
                        elif entry[0][-5:].lower() in plst_extensions4:
                            s.playlists.append(entry)
                        else:
                            others.append(entry)
                    pass
            except:
                pass
        s.media_files = sorted2(s.media_files)
        if s.sort_order == EXT:
            s.others = ext_sort(others)
        else:
            s.others = sorted2(others)
        del others

        s.others = map(lambda x: convert_file(x, s.path), s.others)

        s.dirs = sorted2(s.dirs)
        s.playlists = sorted2(s.playlists)

        plses = []
        for pls in s.playlists:
            plsdict = convert_pls(pls[0], s.path)
            plsdict['size'] = pls[3]
            plses.append(plsdict)

        del s.playlists
        s.playlists = plses

        s.dir_entries = []
        subpaths = set(s.children.keys())
        for dirname in s.dirs:
            cdir = convert_dir(dirname,s.path)
            cdir['owner'] = s
            s.dir_entries.append(cdir)
        for p in subpaths:
            del s.children[p]

        if s.depth == 0 and autofs.has_parent(path):
            s.dir_entries.insert(0, convert_dir([u'..', 'D', ' '],s.path))
        s.analyse()
        if s.depth != 0:
            for r in s.dir_entries + s.tracks + s.playlists + s.others:
                r['depth'] = s.depth

    def cue_parser(s, file_path):

        cuesheet = None
        try:
            cuesheet = c.cue_parser(file_path)
        except Exception, e:
            pass

        
        if not cuesheet:
            s.bad_cuefiles.append({ 'file' : file_path})
        else:
            s.cues.append(cuesheet)
        #cue_parser

    def analyse(s):
        mfiles = []
        speeds = {}
        if s.cues != []:
            s.not_in_cue = []
            media_dict = dict()

            for cue in s.cues:
                for track in cue[1:]:
                    if track['file'][:7] == 'file://':
                        track['file'] = track['file'][7:]
                    media_dict[fs.auto.abspath(track['file'])] = False

            for mfile in s.media_files:
                path = fs.auto.abspath( mfile[0], s.path )
                if media_dict.has_key(path):
                    media_dict[ path ] = True
                else:
                    s.not_in_cue.append( c.file_to_track( path ) )

            for cue in s.cues:
                for track in cue[1:]:
                    if media_dict[fs.auto.abspath(track['file'])] == True:
                        s.tracks.append(track)
                        
            s.internal_check_bad_cue()
            #del media_dict
        else:
            s.medias = s.media_files
            for m in s.medias:
                s.tracks.append( c.file_to_track( autofs.abspath( m[0], s.path), size = m[3] ) )
            s.tracks = sortedTT(s.tracks)

        for track in s.tracks:
            #c.get_track_time(track)
            c.add_image_tags_to_cue(track, speeds)
            if not track.has_key('ext') or track['type'] == 'cue':
                adr = track.get('file', track.get('addr') )
                track['ext'] = adr.split('.')[-1].lower()
            if track.get('type') == 'cue':
                try:
                    c.set_tags_from_path(track)
                    c.get_cdno_from_album_name(track)
                except Exception, e:
                    pass

    def internal_check_bad_cue(s):
        if s.cues == []:
            return
        not_in_cues = []

        for media_file in s.not_in_cue:
            path = media_file.get('path').lower()
            if '.' in os.path.basename(path):
                point = path.rfind('.')
                not_in_cues.append(path.lower()[:point])

        if not_in_cues == []:
            return

        in_bad_cue = dict()
        for cue_file in s.cues:
            for cue    in cue_file[1:]:
                path = cue.get("file")
                if '.' in os.path.basename(path):
                    point = path.rfind('.')
                    path_basename = path.lower()[:point]

                    if path_basename in not_in_cues:
                        no = not_in_cues.index(path_basename)
                        in_bad_cue[no] = s.not_in_cue[no]
                        cue['file'] = s.not_in_cue[no]['path']
                        s.tracks.append(cue)

        if in_bad_cue != dict():
            for no in reversed( in_bad_cue.keys() ):
                s.not_in_cue.pop(no)

        mfiles = []
        for track in s.not_in_cue:
            mfiles.append(track)
            #s.tracks.append(track)
        s.tracks += sortedTT(mfiles)

        del s.not_in_cue

    def get_fsmode(s):
        parent = s.parent
        fsmode = s.fsmode
        while parent != None:
            fsmode = parent.fsmode
            parent = parent.parent
        return fsmode
            
    def get_elements(s):
        if s.get_fsmode()%2 == 1:
            ret = s.dir_entries +    s.tracks + s.playlists + s.others
        else:
            ret = s.dir_entries +    s.tracks + s.playlists
        return ret

    def open_subdir(s, delm):
        m = media_fs(delm['owner'])
        m.open_dir( delm['path'] )
        s.children[ delm['path'] ] = m
        delm['opened'] = True
        delm['children'] = m.get_elements()
        return delm['children']

    def close_subdir(s, delm):
        del delm['opened']
        del s.children[delm['path']]
        del delm['children']

    def close_subdirs(s):
        for d in s.dir_entries:
            if d.has_key('children'):
                del d['children']
                try:
                    del s.children[ d['path'] ]
                except:
                    pass
                if d.has_key('opened'):
                    del d['opened']

        s.children= {}

    def unzip(s, elms):
        ret = []
        for e in elms:
            if e.has_key('children'):
                children = s.unzip( e['children'] )
                e['opened'] = True
                ret.append(e)
                ret += children
            else:
                ret.append(e)
        return ret
    
    def get_files(s):
        return s.others

    def _free(s, do_back=False):
        if not do_back:
            s.children = {}
        s.dirs = []
        s.files = []
        s.hidden_dirs = []
        s.hidden_files = []
        s.media_files = []
        s.cues = []
        s.cue_files = []
        s.medias = []
        s.playlists = []
        s.tracks = []
        s.dir_entries = []
        s.others = []
        s.bad_cuefiles = []
        s.filesize = dict()
        s.total = 0
        s.free = 0

def list_dir(path):
    tracks = []
    m = media_fs()
    pth = path

    m.open_dir(pth)
    tracks += m.tracks
    dirs = map(lambda x: x[0], m.dirs)
    m._free()
    del m
    for dr in dirs:
        if dr != u"/.." and dr != u"~..":
             tracks += list_dir(os.path.join(path, dr))
    return tracks

def parm_cmp(parm, wanted):
    n=0
    for substring in wanted:
        if parm.count(substring.lower()) == 0:
            return False
    return True

def track_cmp(track, wanted):
    for key in wanted.keys():
        if not track.has_key(key):
            return False
        if not parm_cmp(track[key].lower(), wanted[key]):
            return False
    return True
        
        
def search_track(path, wanted, engine):
    m = media_fs()
    m.open_dir(path)
    tracks = m.tracks
    dirs = m.dirs
    del m
    for track in tracks:
        if track_cmp(track, wanted):
            engine.on_search_track(track)

    del tracks
    for dr in dirs:
        if dr[0] != u"/.." and dr[0] != u"~.." and dr[0] != '..':
            search_track( os.path.join(path, dr[0]), wanted, engine)
    del dirs


def cuetracks_to_files(ctracks):
    files = dict()

    for track in ctracks:
        files[track['file']] = True
        cf = track['addr'][6:].split('#')[0]
        files[cf] = True
    ret = []
    for fl in files.keys():
        ret.append( convert_file2(fl) )

    return ret


def get_elm_size(elements):
    total = 0
    cues = []
    for elm in elements:
        if elm.get('islink', False):
            continue
        if elm['type'] == 'cue':
            cues.append(elm)

        if elm.has_key('size'):
            total += elm.get('size', 0)
    if cue != []:
        cfiles = cuetracks_to_files(cues)
        for elm in cfiles:
            if elm.get('islink', False):
                continue
            total += elm.get('size', 0)
            

    return total

