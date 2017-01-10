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

import sys, os
import curses,curses.panel, threading
import gettext
import progress
from semaphores import curses_lock, curses_unlock

config = None
GOLDEN_RATIO = 1.61803399
def progress_initialize(cfg):
	global config
	config = cfg

def unicode2(s):
	if type(s) == str:
		return unicode(s.decode('utf-8'))
	else:
		return s
def _(s):
	return unicode2(gettext.lgettext(s))

def ncargs(scheme_element):
	return c.color_pair(scheme_element.get_pair_no())|scheme_element.get_args()

c = curses
p = c.panel

class Process:
	def __init__(s, win, y0, colors, p):
		s.win = win
		s.y0 = y0
		s.colors = colors
		s.p = p
	
	def _get_line(s, text, x):
		if not text or len(text) == 0:
			ret = u" "*x
		else:
			if len(text) >= x:
				ret = text[:x]
			else:
				d = x - len(text)
				d1 = d/2
				dr = d - d1
				ret = u" "*d1 + text + " "*dr
		return ret

		
	def print_text_message(s, top_str = None, bottom_str = None):
		try:
			y,x = s.win().getmaxyx()
		except:
			pass
		curses_lock()
		try:
			s.win().addstr( s.y0, 0, s._get_line(top_str, x).encode('utf-8'), ncargs(s.colors['panel progress']))
			s.win().addstr( s.y0+1, 0,  s._get_line(bottom_str,x).encode('utf-8'), ncargs(s.colors['panel progress']))
		except Exception,e:
			pass
		curses_unlock()
		s.refresh()

	def refresh(s):
		if not s.p.engine.visibility.is_set():
			return
		curses_lock()
		try:
			s.win().refresh()
		except:
			pass
		curses_unlock()
	
	def set_progress(s, intmax, scalestr = ""):
		s.imax = intmax
		s.ipos = 0
		s.scalestr = scalestr
	
	def increment(s):
		s.ipos += 1
		s._print()
	def _print(s):
		try:
			y,x = s.win().getmaxyx()
			W = int(x/GOLDEN_RATIO)
			PP = (s.ipos*100/s.imax)%101
			scl = W/100.
			status = int(PP*scl)
			text = u"%i/%i" % ( s.ipos, s.imax)
			text += " " + s.scalestr
			progress = config.progress_bar_chars[0]*status + config.progress_bar_chars[1]*( W - status )
			s.print_text_message( progress, text )
			progress = '*'*status + 'o'*( W - status )
		except Exception,e:
			pass
		s.refresh()
	


