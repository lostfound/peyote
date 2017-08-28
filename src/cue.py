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
import os, os.path
import codecs
import mutagen
import fs.auto
from mutagen.wavpack import WavPack
from mutagen.apev2 import APEv2
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from mutagen import File
from sets import config
import gsttag
from sorts import parse_string
from math import isnan

def cue_time_to_s(time_cue):
    if time_cue == None:
        return None
    ret = 0
    s = .0;
    m = 0
    h = 0
    _time = time_cue.split(':')
    _time.reverse()
    _time_len = len(_time)
    if _time_len > 2:
        h = long(_time[2])
    if _time_len > 1:
        m = long(_time[1])

    s,f = map(lambda x: float(x), _time[0].split('.'))
    s=s+f*1/75.
    #s = float(_time[0])
    ret += float(s)
    ret += long(m)*60
    ret += long(h)*3600
    return ret

def cue_time_to_ns(time_cue):
    if time_cue == None:
        return None
    ret = 0
    s = .0;
    m = 0
    h = 0
    _time = time_cue.split(':')
    _time.reverse()
    _time_len = len(_time)
    if _time_len > 2:
        h = long(_time[2])
    if _time_len > 1:
        m = long(_time[1])

    s,f = map(lambda x: float(x), _time[0].split('.'))
    s=s+f*1/75.
    #s = float(_time[0])
    ret += long(s*1000000000L)
    ret += long(m)*60*1000000000L
    ret += long(h)*3600*1000000000L

    return ret

def item_value(line):
    line.strip()
    for c in line:
        if c == ' ' or c == '\t':
            item = line[:line.find(c)]
            value= line[line.find(c):].rstrip()
            value = value.strip()
            if value not in ["", '"']:
                if value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]
            return item.strip().upper(),value

unquotes = lambda val: val[1:-1] if val[0] == '"' and val [1] == '"' and len(val) > 2 else val

