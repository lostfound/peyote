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

import httplib, urllib
lyrics_wikia = "lyrics.wikia.com"
from urllib import quote,unquote
from local_library import FengShui
import lxml.html

def get_lyrics_from_lyricswikia(artist, song_name):
    Artist = FengShui(artist)
    Song_name = FengShui(song_name)

    page_name = '/wiki/' + Artist + ":" + Song_name

    url = lyrics_wikia + page_name
    conn = httplib.HTTPConnection(lyrics_wikia)
    conn.request("GET", page_name )

    cnt = conn.getresponse()
        
    if cnt.status != 200:
        return None

    page = cnt.read()
    doc = lxml.html.fromstring(page)
    lyricbox = doc.cssselect(".lyricbox")[0]
    song_lyrics = u''
    if lyricbox.text: song_lyrics+=lyricbox.text
    for node in lyricbox:
        if str(node.tag).lower() == "br": song_lyrics+="\n"
        if node.tail:
            song_lyrics += node.tail
        if node.text:
            song_lyrics += node.text
            
    song_lyrics = song_lyrics.strip()
    if not song_lyrics: return None
    return song_lyrics
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        sys.exit()
    print get_lyrics_from_lyricswikia(sys.argv[1], sys.argv[2])