class ProgressWin:
	def __init__(s, title, messages, colors, engine):
		s.abort_message = _(u"Press ENTER key to abort")
		s.pp = []
		s.pp_pos = []
		s.title = title
		s.messages = []
		s.width = 2 + len(s.abort_message)
		s.engine = engine
		s.colors = colors
		s.ppy = None

		if len(title) > s.width + 2:
			s.width = len(title)

		n = 1
		for message in messages:
			s.messages.append([n, message])
			n += len (message) + 1
			s.pp.append(None)
			s.pp_pos.append(n-1)

		s.height = 1 + n
		s.win = None

	def __del__(s):
		s.del_wins()
		del s.pp
		del s.pp_pos
		del s.title
		del s.messages
		del s.width
		del s.ppy


	def gen_wins(s, parent):
		curses_lock()
		try:
			yx = parent.getmaxyx()
		except:
			pass
		curses_unlock()

		if yx[1]<=40:
			s.width = yx[1] - 2
		else:
			s.width = max( int((yx[1] - 2)/GOLDEN_RATIO), len(s.abort_message) + 2 )

		if yx[0] < s.height:
			raise "y"
		y_pos = (yx[0] - s.height)/2
		x_pos = (yx[1] - s.width)/2

		curses_lock()
		try:
			s.win = parent.derwin(s.height, s.width, y_pos, x_pos)
			s.win.border()
			yx = s.win.getmaxyx()

			tx = (yx[1] - len(s.title))/2
			s.win.bkgd(' ', ncargs(s.colors['progress']))
			s.win.border()
			s.win.addstr( 0, tx, s.title.encode('utf-8'))
			for n in range(1, s.height - 1):
				s.win.addstr( n, 1, (u" " * (s.width -2)).encode('utf-8'))
		except:
			pass
		curses_unlock()

		for y in range(len(s.messages)):
			s.print_n(y)

		curses_lock()
		try:
			s.win.addstr(s.height - 1, 1, s.abort_message)
		except:
			pass
		curses_unlock()

		s.refresh()

	def redraw(s):
		for y in range(len(s.messages)):
			try:
				s.print_n(y)
				s.update_progress(y, 0)
			except:
				pass
		yx = s.win.getmaxyx()

		tx = (yx[1] - len(s.title))/2

		curses_lock()
		try:
			try:
				s.win.border()
				s.win.addstr( 0, tx, s.title.encode('utf-8'))
			except:
				pass
		except:
			pass
		curses_unlock()

		s.print_progress_line()
		s.refresh()
		
	def del_wins(s):
		s.win = None

	def print_n(s, n):
		if s.win:
			try:
				curses_lock()
				try:
					yx = s.win.getmaxyx()
				except:
					pass
				curses_unlock()

				y, messages = s.messages[n]
				for i,msg in enumerate(messages):

					curses_lock()
					try:
						s.win.addstr( y+i, 1, (u" " * (s.width -2)).encode('utf-8'))
					except:
						pass
					curses_unlock()

					if len(msg) > s.width - 2:
						wh = (s.width-2)//2
						message = msg[:wh -2] + u'~' + msg[-wh-1:]
					else:
						message = msg
					px = (yx[1] -  len(message))/2

					curses_lock()
					try:
						s.win.addstr( y+i, px, message.encode('utf-8'))
					except:
						pass
					curses_unlock()
			except:
				pass

	def change_str(s, msg_id, n, string):
		y, messages = s.messages[msg_id]
		messages[n] = string
		s.print_n(msg_id)

	def set_progress(s, msg_id, intmax, scalestr):
		s.pp[msg_id] = [0, intmax, scalestr]
	
	def convert_bytes(s, bytes):
		pass
	def update_progress(s, msg_id, increment):
		s.pp[msg_id][0] += increment
		try:
			if s.win == None:
				return
		except:
			return
		pp = s.pp[msg_id]
		status_str = u""
		if pp[1] != 0:
			PP = (pp[0]*100//pp[1])%101
			if pp[2] == "Bytes":
				if pp[1] > 10737418240:
					total_bytes = unicode(pp[1]//1073741824)
					cur_bytes = unicode(pp[0]//1073741824)
					scale = "GB"
				elif pp[1] > 10485760:
					total_bytes = unicode(pp[1]//1048576)
					cur_bytes = unicode(pp[0]//1048576)
					scale = "MB"
				elif pp[1] > 10240:
					total_bytes = unicode(pp[1]//1024)
					cur_bytes = unicode(pp[0]//1024)
					scale = "KB"
				else:
					total_bytes = unicode(pp[1])
					cur_bytes = unicode(pp[0])
					scale = "B"
					
				status_str = u"".join([unicode(PP), "%", " ", cur_bytes, "/", total_bytes, " ", scale])
			else:
				status_str = u"".join([unicode(PP), "%", " ", unicode(pp[0]), "/", unicode(pp[1]), ' ', pp[2]])
			try:
				s.messages[msg_id][1][-1] = status_str
			except:
				pass
			s.print_n(msg_id)
			scl = (s.width-4)/100.
			status = int(PP*scl)

			curses_lock()
			try:
				s.win.addstr(s.pp_pos[msg_id],
						2, (config.progress_bar_chars[0]*status + 
						config.progress_bar_chars[1]*(s.width-4-status)).encode('utf-8'))
			except:
				pass
			curses_unlock()

			s.refresh()

	def update_pp(s, pp):
		pass

	def print_progress_line(s):
		for n, pp in enumerate(s.pp):

			curses_lock()
			try:
				s.win.addstr(s.pp_pos[n], 1, u' ')
				s.win.addstr(s.pp_pos[n], s.width-2, u' ')
			except:
				pass
			curses_unlock()

			try:
				s.update_progress(n,0)
			except:
				curses_lock()
				try:
					s.win.addstr(s.pp_pos[n], 2, (u' '*(s.width-4)).encode('utf-8'))
				except:
					pass
				curses_unlock()

	def refresh(s):
		if s.engine.visibility.is_set():
			curses_lock()
			try:
				s.win.refresh()
			except:
				pass
			curses_unlock()