def cue_parser(cuefile):
    def parse_value(v):
        """"""
        v = v.lstrip()
        s = v.find('"')
        e = v.rfind('"')
        sp= v.find(" ")
        st= v.find("\t")
        if sp > st and st != -1:
            sp = st
        if s > sp and sp != -1:
            res = [ v[:sp] ] + parse_value( v[ sp+1: ] )
            return res

        if s > -1 and e > -1:
            res = [ v[s+1:e] ] + parse_value(v[e+1:]) 
            return res
        if sp != -1:
            res = [ v[:sp] ] + parse_value ( v[ sp+1: ] )
            return res
            
        return [v]

    # Директория в которой находится cue-файл
    # она нужна, чтобы устанавливать точный путь до аудио файла
    cuedir = fs.auto.abspath( os.path.dirname(cuefile) )

    ret = [[],]
    with fs.auto.open(cuefile, "r") as f:
        content = f.read()
    
    #Детектируем кодировочку
    coding_detect = True
    next_coding = 'utf8'
    while coding_detect == True:
        try:
            if next_coding != config.GetSCEnc():
                cue = content.decode(next_coding).split('\n')
                if next_coding == 'utf16' and filter( lambda x: 'FILE' in x, cue) == []:
                    raise e
            elif not config.DoISO8859Check():
                cue = content.decode(next_coding).split('\n')
            else:
                lines = filter( lambda x: "FILE" in x or "PERFORMER" in x or "TITLE" in x, content.split('\n') )
                words = []
                for line in lines:
                    try:
                        value = item_value(line)[1]
                    except:
                        continue
                    words += parse_value(value)[0].split()
                coding = ISO8859Check(words)
                cue = content.decode(coding).split('\n')
        except UnicodeDecodeError,e:
            if next_coding == 'utf8':
                next_coding = 'utf16'
            elif next_coding == 'utf16':
                next_coding = config.GetSCEnc()
            else:
                raise e
        except Exception,e:
            pass
        else:
            coding_detect = False
        

            
    depth = 0
    path = None
    track= None
    prev_track = None
    title= None
    performer=None
    date=None
    genre=None



    # построчный парсинг cue
    for line in cue:
        #избавляемся от отступления 
        line = line.lstrip()
        item = None
        value = None
        
        # разделяем строчку на параметр и значение
        try:
            item,value=item_value(line)
        except:
            continue
        #for c in line:
        #    if c == ' ' or c == '\t':
        #        item = line[:line.find(c)]
        #        value= line[line.find(c):].rstrip()
        #        break

        if item == "REM":
            # в комментариях может содержаьтся, более подробная информация чем
            # performer, title, track
            # поэтому первый элемент возвращаемого списка у нас комментарии
            # ret[0].append( parse_value(value) )
            ret[0].append(value)
            try:
                item,value = item_value(value)
            except:
                continue
            if item == "DATE":
                date = value
            elif item == "GENRE":
                genre = value
            continue

        elif item == "PERFORMER":
            value = unquotes(value)
            if track != None:
                track['performer'] = unicode(value)
            else:
                performer = unicode(value)
        elif item == "TITLE":
            value = unquotes(value)
            if track != None:
                track['title'] = value
            else:
                album  = unicode(value)

        elif item == "TRACK":
            if track != None:
                # если у нас не первый трэк, то его начало является
                # концом для предыдущего, если у них одинаковый медиа файл
                if ret[-1] != ret[0]:
                    if ret[-1]['file'] == track['file']:
                        ret[-1]['end'] = track['begin']
                ret.append(track)
            track = dict()
            track['type'] = 'cue'
            if performer: track['performer'] = performer
            if album: track['album'] = album
            track['title'] = u'Track-' + parse_value(value)[0]
            track['file'] = path
            track['ext'] = get_file_type(path)
            track['begin'] = None
            track['end'] = None
            track['id'] = parse_value(value)[0]
            track['addr'] = u'cue://' + fs.auto.abspath(cuefile) + u'#' + unicode(track['id'])
            if date:
                track['date'] = date

        elif item == "FILE":
            #когда на следующей линии мы встретим track, у нас уже будет полный путь к файлу
            path = cuedir + "/" + parse_value(value)[0]

        elif item == "INDEX":
            index = parse_value(value)
            ms = index[1].rfind(':')
            # время в cue выглядит так min:sec:sec/100
            # мы его переводим в min:float_sec
            if ms != -1:
                index_time = index[1][:ms] + '.' + index[1][ms+1:]
            #if track != None and not track.get('begin'):
            track['begin'] = index_time
            
            if track.get('file') != path:
                track['file'] = path
    
    # мы пропарсили 
    if track != None and track != ret[-1]:
        if ret[-1] != ret[0]:
            if ret[-1]['file'] == track['file']:
                ret[-1]['end'] = track['begin']
        ret.append(track)

    if ret == [[],]:
        return [[],]

    for track in ret[1:]:
        if track.has_key('end') and track.get('end') != None:
            track['time'] = cue_time_to_s(track.get('end')) - cue_time_to_s(track.get('begin', '0:0.0'))
    return ret

def ISO8859Check(words):
    symbols = set()
    for word in words:
        lat_chars = 0
        oth_chars = 0
        for n in range(len(word)):
            if ord(word[n]) & 0x80:
                symbols.add(word[n])
                oth_chars += 1
            elif word[n].isalpha():
                lat_chars += 1
        if lat_chars == 0 and oth_chars > 2:
            return config.GetSCEnc()
            break
    else:
        if len ( symbols ) == 1 and symbols.pop().decode(config.GetSCEnc()) == u'’':
                return config.GetSCEnc()
        else:
            return "iso8859-1"
    return config.GetSCEnc()

def magic_convert(unistr):
    if type(unistr) == list:
        us = unistr[0]
    else:
        us = unistr
    try:
        raw = unicode_to_raw(us)
        if config.DoISO8859Check():
            coding = ISO8859Check(raw.split())
        else:
            coding = config.GetSCEnc()
        unico = raw.decode(coding)
        return unico
    except:
        return us
    
    
def unicode_to_raw(unistr):
    rawstr = ""
    n=0
    l=len(unistr)
    for c in unistr:
        rawstr+=chr(ord(c))
    return rawstr

def gst_update_track(track,tag):
    try:
        if tag.has_key("artist"):
            track["performer"] = magic_convert(tag['artist'])
        if tag.has_key("album"):
            track["album"] = magic_convert(tag['album'])
        if tag.has_key("title"):
            track['title'] = magic_convert(tag['title'])
        if tag.has_key("date"):
            track['date'] = unicode(tag['date'].year)
        if tag.has_key("track-number"):
            track['id'] = unicode(tag['track-number'])
        #if tag.info.length != None:
        #    track['time'] = tag.info.length
    except:
        pass
    try:
        if tag.has_key("duration"):
            track['time'] = tag['duration']
    except:
        pass
