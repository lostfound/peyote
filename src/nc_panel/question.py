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
                                    
import curses
from semaphores import curses_lock, curses_unlock

c = curses

def ncargs(scheme_element):
	return c.color_pair(scheme_element.get_pair_no())|scheme_element.get_args()

class InputLine:
	def __del__(s):
		if s.win:
			curses_lock()
			try:
				s.win.addstr(s.y, s.x0, u' '*s.length)
				s.win.refresh()
			except:
				pass
			curses_unlock()
		del s.y
		del s.x0
		del s.x1
		del s.length
		del s.before
		del s.after
		del s.offset
		del s.attr_line
		del s.attr_cursor

	def __init__(s, win, y, x0, x1, line, offset, pos, attr_line, attr_cursor):
		s.win = win
		s.y = y
		s.x0 = x0
		s.x1 = x1
		s.length = x1 - x0
		s.before = u""
		s.after  = u""
		if s.length +offset - pos <= 0 :
			s.offset = pos - offset - s.length + 1
			#print offset, pos, s.length
		else:
			s.offset = offset
		s.pos = pos
		s.attr_line = attr_line
		s.attr_cursor = attr_cursor
		try:
			s.before = line[:pos]
			s.after  = line[pos:]
			#s.before = u'path'
			#s.after  = u'/'
		except: 
			pass

	def print_line(s):
		try:
			begin = s.before[s.offset:]
		except:
			begin = u""

		curses_lock()
		try:
			s.win.addstr(s.y, s.x0, u' '*s.length, s.attr_line)
			s.win.addstr(s.y, s.x0, (begin+s.after)[:s.length].encode('utf-8'), s.attr_line)
		except:
			pass
		curses_unlock()

	def print_cursor(s):
		try:
			cval = s.after[0]
		except:
			cval = " "
		cpos = len(s.before[s.offset:])

		curses_lock()
		try:
			s.win.addstr(s.y, s.x0 + cpos, cval.encode('utf-8'), s.attr_cursor)
		except:
			pass
		curses_unlock()

	def edit_line(s):
		input_key = ""
		ukey = u""
		while True:
			s.print_line()
			s.print_cursor()

			curses_lock()
			try:
				s.win.refresh()
			except:
				pass
			curses_unlock()

			try:
				k = s.win.getch()
			except:
				return "error"

			if k in [c.KEY_RIGHT]: #Right
				try:
					s.before += s.after[0]
					s.after = s.after[1:]
					if len(s.before[s.offset:]) > s.length - 1:
						s.offset +=  (s.length)/2
				except:
					pass
			elif k in [c.KEY_LEFT]: #Left
				try:
					s.after = s.before[-1] + s.after
					s.before= s.before[:-1]
					if len(s.before[s.offset:]) == 0:
						s.offset = max(0,s.offset-(s.length)/2)
				except:
					pass

			elif k in [c.KEY_HOME]:
				s.after = s.before + s.after
				s.before = u""
				s.offset = 0

			elif k in [c.KEY_END]:
				s.before += s.after
				s.after = u""
				if len(s.before[s.offset:]) >= s.length - 1:
					s.offset = len(s.before) - s.length + 1 

			elif k in [c.KEY_DC]: #del
				try:
					s.after = s.after[1:]
				except:
					s.after = u""
			elif k in [10, 27, c.KEY_DOWN, c.KEY_UP, 9, c.KEY_BTAB]: #enter/tab
				if k == 10:
					return "enter"
				elif k == c.KEY_DOWN:
					return "down"
				elif k == c.KEY_UP:
					return "up"
				elif k == 9:
					return "tab"
				elif k == c.KEY_BTAB:
					return "backtab"
				elif k == 27:
					return "esc"
			elif k in [c.KEY_MOUSE]:
				return "mouse"

			elif k in [c.KEY_BACKSPACE, 127]: #backspace
				try:
					s.before= s.before[:-1]
					if len(s.before[s.offset:]) == 0:
						s.offset = max(0,s.offset-(s.length)/2)
				except:
					pass
				
			else:
				try:
					c.ungetch(k)
					key = s.win.getkey()
				except:
					return "error"
				try:
					input_key += key
					ukey += input_key.decode('utf-8')
					input_key = ""
					s.before += ukey
					ukey = u""
					if len(s.before[s.offset:]) > s.length-1:
						s.offset +=  (s.length)/2
				except:
					pass

