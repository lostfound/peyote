#!/usr/bin/python2
# -*- coding: utf8 -*-

#
# Copyright (C) 2010  Platon Peacel☮ve <platonny@ngs.ru>
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
import filefs
config = None
import httpfs

def Init(cfg):
	global config
	config = cfg

def is_entry_link (fsentry):
	return fsentry[2] == 'S'

def get_entry_size (fsentry):
	return fsentry[3]

def abspath (pth, pwd = None):
	n = pth.rfind('://')
	if n >= 0:
		pth_preffix = pth[:n+3]
		pth_body = pth[n+3:]
	else:
		pth_body = pth
		pth_preffix = ""
	
	if pth_body == '':
		return pth
	
	
	if 'http://' in pth_preffix.lower():
		n = pth_body.find('/')
		if n < 0:
			return pth
		server = pth_body[:n]
		addr = pth_body[n:]
		return pth_preffix + server + os.path.abspath(addr)

	elif pth_body.startswith('/'):
		return pth_preffix + os.path.abspath(pth_body)

	if pwd:
		n = pwd.rfind('://')
		if n >= 0:
			pwd_preffix = pwd[:n+3]
			pwd_body = pwd[n+3:]
		else:
			pwd_preffix = ""
			pwd_body = pwd
		if 'cue://' in pth_preffix.lower():
			pwd_preffix = 'cue://' + pwd_preffix

		if 'http://' in pwd_preffix.lower():
			n = pwd_body.find('/')
			if n < 0:
				pwd_preffix += pwd_body
				pwd_body = "/"
			else:
				pwd_preffix += pwd_body[:n]
				pwd_body = pwd_body[n:]
		return pwd_preffix + os.path.abspath( os.path.join(pwd_body, pth_body))
			

	return pth_preffix + os.path.abspath(pth_body)


def get_size(pth):
	if pth[:7].lower() == 'http://':
		return httpfs.get_size(pth)
	else:
		return filefs.get_size(pth)
def parentdir(pth):
	if pth[-1] != '/':
		return os.path.dirname(pth)
	os.path.dirname(pth[:-1])
def islink(pth):
	if pth[:7].lower() != 'http://':
		return False
	else:
		return os.path.islink(pth)

def isdir (pth):
	if pth[:7].lower() != 'http://':
		return os.path.isdir(pth)
	else:
		return httpfs.isdir(pth)
	return True

def isfile(pth):
	if pth[:7].lower() != 'http://':
		return os.path.isfile(pth)
	else:
		return httpfs.isfile(pth)

def exists (pth):
	if pth[:7].lower() == 'http://':
		return httpfs.exists(pth)
	elif pth[:7].lower() == 'file://':
		return os.path.exists(pth[7:])
	else:
		return os.path.exists(pth)
		
	return True


def has_parent(pth):
	if pth != '/':
		return True
	return False
		
def list_dir(addr):
	if addr[:7].lower() == 'http://':
		return httpfs.list_dir(addr)
	return filefs.list_dir(addr)

def open(addr, mode):
	if addr[:7].lower() == 'http://':
		return httpfs.open(addr, mode)
	else:
		return filefs.fsopen(addr, mode)
def full_split(pth):
	r = []
	p = pth
	while True:
		p,d = os.path.split(p)
		if d == '':
			r.insert(0, p)
			break
		r.insert(0,d)
	return r

def relative(parent_addr, addr):
	if addr[:7].lower() == 'http://':
		return addr
	if addr[:7].lower() == 'file://':
		path = full_split ( addr[7:] )
	else:
		path = full_split ( addr )
	
	if parent_addr == 'file://':
		parent = full_split( parent_addr[7:] )
	else:
		parent = full_split ( parent_addr )
	for n in range( min(len(path), len(parent)) ):
		if path[n] != parent[n]:
			break
	else:
		n+=1
	ret =u""
	for v in parent[n:]:
		 ret = os.path.join(ret, u'..')
	
	for p in  path[n:]:
		ret = os.path.join(ret, p)
	return ret

