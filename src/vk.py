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

import sets
from icecast import gzip_get2
from urllib import quote
from xml.sax import make_parser, handler, SAXParseException
from sets import config
from xml.sax.saxutils import unescape

VKM="https://api.vk.com/method/"
PEYOTE_ID=3087549
GET_TOKEN="http://peyote.t7d.ru/get_token.html"
class VKPLSParser(handler.ContentHandler):

    def __init__(s):
        s.path = ""
        s.tracks = []
        s.location = None
        s.error = False

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
        if s.path == "/error":
            s.error = "Error"
        elif s.path == "/response/audio":
            s.track = {'type': 'file'}


    def characters(s, content):
        s.content = s.content + content

    def endElement(s, name):
        if s.path == "/error/error_msg":
            s.error = s.content
        elif s.path == '/response/count':
            s.count = int(s.content)
        elif s.path == '/response/audio':
            s.tracks.append(s.track)
        elif s.path == "/response/audio/aid":
            s.track['vk-aid'] = s.content
        elif s.path == "/response/audio/owner_id":
            s.track['vk-owner_id'] = s.content
        elif s.path == "/response/audio/artist":
            s.track['performer'] = unescape(s.content)
        elif s.path == '/response/audio/title':
            s.track['title'] = unescape(s.content)
        elif s.path == '/response/audio/url':
            s.track['addr'] = s.content
        elif s.path == '/response/audio/duration':
            s.track['time'] = float(s.content)


        s.path = s.path.rsplit("/", 1)[0]

class vk_api:
    def __init__(s):
        s.error = None
    def get_error(s):
        error = unicode(s.error)
        s.error = None
        return error 
    def update_tracks(s, tracks):
        audios=u""
        for track in tracks:
            try:
                audios+="%i_%i," %(int(track['vk-owner_id']), int(track['vk-aid']))
            except:
                continue
        audios = audios[:-1]
        data = gzip_get2(VKM+"audio.getById.xml?audios=%s&access_token=%s" % (audios,config.vk_token) )
        parser = make_parser()
        handler = VKPLSParser()
        parser.setContentHandler(handler)
        parser.feed(data)
        for t in handler.tracks:
            _tracks = filter(lambda x: x['vk-owner_id'] == t['vk-owner_id'] 
                and x['vk-aid'] == t['vk-aid'], tracks)
            for track in _tracks:
                try:
                    del track['broken']
                except:
                    pass
                track['addr'] = t['addr']
                

        
    def audio_search(s, artist, title, accurate = False):
        query = u"%s - %s" % (artist, title)
        count = 0
        offset = 0
        tracks = []
        artist_words = map(lambda x: x.lower(), artist.split())
        title_words = map(lambda x: x.lower(), title.split())
        while offset == 0 or ( offset < 2000 and count > offset):
            handler = s._audio_search(query, offset)
            if handler.error:
                s.error = handler.error
                return None
            offset+=200
            if count == 0:
                count = handler.count
            tracks +=handler.tracks

        ret = []
        for track in tracks:
            spl = map(lambda x: x.lower(), track.get('performer', u"").split())
            try:
                for w in artist_words:
                    spl.remove(w)
            except:
                continue
            if len(artist_words) != 0:
                track['artist_hits'] = len(spl)
            else:
                track['artist_hits'] = 0
            spl = map(lambda x: x.lower(), track.get('title', u"").split())
            try:
                for w in title_words:
                    spl.remove(w)
            except:
                continue

            if len(title_words) != 0:
                track['title_hits'] = len(spl)
            else:
                track['title_hits'] = 0

            ret.append(track)

        if not accurate:
            ret = sorted(ret, lambda x,y: x['title_hits'] - y['title_hits'])
            ret = sorted(ret, lambda x,y: x['artist_hits'] - y['artist_hits'])
        else:
            ret = filter(lambda x: x['title_hits'] == 0 and x['artist_hits'] == 0, ret)
        for t in ret:
            del t['title_hits']
            del t['artist_hits']
        #strip
        exclusive_tracks = []
        dct = {}
        try:
            for track in ret:
                key = (track['title'], track['performer'])
                duration = int(track['time'])
                for tm in dct.get(key, []):
                    if abs(duration - tm) <= 2:
                        break
                else:
                    lst = dct.get(key, [])
                    lst.append(duration)
                    dct[key]=lst
                    exclusive_tracks.append(track)
        except:
            return ret
        return exclusive_tracks

    def _audio_search(s, query, offset = 0):
        data = gzip_get2(VKM+"audio.search.xml?q=%s&auto_complete=0&count=200&offset=%i&sort=2&access_token=%s" % 
            (quote(query), offset, config.vk_token))
        parser = make_parser()
        handler = VKPLSParser()
        parser.setContentHandler(handler)
        parser.feed(data)
        return handler