def _get_tag_prop(tag, keys):
    for k in keys:
        try:
            rc = tag.get(k)
        except:
            continue
        if not rc:
            continue
        try:
            t = type(rc)
            if t in [ mutagen.id3.TPE1
                , mutagen.id3.TIT2
                , mutagen.id3.TALB
                , mutagen.id3.TRCK]:
                rc = rc.text

            elif t in [ mutagen.apev2.APETextValue ]:
                rc = rc[0]
            elif t == mutagen.id3.TDRC:
                try:
                    rc = unicode(rc.text[0]) 
                except:
                    rc = None
            elif t in [list, tuple]:
                try:
                    rc = rc[0]
                except:
                    pass
            elif t not in [str, unicode, list, tuple]:
                try:
                    rc = rc.text
                except:
                    try:
                        rc = rc[0]
                    except:
                        continue
                
            if rc and rc != []:
                return rc
        except:
            pass

def update_track(track,tag, gstdt = None):
    try:
        try:
            if tag.info.length != None:
                track['time'] = tag.info.length
        except:
            pass
        try:
            if tag.info.bitrate != 0:
                track['bitrate'] = tag.info.bitrate
        except:
            pass

        try:
            if tag.info.sample_rate != 0:
                track['sample_rate'] = tag.info.sample_rate
        except:
            pass

        try:
            if tag.info.channels != 0:
                trach['channels'] = tag.info.channels
        except:
            pass

        artist = _get_tag_prop(tag, [ "artist", '\xa9ART', '\xa9art', 'TPE1' ] )
        album  = _get_tag_prop(tag, [ "album", '\xa9alb', '\xa9ALB', 'TALB' ] )
        title  = _get_tag_prop(tag, [ "title", '\xa9nam', '\xa9NAM', 'TIT2' ] )
        date   = _get_tag_prop(tag, [ "date", '\xa9day', '\xa9DAY', 'TRDC', 'TDRC', "Year", "year" ] )
        tid    = _get_tag_prop(tag, [ "tracknumber", 'trkn', 'TRCK' ] )
        diskno = _get_tag_prop(tag, [ "discnumber", '\xa9disk', 'disk', 'part', 'Part', 'TPOS'] )

        if artist:
            track["performer"] = magic_convert( artist )

        if album:
            track["album"] = magic_convert( album )

        if title:
            track['title'] = magic_convert( title )

        if date:
            track['date'] = magic_convert( date )

        if tid:
            while type(tid) in [ list, tuple ]:
                tid = tid[0]
            if type(tid) in [ int, long ]:
                tid = "%i" % tid
            if tid:
                track['id'] = tid
        if diskno and diskno not in [0, '']:
            if type(diskno) in [tuple, list]:
                if len(diskno) == 2 and diskno[0] == 1 and diskno[1] == 1:
                    diskno = None
                else:
                    diskno = unicode(diskno[0])
            if type(diskno) in [str, unicode]:
                if '/' in diskno:
                    dn_spl = diskno.split('/')
                    if len(dn_spl) == 2 and int(dn_spl[0].lstrip('0')) == 1 and int(dn_spl[1].lstrip('0')) == 1:
                        diskno = None
                    else:
                        diskno = dn_spl[0]
            if diskno:
                if type(diskno) in [str, unicode]:
                    diskno = int(diskno.lstrip('0'))
                if type(diskno) in [int, long]:
                    track['cdno'] = unicode(diskno)

    except Exception,e:
        pass
    get_duration(track, gstdt=gstdt)

def get_duration(track, gstdt = None):
    if not track.get('time'):
        try:
            addr = track.get('addr') if not track.has_key('file') else track['file']
            if gstdt:
                dr = gstdt.get_duration(addr)
            else:
                dr = gsttag.GstDetect().get_duration(addr)
            if dr != None:
                track['time'] = dr
        except:
            pass

def add_image_tags_to_cue(track, speeds):
    if track['type'] == 'cue':
        if not speeds.get(track['file']):
            speeds[track['file']] = addr_to_track(track['file'])

        get_track_time(track, speeds)
        image = speeds[track['file']]
        for prop in ['cdno', 'bitrate', 'sample_rate', 'channels']:
            if image.get(prop, '') != '':
                track[prop] = image[prop]
    
