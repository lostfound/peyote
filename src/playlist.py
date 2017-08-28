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

import os
import fs.auto
import stat, codecs
import cue
from xml.dom.minidom import Document
from urllib import unquote
from sets import config
from useful import unicode2,is_track2, quote, quote_uri, unquote_uri
from sorts import parse_string
from xml.sax import make_parser, handler, SAXParseException
import vk
PEYOTE_EXTNSION="http://peyote.sf.net/playlist/0"
VLC_EXTNSION="http://www.videolan.org/vlc/playlist/0"
VLC_NS="http://www.videolan.org/vlc/playlist/ns/0/"


T_M3U = 0
T_PLS = 1
T_XSPF = 2
def is_xml(data):
    # returns : empty -1, xml 1, else 0
    if data.strip() == "":
        return -1
    
    parser = make_parser ()
    try:
        parser.feed(data.encode('utf-8'))
    except:
        return 0
    else:
        return 1

class PlaylistParser(object):
    
    def __init__(s):
        s.urls = []
        s.title = None

    def addURL(s, URL):
        if 'http://' not in URL.lower():
            s.urls.append(unquote(str(URL)))
        else:
            s.urls.append(URL)

    def getURLList(s):
        return s.urls

    def getTitle(s):
        return s.title

    def parseFile(s, fileName):
        raise NotImplementedException

def parse_xspf(data, info=None):
    handler = XSPFParser2()
    parser = make_parser()
    parser.setContentHandler(handler)
    try:
        parser.feed(data.encode('utf-8'))
    except:
        return []
    

    handler = XSPFParser()
    parser = make_parser()
    parser.setContentHandler(handler)
    try:
        parser.feed(data.encode('utf-8'))
    except:
        return []
    if info != None:
        info['title'] = handler.title

    return handler.urls

def parse_xspf2(data, info=None):
    handler = XSPFParser2()
    parser = make_parser()
    parser.setContentHandler(handler)
    try:
        parser.feed(data.encode('utf-8'))
    except:
        return None
    if info != None:
        info['title'] = handler.title

    return handler

class XSPFParser2(handler.ContentHandler):

    def __init__(s):
        s.path = ""
        s.curURL = ""
        s.title = u""
        s.tracks = []
        s.location = None
        s.is_peyote_ext = False
        s._key = None
        s._type = None

    def parseFile(s, fileName):
       
        try:
            parser = make_parser()
            parser.setContentHandler(s)
            parser.parse(fileName)
            return True
        except SAXParseException:
            return False

    def startElement(s, name, attrs):
        s.path += "/%s" % name
        s.content = ""
        if s.path == "/playlist/trackList/track":
            s.track = {}
        elif s.path ==  "/playlist/trackList/track/extension" \
                and (u"application", PEYOTE_EXTNSION) in attrs.items():
            s.is_peyote_ext = True
        elif s.is_peyote_ext:
            s._key = name
            s._type = attrs['type']

    def characters(s, content):
        s.content = s.content + content

    def endElement(s, name):
        if s.is_peyote_ext:
            if s.path ==  "/playlist/trackList/track/extension":
                s.is_peyote_ext = False
            elif s._type == "str":
                s.track[name] = s.content
            elif s._type == "float":
                s.track[name] = float(s.content)
            elif s._type == "int":
                s.track[name] = long(s.content)
            elif s._type == "bool":
                s.track[name] = bool(int(s.content))
            
        elif s.path == "/playlist/trackList/track":
            if s.track.get('location'):
                s.tracks.append(s.track)
            del s.track
        elif s.path == "/playlist/title":
            s.title = s.content
        elif s.path == "/playlist/trackList/track/location":
            s.track['location'] = s.content
        elif s.path == "/playlist/trackList/track/title":
            s.track['title'] = s.content
        elif s.path == "/playlist/trackList/track/creator":
            s.track['performer'] = s.content
        elif s.path == "/playlist/trackList/track/album":
            s.track['album'] = s.content
        

        s.path = s.path.rsplit("/", 1)[0]

