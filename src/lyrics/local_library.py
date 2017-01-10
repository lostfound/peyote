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

import os
import gzip
config = None
def initialize(cfg):
	global config
	config = cfg

def strip_title(title):
	t = title.rstrip().strip()

	if t.count('(') == 1 and t.count(')') == 1:
		l = t.find('(')
		r = t.find(')')
		if l < r:
			return t[:l] + t[r+1:]
	return t
def FengShui(line):
	words = map(lambda word: word[0].upper() + word[1:].lower(), line.split())
	#words = map(lambda word: word[0].upper() + word[1:].lower(), strip_title(line).split())
	ret = reduce(lambda x,y: u"%s_%s" % (x,y), words)
	return ret

class LyricsLibrary:
	def __init__ (s):
		if not os.path.exists(config.lyrics_dir):
			os.mkdir(config.lyrics_dir)

	def get_lyrics(s, artist, song_name, album=None):
		Artist = FengShui(artist)
		Artist_dir = os.path.join( config.lyrics_dir, Artist)
		
		if not os.path.isdir( Artist_dir ):
			return None
		
		Song   = FengShui(song_name)
		Song_path = os.path.join( Artist_dir, Song ) + '.gz'
		if  not os.path.isfile ( Song_path ):
			return None
		try:
			f = gzip.open (Song_path, "r")
			lyrics = f.read()
			f.close()
			return lyrics
		except:
			return None

	def add_lyrics( s, artist, song_name, lyrics ):
		Artist = FengShui(artist)
		Artist_dir = os.path.join( config.lyrics_dir, Artist)
		
		if not os.path.isdir( Artist_dir ):
			os.mkdir(Artist_dir)

		Song   = FengShui(song_name)
		Song_path = os.path.join( Artist_dir, Song ) + ".gz"
		f = gzip.open ( Song_path, "wb", 9 )
		f.write(lyrics.encode('utf-8'))
		f.close()