def get_track_time(track, speeds = None):
    if track.get('time') != None:
        return
    if track['type'] == 'cue':
        #if not track.has_key('end'):
        if speeds != None:
            if not speeds.get(track['file']):
                speeds[track['file']] = addr_to_track(track['file'])

            image = speeds[track['file']]
                
        else:
            image =    addr_to_track(track['file'])
        end = image.get('time')
        if end != None:
            track['time'] = end - cue_time_to_s(track.get('begin', '0:0.0'))
            del image


def split_name(name, minv, maxv):
        tid = None
        name_int = ""
        name_str = ""
        if name != "":
            if name[0].isdigit():
                tid = 0
                for c in name:
                    if c.isdigit():
                        tid*=10
                        tid+=int(c)
                    else:
                        name_int = repr(tid)
                        name_str = name[name.find(c):]
                        break
                name_str = name_str.strip()
                if name_int != "" and name_str!="" and minv < tid < maxv:
                    l = len ( name_str ) 
                    if name_str.startswith('.') and l > 2:
                        name_str = name_str[1:].strip()
                    elif name_str.startswith('-') and l > 2:
                        name_str = name_str[1:].strip()

                    if name_str == "":
                        name_int = ""
                else:
                    name_str = name
                    name_int = ""
            else:
                name_int = ""
                name_str = name
        return name_str, name_int

def get_cdno_from_album_name( track ):
    config.IsCursed( track )
    if not config.remove_cdno_from_album_name:
        return

    if track.get('album', '') == '':
        return
    
    album_l = track['album'].lower()
    disk_names = ['disk', 'disc', 'cd']
    cdno = 0
    for disk_name in disk_names:
        pos = album_l.rfind(disk_name)
        if pos > 0:
            isdisk = False
            ps = parse_string( album_l[pos:] )
            if len(ps) >= 2 and type(ps[1]) == int:
                if len(ps[0].rstrip()) != len(disk_name):
                    ps0spl = ps[0].split()
                    if ps0spl[0] == disk_name:
                        if len(ps0spl) == 2 and ps0spl[1] == '-':
                            isdisk = True
                        elif len(ps0spl) == 1:
                            isdisk = True
                else:
                    isdisk = True
                if isdisk:
                    cdno = ps[1]
                    ec = album_l[:pos].strip()[-1]
                    if ec in ['-', ',']:
                        album = track['album'][:track['album'][:pos].rfind(ec)].rstrip()
                    elif ec in ['[', '(']:
                        bracket = ']' if ec == '[' else ')'
                        album = track['album'][:track['album'][:pos].rfind(ec)].rstrip()
                        bpos = track['album'][pos:].find(bracket)
                        if bpos >= 0:
                            pass
                            album += track['album'][pos + bpos+1:]
                    else:
                        album = track['album'][:pos].strip()

                    track['cdno'] = unicode(cdno)
                    track['album'] = album
                    return

def useless_title(ttl):
    if type(ttl) not in [str, unicode]:
        return False
    title = ttl.lower()
    tl = len(title)
    if title.find('audiotrack') != -1 and tl < 13:
        return True
    if title.lower().find('track') != -1 and tl <= 10:
        return True
    return False

