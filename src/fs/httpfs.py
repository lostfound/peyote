#!/usr/bin/python
# -*- coding: utf8 -*-

#
# Copyright (C) 2017  Platon Peacel☮ve <platonny@ngs.ru>
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
import stat
from auto import config
import httplib, urllib
from HTMLParser import HTMLParser

def _get_alt_code_page():
	if config:
		return config.etSCEnc()
	else:
		return 'cp1251'

def _improved_unquote(strg):
	unquoted = urllib.unquote(strg)
	try:
		uniunqed = unquoted.decode('utf-8')
	except UnicodeDecodeError:
		uniunqed = unquoted.decode( _get_alt_code_page() )
	return uniunqed
	#etSCEnc
class FsHTMLParser(HTMLParser):
	def __init__(s):
		s.td_s = 0
		HTMLParser.__init__(s)
		s.dirs = []
		s.files = []

	def handle_starttag(s, tag, attrs):
		if tag.lower() == 'a':
			for a in attrs:
				if a[0] == 'href':
					entry = a[1]
					if entry[0] != '/':
						if entry[-1] == '/':
							s.dirs.append( _improved_unquote(entry[:-1]) )
						else:
							s.files.append( _improved_unquote(entry) )
	def handle_starttag2(s, tag, attrs):
		if tag.lower() == 'td':
			s.td_s = 1
		elif s.td_s == 1 and tag.lower() == 'a':
			for a in attrs:
				if a[0] == 'href':
					entry = a[1]
					if entry[0] != '/':
						if entry[-1] == '/':
							s.dirs.append(urllib.unquote(entry).decode('utf-8'))
						else:
							s.files.append(urllib.unquote(entry).decode('utf-8'))
	def handle_endtag(s, tag):
		if tag.lower() == 'td':
			s.td_s = 0
		pass

def quote(addr):
	if "%" not in addr:
		return urllib.quote(addr.encode('utf-8'))
	else:
		return addr

def isdir(addr):
	try:
		serv = addr[7:]
		if serv.find('/') == -1:
			path = '/'
		else:
			path = serv[serv.find('/'):]
			serv = serv[:serv.find('/')]

		path = quote(path)
		if path[-1] != '/':
			path += '/'

		conn = httplib.HTTPConnection(serv)
		conn.request("HEAD", path)
		cnt = conn.getresponse()
		conn.close()
		if cnt.status == 200:
			return True
		else:
			return False
	except:
		return False

def isfile(addr):
	splited_addr = addr[7:].split('/',1)
	serv = splited_addr[0]
	if len(splited_addr) != 1:
		_path = splited_addr[1]
	else:
		_path = ''
	path = 'http://' + os.path.join(serv, quote(_path))

	try:
		conn = httplib.HTTPConnection(serv)
		conn.request("HEAD", path)
		#conn.request("GET", path)
		try:
			cnt = conn.getresponse()
		except httplib.BadStatusLine:
			return True

		conn.close()
		if cnt.status == 200:
			return True
		else:
			try:
				_path.decode('ascii')
			except:
				path = 'http://' + os.path.join(serv, urllib.quote ( _path.encode ( _get_alt_code_page() ) ))
				conn = httplib.HTTPConnection(serv)
				conn.request("HEAD", path )
				try:
					cnt = conn.getresponse()
				except httplib.BadStatusLine:
					return True

				conn.close()
				if cnt.status == 200:
					return True
			return False
	except:
		return False

def exists(addr):
	if addr[-1] == '/':
		return isdir(addr)
	else:
		if not isfile(addr):
			return isdir(addr)
		else:
			return True
	return False

class HTTPdescriptor:
	def __init__(s, addr, mode):
		if addr[:7].lower() != 'http://':
			raise IOError("incorrect address")
		if "w" in mode:
			raise IOError("Read Only!")

		s.serv = addr[7:]
		if s.serv.find('/') == -1:
			path = '/'
		else:
			path = s.serv[s.serv.find('/'):]
			s.serv = s.serv[:s.serv.find('/')]

		s.path = quote(path)
		
		try:
			s.open_descriptor()
		except httplib.BadStatusLine:
			raise IOError("getresponse raises BadStatusLine")
		except:
			s.path = urllib.quote ( path.encode ( _get_alt_code_page() ) )
			try:
				s.open_descriptor()
			except httplib.BadStatusLine:
				raise IOError("getresponse raises BadStatusLine")
		

	def open_descriptor(s):
		s.conn = httplib.HTTPConnection(s.serv)
		s.conn.request("GET", s.path)

		s.cnt = s.conn.getresponse()
		
		if s.cnt.status == 200:
			return
		else:
			sts = s.cnt.status
			del s.conn
			del s.cnt

			raise IOError("Not found: %s\n server returned: " % s.path + repr(sts) )
		


	def close(s):
		s.conn.close()
		s.__exit__()

	def readlines(s):
		if s.cnt:
			buf = s.cnt.read()
			return buf.split('\n')
	def read(s, size = -1):
		if size == -1:
			rc = s.cnt.read()
		else:
			rc = s.cnt.read(size)
		return rc

	def stop(s):
		s.conn.close()
		s.__exit__()

	def tell(s):
		return s.pos
		pass

	def seek(s, pos, w=0):
		s.stop()
	
	def truncate(s):
		pass


	def __enter__(s):
		return s

	def __exit__(s, _type=None, value=None, traceback=None):
		try:
			del s.conn
			del s.cnt
		except:
			pass
		s.cnt = None
		s.conn = None

def open(addr, mods):
	return HTTPdescriptor(addr, mods)

def get_size(addr):
	if addr[:7].lower() != 'http://':
		raise IOError("incorrect address")
	serv, path = addr[7:].split('/',1)
	path = 'http://' + os.path.join(serv, quote(path))
	c = httplib.HTTPConnection(serv)
	c.request( 'GET', path )
	try:
		rq = c.getresponse()
	except httplib.BadStatusLine:
		return 0

	c.close()
	if rq.status != 200:
		if rq.status == 404:
			serv, path = addr[7:].split('/',1)
			path = 'http://' + os.path.join(serv, urllib.quote ( path.encode ( _get_alt_code_page() ) ))
			c = httplib.HTTPConnection(serv)
			c.request( 'GET', path )
			try:
				rq = c.getresponse()
			except httplib.BadStatusLine:
				return 0
			c.close()
			if rq.status != 200:
				return 0
		else:
			return 0

	if type(rq.length) == int:
		return rq.length
	else:
		return 0

def list_dir(addr):
	def is_not_artifact(a):
		if a[0] == '?' and '=' in a:
			return False
		return True
	with open( addr + '/', 'r') as f:
		xmllist = f.read()
	parser = FsHTMLParser()
	parser.feed(xmllist)

	return map(lambda e: [e, 'D', ' '], parser.dirs) + map(lambda e: [e, 'F', ' ', get_size(os.path.join(addr,e))], filter(is_not_artifact, parser.files))
	
