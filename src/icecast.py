#!/usr/bin/python
# -*- coding: utf8 -*-

#
# Copyright (C) 2010-2012  Platon Peacel☮ve <platonny@ngs.ru>
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

from xml.sax import parseString,handler,SAXParseException
import httplib, urllib2
from urllib import urlencode, quote
from gzip import GzipFile
from StringIO import StringIO
from HTMLParser import HTMLParser
from playlist import playlist_to_urlist, parse_xspf
import pickle
from sets import config
import os.path

YP_SERVER="dir.xiph.org"
YP_PATH="/yp.xml"
GZ_HEADER = {"Accept-Encoding" : "gzip,deflate", "Accept-Charset" : "UTF-8,*"} 
GZ2_HEADER = {"Accept-Encoding" : "gzip, deflate" }
HTTP_TIMEOUT=5


def receive_yp():
    conn = httplib.HTTPConnection(YP_SERVER, timeout=HTTP_TIMEOUT)
    conn.request("GET", YP_PATH, headers = GZ_HEADER)
    response = conn.getresponse()
    if response.status == 200:
        raw_data = response.read()
        stream = StringIO(raw_data)
        decompressor = GzipFile(fileobj=stream) 
        return decompressor.read()


    #data = r.read()
def gzip_get(server, path):
    conn = httplib.HTTPConnection(server, timeout=HTTP_TIMEOUT)
    conn.request("GET", path, headers = GZ_HEADER)
    response = conn.getresponse()
    if response.status == 200:
        raw_data = response.read()
        stream = StringIO(raw_data)
        decompressor = GzipFile(fileobj=stream) 
        conn.close()
        return decompressor.read()
    conn.close()

def gzip_get2(url):
    req = urllib2.Request(url, headers = GZ_HEADER)
    response = urllib2.urlopen(req)
    raw_data = response.read()
    try:
        stream = StringIO(raw_data)
        decompressor = GzipFile(fileobj=stream)
        return decompressor.read()
    except:
        return raw_data

def gzip_post2(server, path, params ):
    req = urllib2.Request('http://'+server+path, urlencode(params), GZ_HEADER)
    response = urllib2.urlopen(req)
    raw_data = response.read()
    stream = StringIO(raw_data)
    decompressor = GzipFile(fileobj=stream)
    return decompressor.read()

class shoutcastStreamsParser(HTMLParser):
    def __init__(s):
        HTMLParser.__init__(s)
        s.path = ""
        s.end = None
        s.streams = []
        s.key = None

    def handle_starttag(s, tag, attrs):
        if tag == "div" and ('class' , 'dirlist') in attrs:
            s.end = s.path
            s.stream = {}
        elif s.end != None:
            if tag.lower() == 'a':
                if not s.stream.has_key('playlist'):
                    for a,v in attrs:
                        if a.lower() == 'href':
                            s.stream['playlist'] = v
                        elif a.lower() == 'title':
                            s.stream['station_name'] = v
            elif tag.lower() == 'div':
                for a,v in attrs:
                    if a.lower() == 'class':
                        if v.lower() =='dirlistners':
                            s.key = 'listners'
                        elif v.lower() == "dirbitrate":
                            s.key = 'bitrate'
                        elif v.lower() == 'dirtype':
                            s.key = 'ext'
                        break
        s.path += "/%s" % tag.lower()
    def handle_data(s, data):
        if s.key:
            s.stream[s.key] = data

    def handle_endtag(s, tag):
        s.key = None
        offset = s.path.rfind("/")

        if offset >= 0:
            s.path = s.path[0:offset]
        if s.end != None and s.end == s.path:
            s.streams.append(s.stream)
            s.end = None
                    
            
class shoutcastIndexParser(HTMLParser):
    def __init__(s):
        HTMLParser.__init__(s)
        s.is_genre_section = False
        s.path = ""
        s.genres = []
    
    def handle_starttag(s, tag, attrs):
        if s.is_genre_section == False and tag.lower() == 'div' and ("id", "radiopicker") in attrs:
            s.genre = {}
            s.is_genre_section = True
        if s.is_genre_section:
            s.path += "/%s" % tag.lower()
            if s.path == '/div/ul/li':
                s.genre = {}
                for a,v in attrs:
                    if a == 'id':
                        s.genre['id'] = v
            elif s.path == '/div/ul/li/a':
                for a,v in attrs:
                    if a.lower() == 'href' and v.startswith('/radio/'):
                        s.genre['genre'] = v[7:]
                
    def handle_endtag(s, tag):
        if s.is_genre_section:
            offset = s.path.rfind("/")
            if s.path == '/div/ul/li':
                s.genres.append(s.genre)
            if offset >= 0:
                s.path = s.path[0:offset]
            if s.path == "":
                s.is_genre_section = None

