#!/usr/bin/python
# -*- coding: utf-8 -*-

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
                                    

from __future__ import with_statement
import pickle
import os
import time
import storage, media_fs, playlist, peyote_exec, cue
import gettext
import fs.auto
from nc_panel import panel
from panel_equalizer import PEqualizer
from panel_playlist import PPlaylist
from panel_locations import PLocations
from panel_lyrics import PLyrics
from panel_fs import PFS, PThread
from panel_radio import PRadio
from panel_config import PConfig
from useful import *
from sets import config, get_performer_alias, get_album_alias
from thread_system.thread_polls import polls
from threading import Event
from Queue import Queue
from panel_equalizer import ARTIST_KEY, ALBUM_KEY, TITLE_KEY, DEPTH_KEY, ISFAKE_KEY, CHILDREN_KEY, DEFAULT_KEY
from threading import Semaphore
from random import randint

import gettext
from debug import debug, trace

_ = localise

exists = fs.auto.exists



parentw = None
tw = None
ldlt = 0
middle = None
opm = False
def get_opm():
    return opm

def sw_opm():
    global opm
    opm = not opm
    return opm


def left_panel_increase():
    global ldlt,tw,middle
    if ldlt != None:
        if tw - middle - ldlt > 40:
            ldlt += 1

def left_panel_decrease():
    global ldlt,tw, middle
    if ldlt != None:
        if ldlt + middle > 40:
            ldlt -= 1
def get_pppp():
    global tw, ldlt,middle
    return float(middle + ldlt)/float(tw)

def set_pppp(pp):
    global tw, ldlt,middle
    ldlt = int(pp*tw - middle)
    tw = None
    panel_position('left')

def panel_position(pp):
    """ returns y,x, w, h """
    global tw, ldlt,middle
    size_yx = parentw.getmaxyx()
    if tw != size_yx[1]:
        tw = size_yx[1]
        middle = tw/2
        if ldlt != 0:
            if middle + ldlt < 40:
                ldlt = 40 - middle
            elif tw - middle - ldlt < 40:
                ldlt = tw - middle - 40

    y = 0
    h = size_yx[0]- 3
    h = h + int(config.hide_keybar)
    if opm:
        return (y, 0, tw, h)
    if pp == 'left':
        x = 0
        w = middle + ldlt
    else:
        x = middle + ldlt
        w = tw - middle - ldlt
    
    return (y, x, w, h)

def get_color_scheme(elm):
    if type(elm) != dict:
        return "body"
    stype = "body"
    if elm['type'] == 'stream':
        stype = 'stream'
    elif is_track(elm):
        ext = elm.get('ext', 'mp3')
        if elm.get('broken'):
            stype = 'broken link'
        elif ext in config.audio_extensions[0]:
            stype = "elm is media1"
        elif ext in config.audio_extensions[1]:
            stype = "elm is media2"
        elif ext in config.audio_extensions[2]:
            stype = "elm is media3"
    elif elm['type'] is 'dir':
        if elm['islink']:
            stype = "elm is symdir"
        else:
            stype = "elm is dir"
    elif elm['type'] is 'playlist':
        stype = "elm is playlist"
    elif elm['type'] is 'mount_point':
        stype = "mount_point"
    elif elm['type'] is 'system_location':
        stype = "system_location"
    elif elm['type'] is 'user_location':
        stype = "user_location"
    elif elm['type'] is 'lyrics':
        stype = "lyrics"
    elif elm['type'] is 'eq_tag':
        if elm[ISFAKE_KEY]:
            stype = "equalizer tag1"
        else:
            stype = "equalizer tag2"
    

    return stype
def tab(d, string = None, l=False):
    t = d*u'  '
    length = len(t)

    ret = []
    if l:
        return [length, t + string]
    
    if string != None:
        return t + string

    
def addword(a,b):
    if a != u"" and a[-1] == config.cue_char:
        return (a+b).strip()
    return (a + ' ' + b).strip()

def track_time(sec):
    def int2(i):
        r = repr(i)
        if len(r)==1:
            return '0' + r
        else:
            return r
    if sec == None:
        return " --:--s "
    h = int(sec/3600)
    m2 = int(sec/60)
    m = m2%60
    s = int(sec)%60
    if h > 0:
        if m2 <100:
            return ' ' + int2(m2) +':' + int2(s) + 's' + ' '
        else:
            return ' ' + int2(h) + ':' + int2(m) + 'm' + ' '
    else:
        return ' ' + int2(m) + ':' + int2(s) + 's' + ' '
    
