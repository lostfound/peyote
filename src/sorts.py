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

from sets import config, get_performer_alias, get_album_alias
def parse_string(e):
    try:
        if type(e) == []:
            s == e[0]
        else:
            s = e
        if type(s) == str:
            s = s.decode('utf-8')

        if s == "" or s == None:
            return [u""]
        if s[0].isdigit():
            ret=[0]
        else:
            ret=[u""]
        for c in s:
            if c.isdigit():
                if type(ret[-1]) == int:
                    ret[-1]*=10
                else:
                    ret.append(0)
                ret[-1]+=int(c)
            else:
                if type(ret[-1]) == int:
                    ret.append(u"")
                ret[-1]+=c
        return ret
    except:
        return [s]
class SortContainer:
    def __init__(s, v):
        s.v = v
    def __cmp__(s, v):
        return 0
    
def sorted2(l):
    if l != [] and type(l[0]) == list:
        s = map( lambda x: parse_string(x[0]) + [ SortContainer(x) ], l)
    else:
        s = map( lambda x: parse_string(x) + [SortContainer(x)], l)
    s.sort()
    return map(lambda x: x[-1].v, s)

def sortedZ(l, keys):
    L=[]
    for t in l:
        Ls = u""
        for k in keys:
            if t.has_key(k) and t[k] != None:
                Ls += ' ' + t[k]
        L.append([Ls, t])
    return map(lambda ll: ll[-1], sorted2(L))

def sortedTT(l, al = 1):
    albums = {} #k - album v- artists, tracks
    L=[]
    for t in l:
        artist = get_performer_alias( t.get('performer', ''), al )
        album  = get_album_alias( t.get('album', ''), al )
        if not albums.has_key(album):
            albums[album] = [set(), []]
        albums[album][0].add(artist)
        albums[album][1].append(t)

    for album in albums.keys():
        albums[album][1] = _sortedTalb(albums[album][1])
        if len(albums[album][0]) != 1:
            L.append(['2 ' + album, albums[album][1]])
        else:
            artist = albums[album][0].pop()
            L.append(['1 ' + artist + ' ' + album, albums[album][1]])

    sorted_albums = map(lambda ll: ll[-1], sorted2(L))
    ret = []
    for a in sorted_albums:
        ret += a
    
    return ret

def _sortedTalb(l, al = 1):
    L=[]
    for t in l:
        tid = t.get('id', '')
        title = t.get('title', '')
        dn = t.get('cdno', '')
        L.append([dn +' ' +  tid + ' ' + title, t])
    return map(lambda ll: ll[-1], sorted2(L))

def sortedC(l, al = 1):
    L=[]
    for t in l:
        L.append([repr(t.get('timestamp', 0.)), t])
    return map(lambda ll: ll[-1], sorted(L))

def sortedT(l, al = 1):
    L=[]
    for t in l:
        artist = get_performer_alias( t.get('performer', ''), al )
        album  = get_album_alias( t.get('album', ''), al )
        tid = t.get('id', '')
        title = t.get('title', '')
        dn = t.get('cdno', '')
        L.append([artist + ' ' + album + dn +' ' +  tid + ' ' + title, t])
    return map(lambda ll: ll[-1], sorted2(L))

def ext_sort(m):
    ext_dict = {}
    for e in m:
        n = e[0].rfind('.')
        if n > 0:
            ext = e[0][n:]
        else:
            ext = ""
        if not ext_dict.has_key(ext):
            ext_dict[ext] = []

        ext_dict[ext].append(e)

    ret = []
    for k in sorted2(ext_dict.keys()):
        ret += map(lambda fl: fl, sorted2(ext_dict[k]) )

    del ext_dict
    return ret