def _genre_entry( name, depth):
    genre = {}
    genre['type'] = 'submenu'
    genre['status'] = 0
    genre['menu-type'] = 'genre'
    genre['stations'] = []
    genre['name'] = name
    genre['depth'] = depth
    return genre

class ShoutCast:
    def __init__(s, depth = 0):
        s.shoutcast_srv = "www.shoutcast.com"
        s.genre_path = "/genre.jsp"
        s.search_basedir = '/search-ajax/'
        s.genre_basedir = '/genre-ajax/'
        s.depth = depth
        s.shoutcast_genres = os.path.join(config.peyote_cache_dir, 'shoutcast-genres')

    def check_genres(s):
        try:
            with open(s.shoutcast_genres, "r") as f:
                s.genres = pickle.load(f)
        except:
            return False
        return True

    def receive_genres(s,progress=None):
        s.genres = []
        data = gzip_get(s.shoutcast_srv, "/")
        parser = shoutcastIndexParser()
        try:
            parser.feed(data)
        except:
            pass
        if progress:
            progress.set_progress(len(parser.genres))
            progress.increment()

        for gnr in parser.genres:
            genre = {}
            genre['type'] = 'submenu'
            genre['status'] = 0
            genre['menu-type'] = 'genre'
            genre['children'] = []
            genre['stations'] = []
            genre['name'] = gnr['genre']
            genre['depth'] = s.depth
            
            data = gzip_post2(s.shoutcast_srv, s.genre_path, gnr) 
            lines = data.split("\n")
            if progress:
                progress.increment()
            for line in lines:
                try:
                    subgenre = line.split("/radio/",1)[1].split('"')[0]
                except:
                    pass
                else:
                    genre['children'].append(_genre_entry(subgenre, s.depth + 1))
                    

            if genre['children'] == []:
                del genre['children']
            else:
                self = dict(genre)
                self['depth'] += 1
                del self['children']
                genre['children'].insert(0, self)
            s.genres.append(genre)
        with open(s.shoutcast_genres, "w") as f:
            pickle.dump(s.genres, f)

    def search_stations(s, request, progress = None):
        return s.stations(s.search_basedir + quote(request['value']), request, progress)
        
    def receive_stations(s, genre, progress = None, cont = False):
        path = quote(s.genre_basedir + genre['name'])
        return s.stations(path, genre, progress, cont)

    def stations(s, path, inst, progress = None, cont = False):
        args = {'ajax' : 'true', 'count' : config.shoutcast_RpP, 'strIndex' : '0', 'order' : 'ask'}
        if path.startswith(s.search_basedir):
            if config.shoutcast_sort == 'bitrate':
                args['mode'] = 'bitrate'
            else:
                args['mode'] = 'listeners'
        else:
            if config.shoutcast_sort == 'bitrate':
                args['mode'] = 'bitratehead1'
            else:
                args['mode'] = 'listeners'
        if cont:
            args['strIndex'] = str( len(inst.get('stations', 0)) ) 


        data = gzip_post2(s.shoutcast_srv, path, args)
        sparcer = shoutcastStreamsParser()
        sparcer.feed(data)
        if progress:
            progress.set_progress( len(sparcer.streams) )
            progress.increment()
        if not cont:
            inst['stations'] = []

        for stream in sparcer.streams:
            stream['depth'] = inst['depth'] + 1
            stream['type'] = 'stream'
            data = gzip_get2(stream['playlist'])
            try:
                stream['addr'] = playlist_to_urlist(data=data)[0]
            except:
                pass
            else:
                inst['stations'].append(stream)
            if progress:
                progress.increment()
            #print "   " + stream['title'], stream.get('listners', '0'), stream.get('bitrate', '0')
        

            
        
# sc = ShoutCast()
# sc.receive_genres()
# sc.receive_stations(sc.genres[20]['children'][2])
# k
# for genre in sc.genres:
#     print genre['name']
#     for subgenre in genre.get('children',[]):
#         print "   " + subgenre['name']
# 