class PShort:
    def element_to_short(s, elm):
    
        tp = type(elm)
        if s.type == 'config':
            tp = dict
        if tp == unicode:
            return [elm[:s.width].encode('utf-8'), "body"]

        elif tp == dict:
            stype = get_color_scheme(elm)

            if s.type == 'playlist':
                if elm['type'] == 'stream':
                    left = ""
                    if elm.get('playback_num', 0) > 0:
                        status_ico = config.track_status_chars[0]
                    else:
                        status_ico = config.track_status_chars[1]
                    try:
                        br = status_ico + " [%3i]" % int(elm.get('bitrate', '0'))
                    except:
                        br = status_ico + " [  0]"
                    if elm.get("ext"):
                        tp = "<%s>" %  elm.get("ext", "???")
                    else:
                        tp = "<???>"
                    if elm.has_key('station_name'):
                        left += "%s %s %s" %(br, tp, elm['station_name'])
                    else:
                        left += "%s %s %s" % (br, tp, elm['addr'])
                    return [unicode(left)[:s.width].encode('utf-8'), stype]
                short = s.plement_to_short(elm)
                if type(short) == list:
                    return [short, (stype, stype+'(c2)')]
                return [short, stype]

            if is_track(elm) and elm.get('type') != 'stream':
                short = s.plement_to_short(elm)
                if type(short) == list:
                    return [short, (stype, stype+'(c2)')]
                return [short, stype]

            if elm.has_key('depth') and s.type != 'playlist':
                dpth = tab(elm['depth'], '' )
            else:
                dpth = ""

            if elm['type'] == 'dir':
                if not s.tree_mode or elm['name'] == '/..':
                    pass
                elif elm.has_key('opened'):
                    dpth += u"%s " % config.tree_chars[1]
                else:
                    dpth += u"%s " % config.tree_chars[0]

                if elm['islink']:
                    dpth += u'~'
                else:
                    dpth += u'/'
                return [ "".join( [dpth, elm['name'][1:]])[:s.width].encode('utf-8'), stype ]

            elif elm['type'] == 'playlist':
                stype = "elm is playlist"
                if elm['islink']:
                    dpth += u'~'
                return [ u"".join( [dpth, elm['name']] )[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'fsfile':
                stype = 'elm is fsfile'
                if elm['islink']:
                    dpth += u'~'
                l = s.width - len(dpth)
                if l <= 0:
                    return [dpth[s.width].encode('utf-8'), stype]

                if len(elm['name']) <= l:
                    return ["".join( [dpth, elm['name']] ).encode('utf-8'), stype]

                if elm.get('ext') and len(elm['ext']) + 3 <= l:
                    L = l - len(elm['ext']) - 1
                    name = dpth + elm['name'][:L] + config.points_char[0] + elm['ext']
                    return [name[:s.width].encode('utf-8'), stype]
                else:
                    return [unicode(dpth + elm['name'])[:s.width].encode('utf-8'), stype]
                

            elif elm['type'] in ['system_location', 'user_location'] :
                left = elm['path'] if not elm.has_key('name') else elm['name']
                right = elm.get('free','') + u' / ' + elm.get('total', '')
                if right == u' / ':
                    right = u''
                blnk = s.width - len( left ) - len( right )
                if blnk > 0:
                    return [unicode(left + u' '*blnk + right).encode('utf-8'), stype]
                return [unicode(left + u' ' + right)[:s.width].encode('utf-8'), stype]

            elif elm['type'] in ['lyrics'] :
                right = ""
                left = u'"%s" by "%s"' % ( elm.get('title',''), elm.get('artist', '') )
                blnk = s.width - len( left ) - len( right )
                if blnk > 0:
                    return [unicode(left + u' '*blnk + right).encode('utf-8'), stype]
                return [unicode(left + u' ' + right)[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'home_dir':
                left = elm['name']
                right = elm.get('free','') + ' / ' + elm.get('total', '')
                blnk = s.width - len( left ) - len( right )
                if blnk > 0:
                    return [unicode(left + u' '*blnk + right).encode('utf-8'), stype]
                return [unicode(left + u' ' + right)[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'option':

                if elm.has_key('icon'):
                    left = dpth + u'%s ' %elm['icon'] + elm['name']
                else:
                    left = dpth + u'%s ' % config.config_chars[1] + elm['name']

                right = elm['value']
                blnk = s.width - len( left ) - len( right )
                if blnk > 0:
                    return [unicode(left + u' '*blnk + right).encode('utf-8'), stype]
                return [unicode(left + u' ' + right)[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'submenu':
                if elm['status'] == 0:
                    left = u"%s " % config.tree_chars[0]
                else:
                    left = u"%s " % config.tree_chars[1]

                left = dpth + left

                left += elm['name']
                if elm.has_key('value'):
                    right = elm['value']
                    blnk = s.width - len( left ) - len( right )
                    return [unicode(left + u' '*blnk + right)[:s.width].encode('utf-8'), stype]
                else:
                    return [unicode(left)[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'stream':
                left = dpth
                if elm.get('playback_num', 0) > 0:
                    status_ico = config.track_status_chars[0]
                else:
                    status_ico = config.track_status_chars[1]
                try:
                    br = status_ico + "[%3i]" % int(elm.get('bitrate', '0'))
                except:
                    br = status_ico + "[  0]"
                tp = "<%s>" % elm.get("ext", "???")
                
                if elm.has_key('station_name'):
                    left += " %s %s %s" %(br, tp, elm['station_name'])
                else:
                    left += " " + elm['addr']
                return [unicode(left)[:s.width].encode('utf-8'), stype]

            elif elm['type'] == 'eq_tag':
                retstr = u""


                if elm[DEPTH_KEY] != DEFAULT_KEY:
                    retstr += u"   "*elm[DEPTH_KEY]
                else:
                    retstr += u"  " + _("Default")

                retstr += u" "
                if elm.get(DEPTH_KEY) in [ARTIST_KEY, ALBUM_KEY] and elm[CHILDREN_KEY] != []:
                    retstr += u"▾ "
                else:
                    retstr += u"  "

                for d in [ARTIST_KEY, ALBUM_KEY, TITLE_KEY]:
                    if elm[DEPTH_KEY] == d:
                        retstr +=u'"' + unicode2(elm[d]) + '"'
                return [ retstr[:s.width].encode('utf-8'), stype ]

            else:
                return [unicode("Fix me!" + elm['type'])[:s.width].encode('utf-8'), stype]

        elif s.type == 'equalizer':
            txt_val = unicode( '%5.1f Db %7.1f Hz' % ( elm.get_gain(), elm.get_freq()) )
            txt_val += ' ' * ( 20 - len(txt_val) )
            
            pp = (24+elm.get_gain())/36.
            l = s.width - 19
            elm.coord = (20, l)
            l0=int(l*pp)
            l1=l-l0
            eqstr = config.equalizer_chars[0]*l0 + config.equalizer_chars[1]*l1
            return [unicode(txt_val + eqstr).encode('utf-8'), "body"]
            
        else:
            return [u"Fix me!!"[:s.width].encode('utf-8'), "body"]


    def plement_to_short(s, elm):

        if type(elm) != dict:
            return u"!dict"

        if not is_track(elm):
            return elm['type']
        
        if s.type == 'playlist':
            nt = 2
            plisting_mode   = config.playlist_title_formats
            modes        = len(plisting_mode)
            current_mode    = plisting_mode[s.playlist_mode%modes]
        elif s.type == 'fs':
            nt = 1
            plisting_mode   = config.fs_title_formats
            modes = len(plisting_mode)
            current_mode    = plisting_mode[s.fs_mode%modes]
        else:
            return 'error'

        stype = "body"


        left = ""

        if elm.has_key('performer') and elm['performer'] != "":
            performer = '"' + get_performer_alias(elm['performer'], nt) + '"'
        else:
            performer = None

        album = None
        if  elm.has_key('album') and elm['album'] != '':
            album = '"' + get_album_alias(elm['album'], nt) + '"'
        else:
            album = None

        if elm.has_key('title') and elm['title'] != "":
            title = '"' + elm['title'] + '"'
        else: 
            title = None

        if elm.has_key('id') and elm['id'] != "" and elm['id'] != None:
            tr_id = elm['id'].split('/')[0]
            if len(tr_id) == 1:
                tr_id = '0' + tr_id
        else:
            tr_id = '  '

        if elm.has_key('addr')  and elm['addr'] != "":
            addr = elm['addr']
        else:
            addr = ""

        if len(addr) > 7:
            if addr[:7] == 'file://':
                addr = addr[7:]
        addr = '"' + addr + '"'


        if elm['type'] == 'cue':
            cue = config.cue_char
        else:
            cue = ''

        lr=[None,None]
        ext = elm.get('ext', '')
        cdno = unicode(elm.get('cdno', ''))
        bitrate = elm.get('bitrate', 0)
        sample_rate = elm.get('sample_rate', 0 )
        channels = unicode( elm.get('channels', '') )

        if bitrate != 0:
            bitrate /= 1000
        if bitrate != 0:
            bitrate = unicode(bitrate) + 'k bps'
        else:
            bitrate = ''

        if cdno != '':
            cdno = u'CD-' + cdno

        if sample_rate != 0:
            sample_rate = unicode(sample_rate) + ' hz'
        else:
            sample_rate = ''

        colors = [[], []]
        prev_color = 1

        for i in [0,1]:
            part = u""
            rlist = []
            clist = []
            for melm in current_mode[i]:
                if melm == "title":
                    if title:
                        part = addword(part,title)
                        rlist.append(title)
                        clist.append(prev_color)
                elif melm == "artist":
                    if performer:
                        part = addword(part,performer)
                        rlist.append(performer)
                        clist.append(prev_color)
                elif melm == "album":
                    if album:
                        part = addword(part,album)
                        rlist.append(album)
                        clist.append(prev_color)
                elif melm == "date":
                    part = addword(part,elm.get('date', ''))
                    rlist.append(elm.get('date', ''))
                    clist.append(prev_color)

                elif melm == "status":
                    if elm.get('cursed', False) or elm.get('broken'):
                        status_ico = config.curse_char[0]
                    elif elm.get('playback_num', 0) > 0:
                        status_ico = config.track_status_chars[0]
                    else:
                        status_ico = config.track_status_chars[1]
                    part = addword(part, status_ico)
                    rlist.append( status_ico )
                    clist.append(prev_color)
                elif melm == "time":
                    part = addword(part,track_time(elm.get('time')))
                    rlist.append(track_time(elm.get('time')))
                    clist.append(prev_color)
                elif melm == "id":
                    part = addword(part, tr_id)
                    rlist.append( tr_id)
                    clist.append(prev_color)
                elif melm == 'cue':
                    part = addword(part, cue)
                    rlist.append( cue)
                    clist.append(prev_color)
                elif melm == 'ext':
                    part = addword( part, ext )
                    rlist.append( ext )
                    clist.append(prev_color)
                elif melm == 'cdno':
                    part = addword( part, cdno )
                    rlist.append( cdno )
                    clist.append(prev_color)
                elif melm == 'bitrate':
                    part = addword( part, bitrate )
                    rlist.append( bitrate )
                    clist.append(prev_color)
                elif melm == 'sample_rate':
                    part = addword( part, sample_rate )
                    rlist.append( sample_rate )
                    clist.append(prev_color)
                elif melm == 'channels':
                    part = addword( part, channels )
                    rlist.append( channels )
                    clist.append(prev_color)
                elif melm in ['file']:
                    part = addword(part,os.path.basename ( elm.get('file', addr) ) )
                    rlist.append(os.path.basename ( elm.get('file', addr) ) )
                    clist.append(prev_color)
                elif melm in ['filename']:
                    fl = os.path.basename ( elm.get('file', addr) )
                    part = addword(part, fl)
                    rlist.append(fl)
                    clist.append(prev_color)
                elif melm in ['basename']:
                    fl = os.path.basename ( elm.get('file', addr) )
                    fl_spl = fl.rsplit('.',1)
                    if len(fl_spl) == 2:
                        part = addword(part, fl_spl[0])
                        rlist.append(fl_spl[0])
                        clist.append(prev_color)

                elif melm in ["addr", "path"]:
                    part = addword(part,addr)
                    rlist.append(addr)
                    clist.append(prev_color)

                elif melm in ['color1', 'c1']:
                    if prev_color != 1:
                        colors[i].append( [len(part), 1] )
                        prev_color = 1
                elif melm in ['color2', 'c2']:
                    if prev_color != 2:
                        colors[i].append( [len(part), 2] )
                        prev_color = 2
            lr[i] = part


        left,right = lr

        rlcolors = colors[0] + colors[1]
        #without colors
        if rlcolors == [] or ( len (rlcolors) == 1 and rlcolors[0] == 1 ):
            if elm.get('depth', 0) and s.type != 'playlist':
                left = tab(elm['depth'], left)

            #always show duration
            if current_mode[i] != [] and current_mode[i][-1] == 'time':
                if len( left ) >= s.width - 7:
                    if s.width > 7:
                        ret = left[:s.width - 7] + ' ' + right[-6:]
                        return ret.encode('utf-8')
                    return unicode(left)[:s.width].encode('utf-8')

            blnk = s.width  - len( left ) - len( right )
            if 0 < blnk:
                return unicode(left + u' '*blnk + right).encode('utf-8')

            if len( left ) >= s.width:
                return unicode(left)[:s.width].encode('utf-8')
            
            rlen = blnk = s.width  - len(left)
            right = u""
            for i in reversed( range( len(rlist) ) ):
                prop = rlist[i]
                if len(prop) < rlen:
                    if right == "":
                        right = prop
                        rlen -= len(prop) 
                    else:
                        right = prop + ' ' + right
                        rlen -= 1 + len(prop) 
                else:
                    if rlen:
                        right = prop[:rlen-1] + ' ' + right
                    break
            return unicode( left + ' ' + right ).encode('utf-8')


        if elm.get('depth', 0) and s.type != 'playlist':
            offset,left = tab(elm['depth'], left, True)
            colors[0] = map(lambda x: [x[0] + offset, x[1]], colors[0])

        if current_mode[i] != [] and current_mode[i][-1] == 'time':
            if len( left ) >= s.width - 7:
                if s.width > 7:
                    _colors = []
                    for pos,col in colors[0]:
                        if pos > s.width - 7:
                            break
                        _colors.append([pos,col])
                    if _colors == []:
                        if  clist[-1] != 1:
                            _colors.append( [s.width - 6,  clist[-1] ] )
                    elif  _colors[-1][1] != clist[-1]:
                        _colors.append( [s.width - 6,  clist[-1] ] )

                    return s.multicolor_short( left[:s.width - 7] + ' ' + right[-6:], _colors)

                return "fiiixme"
                return unicode(left)[:s.width].encode('utf-8')
        blnk = s.width  - len( left ) - len( right )
        if 0 < blnk:
            ll = len(left)
            _colors = colors[0] + map(lambda x: [x[0] + blnk + ll, x[1]], colors[1])
            string = left + u' '*blnk + right

            return s.multicolor_short(string, _colors)

        if len( left ) >= s.width:
            _colors = []
            for pos,col in colors[0]:
                if pos >= s.width:
                    break
                _colors.append([pos,col])
            return s.multicolor_short( unicode(left)[:s.width], _colors )

        rlen = s.width  - len(left)
        right = u""
        _colors = []
        for pos,col in colors[0]:
            _colors.append([pos,col])

        _rcolors = []
        for i in reversed( range( len(rlist) ) ):
            prop = rlist[i]
            cls = clist[i]
            if len(prop) < rlen:
                if len(prop) == 0:
                    pass
                elif right == "":
                    right = prop
                    rlen -= len(prop)
                    _rcolors = [ [len(prop), cls] ] + _rcolors
                else:
                    right = prop + ' ' + right
                    rlen -= 1 + len(prop) 
                    _rcolors = [ [len(prop) + 1, cls] ] + _rcolors
            else:
                if rlen:
                    right = prop[:rlen-1] + ' ' + right
                    _rcolors = [ [ rlen - 1, cls ] ] + _rcolors
                break
        pos = len(left) + 1
        for l,col in _rcolors:
            if _colors == []:
                if col != 1:
                    _colors.append([pos, col])
            elif _colors[-1][1] != col:
                _colors.append([pos, col])
            pos += l

        return s.multicolor_short( unicode( left + ' ' + right ), _colors )

    def multicolor_short(s, string, colors):
        try:
            ret = []
            if colors == []:
                return string.encode('utf-8')
            for pos,col in reversed(colors):
                ret =  [ string[pos:].encode('utf-8') ] + ret
                string = string[:pos]
            if colors[0] == 0:
                ret = [u''] + ret
            else:
                ret = [string.encode('utf-8')] + ret

            return ret
        except Exception, e:
            pass
        

class PEvents:
    def on_shuffle(s):
        s.panel.redraw()
        s.panel.center()
        s.panel.redraw()
        s.print_info()
        s.panel.refresh()
    def on_move(s):
        s.panel.redraw()
        s.panel.refresh()
    def on_fill(s):
        """ storage-event->on_fill->panel"""
        s.print_info()
        s.panel.on_fill()
    def on_append(s):
        """ storage-event->on_append->panel"""
        s.print_info()
        s.panel.on_append()


    


class PInterface(PFS, PPlaylist, PEqualizer, PLocations, PLyrics, PRadio):
    def up(s):
        if not s.busy.is_set():
            s.panel.up()
            s.print_info()
        elif s.question:
            s.panel.up()
    def down(s, pos=None):
        if not s.busy.is_set():
            if pos == None:
                s.panel.down()
            else:
                s.panel.select(pos)
            s.print_info()
        elif s.question:
            s.panel.down()
    def pgup(s):
        if not s.busy.is_set():
            s.panel.page_up()
            s.print_info()
        elif s.question:
            s.panel.page_up()
    def pgdown(s):
        if not s.busy.is_set():
            s.panel.page_down()
            s.print_info()
        elif s.question:
            s.panel.page_down()
    def home(s):
        if not s.busy.is_set():
            s.panel.home()
            s.print_info()
        elif s.question:
            s.panel.home()
    def end(s):
        if not s.busy.is_set():
            s.panel.end()
            s.print_info()
        elif s.question:
            s.panel.end()
    def random_entry(s):
        if not s.busy.is_set() and not s.question:
            if s.storage.nol:
                n = randint(0, s.storage.nol-1)
                s.panel.pos = n
                s.panel.redraw()
                s.panel.center()
                s.print_info()
                s.panel.redraw()
                s.panel.refresh()


    def move_by_title(s, n, check_playlist = True):
        if s.question:
            s.panel.right()
        elif not s.busy.is_set():
            if check_playlist and s.type == "playlist":
                if s.playlist.was_changed(s.storage.elements):
                    s.playlist_back_args = n
                    s.panel.run_yesno(_(u" quit "), [_("Playlist was modified,"), _("save with exit?"), ""], [_("<Yes>"), _("<No>"), _("<Cancel>")])
                    s.question = True
                    s.cmd = "playlist_back"
                    return

            location =  s.panel.helocate(n)
            if location:
                if s.location[:len(location):] == location:
                    child = s.location[len(location):]
                else:
                    child = None
                s.set_location(location)
                if s.type == "fs":
                    child = child.split('/')
                    if len ( child ) > 1:
                        if fs.auto.isdir ( os.path.join(s.location, child[1]) ):
                            child = '/' + child[1]
                        else:
                            child = child[1]
                    else:
                        child = None

                    PFS.open_location(s, child)
                else:
                    s.change_location()
                
                s.print_info()

    def mouse_mark(s, n):
        if s.question:
            return
        elif not s.busy.is_set():
            if s.panel.first_no != None:
                pos = n + s.panel.first_no
            else:
                return

            if pos < s.storage.nol:
                s.panel.mmark(pos)
        
    def has_scroll(s):
        if s.type in ["fs", "playlist", "radio"]:
            return True
        return False

    def mouse_scroll(s, y):
        if not s.question and not s.busy.is_set() and s.has_scroll():
            s.panel.scroll_by_y(y)
            s.print_info()

    def mouse_select(s, y, x):
        if s.question:
            rc = s.panel.yesno.mouse_click(x, y)
            if rc != None:
                if rc == s.panel.yesno.pos:
                    s.enter()
                else:
                    s.panel.yesno.pos = rc
                    s.panel.yesno.draw()
            return
        elif not s.busy.is_set():
            if s.panel.first_no != None:
                pos = y + s.panel.first_no
            else:
                return
            if s.type == 'equalizer' and PEqualizer.mouse_select(s, y, x):
                return
            
            if pos < s.storage.nol:
                if x >= 2 and type(s.storage[pos])== dict and is_track(s.storage[pos]):
                    if type(s.storage.shorts[pos][0]) != list:
                        short_smbl = s.storage.shorts[pos][0].decode('utf-8')
                    else:
                        short_smbl = u''
                        for p in s.storage.shorts[pos][0]:
                            short_smbl += p.decode('utf-8')
                    try:
                        smbl = unicode(short_smbl)[x-2]
                    except:
                        pass
                    else:
                        if smbl == config.track_status_chars[1]:
                            s.storage.elements[pos]['playback_num'] = 1
                            s.storage.reshort_no(pos)
                        elif smbl == config.track_status_chars[0]:
                            s.storage.elements[pos]['playback_num'] = 0
                            s.storage.reshort_no(pos)
                    s.panel.select(pos)
                elif s.type == "fs" and s.storage[pos]['type'] == 'dir':
                    s.panel.select(pos)
                    short_smbl = s.storage.shorts[pos][0].decode('utf-8')
                    try:
                        smbl = unicode(short_smbl)[x-2]
                    except:
                        pass
                    else:
                        if smbl == config.tree_chars[0]:
                            s.tree_right()
                        elif smbl == config.tree_chars[1]:
                            PFS.back(s)
                else:
                    s.panel.select(pos)
                                
                s.print_info()

    def right(s, pc):
        if s.question:
            s.panel.right()
        elif not s.busy.is_set():
            if s.type == "fs":
                if s.tree_mode and s.storage[s.panel.pos]['type'] == 'dir' and s.storage[s.panel.pos]['name'] not in ['~..', '/..', '..']:
                    s.tree_right()
                elif pc.ntrack and pc.ntrack.storage == s.storage and pc.ntrack.pos == s.panel.pos:
                    pc.next_track()
                elif not pc.set_next_track(s.storage, s.panel.pos):
                    PFS.enter(s)
            elif s.type == "playlist":
                if pc.ntrack and pc.ntrack.storage == s.storage and pc.ntrack.pos == s.panel.pos:
                    pc.next_track()
                else:
                    pc.set_next_track(s.storage, s.panel.pos)
            elif s.type == 'equalizer':
                PEqualizer.right(s)
            elif s.type == 'locations':
                PLocations.enter(s)
            elif s.type == 'config':
                PConfig.right(s)
            elif s.type == 'radio':
                if pc.ntrack and pc.ntrack.storage == s.storage and pc.ntrack.pos == s.panel.pos:
                    pc.next_track()
                elif s.storage[s.panel.pos]['type'] == 'stream':
                    pc.set_next_track(s.storage, s.panel.pos)
                else:
                    s.radio_right()
    def left(s):
        if s.question:
            s.panel.left()
        elif not s.busy.is_set():
            if s.type == "fs":
                return s.back()
            elif s.type == "playlist":
                return s.back()
            elif s.type == 'equalizer':
                PEqualizer.left(s)
            elif s.type in [ 'config' ]:
                PConfig.left(s)
            elif s.type in [ 'lyrics' ]:
                s.cd('locations://')
            elif s.type == 'radio':
                s.radio_left()

    def move(s,direction):
        if s.question or s.busy.is_set():
            return
        if s.type == 'config':
            PConfig.move(s, direction)
            return
        elif s.type == 'fs' and s.tree_mode:
            s.storage.treemove(s.panel.pos, direction)
            return
        elif s.type == 'equalizer':
            s.storage.move(s.panel.pos, direction, True)
            s.equalizer_aftermove()
            return
        s.storage.move(s.panel.pos, direction)
        if s.type == 'locations':
            PLocations.aftermove(s)

    def back(s):
        if s.question or s.busy.is_set():
            return
        if s.type == "fs":
            PFS.back(s)
        elif s.type == "playlist":
            PPlaylist.back(s)

    def go_to_mark(s, direction):
        if s.question or s.busy.is_set():
            return
        pos = s.panel.pos
        if direction: #down
            if s.storage.marked_elements[pos + 1:].count(True):
                numbers = map (  lambda x: x[1], filter( lambda fn: fn[0], \
                    zip (s.storage.marked_elements[pos + 1:], range(pos + 1, s.storage.nol)) )  )
                s.panel.select(numbers[0])
                s.print_info()
                return

            if pos != 0 and s.storage.marked_elements[:pos].count(True):
                numbers = map (  lambda x: x[1], filter( lambda fn: fn[0], \
                    zip (s.storage.marked_elements[:pos], range(pos)) )  )
                s.panel.select(numbers[0])
                s.print_info()
        else: #up
            if pos != 0 and s.storage.marked_elements[:pos].count(True):
                numbers = map (  lambda x: x[1], filter( lambda fn: fn[0], \
                    zip (s.storage.marked_elements[:pos], range(pos)) )  )
                s.panel.select(numbers[-1])
                s.print_info()
                return

            if s.storage.marked_elements[pos + 1:].count(True):
                numbers = map (  lambda x: x[1], filter( lambda fn: fn[0], \
                    zip (s.storage.marked_elements[pos + 1:], range(pos + 1, s.storage.nol)) )  )
                s.panel.select(numbers[-1])
                s.print_info()


    def go_to_player_cursor(s, pc):
        if s.question or s.busy.is_set():
            return
        
        if s.type == "playlist" or s.type == "fs":
            if s.storage.cursors != []:
                pos = s.panel.pos
                if pc.ctrack and pc.ctrack.storage == s.storage:
                    cpos = pc.ctrack.pos
                else:
                    cpos = None
                if pc.ntrack and pc.ntrack.storage == s.storage:
                    npos = pc.ntrack.pos
                else:
                    npos = None
                if npos == pos:
                    pos = cpos
                elif cpos == pos:
                    pos = npos
                else:
                    pos = cpos if cpos != None else npos
                if pos != None:
                    s.panel.select(pos)
                    s.print_info()

    def rename(s):
        if s.question or s.busy.is_set():
            return

        if s.type == "fs":
            PFS.rename(s)
        elif s.type == "playlist":
            PPlaylist.rename(s)
        elif s.type == "locations":
            PLocations.rename(s)

    def enter(s, pc = None):
        if s.busy.is_set() and not s.question:
            s.stop_thread_flag = True
        if s.question:
            if s.cmd == "audiosearch":
                PPlaylist.question_enter(s)
            elif s.type == "fs":
                PFS.question_enter(s)
            elif s.type == "playlist":
                PPlaylist.question_enter(s)
            elif s.type == "locations":
                PLocations.question_enter(s)
            elif s.type == 'config':
                PConfig.question_enter(s)
            elif s.type == 'equalizer':
                PEqualizer.question_enter(s)

        elif s.type == "fs":
            if not pc:
                PFS.enter(s)
            elif not pc.set_next_track(s.storage, s.panel.pos):
                PFS.enter(s)
            else:
                pc.next_track()

        elif s.type == "playlist":
            if pc.set_next_track(s.storage, s.panel.pos):
                pc.next_track()

        elif s.type == 'locations':
            PLocations.enter(s)

        elif s.type == 'config':
            PConfig.enter(s)

        elif s.type == 'equalizer':
            PEqualizer.enter(s)

        elif s.type == 'radio':
            if not pc or not pc.set_next_track(s.storage, s.panel.pos):
                PRadio.enter(s)
            else:
                pc.next_track()
    

    def play_everything_thread(s, pc):
        s.busy.set()
        try:
          pc.calculate_next_by_storage(s.storage)
          pc.next_track()
        except Exception,e:
          trace()
        s.busy.clear()
    def play_everything(s, pc):
        s.AddTask(s.play_everything_thread, [pc])

    def play_path_thread(s, pc, path ):
        s.busy.set()
        try:
            pc.calculate_next_by_storage(s.storage, path)
            pc.next_track()
        except:
            pass
        s.busy.clear()
    def play_path(s, pc, path):
        s.AddTask(s.play_path_thread, [pc, fs.auto.abspath(path)])

    def set_current_track_thread(s, pc, addr):
        s.busy.set()
        try:
            pc.set_current(s.storage, addr)
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass
        s.busy.clear()
    def set_current_track(s, pc, addr):
        s.AddTask(s.set_current_track_thread, [pc, addr] )

    def set_next_track_thread(s, pc, addr):
        s.busy.set()
        try:
            pc.set_next(s.storage, addr)
            s.panel.redraw()
            s.panel.refresh()
        except:
            pass

        s.busy.clear()
    def set_next_track(s, pc, addr):
        s.AddTask(s.set_next_track_thread, [pc, addr] )

    def center(s):
        if s.busy.is_set() and not s.question:
            return
        s.panel.cursor_center()

    def show(s, position="left", force = False):
        regenerate_flag = False
        s.visibility.clear()
        if force:
            regenerate_flag = True
        if s.panel_position == None:
            s.panel_position = position
            regenerate_flag = True

        elif s.panel_position != position:
            s.panel_position = position
            regenerate_flag = True
            s.panel.del_wins()

        panel_coords = panel_position(position)
        if not regenerate_flag and panel_coords != s.panel_coords:
            regenerate_flag = True


        if regenerate_flag == True:
            s.panel_coords = panel_coords
            y,x,w,h = panel_coords
            s.panel.gen_wins(h, w, x_pos = x )
            s.panel.redraw()

        s.visibility.set()
        s.panel.head(s.location)
        s.panel.show()
        s.redraw_info()
        s.panel.refresh()

    def on_cursebless(s, skulls):
        if s.type not in ['playlist', 'fs'] or skulls == set():
            return

        mdf=False

        if not s.busy.is_set():
            for n,e in enumerate(s.storage.elements):
                if is_track(e) and e['addr'] in skulls:
                    if e['addr'] in config.skulls:
                        e['cursed'] = True
                    else:
                        try:
                            del e['cursed']
                        except:
                            pass
                    mdf = True
                s.storage.reshort_no(n)
        if mdf:
            s.panel.redraw()
            s.panel.refresh()


        
    def bless(s):
        skulls = set()
        if not s.busy.is_set() and not s.question and s.type in ['playlist', 'fs']: 
            if s.type not in ['playlist', 'fs']:
                return skulls

            if s.storage.marked_elements.count(True) > 0:
                for n,m in enumerate( s.storage.marked_elements):
                    if m and is_track ( s.storage[n] ) \
                      and s.storage[n].get('cursed', False):
                        skulls.add( s.storage[n]['addr'])
                        #Bless
                        del s.storage[n]['cursed']
            else:
                if is_track( s.storage.current_element() ) \
                  and s.storage.current_element().get('cursed', False):
                    skulls.add( s.storage.current_element()['addr'] )
                    #Bless
                    del s.storage.current_element()['cursed']
        if skulls != set():
            s.panel.redraw()
            s.panel.refresh()
            config.Bless(skulls)

        return skulls

    def curse(s):
        skulls = set()
        if not s.busy.is_set() and not s.question and s.type in ['playlist', 'fs']: 
            if s.type not in ['playlist', 'fs']:
                return skulls

            if s.storage.marked_elements.count(True) > 0:
                for n,m in enumerate( s.storage.marked_elements):
                    if m and is_track ( s.storage[n] ) \
                      and not s.storage[n].get('cursed', False):
                        skulls.add( s.storage[n]['addr'])
                        #CURSE
                        s.storage[n]['cursed'] = True
            else:
                if is_track( s.storage.current_element() ) \
                  and not s.storage.current_element().get('cursed', False):
                    skulls.add( s.storage.current_element()['addr'] )
                    #Curse
                    s.storage.current_element()['cursed'] = True
        if skulls != set():
            s.panel.redraw()
            s.panel.refresh()
            config.Curse(skulls)
        return skulls

    def select(s):
        if not s.busy.is_set() and not s.question and s.type in ['playlist', 'fs']:
            s.panel.run_yesno(_(' Select '), [_(u'Title:'),[""], _(u"Artist:"), [""], _(u"Album:"), [""], ""], [_(u'<Select>'), _(u'<Cancel>')])
            s.question = True
            s.cmd = "audioselect"
    
    def unselect(s):
        if s.busy.is_set() and not s.question and s.type in ['playlist', 'fs']:
            pass

    def chronology(s):
        if s.busy.is_set() and not s.question:
            return
        if s.type == 'playlist':
            s.storage.sort(1)
    def sort(s):
        if s.busy.is_set() and not s.question:
            return
        if s.type == 'playlist':
            s.storage.sort()

    def shuffle(s):
        if s.busy.is_set() and not s.question:
            return
        if s.type == 'playlist':
            s.storage.shuffle()

    def hide(s):
        s.visibility.clear()
        s.panel.hide()

    def chfocus(s, focus = True):
        s.focus = focus
        if focus:
            s.panel.show_cursor()
        else:
            s.panel.hide_cursor()

    def psi_redraw(s):
        s.panel.redraw()
        s.panel.refresh()

    def redraw(s):
        if s.panel_position == None:
            return
        s.panel.del_wins()
        y,x,w,h = panel_position(s.panel_position)
        s.panel_coords = (y,x,w,h)
        s.panel.gen_wins(h, w, x_pos = x )
        s.panel.redraw()
        s.panel.head(s.location)
        s.panel.show()
        s.redraw_info()
        s.panel.refresh()

    def mark_all_played_tracks(s):
        if s.question or s.busy.is_set():
            return
        if s.type in ['fs', 'playlist']:
            do_reshort = False
            for i,entry in enumerate(s.storage.elements):
                if entry.get('playback_num', 0):
                    s.storage.marked_elements[i] = 1
                    s.storage.reshort_no(i)
            s.marked_size =  media_fs.get_elm_size(s.storage.get_marked_elements())
            s.panel.redraw()
            s.print_info()
            s.panel.refresh()

            

    def mark_all_tracks(s):
        if s.question or s.busy.is_set():
            return
        i = 0

        if s.type == 'equalizer':
            PEqualizer.mark(s, 1)
            return
        for elm in s.storage.elements:
            if type(elm) == dict:
                if elm['type'] != 'dir':
                    s.storage.marked_elements[i] = not s.storage.marked_elements[i]
            else:
                s.storage.marked_elements[i] = not s.storage.marked_elements[i]
            i += 1

        if s.type in ['playlist', 'fs']:
            s.marked_size =  media_fs.get_elm_size(s.storage.get_marked_elements())

        s.panel.redraw()
        s.print_info()
        s.panel.refresh()

    def mark(s, direction = 0):
        if s.question or s.busy.is_set():
            return
        if s.type == 'equalizer':
            PEqualizer.mark(s)
            if direction == 0:
                s.panel.down()
            else:
                s.panel.up()

        elif s.storage.nol:
            s.panel.mark(direction)
            if s.type in ['playlist', 'fs']:
                s.marked_size =  media_fs.get_elm_size(s.storage.get_marked_elements())
                s.print_info()
                s.panel.refresh()

    def showfiles(s):
        if s.busy.is_set() or s.question:
            return
        elif s.type == "fs":
            s.fs.fsmode = 1 - s.fs.fsmode
            s.fs_files()
        elif s.type == 'equalizer':
            s.eq_switch_tagshowing()

    def switch_mode(s):
        if s.busy.is_set() or s.question:
            return
        elif s.type == "fs":
            s.fs_mode += 1
            s.storage.reshort()
            s.panel.redraw()
            s.panel.refresh()

        elif s.type == "playlist":
            s.playlist_mode += 1
            s.storage.reshort()
            s.panel.redraw()
            s.panel.refresh()

    def prev_track(s):
        if s.type == "playlist":
            PPlaylist.prev_track(s)

    def next_track(s):
        if s.type == "playlist":
            PPlaylist.next_track(s)

    def mark_unplayed(s):
        if s.question or s.busy.is_set():
            return
        if s.type in ['fs', 'playlist']:
            tagged = s.storage.get_marked_elements()
            if not tagged and s.storage.nol:
                entry = s.storage.elements[s.panel.pos]
                if is_track(entry) and entry.get('playback_num', 0):
                    del entry['playback_num']
                    s.storage.reshort_no(s.panel.pos)
                    s.panel.redraw()
                    s.panel.refresh()
            else:
                for entry in tagged:
                    if is_track(entry) and entry.get('playback_num', 0):
                        del entry['playback_num']

                s.storage.reshort()
                s.panel.redraw()
                s.panel.refresh()

    def untag_all_tagged_entries(s):
        if s.question or s.busy.is_set():
            return
        if s.storage.nol:
            s.storage.marked_elements = [0]*s.storage.nol
            s.panel.redraw()
            s.panel.refresh()


    def mark_played(s):
        if s.question or s.busy.is_set():
            return
        if s.type in ['fs', 'playlist']:
            tagged = s.storage.get_marked_elements()
            if not tagged and s.storage.nol:
                entry = s.storage.elements[s.panel.pos]
                if is_track(entry):
                    entry['playback_num'] = 1 + entry.get('playback_num', 0)
                    s.storage.reshort_no(s.panel.pos)
                    s.panel.redraw()
                    s.panel.refresh()
            else:
                for entry in tagged:
                    if is_track(entry):
                        entry['playback_num'] = 1 + entry.get('playback_num', 0)

                s.storage.reshort()
                s.panel.redraw()
                s.panel.refresh()


    def cancel(s):
        if s.question and not s.busy.is_set():
            cmd = None
            del s.panel.yesno.win
            del s.panel.yesno

            s.panel.yesno = None
            s.question = False
            s.panel.redraw()
            s.panel.refresh()

    def fsmove(s, destination):
        if s.question or s.busy.is_set():
            return
        if s.type == 'fs' and s.location[:7].lower != 'http://':
            PFS.fsmove(s, destination)


    def delete(s):
        if s.question or s.busy.is_set():
            return

        if s.type == "playlist":
            PPlaylist.delete(s)

        elif s.type == "fs":
            PFS.delete(s)
        elif s.type == 'locations':
            PLocations.delete(s)
        elif s.type == 'config':
            PConfig.delete(s)
        elif s.type == "equalizer":
            PEqualizer.delete(s)

    def on_search_tracks(s, locations):
        if s.question or s.busy.is_set():
            return
        if s.type == 'playlist':
            s.panel.run_yesno(_(' Search '), [_(u'Title:'),[""], _(u"Artist:"), [""], _(u"Album:"), [""], ""], [_(u'<Search>'), _(u'<Append>'), _(u'<Cancel>')])
        else:
            s.panel.run_yesno(_(' Search '), [_(u'Title:'),[""], _(u"Artist:"), [""], _(u"Album:"), [""], ""], [_(u'<Search>'), _(u'<Cancel>')])
        s.question = True
        s.cmd = "audiosearch"
        s.cmd_args = locations

        
    def search_tracks(s):
        if s.question or s.busy.is_set():
            return
        if s.type ==  "fs":
            marked_dirs = filter ( lambda x: x['type'] == 'dir',  s.storage.get_marked_elements() )
            if marked_dirs:
                paths = map( lambda entry: entry['path'], marked_dirs)
                root = None
                dirs = set()

                for path in sorted(paths):
                    if not root:
                        root = path
                    elif not path.startswith(root):
                        root = path
                    if root == path:
                        dirs.add(path)
                locations = list(sorted(dirs))
                if locations != []:
                    return locations
                return 

            else:
                return [ s.location ]
        


    def save(s):
        if s.question or s.busy.is_set():
            return

        if s.type == "playlist":
            PPlaylist.save(s)

        elif s.type == "equalizer":
            
            s.save_equalizer()

    def copy(s):
        if s.question or s.busy.is_set():
            return
        if s.type not in ['playlist', 'fs', 'radio']:
            return
        """Returns tracks/elements"""
        if s.storage.marked_elements.count(True) > 0:
            elements = map(lambda x: x.copy(), s.storage.get_marked_elements())

            
            for elm in elements:
                if type(elm) == dict and elm.has_key('playback_num'):
                    del elm['playback_num']
            
            s.panel.redraw()
            if s.visibility.is_set():
                s.panel.refresh()
            if s.type == 'radio':
                elements = filter(lambda x: type(x) == dict and x['type'] == 'stream', elements)
            return elements
        else:
            if not s.storage.nol:
                return None
            element = s.panel.get_current_item().copy()
            if type(element) == dict and element.has_key('playback_num'):
                del element['playback_num']

            if element != None:
                return [ element ]
            return None
    def on_copy(s, elements, source_location, copymode=0):
        if s.question or s.busy.is_set():
            return

        if s.type == "playlist":
            PPlaylist.on_copy(s, elements, None, copymode)
        elif s.type == "fs":
            PFS.on_copy(s, elements, source_location, copymode)
        elif s.type == "locations":
            elements = filter(lambda e: e['type'] in ['playlist', 'dir'], elements)
            if elements:
                PLocations.on_copy(s, elements, source_location, copymode)
        elif s.type == 'lyrics':
            PLyrics.on_copy(s, elements, source_location, copymode)

    def newelement(s):
        if s.question or s.busy.is_set():
            return

        if s.type == "fs":
            s.panel.run_yesno(_(' New '), [_(u'What you want to create?'), ""], [_(u'<Directory>'), _(u'<Playlist>'), _(u'<Nothing>')])
            s.question = True
            s.cmd = "newelement"

        elif s.type == "playlist":
            addr = s.panel.cmd_add('http://')
            if addr:
                track = cue.addr_to_track(addr)
                if track:
                    s.storage.append([track])
        elif s.type == "locations":
            PLocations.new_element(s)

    def execute(s):
        if s.question or s.busy.is_set():
            return
        if s.type == "fs":
            PFS.execute(s)
    def fast_search(s):
        if s.question or s.busy.is_set():
            return
        if s.type in ['playlist', 'fs']:
            s.panel.fast_search()
    def on_fast_search(s, pattern):
        def my_check(pattern, entry, alias_no = None):
            if pattern == u"":
                return False
            if entry['type'] in ['dir', 'fsfile', 'playlist']:
                name = entry.get('name', u'')
                if len(pattern) <= len(name):
                    if name[:len(pattern)] == pattern:
                        return True
            elif is_track(entry):
                tagfxlst = zip(['id', 'title', 'album', 'performer']
                           , [None, None, get_album_alias, get_performer_alias])
                for nm,fx in tagfxlst:
                    name = entry.get(nm, "")
                    if fx and alias_no != None:
                        name = fx(name, alias_no)
                    if len(pattern) <= len(name):
                        if name[:len(pattern)] == pattern:
                            return True
            return False
        ret = []
        alias_no = None
        if s.type == 'fs':
            alias_no = 1
        elif s.type == 'playlist':
            alias_no = 2
        if s.storage.nol and s.storage.nol > 0:
            for pos,entry in enumerate(s.storage.elements):
                if my_check(pattern, entry, alias_no):
                    ret.append(pos)
        return ret

         


class PEngine(PShort, PThread, PEvents, PInterface, PConfig):
    def __del__(s):
        try:
            s.callback.inotify_unsubscribe(s)
            s.destroy()
        except:
            pass
    def destroy(s):
        try:
            s.storage.clear()
        except:
            pass
        if s.type == 'lyrics':
            s.lyrics_deinit()

        elif s.type == 'equalizer':
            s.equalizer_deinit()
        elif s.type == 'radio':
            s.radio_deinit()

        elif s.type == 'fs':
            s.callback.inotify_unsubscribe(s)
        s.death.set()
        try:
            s.tasks.put(None)
        except:
            pass
        del s.location
        del s.type
        del s.question
        del s.width
        del s.callback
        del s.storage
        del s.fs
        del s.playlist
        del s.panel_position
        del s.panel_coords
        del s.box
        del s.busy
        del s.playlist_mode
        del s.panel
        del s.info_sem


    def __init__(s, loc, callback, pair, colors, cursor = None ):
        s.total_time = 0.
        s.total_time_str = u''
        s.info_sem = Semaphore(1)
        s.tree_mode = False
        s.location = u"/"
        s.type = "fs"
        s.question = False
        s.width = 10
        s.visibility = Event() #false
        s.callback = callback
        s.storage = storage.storage(s)
        s.fs = media_fs.media_fs()
        s.playlist = playlist.Playlist()
        s.played_songs = []
        s.marked_entries = []
        s.death = Event()
        s.tasks = Queue()
        polls.Run(s.TaskThread)

        s.panel = panel.Panel(s, pair, colors)
        s.panel_position = None
        s.panel_coords = None
        s.focus_flag = False
        s.box = None
        s.busy = Event()
        s.playlist_mode = 0
        s.fs_mode = 0

        if type(loc) == file:
            s.panelup(loc)
            return
        else:
            location = loc
            if location == s.location:
                s.fs.open_dir(s.location)
                s.storage.fill(s.fs.get_elements())
            else:
                rc = s.cd( location )
                if rc[0] == None:
                    s.change_location()
                if rc[1]:
                    s.play_path(cursor, unicode2(location) )
    def update_total_time(s):
        s.total_time = 0.
        s.total_time_str = ""
        try:
            s.total_time = sum( map (lambda e: e.get('time', 0), 
                filter( lambda e: is_track( e ), s.storage.elements ) ) )
        except Exception,e:
            s.total_time = 0.
            s.total_time_str = ""
            return
        if s.total_time > 0.:
            try:
                s.total_time_str = time2str(s.total_time)
            except:
                s.total_time_str = u'EE'

    def AddTask(s, fx, args = []):
        if not s.death.is_set():
            s.tasks.put([fx,args])

    def TaskThread(s):
        while True:
            task = s.tasks.get()
            s.tasks.task_done()
            if s.tasks == None:
                break
            try:
                task[0](*task[1])
            except Exception, e:
                pass
        while not s.tasks.empty():
            s.tasks.get()
            s.tasks.task_done()
        s.tasks.join()
        del s.tasks

    def panelup(s, fd):
        location = pickle.load(fd)
        s.playlist_mode, s.fs_mode, s.fs.fsmode, s.tree_mode = pickle.load(fd)
        opened_dirs = pickle.load(fd)
        played_songs = pickle.load(fd)
        marked_entries = pickle.load(fd)
        pos_id = pickle.load(fd)
        s.set_location( location )

        if s.type == "fs":
            PFS.open_location( s, played_songs = played_songs, marked_entries = marked_entries, opened_dirs = opened_dirs, pos_id = pos_id )

                        
        elif s.type == "playlist":
            s.played_songs = played_songs
            s.marked_entries = marked_entries
            s.open_playlist(pos_id)
        else:
            s.change_location()

        s.panel.head(s.location)
        s.panel.refresh()

    def save_panel(s, fd):
        pickle.dump( unicode2(s.location), fd )
        pickle.dump([s.playlist_mode, s.fs_mode, s.fs.fsmode, s.tree_mode], fd)
        played_songs = []
        marked_entries = []
        opened_dirs = []
        pos_id = None
        if s.type == 'fs':
            opened_dirs = map(lambda y: y['path'], filter(lambda x: x.get('opened'), s.storage.elements) )
        if s.type in ['playlist', 'fs']:
            for i,elm in enumerate(s.storage.elements):
                if elm.get('playback_num', 0) > 0:
                    played_songs.append(elm.get('addr','none'))
                if s.storage.marked_elements[i]:
                    marked_entries.append(elm.get('addr','none'))
            try:
                pos_id = get_id(s.storage[s.panel.pos])
            except:
                pos_id = None
        pickle.dump(opened_dirs, fd)
        pickle.dump(played_songs, fd)
        pickle.dump(marked_entries, fd)
        pickle.dump(pos_id, fd)
            


    def admittance(s):
        if s.busy.is_set() or s.question:
            return False
        return True

    def cmp_locations(s, location):
        if location[-1] != '/' and s.location[-1] != '/':
            if s.location == location:
                return True
        elif location[-1] != '/' and s.location[-1] == '/':
            if s.location[:-1] == location:
                return True
        else:
            if s.location == location[:-1]:
                return True

    def set_location(s, location, tp = None):
        """ Первый возвращаемый аргумент - локация индентична существующей, None если нет указанного путя
        Второй - локация содержит путь к файлу"""
        if location in ['equalizer://', 'locations://', 'lyrics://', 'config://', 'radio://']:
            if s.location == location:
                return (True, False)
            s.location = location

            if s.type == 'lyrics':
                s.lyrics_deinit()

            elif s.type == 'equalizer':
                s.equalizer_deinit()
            elif s.type == 'radio':
                s.radio_deinit()
            elif s.type == 'fs':
                s.callback.inotify_unsubscribe(s)

            s.type = location.split('://')[0]
            return (False, False)

        if not tp and not exists(location):
            return (None, False)

        if s.type == 'lyrics':
            s.lyrics_deinit()

        elif s.type == 'equalizer':
            s.equalizer_deinit()

        elif s.type == 'radio':
            s.radio_deinit()
        elif s.type == 'fs':
            s.callback.inotify_unsubscribe(s)

        if tp: # by search tracks
            s.type = tp
            s.location = location
            return 

        s.type = "none"
        if fs.auto.isdir(location):
            s.type = "fs"
            if s.cmp_locations(location):
                return (True, False)
            s.location = location
            return (False, False)

        elif media_fs.is_audio_file(location) or media_fs.is_cue_file(location):
            s.type = "fs"
            slocation = os.path.dirname(location)
            if s.cmp_locations(slocation):
                return (True, True)
            else:
                s.location = slocation
            return (False, True)
        else:
            s.type = "playlist"
            if s.location == location:
                return (True, False)
            s.location = location
            return (False, False)

    def change_location(s):
        s.clear_info()
        if s.type == "fs":
            PFS.open_location(s,None)
        elif s.type == "playlist":
            s.open_playlist()
        elif s.type == 'locations':
            PLocations.load_locations(s)
            s.panel.head(s.location)
            s.panel.refresh()
        elif s.type == 'equalizer':
            PEqualizer.equalizer_init(s)
            s.panel.head(s.location)
            s.panel.refresh()
        elif s.type == 'lyrics':
            s.lyrics_init()
            s.panel.head(s.location)
            s.panel.refresh()
        elif s.type == 'config':
            s.init_config()
            s.panel.head(s.location)
            s.panel.refresh()
        elif s.type == 'radio':
            s.radio_init()
            s.panel.head(s.location)
            s.panel.refresh()

    def redraw_info(s):
        if not s.busy.is_set() and not s.question:
            s.print_info()
        elif s.busy.is_set():
            s.panel.process.print_text_message('')
        
    def clear_info(s):
        s.info_sem.acquire()
        try:
            s.panel.clear_info()
        except:
            pass
        s.info_sem.release()
        
    def print_info(s):
        s.info_sem.acquire()
        try:
            if s.type == 'playlist':
                mc = s.storage.marked_elements.count(True)
                if mc == 0:
                    s.panel.print_info( unicode(s.panel.pos) + ':' + unicode(s.storage.nol), s.total_time_str )
                else:
                    s.panel.print_info( unicode( mc ) + '/' + unicode(s.panel.pos) + ':' + unicode(s.storage.nol), s.total_time_str )
            elif s.type == 'fs':
                mc = s.storage.marked_elements.count(True)
                if mc == 0:
                    s.panel.print_info(
                        unicode(s.panel.pos) + ':' + unicode(s.storage.nol),
                        s.fs.disc_space,
                        s.total_time_str)
                else:
                    s.panel.print_info( 
                        unicode( mc ) + '/' + unicode(s.panel.pos) + ':' + unicode(s.storage.nol),
                        get_human_readable(s.marked_size) + " : " + s.fs.disc_space,
                        s.total_time_str)
            elif s.type == 'config':
                try:
                    aux = s.storage[s.panel.pos].get_aux()
                    width = s.panel.x
                    if len(aux) > width:
                        auxl = [ aux[:width], aux[width:] ]
                        if len (auxl[1]) < width:
                            n = auxl[0].rfind(',')
                            if n > 0 and len(auxl[1]) + len(auxl[0][n:]) < width:
                                auxl[1] = auxl[0][n:] + auxl[1]
                                auxl[0] = auxl[0][:n]
                                
                    else:
                        auxl = [aux]
                    s.panel.print_info2( auxl )
                except:
                    pass
            elif s.type == 'radio':
                try:
                     s.panel.print_info( unicode(s.panel.pos) + ':' + unicode(s.storage.nol) )
                     if s.storage[s.panel.pos]['type'] == 'stream':
                        s.panel.print_info(middle = s.storage[s.panel.pos].get('addr', ''), N = 0 )
                except Exception, e:
                    pass
            else:
                s.panel.print_info('')


        except:
            pass
        s.info_sem.release()

    def reshort(s, width):
        """4 panel"""
        s.width = width + 1
        s.storage.reshort()

    def cd(s, lc=None):
        if not s.busy.is_set() and not s.question:
            if not lc:
                location = s.panel.cd(u'/')
            else:
                location = unicode2(lc)
            if location:
                if location == 'equalizer://':
                    s.type = 'equalizer'
                    s.change_location()
                    PEqualizer.load_equalizer(s)
                    s.location = location
                    s.panel.head(s.location)
                    s.panel.refresh()
                    return

                location = fs.auto.abspath(location, s.location)

                rc = s.set_location(location)
                if rc[0] == False:
                    s.change_location()
                return rc
    def fsremove(s, elm):
        try:
            if elm.has_key('path'):
                path = elm['path']
                if os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.removedirs(path)
                else:
                    os.remove(path)
        except:
            pass

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
        if s.type == "fs":
            PFS.dirsize(s)

    def play(s):
        pass