def set_tags_from_path(track):
    """Очень часто бывает так, что анализируя путь, можно 
    узнать имя альбома, артиста и трека.
    Если в тэгах этой информации нет, то возмём её из фс
    """
    performer = None
    album = None
    year = ""

    
    if track['type'] != 'cue' and ( not track.has_key('title') or useless_title(track['title']) or not track.has_key('id') ):
        # отсекаем от имени файла окончание
        name = track['basename']
        ext_pos = name.rfind('.')
        if ext_pos != - 1:
            name = name[:ext_pos]
        name_str, name_int = split_name(name, 0, 300)
        name = name_str

        if not track.has_key('title') or useless_title(track['title']):
            # отсекаем от имени файла окончание
            track['title'] = name
            
        if track.get('id', 0) in [0,'0'] and name_int != "":
            track['id'] = name_int

    #if not track.has_key('performer') or not track.has_key('album') or not track.has_key('date'):
    if True:
        # Обычно хранится так Artist/Album/title.flac
        # или так 1998 - Album
        # может быть вот так:
        #     Artist/Album/cd No/title.flac
        if track['addr'][:7] == 'file://':
            sp = os.path.split(track['addr'][7:])[0]
        elif track['addr'][:7] == 'http://':
            sp = os.path.split(track['addr'][7:])[0]
        else:
            sp = os.path.split(track['addr'])[0]

        while sp != '':
            
            sp, dir_name = os.path.split(sp)
            if dir_name[:4].lower() in [u'disk', u'disc']:
                if len(dir_name) <= 7 and dir_name[-1].isdigit():
                    continue
            elif  dir_name[:2].lower() == u'cd':
                if len(dir_name) <= 5:
                    continue
            if dir_name == '':
                break

                
            album, year = split_name(dir_name, 1900, 2013)
            #album = dir_name
            performer = os.path.split(sp)[1]
            if performer == '':
                performer = None
            break
        else:
            return

    if performer != None:
        track['performer'] = track.get('performer', performer)

    if album != None:
        track['album'] = track.get('album', album)
    
    if year != "":
        track['date'] = year #track.get('date', year)
    

def get_file_type(path):
    bpath = os.path.basename(path)
    n = bpath.rfind('.')
    if n == -1:
        return None
    return bpath[n+1:].lower()

def get_tags(path, track, gstdt = None):
    ext = track.get('ext', None).lower()
    if path[:7].lower() == u'http://':
        try:
            tag = gsttag.GstDetect().get_tags(path)
            gst_update_track(track,tag)
        except Exception,e:
            get_duration(track, gstdt = gstdt)
            pass
    else:
        try:
            tag = File(path)
            update_track(track, tag, gstdt = gstdt)
        except:
            get_duration(track, gstdt = gstdt)
    

import urllib
from useful import unicode2

def http_to_track(link):
    if link[:7].lower() == u'http://':
        track = dict()
        track['type'] = 'http'
        track['server'] = link[7:].split('/')[0]
        #useful fix for tomsk users
        if track['server'] == 'darkside.cc':
            try:
                track['addr'] = 'http://' + urllib.unquote( link[7:] ).encode('utf-8') 
                #track['addr'] = 'http://' + unicode2( urllib.quote( urllib.unquote( link[7:] ).encode('utf-8') ) )
            except Exception,e:
                pass
        else:
            track['addr'] =  u'http://' + link[7:]

        track['basename'] = os.path.basename(link)
        track['ext'] = get_file_type(track['basename'])
        try:
            track['size'] = fs.httpfs.get_size(link)
        except Exception,e:
            pass

        return track

def file_to_track(path, alterpath = None, gstdt = None, size = None):
    if alterpath == None:
        track = dict()
        if path[:7].lower() != 'http://':
            track['addr'] = u'file://' + path
        else:
            track['addr'] = path
    
        track['path'] = path
        track['basename'] = os.path.basename(path)
        track['type'] = u'file'
        track['ext'] = get_file_type(path)
        try:
            track['islink'] = os.path.islink(path)
        except:
            pass
        
        try:
            if track['islink']:
                track['size'] = 0
            elif type(size) == int:
                track['size'] = size
            else:
                try:
                    track['size'] = os.path.getsize(path)
                except:
                    pass
        except:
            pass

        get_tags(path, track, gstdt = gstdt)
        set_tags_from_path(track)
        get_cdno_from_album_name(track)
        return track
    else:
        track = dict()
        if path[:7].lower() != 'http://':
            track['addr'] = u'file://' + path
        else:
            track['addr'] = path
        track['path'] = path
        track['basename'] = os.path.basename(alterpath)
        track['type'] = u'file'
        track['ext'] = get_file_type(alterpath)
        ##Error in here
        get_tags(path, track, gstdt = gstdt)
        track['addr'] = u'http://' + alterpath
        set_tags_from_path(track)
        get_cdno_from_album_name(track)
        return track

