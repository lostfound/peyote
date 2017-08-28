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
elyrics = "www.elyrics.net"
from urllib import quote,unquote
from local_library import FengShui, LyricsLibrary, strip_title
from HTMLParser import HTMLParser

class ELyricsHTMLParser(HTMLParser):
	def __init__(s, artist, mi = 0):
		s.td_s = 0
		HTMLParser.__init__(s)
		s.deep = 0
		s.dirs = []
		s.files = []
		s.artist = artist.upper().split()
		if s.artist and s.artist[0] == 'THE':
			del s.artist[0]
		s.ahref = None
		s.ano = -1
		s.result = None
		if not mi:
			s.magic = '/song/'
		else:
			s.magic = '/read/'


	def handle_data(s, data):
		if s.ahref and not s.result:
			spl = data.upper().split()
			if spl[-1] != 'LYRICS':
				return
			del spl[-1]
			#print spl, s.artist
			if spl == s.artist:
				s.result = s.ahref

	def handle_starttag(s, tag, attrs):
		if tag.lower() == 'a':
			for n,v in attrs:
				if n.lower() == 'href' and v and v[:6].lower() == s.magic:
					#print v
					s.ahref = v
					s.ano = s.deep
		#print " "*s.deep, tag, attrs
		s.deep += 1
	def handle_endtag(s, tag):
		s.deep -= 1
		if s.ano == s.deep:
			s.ano = -1
			s.ahref = None

class ELyricsHTMLParser2(HTMLParser):
	def __init__(s):
		s.td_s = 0
		HTMLParser.__init__(s)
		s.deep = 0
		s.are_here = 0
		s.result = u""


	def handle_data(s, data):
		if s.are_here:
			try: #FIX ME, convert str to unocode first
				s.result += data
			except:
				pass

	def handle_starttag(s, tag, attrs):
		if s.are_here:
			if tag.lower() == 'br':
				s.result += '\n'
		elif tag.lower() == 'div' and ('class', 'ly') in attrs:
			s.are_here = 1
		
		if tag.lower() not in ['br', 'hr']:
			s.deep += 1
	def handle_endtag(s, tag):
		if s.are_here and tag.lower() == 'div':
			s.are_here = 0

		if tag.lower() not in ['br', 'hr']:
			s.deep -= 1

	
def get_lyrics_from_elyrics(artist, song_name):
	song_lyric = ""
	page_name = u"/find.php?q=%s&s=1" % reduce(lambda x,y: u"%s+%s" % (x.lower(),y.lower()), artist.split())

	url = elyrics + page_name
	conn = httplib.HTTPConnection(elyrics)
	conn.request("GET", page_name )

	cnt = conn.getresponse()
		
	if cnt.status != 200:
		return None
	

	page = cnt.read()
	parser = ELyricsHTMLParser(artist)
	parser.feed(page)
	if not parser.result:
		return None

	page_name = parser.result
	conn.request("GET", page_name )
	cnt = conn.getresponse()
	if cnt.status != 200:
		return None
	page = cnt.read()
	parser = ELyricsHTMLParser( strip_title(song_name), 1 )
	parser.feed(page)
	if not parser.result:
		return None
	page_name = parser.result
	del parser
	conn.request("GET", page_name )
	cnt = conn.getresponse()
	if cnt.status != 200:
		return None
	page = cnt.read()
	parser = ELyricsHTMLParser2()
	parser.feed(page)
	if not parser.result:
		return None
	lyrics = parser.result.strip().rstrip().split('\n')
	del parser
	if 'lyrics' in lyrics[0].lower():
		del lyrics[0]
	

	ret = ""
	if lyrics and 'these lyrics' in lyrics[-1]:
		del lyrics[-1]

	for line in lyrics:
		if elyrics not in line:
			ret += line + '\n'
	
	if not lyrics:
		return None
	
	return ret.strip().rstrip()


if __name__ == "__main__":
	import sys
	if len(sys.argv) != 3:
		sys.exit()
	print get_lyrics_from_elyrics(sys.argv[1], sys.argv[2])



