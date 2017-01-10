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

import httplib, urllib
lyrics_wikia = "lyrics.wikia.com"
from urllib import quote,unquote
from local_library import FengShui

def num_to_chr(s):
	r = ""
	if s:
		if s[-1] != '\n':
			r = unichr(int(s))
		else:
			r  = unichr(int(s[:-1])) + '\n'
	return r

	
def get_lyrics_from_lyricswikia(artist, song_name):
	Artist = FengShui(artist)
	Song_name = FengShui(song_name)

	page_name = '/' + Artist + ":" + Song_name

	url = lyrics_wikia + page_name
	conn = httplib.HTTPConnection(lyrics_wikia)
	conn.request("GET", page_name )

	cnt = conn.getresponse()
		
	if cnt.status != 200:
		return None

	page = cnt.read().split('\n')

	for line in page:
		if "class='lyricbox'" in line:
			line = line.replace('&#', '\n&#', 1).split('\n')[1]
			line = line.replace('<br/>', '\n').replace('<br />', '\n').replace('<!--', '').replace(';', '')
			lines = line.split('&#')
			song_lyrics = u''
			for line in lines:
				if line:
					try:
						song_lyrics += num_to_chr(line)
					except:
						pass
			if "[...Unfortunately, we are not licensed to display" in song_lyrics:
				return None
			return song_lyrics

	return None
	

if __name__ == "__main__":
	import sys
	if len(sys.argv) != 3:
		sys.exit()
	print get_lyrics_from_lyricswikia(sys.argv[1], sys.argv[2])