class XSPFParser(PlaylistParser, handler.ContentHandler):

    def __init__(s):
        PlaylistParser.__init__(s)
        s.path = ""
        s.curURL = ""
        s.title = u""

    def parseFile(s, fileName):
       
        try:
            parser = make_parser()
            parser.setContentHandler(s)
            parser.parse(fileName)
            return True
        except SAXParseException:
            return False

    def startElement(s, name, attrs):
        s.path += "/%s" % name
        s.content = ""

    def characters(s, content):
        s.content = s.content + content

    def endElement(s, name):
        if s.path == "/playlist/title":
            s.title = s.content

        if s.path == "/playlist/trackList/track/location":
            s.addURL(s.content)

        if s.path == "/playlist/title":
            s.title = s.content

        s.path = s.path.rsplit("/", 1)[0]


def playlist_to_urlist(lines = None, data = None):
    if lines in [None,[]] and not data:
        return []
    if lines in [None,[]]:
        lines = data.split("\n")
    #strip lines
    
    lines = map(lambda line: line.strip().rstrip(), lines)
    lines = filter(lambda line: line if line != "" and line[0] != '#' else None, lines)
    if lines == []:
        return []
    ret = []
    if lines[0].lower() == '[playlist]':
        for line in lines:
            try:
                name,value = line.split('=')
            except:
                continue

            if name.lower().startswith('file'):
                num = name[4:]
                try:
                    n = int(num)
                except:
                    pass
                else:
                    ret.append(value)
    return ret