class Icecast(handler.ContentHandler):

    def __init__(s):
        s.track = ""
        s.path = ""
        s.curURL = ""
        s.genres = set()
        s.streams = []
    def reload(s):
        """returns None or error description"""
        if s.receive():
            if s.parse():
                return None
            else:
                return u"%s http://%s%s" % ("Can't parse", YP_SERVER, YP_PATH )
        else:
            return u"%s http://%s%s" % ( "Can't wget", YP_SERVER, YP_PATH )

    def receive(s):
        try:
            s.data = receive_yp()
        except:
            return False
        else:
            if s.data == None:
                return False
        return True

    def add_to_gtree(s):
        if s.entry.has_key('genre'):
            g = s.entry['genre']
            if g.strip() == "":
                g = "other"
        else:
            g = "other"
        if s.gtree.has_key(g):
            s.gtree[g].append(s.entry)
        else:
            s.gtree[g]= [s.entry]
    def parse(s):
        s.streams = []
        s.genres = set()
        s.gtree = {}
        if s.data:
            try:
                parseString(s.data, s)
                del s.data
                return True
            except SAXParseException:
                del s.data
                return False

    def startElement(s, name, attrs):
        s.path += "/%s" % name
        if s.path == "/directory/entry":
            s.entry = {"type": "stream"}

        s.content = ""

    def characters(s, content):
        s.content = s.content + content

    def endElement(s, name):

        if s.path == "/directory/entry":
            if s.entry.get('addr'):
                s.streams.append(s.entry)
                s.add_to_gtree()
                
        elif s.path == "/directory/entry/server_name":
            s.entry['station_name'] = unicode(s.content)
            try:
                unicode(s.content)
            except:
                pass
        elif s.path == "/directory/entry/server_type":
            if s.content == 'audio/mpeg':
                s.entry['ext'] = 'MP3'
            elif s.content == 'audio/aacp':
                s.entry['ext'] = 'AAC+'
            elif s.content == 'application/ogg':
                s.entry['ext'] = 'OGG'
            elif s.content.startswith('audio/'):
                s.entry['ext']  = s.content[6:].upper()

        elif s.path == "/directory/entry/listen_url":
            s.entry['addr'] = s.content
        elif s.path == "/directory/entry/bitrate":
            s.entry['bitrate'] = s.content
        elif s.path == "/directory/entry/genre":
            s.entry['genre'] = s.content
            s.genres.add(s.content)



        offset = s.path.rfind("/")
        if offset >= 0:
            s.path = s.path[0:offset]
class IcecastSearchParser(HTMLParser):
    def __init__(s):
        HTMLParser.__init__(s)
        s.path = ""
        s.baseurl = "http://dir.xiph.org/"
        s.xspf_list = []
    
    def handle_starttag(s, tag, attrs):
        s.path += "/%s" % tag.lower()
        if tag.lower() == 'a':
            for k,v in attrs:
                if k.lower() == 'href':
                    if v.endswith('.xspf'):
                        s.xspf_list.append(s.baseurl + v)
                
    def handle_endtag(s, tag):
        s.path = s.path.rsplit("/", 1)[0]


class IcecastSearch:
    def __init__(s):
        s.search_url = u'http://dir.xiph.org/by_genre/%s?search=%s&page=%i'
        s.tag = None
        s.page = 0
    def _get_url(s):
        qtag=quote(s.tag)
        return s.search_url % (qtag, qtag, s.page) 
    def search(s, tag, progress=None):
        s.tag = tag
        s.page = 0
        return s._search(progress)

    def show_more(s, progress = None):
        s.page += 1
        return s._search(progress)

    def _search(s, progress):
        # get html page
        try:
            page = gzip_get2(s._get_url())
        except:
            return []
        # parse it
        parser = IcecastSearchParser()
        try:
            parser.feed(page)
        except:
            return []
        ret = []
        if progress:
            progress.set_progress( len(parser.xspf_list) )
            progress.increment()
        for xspf in  parser.xspf_list:
            info = {}
            try:
                plraw = gzip_get2(xspf)
                urls = parse_xspf(plraw, info)
            except:
                if progress:
                    progress.increment()
                continue

            if progress:
                progress.increment()

            if len(urls) > 0:
                ret.append( _get_stream(info['title'], urls[0]) )
        return ret

def _get_stream(title, url):
    stream = {}
    stream['depth'] = 2
    stream['type'] = 'stream'
    stream['addr'] = url
    stream['station_name'] = title
    stream['time'] = 0.
    return stream

if __name__ == '__main__':
    ics = IcecastSearch()
    for n in ics.search("Jrock"):
        print n
