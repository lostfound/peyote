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
from local_library import FengShui, LyricsLibrary
from com_lyrics_wikia import get_lyrics_from_lyricswikia
from elyrics import get_lyrics_from_elyrics

library = LyricsLibrary()

#search_order = [ get_lyrics_from_elyrics, get_lyrics_from_lyricswikia ]
search_order = [ get_lyrics_from_lyricswikia]
def search_lyrics(artist, song_name):
	song_lyrics = library.get_lyrics( artist, song_name )
	if song_lyrics:
		return song_lyrics
	
	for get_lyrics in search_order:
		try:
			song_lyrics = get_lyrics(artist, song_name)
		except:
			pass
		else:
			if song_lyrics:
				song_lyrics = song_lyrics.strip()
				library.add_lyrics(artist, song_name, song_lyrics)
				return song_lyrics
	return None
	

if __name__ == "__main__":
	import sys
	if len(sys.argv) != 3:
		sys.exit()
	print search_lyrics(sys.argv[1], sys.argv[2])