class Playlist:
    def __init__(s):
        s.history_tracks = []
        s.tracks = []
        s.has_file = False
        s.shuffle = False
        s.repeat  = False

    def was_changed(s, tracks):
        if s.has_file:
            len1 = len(tracks)
            len2 = len(s.tracks)
            if len1 != len2:
                return True

            for it1,it2 in zip(tracks, s.tracks):
                if it1 != it2:
                    return True
            return False

    def blank_playlist(s):
        del s.tracks
        s.tracks = []
        s.has_file = False

    def _get_songs_from_pls(s, lines):
        titles = {}
        songs = {}
        for line in lines:
            spl = line.split( '=', 1)
            if len(spl) == 2:
                name, value = spl

                if name.lower().startswith('title'):
                    num = name[4:]
                    try:
                        n = int(num)
                    except:
                        pass
                    else:
                        titles[parse_string(num)[0]]  = value

                elif name.lower().startswith('file'):
                    num = name[4:]
                    try:
                        n = int(num)
                    except:
                        pass
                    else:
                        songs[parse_string(num)[0]]  = value
        ret = []
        for k in sorted(songs.keys()):
            ret.append( (songs[k], titles.get(k, None) ) )
        return ret
                
    
    def open_playlist(s, path, progress = None):
        s.has_file = True
        del s.tracks
        s.tracks = []
        s.shuffle = False
        pwd = os.path.split(path)[0]
        try:
            with fs.auto.open(path, "r") as f:
                data = f.read().decode('utf-8')
        except UnicodeDecodeError,e:
            try:
                with fs.auto.open(path, "r") as f:
                    data = f.read().decode(config.GetSCEnc())
            except:
                data = None
        if data == None:
            return
        
        rc = is_xml(data)
        if rc == -1: #empty
            return
        elif rc == 1: #XML
            p = parse_xspf2(data)
            if not p:
                return

            if progress:
                progress.pl_progress_maximum(len(p.tracks))

            speeds = dict()

            parent = fs.auto.parentdir(path)

            invalid_url_tracks = []
            for track in p.tracks:
                if track.has_key('addr'): # by peyote
                    if track.has_key('playlist_time'):
                        track['timestamp'] = track['playlist_time']
                        del track['playlist_time']

                    del track['location']
                    track['addr'] = fs.auto.abspath(track['addr'], parent)
                    if track.get('file') :
                        track['file'] = fs.auto.abspath(track['file'], parent)
                    location = track['addr']
                    if config.is_cursed( location ):
                        if progress:
                            progress.pl_progress_up(1)
                        continue
                    if track.has_key('broken'):
                        del track['broken']

                    if 'http://' in location.lower():
                        if config.xspf_check_http:
                            try:
                                if track['type'] == 'cue':
                                    if not fs.auto.exists( quote_uri(track['file']) ):
                                        track['broken'] = True
                                        invalid_url_tracks.append(track)
                                elif not fs.auto.exists( quote_uri(location) ):
                                    track['broken'] = True
                                    invalid_url_tracks.append(track)
                                s.tracks.append(track)
                            except Exception,e:
                                pass
                        else:
                            s.tracks.append(track)
                    elif config.xspf_reload_file:
                        ftrack = cue.get_track_by_addr(location, pwd, speeds)
                        if ftrack != None:
                            if track.has_key('timestamp'):
                                ftrack['timestamp'] = track.get('timestamp')
                            s.tracks.append(ftrack)
                        else:
                            track['broken'] = True
                            s.tracks.append(track)
                    else:
                        if not fs.auto.exists(location):
                            track['broken'] = True
                        s.tracks.append(track)
                        


                else: # by other program
                    location = track['location']
                    ulocation = unquote(location)
                    if config.is_cursed( location ) or config.is_cursed(ulocation):
                        if progress:
                            progress.pl_progress_up(1)
                        continue
                    if 'http://' not in location.lower():
                        location = ulocation
                    track = cue.get_track_by_addr(location, pwd, speeds)
                    if track != None and is_track2(track):
                        s.tracks.append(track)
                    else:
                        pass

                if progress:
                    progress.pl_progress_up(1)
            invalid_url_tracks = filter(lambda x: x.has_key("vk-aid"), invalid_url_tracks )
            if 0 and config.vk_token != "":
                if not config.xspf_check_http: 
                    invalid_url_tracks = filter(lambda x: x.has_key("vk-aid"), s.tracks)
                
                while invalid_url_tracks != []:
                    try:
                        vki = vk.vk_api()
                        vki.update_tracks(invalid_url_tracks[:100])
                    except:
                        pass
                    invalid_url_tracks = invalid_url_tracks[100:]
                del invalid_url_tracks

        else: #plain text
            lines = data.split('\n')
            maximum = 0
            lines = map(lambda line: line.strip().rstrip(), lines)
            lines = filter(lambda line: line if line != "" and line[0] != '#' else None, lines)
            if lines == []:
                return
            s.pls_type = T_M3U
            #detect type of playlist
            if '[playlist]' in lines:
                s.pls_type = T_PLS

            if s.pls_type == T_PLS:
                try:
                    lines = s._get_songs_from_pls(lines)
                except Exception,e:
                    pass    

            
            maximum = len(lines)
            if progress:
                progress.pl_progress_maximum(maximum)
        

            speeds = dict()
            for line in lines:
                if s.pls_type == T_PLS:
                    line, title = line
                track = cue.get_track_by_addr(unquote_uri(line.rstrip()), pwd, speeds)
                if track != None and is_track2(track):
                    if s.pls_type == T_PLS:
                        if title and track.get('title') not in [None, ""]:
                            track['title'] = title
                    s.tracks.append(track)
                else:
                    pass
                    

                if progress:
                    progress.pl_progress_up(1)
    def save_pls(s, path, relative = False):
        if relative:
            par = fs.auto.parentdir(path)
        with fs.auto.open(path, "w") as f:
            f.write('[playlist]\n')
            for n,track in enumerate(s.tracks):
                f.write("File" + str(n + 1) + '=')
                if relative:
                    addr = quote_uri( track['addr'], fs.auto.parentdir(path) )
                else:
                    addr = quote_uri( track['addr'] )

                f.write(addr)
                f.write('\n')

    def save_xspf(s, path, relative = False):
        doc = Document()

        with fs.auto.open(path, "w") as f:
            #head
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            if config.xspf_vlc_compatibility:
                f.write('<playlist version="1" xmlns="http://xspf.org/ns/0/"' + \
                    ' xmlns:vlc="%s">\n' % VLC_NS)
            else:
                f.write('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
            f.write('<trackList>\n')
            for track in s.tracks:
                if track.get('cursed', False):
                    continue
                f.write('\t<track>\n')
                if track.get('title') not in ['', None]:
                    f.write( '\t\t<title>%s</title>\n' \
                        % doc.createTextNode(track['title']).toxml() )
                if track.get('performer') not in ['', None]:
                    f.write('\t\t<creator>%s</creator>\n' \
                        % doc.createTextNode(track['performer']).toxml() )
                if track.get('album') not in ['', None]:
                    f.write( '\t\t<album>%s</album>\n' \
                        % doc.createTextNode(track['album']).toxml() )
                if track.get('id') not in ['', None]:
                    if type(track['id']) == int:
                        no = track['id']
                    elif type(track['id']) in [unicode, str]:
                        no = int( track['id'].split("/")[0].lstrip('0') )
                    else:
                        no = 0
                    if no > 0:
                        f.write( '\t\t<trackNum>%i</trackNum>\n' % no )
                if type(track.get('time')) == float:
                    tm = track['time']*1000
                    if tm%1 >= 0.5:    
                        tm = int(tm) + 1
                    else:
                        tm = int(tm)
                    f.write('\t\t<duration>%i</duration>\n' % tm )

                        

                #write location
                #make valid quoted location
                if track['type'] == 'cue':
                    if not config.xspf_qmmp_compatibility:
                        location = track['file']
                    else:
                        location = track['addr'].replace('file://', '')
                else:
                    location = track['addr']

                if relative:
                    addr = quote_uri( location, fs.auto.parentdir(path) )
                else:
                    if  not config.xspf_qmmp_compatibility and \
                        not 'http://' in location.lower() and \
                        not 'file://' in location.lower():
                        location = 'file://' + location

                    addr = quote_uri( location )

                #write the location
                f.write( '\t\t<location>%s</location>\n' \
                    % doc.createTextNode(addr).toxml() )
                #write other info:
                f.write('\t\t<extension application="%s">\n' % PEYOTE_EXTNSION)
                keys = set(track.keys())
                #keys.discard('id')
                keys.discard('album')
                keys.discard('performer')
                keys.discard('title')
                keys.discard('playback_num')
                keys.discard('cursed')
                for k in sorted(keys):
                    if track[k] != None:
                        v = track[k]
                        t = type(v)
                        if t in [str, unicode]:
                            t = "str"
                            v = unicode2(v)
                        elif t == bool:
                            t = "bool"
                            v = '1' if v else '0'
                        elif t in [int, long]:
                            t = "int"
                            v = str(v)
                        elif t == float:
                            t = "float"
                            v = repr(v)
                        else:
                            continue
                        v = doc.createTextNode(v).toxml()

                        if relative and k in ['addr', 'file']:
                            parent = fs.auto.parentdir(path)
                            if v.lower().startswith('cue://'):
                                v = v[6:]
                                v = 'cue://' + fs.auto.relative(parent, v)
                            else:
                                v = fs.auto.relative(parent, v)

                        f.write(u"\t\t\t<%s type='%s'>%s</%s>\n" \
                                % (k, t, v, k))
                f.write('\t\t</extension>\n')
                if track['type'] == 'cue' and not config.xspf_qmmp_compatibility:
                    begin_ns = cue.cue_time_to_ns(track['begin']) if track.has_key('begin') else 0
                    end_ns = cue.cue_time_to_ns(track['end']) if track.has_key('end') else None

                    if config.xspf_audacious_compatibility:
                        begin_ms = begin_ns/1000000
                        f.write('\t\t<meta rel="seg-start">%i</meta>\n' % begin_ms )
                        if end_ns:
                            end_ms = end_ns/1000000
                            f.write('\t\t<meta rel="seg-start">%i</meta>\n' % end_ms )

                    if config.xspf_vlc_compatibility:
                        f.write('\t\t<extension application="%s">\n' % VLC_EXTNSION)
                        begin = begin_ns/1000000000
                        f.write('\t\t\t<vlc:option>start-time=%i</vlc:option>\n' % begin)
                        if end_ns:
                            end = end_ns/1000000000
                            f.write('\t\t\t<vlc:option>stop-time=%i</vlc:option>\n' % end)
                        f.write('\t\t</extension>\n')
                        

                f.write('\t</track>\n')
            #tail
            f.write('</trackList>\n')
            f.write('</playlist>\n')


            
    def save_playlist(s, path, relative = False):
        if path.lower().endswith(".xspf"):
            s.save_xspf(path, relative)
            return
        if path.lower().endswith(".pls"):
            s.save_pls(path, relative)
            return 
        if relative:
            par = fs.auto.parentdir(path)
        with fs.auto.open(path, "w") as f:
            for track in s.tracks:
                if relative:
                    if track['addr'][:6].lower() == u'cue://':
                        addr = u'cue://' 
                        addr += fs.auto.relative(par, track['addr'][6:])
                    else:
                        addr = fs.auto.relative(par, track['addr'])
                    f.write ( addr +  u"\n" )
                        
                else:
                    f.write(track['addr'] + u"\n")