def fixcue(track, speeds = None):
    path = os.path.dirname(track.get('file'))
    if speeds != None:
        entries = speeds.get(path)
        if entries == None:
            entries = filter(None, map(lambda x: x[0] if x[1]=='F' else None, fs.auto.list_dir(path)))
            speeds[path] = entries
    else:
        entries = filter(None, map(lambda x: x[0] if x[1]=='F' else None, fs.auto.list_dir(path)))
        #entries = os.listdir(path)
    wrong_file = os.path.basename(track.get('file')).lower().split('.')
    if len (wrong_file) <= 1:
        return False

    for entry in entries:
        #if fs.auto.isfile( os.path.join(path, entry) ):
        cndt = entry.lower().split('.')
        if cndt[-1] in config.GetAudioExtensions():
            if len(cndt) == len(wrong_file):
                if cndt[:-1] == wrong_file[:-1]:
                    track['file'] = os.path.join(path, entry)
                    track['ext'] = cndt[-1]
                    return True
    return False

def addr_to_track(path, pwd=None, speeds=None):
    """Конвертирует address(file://path, cue://path#n) в dict
    если по адресу ни кого нет, то возвращает None
    speeds это dict куда записывается распарсеные cue, для ускорения 
    Прописывает тэги
    """
    
    track = dict()
    track['type'] = None
    #CUE Test
    iscue = False
    if path.find('cue://') != -1:
        iscue = True
    elif path.find('#') != -1:
        pth = path.rsplit('#', 1)
        if pth[0][-4:].lower() == '.cue':
            iscue = True
    
    if iscue:
        n = path.find('cue://')
        if n != -1:
            pth = path[:n] +  path[n+6:]
        else:
            pth = path
        n = pth.find('file://')
        if n != -1:
            pth = pth[:n] + pth[n+7:]

        cue_spl = pth.rsplit('#',1)

        if len( cue_spl ) == 1:
            del track
            del cue_spl
            return None

        if pwd != None and pwd != '':
            cue_path = fs.auto.abspath(cue_spl[0], pwd )
        else:
            cue_path = cue_spl[0]

        try:
            cue_trno = int(cue_spl[1])
        except:
            return none

        del cue_spl

        speeds_flg = False
        if speeds and speeds.has_key(cue_path):
            cues = speeds[cue_path]
            speeds_flg = True

        elif fs.auto.exists(cue_path):
            cues = None
            try:
                cues = cue_parser(cue_path)
            except:
                pass

            if speeds != None and cues:
                speeds[cue_path] = cues
        else:
            del track
            return None

        if cues == None:
            del track
            return None
        else:
            try:
                track = filter ( lambda x: int(x.get('id', -1)) == cue_trno,cues[1:] )[0]
            except:
                return None
            if speeds != None:
                pth = track['file']
                if not speeds.has_key(pth):
                    if not fs.auto.exists(track['file']):
                        if not fixcue(track, speeds):
                            del track
                            del cues
                            return None
                        else:
                            for ce in cues[1:]:
                                if ce['file'] == pth:
                                    ce['file'] = track['file']
                            speeds[ track['file'] ] = None
                    else:
                        speeds[pth] = None
                else:
                    fixcue(track, speeds)
                del cues
                if speeds:
                    add_image_tags_to_cue(track, speeds)
                else:
                    get_track_time(track, speeds)
                if speeds_flg:
                    return dict(track)
                return track
            else:
                if not fs.auto.exists(track['file']):
                    if not fixcue(track):
                        del track
                        del cues
                        return None
                del cues
                get_track_time(track)
                return track
    else:
        if path[:7].lower() == u"http://":
            return http_to_track2(path)
        if path[:7].lower() == u"file://":
            track_path = fs.auto.abspath ( path[7:], pwd )
        else:
            track_path = fs.auto.abspath ( path, pwd )

        if fs.auto.exists( track_path ) == True:
            if speeds != None:
                if not speeds.has_key(0):
                    speeds[0] = gsttag.GstDetect()
                return file_to_track( track_path, gstdt = speeds[0])
            return file_to_track(track_path)
        else:
            return None

def http_to_track2(url):
    try:
        track = http_to_track(url)
        tag = gsttag.GstDetect().get_tags(url)
        gst_update_track(track,tag)
        duration =  track.get('time', 0.)
        if duration <= 0.01:
            track['type'] = 'stream'
        else:
            set_tags_from_path(track)
            get_cdno_from_album_name(track)
    except:
        return None

    return track

def get_track_by_addr(addr, pwd=None, speeds=None):
    try:
        track = addr_to_track(addr, pwd, speeds)
    except:
        return
    if track:
        if track.get('type') == 'cue':
            try:
                set_tags_from_path(track)
                get_cdno_from_album_name(track)
            except:
                pass
    return track