_to_X = lambda x: x + 2
_to_x = lambda x: x - 2
_to_y = _to_x
class Question:
	win = None
	def __init__(s, colors, title, question, ansvers):
		s.inputs = []
		s.tlen = len(title)
		qlen = len(question)
		s.acnt = len(ansvers)
		s.inum = 0
		maxx = 0
		s.anslen = 0
		for n,qs in enumerate (question) :
			if type(qs) == list:
				s.inputs.append([n + 2,qs[0], 0, 0])
				s.inum += 1
			elif len(qs) > maxx:
				maxx = len(qs)

		if maxx < s.tlen: maxx = s.tlen
		s.anslen += maxx

		s.question = question
		s.ansvers = ansvers
		s.pos    = -s.inum
		s.minx_t = maxx
		s.miny_t = qlen
		s.title = title
		s.colors= colors
		s.inputlines = []

	def __del__(s):
		if s.win != None:
			s.del_wins()
		del s.inputs
		del s.positions

	def gen_wins(s, parent):
		s.positions={}
		s.tails = 0
		s.qmap = {}
		s.parent = parent
		yx = map( _to_x, list( parent.getmaxyx() ) )
		if yx[1] < s.minx_t:
			s.minx = yx[1] - 2

		s.minx = max( int((yx[1] - 2)/1.61803399), s.minx_t)
		maxx = 2
		N = 0
		for n,ans in enumerate (s.ansvers) :
			mx = maxx + 1 + len(ans)
			if mx > s.minx + 3:
				s.tails += 1
				mx = 2 + len(ans)
				s.qmap[n] = [s.tails + s.miny_t + 2, 2]
				if n != 0:
					ln = len(s.ansvers[n-1]) + s.qmap[n-1][1]
					dlt = (s.minx - ln)/2
					if dlt > 0:
						for i in range (N, n):
							s.qmap[i][1] += dlt
						
				N = n
			else:
				s.qmap[n] = [s.tails + s.miny_t + 2, maxx]
			maxx = mx

		n = len( s.qmap.keys() )
		ln = len(s.ansvers[-1]) + s.qmap[n-1][1]
		dlt = (s.minx - ln)/2
		for i in range (N, n):
			s.qmap[i][1] += dlt

		s.miny = s.miny_t + s.tails + 2

		if yx[0] < s.miny:
			raise "y"


		y_pos = (yx[0] - s.miny)/2
		x_pos = (yx[1] - s.minx)/2

		winargs = map ( _to_X,  [ s.miny, s.minx] ) + [ y_pos, x_pos ]

		curses_lock()
		try:
			s.win = parent.derwin( *winargs )
			s.win.keypad(True)
			s.win.erase()
		except:
			pass
		curses_unlock()

		for ln in s.inputs:
			s.positions[ y_pos + ln[0]] = [ (x_pos + 2, x_pos + s.minx-1, -(s.inum - len(s.inputlines))) ]
			s.inputlines.append(InputLine(s.win, ln[0], 2, s.minx-1, ln[1], ln[2], ln[3], ncargs(s.colors['textpad']), ncargs(s.colors['textpad cursor'])))

		for i in range(0, n):
			s.positions[ y_pos + s.qmap[i][0] ] = s.positions.get( y_pos + s.qmap[i][0], [] ) + [ ( x_pos + s.qmap[i][1], x_pos + s.qmap[i][1] + len (s.ansvers[i]) , i ) ]
		s.y_pos = y_pos
		s.x_pos = x_pos

		s.draw()

	def mouse_click(s, x, y):
		if s.positions.has_key(y):
			rc = filter(lambda n: n != None, map(lambda pos: pos[2] if pos[0] < x <= pos[1] else None, s.positions[y]))
			if rc != []:
				return rc[0]

	def save_state(s):
		n = 0
		for il in s.inputlines:
			s.inputs[n][1] = il.before + il.after
			s.inputs[n][2] = il.offset
			s.inputs[n][3] = len(il.before)
			n+=1

	def del_wins(s, norefresh = False):
		s.save_state()
		#if norefresh:
		for il in s.inputlines:
				il.win = None#if resize
		del s.inputlines
		s.inputlines = []
		del s.win
		s.win = None

	def draw(s):
		yx = s.win.getmaxyx()
		s.a_pos = (yx[1] + 2 - s.anslen)/2
		tx = (yx[1] - s.tlen)/2

		curses_lock()
		try:
			s.win.bkgd(' ', ncargs(s.colors['yesno']))
			s.win.border()
			s.win.addstr( 0, tx, s.title.encode('utf-8'))
			y = 2
			for yy in range(1, s.miny+1):
				s.win.addstr( yy, 1, " "*(s.minx))
			for ql in s.question:
				if len(ql) > yx[1] - 2:
					s.win.addstr( y, 1, ql[-yx[1]+2:].encode('utf-8'))
				else:
					tx = (yx[1] - len(ql))/2
					if type(ql) != list:
						s.win.addstr( y, tx, ql.encode('utf-8'))
				y+=1
		except:
			pass
		curses_unlock()

		for inp in s.inputlines:
			inp.print_line()
			y+=1

		s.draw_ansvers()

		curses_lock()
		try:
			s.win.refresh()
		except:
			pass
		curses_unlock()


	def draw_ansvers(s):
		x_pos = s.a_pos
		y_pos = s.miny - 2
		pos = 0

		for n,ansver in enumerate (s.ansvers):

			curses_lock()
			try:
				if pos == s.pos:
					s.win.addstr( s.qmap[n][0], s.qmap[n][1], ansver.encode('utf-8'), ncargs(s.colors['yesno active button']) )
				else:
					s.win.addstr( s.qmap[n][0], s.qmap[n][1], ansver.encode('utf-8'))
			except:
				pass
			curses_unlock()

			x_pos += len(ansver) + 1
			pos += 1

		curses_lock()
		try:
			s.win.refresh()
		except:
			pass
		curses_unlock()

		while s.pos < 0:
			ipos = s.inum + s.pos
			rc = s.inputlines[ipos].edit_line()
			s.inputlines[ipos].print_line()
			if rc in ['enter', 'down', 'tab']:
				s.pos += 1
			elif rc in ['mouse']:
				mid, x, y, z, bstate =  c.getmouse()
				x -= s.parent.getbegyx()[1]
				rc = s.mouse_click(x+1, y - 1)
				if rc != None:
					s.pos = rc
			else:
				if s.pos > -s.inum:
					s.pos -=  1
				else:
					s.pos = s.acnt - 1
				
			s.save_state()
			pos = 0
			x_pos = s.a_pos
			for n,ansver in enumerate (s.ansvers) :

				curses_lock()
				try:
					if pos == s.pos:
						s.win.addstr( s.qmap[n][0], s.qmap[n][1], ansver.encode('utf-8'), ncargs(s.colors['yesno active button']) )
					else:
						s.win.addstr( s.qmap[n][0], s.qmap[n][1], ansver.encode('utf-8'))
				except:
					pass
				curses_unlock()

				x_pos += len(ansver) + 1
				pos += 1

			curses_lock()
			try:
				s.win.refresh()
			except:
				pass
			curses_unlock()

	def left(s):
		s.pos -= 1
		if s.pos < -s.inum:
			s.pos = s.acnt - 1
		s.draw_ansvers()
	
	def right(s):
		s.pos += 1
		if s.pos == s.acnt:
			s.pos = -s.inum
		s.draw_ansvers()
	
	def enter(s):
		return s.pos
		

