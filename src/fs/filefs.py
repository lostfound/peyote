#!/usr/bin/python
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

from __future__ import with_statement
import os 
from stat import *
import codecs
def fsopen(addr, mods):
	if mods == 'w':
		return codecs.open(addr, mods, "utf8")
	return open(addr, mods)

def get_size(addr):
	return os.stat( addr ).st_size

def list_dir(addr):
	entries = os.listdir(addr)
	ret = []
	for e in entries:
		try:
			pth = os.path.join(addr, unicode(e))
			stt = os.stat( pth )
			re = None
			if S_ISDIR(stt[ST_MODE]):
				re = [e, 'D']
			elif S_ISREG(stt[ST_MODE]):
				re = [e, 'F']

			if re:
				if os.path.islink(pth):
					re.append('S')
				else:
					re.append(' ')
				if re[1] == 'F':
					try:
						re.append(stt.st_size)
					except:
						re.append(0)
				ret.append(re)
			
		except:
			pass
	return ret

