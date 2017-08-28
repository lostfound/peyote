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
                                    
import curses, curses.panel
from  progress import ProgressWin,progress_initialize, Process
from question import InputLine, Question
from semaphores import curses_lock, curses_unlock
from math import isnan

c = curses
p = c.panel
int2 = lambda f: int(f) + 1 if not isnan(f%1) else int(f)

config = None
def initialize(cfg):
	global config
	config = cfg
	progress_initialize(cfg)

def ncargs(scheme_element):
	return c.color_pair(scheme_element.get_pair_no())|scheme_element.get_args()

class Panel:
	def __init__(s, engine, pair, colors):
		#s.storage  = strg
		s.inputline = None
		s.progress  = None

		s.winp = None
		s.win  = None
		s.winfo = None
		s.pair = pair
		s.colors = colors
		s.is_cursor_hide = True

		s.x = -1
		s.y = -1
		s.first_no = 0
		s.pos = 0
		s.cursor_pos = 0
		s.cursor = None
		s.header = None
		s.engine = engine
		s.storage= engine.storage
		s.yesno = None
		s.scroll_pos = 0
		s.process = Process( s._info_win, 0, colors, s)

	def _info_win(s):
		return s.winfo

		#s.infostr = u""

	def left(s):
		if s.yesno != None:
			s.yesno.left()
	def right(s):
		if s.yesno != None:
			s.yesno.right()

	def clear_info(s):
		if s.winfo:
			curses_lock()
			try:
				s.winfo.addstr(0,0, u' '*s.x)
				s.winfo.addstr(1,0, u' '*s.x)
			except:
				pass
			curses_unlock()

	def print_info2(s, infolst):
		if s.winfo:
			curses_lock()
			try:
				s.winfo.addstr(0,0, u' '*s.x)
				s.winfo.addstr(1,0, u' '*s.x)
				if len(infolst) == 2:
					s.winfo.addstr( 0,0, infolst[0][:s.x].encode('utf-8') )
					s.winfo.addstr( 1,0, infolst[1][:s.x].encode('utf-8') )
				else:
					s.winfo.addstr( 1,0, infolst[0].encode('utf-8') )
			except:
				pass
			curses_unlock()

			s.refresh()
	def print_info(s, infostr=None, infostr2=None, middle = None, N = 1):
		if s.winfo:
			curses_lock()
			try:
				pos_r = None
				pos_m = None
				len_l = 0 
				if N == 1:
					s.winfo.addstr(0,0, u' '*s.x)
				s.winfo.addstr(N,0, u' '*s.x)
				if infostr:
					s.winfo.addstr(N,0, infostr[:s.x])
					len_l = len(infostr)
				if infostr2 not in [ None, "" ]:
					len_r = len(infostr2)
					if len_r + len_l < s.x:
						pos_r = s.x - len_r

				if pos_r:
					s.winfo.addstr(N, pos_r, infostr2)
				if middle not in [None, ""]:
					len_m = len( middle )
					pos_m = s.x/2 - len_m/2
					if pos_m > len_l:
						if pos_r and pos_m + len_m >= pos_r:
							pos_m = None
				if pos_m:
					s.winfo.addstr(N, pos_m, middle)
					
			except:
				pass
			curses_unlock()
			s.refresh()
		
	def redraw_yesno(s):
		yx = s.win.getmaxyx()
		x = 30
		y = 4
		ypos = yx[0]/2 - y/2
		xpos = yx[1]/2 - x/2
		s.yesno.redraw(s.win, ypos, xpos, y, x)

	def del_progress(s):
		s.progress = None

	def run_progress(s, title, msgs):
		s.progress = ProgressWin(title, msgs, s.colors, s.engine )
		if s.win != None:
			s.progress.gen_wins(s.win)

	def run_yesno(s, title, question, ansvers):
		s.yesno = Question(s.colors, title, question, ansvers)
		s.yesno.gen_wins(s.win)
		s.engine.question = True
		return 
		
	def helocate(s, hxpos):
		if hxpos < 0:
			return
		elif hxpos == 0 and s.header[0] == '/':
			return '/'
		hl = len (s.header)
		if hl < s.x:
			if hl < hxpos:
				return
			slz = s.header[hxpos:].find('/')
			if slz >= 0:
				return s.header[:hxpos + slz]
			return 
		else:
			before = s.header[:-s.x]
			after = s.header[-s.x:]
			hl = len (after)
			if hl < hxpos:
				return
			slz = after[hxpos:].find('/')
			if slz >= 0:
				return before + after[:hxpos + slz]
		
	def head(s, header = None):
		if header != None:
			s.header = header
		if s.win:
			s.print_border()
			nca = ncargs(s.colors['header']) if s.is_cursor_hide else ncargs(s.colors['active header'])
			curses_lock()
			try:
				if len ( s.header ) > s.x:
					s.winp.addstr(0,1, s.header[-s.x:].encode('utf-8'), nca)
				else:
					s.winp.addstr(0,1, s.header.encode("utf-8"), nca)
			except:
				pass
			curses_unlock()

	def print_border(s):
		curses_lock()
		try:
			s.winp.border()
			if s.storage.engine.has_scroll():
				s._print_scrollbar_full()
				s._print_scrollbar()
		except:
			pass
		curses_unlock()

	def gen_wins(s, y, x, y_pos=0, x_pos=0):
		s.scroll_pos = 0
		s.x = x - 2
		s.y = y -  2 - 3
		s.cursor = " "*(s.x -1)

		curses_lock()
		try:
			s.winp = c.newwin(y, x, y_pos, x_pos)
			s.winp.bkgd(' ', ncargs(s.colors['border']))
		except:
			pass
		curses_unlock()

		s.print_border()

		curses_lock()
		try:
			s.panel = c.panel.new_panel(s.winp)
			s.win = s.winp.derwin(s.y, s.x, 1,  1 )
			s.winfo = s.winp.derwin(y-s.y-2, s.x, s.y+2,  1 )
			s.winp.addstr(s.y+1, 1, (unicode(config.bracelet_chars[0] + config.bracelet_chars[1]) *(x/2 - 1)).encode('utf-8'))
			if x%2 == 1:
				s.winp.addstr(s.y+1, x-2, config.bracelet_chars[0].encode('utf-8'))
				
			s.win.bkgd(' ', ncargs(s.colors['body']))
			s.win.keypad(True)
			s.winp.keypad(True)
			s.winfo.keypad(True)
		except:
			pass
		curses_unlock()

		s.is_info_blank = True
		s.engine.reshort( s.x - 3 )
		if s.yesno != None:
			s.yesno.gen_wins(s.win)
		if s.progress:
			s.progress.gen_wins(s.win)
		if not s.storage.is_empty() and s.pos:
			if s.pos - s.first_no >= s.y:
				s.first_no = s.pos - s.y + 1

	def print_playlist_rules(shuffle_flag, repeat_flag):

		curses_lock()
		try:
			s.winp.hline(s.y+1, 1, '+', 2)
		except:
			pass
		curses_unlock()

		if shuffle_flag:
			pass
		else:
			pass
	def show(s):

		curses_lock()
		try:
			s.panel.top()
			c.panel.update_panels()
		except:
			pass
		curses_unlock()

		if s.yesno != None:
			s.yesno.draw()

		curses_lock()
		try:
			c.doupdate()
		except:
			pass
		curses_unlock()

	def hide(s):
		curses_lock()
		try:
			c.panel.update_panels()
			c.doupdate()
		except:
			pass
		curses_unlock()

	def del_wins(s):
		if s.progress:
			s.progress.del_wins()

		if s.yesno != None:
			s.yesno.del_wins(True)
		if s.inputline:
			s.inputline.win = None
			del s.inputine
			s.inputine = None
		del s.winp
		del s.win
		del s.winfo
		del s.panel
		s.panel = None
		s.winp = None
		s.win  = None
		s.winfo = None

	def improved_input_line(s, offset, value):
		s.inputline = InputLine(s.win, s.cursor_pos, offset + 2, s.x, value, 0, len(value), ncargs(s.colors['panel inputline']), ncargs(s.colors['panel inputline cursor']))
		rc = s.inputline.edit_line()
		if rc == "enter":
			ret = s.inputline.before + s.inputline.after
		else:
			ret = None

		del s.inputline
		s.inputline = None

		curses_lock()
		try:
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		return ret

	def input_line(s, propname, defval):
		curses_lock()
		try:
			s.winfo.addstr(0, 0, propname.encode('utf-8'))
		except:
			pass
		curses_unlock()

		s.inputline = InputLine(s.winfo, 0, len(propname), s.x, defval, 0, len(defval), ncargs(s.colors['panel inputline']), ncargs(s.colors['panel inputline cursor']))
		rc = s.inputline.edit_line()
		if rc == "enter":
			value = s.inputline.before + s.inputline.after
		else:
			value = None

		s.inputline = None

		curses_lock()
		try:
			s.winfo.addstr(0, 0, u' '*len(propname))
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		return value

	def rename(s, basename):
		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'Rename: '.encode('utf-8'))
		except:
			pass
		curses_unlock()

		s.inputline = InputLine(s.winfo, 0, 8, s.x, basename, 0, len(basename), ncargs(s.colors['panel inputline']), ncargs(s.colors['panel inputline cursor']))
		rc = s.inputline.edit_line()
		if rc == "enter":
			location = s.inputline.before + s.inputline.after
		else:
			location = None

		s.inputline = None

		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'       '.encode('utf-8'))
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		return location

	def cmd_add(s, link):

		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'add: '.encode('utf-8'))
		except:
			pass
		curses_unlock()

		s.inputline = InputLine(s.winfo, 0, 4, s.x, link, 0, len(link), ncargs(s.colors['panel inputline']), ncargs(s.colors['panel inputline cursor']))
		rc = s.inputline.edit_line()
		if rc == "enter":
			location = s.inputline.before + s.inputline.after
		else:
			location = None

		s.inputline = None

		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'    '.encode('utf-8'))
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		return location
	def _get_center_coords(s):
		height = s.y 
		middle = height/2
		cursor_no = s.first_no + s.cursor_pos
		first_no = max( 0, cursor_no - middle )
		if s.storage.nol - first_no < height:
			first_no = max(0, s.storage.nol - height )

		cursor_pos = cursor_no - first_no
		return first_no, cursor_pos

	def _get_top_coords(s):
		height = s.y
		cursor_no = s.first_no + s.cursor_pos
		first_no = cursor_no
		if s.storage.nol - cursor_no < height:
			first_no = max(0, s.storage.nol - height)
		cursor_pos = cursor_no - first_no
		return first_no, cursor_pos

	def _get_bottom_coords(s):
		height = s.y
		cursor_no = s.first_no + s.cursor_pos
		first_no = max( 0, cursor_no - height + 1 )
		cursor_pos = cursor_no - first_no
		return first_no, cursor_pos

	def center(s):
		if s.yesno != None:
			return
		s.first_no, s.cursor_pos = s._get_center_coords()

	def cursor_center(s, auto=True):
		if s.yesno != None:
			return
		coords = ( s.first_no, s.cursor_pos )
		top_coords = s._get_top_coords()
		bottom_coords = s._get_bottom_coords()
		center_coords = s._get_center_coords()
		if coords == center_coords:
			coords = top_coords if center_coords != top_coords else bottom_coords
		elif coords == top_coords:
			coords = bottom_coords if bottom_coords != top_coords else center_coords
		else:
			coords = center_coords

		if (s.first_no, s.cursor_pos) == coords:
			return
		s.first_no, s.cursor_pos = coords
		s.redraw()
		s.refresh()

	def cd(s, path):
		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'CD: '.encode('utf-8'))
		except:
			pass
		curses_unlock()

		s.inputline = InputLine(s.winfo, 0, 4, s.x, path, 0, len(path), ncargs(s.colors['panel inputline']), ncargs(s.colors['panel inputline cursor']))
		rc = s.inputline.edit_line()
		if rc == "enter":
			location = s.inputline.before + s.inputline.after
		else:
			location = None

		s.inputline = None

		curses_lock()
		try:
			s.winfo.addstr(0, 0, u'    '.encode('utf-8'))
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		return location

	def fast_search(s):
		na = ncargs(s.colors['fast search'])

		curses_lock()
		try:
			s.winfo.addstr(0,0, " "*s.x, na)
			s.winfo.refresh()
		except:
			pass
		curses_unlock()

		input_str = ""
		unistr = u""
		prev_no = None
		rc = []
		while True:
			try:
				key = s.win.getch()
			except:
				return
			if key == 10:
				break
			elif key in [c.KEY_BACKSPACE, 127]:
				unistr = unistr[:-1]
			elif key in [c.KEY_LEFT, c.KEY_RIGHT]:
				pass
			elif key in [c.KEY_UP, c.KEY_DOWN, c.KEY_PPAGE, c.KEY_NPAGE, c.KEY_HOME, c.KEY_END]:
				if rc and rc != [] and len(rc) > 1:
					if key == c.KEY_UP:
						if rc.index(no) != 0:
							no = rc[rc.index(no) - 1]
						else:
							no = rc[-1]
					elif key == c.KEY_DOWN:
						if no != rc[-1]:
							no = rc[rc.index(no) + 1]
						else:
							no = rc[0]
					elif key == c.KEY_PPAGE:
						lpage = 10
						if rc.index(no) > lpage:
							no = rc[rc.index(no) - lpage]
						else:
							no = rc[0]
					elif key == c.KEY_NPAGE:
						lpage = 10
						if rc.index(no) + lpage < len(rc):
							no = rc[rc.index(no) + lpage]
						else:
							no = rc[-1]
					elif key == c.KEY_HOME:
						no = rc[0]
					elif key == c.KEY_END:
						no = rc[-1]


					curses_lock()
					try:
						s.winfo.addstr(0, 0, unistr.encode('utf-8'), na)
						s.winfo.refresh()
					except:
						pass
					curses_unlock()

					s.select(no)
					prev_no = no
				continue
					
			
			elif key == 27:
				break
			else: 
				try:
					c.ungetch(key)
					key = s.win.getkey()
					input_str += key
					unistr += input_str.decode('utf-8')
					input_str = ""
				except:
					pass
			try:
				rc = s.engine.on_fast_search(unistr)
				if rc != []:
					if prev_no != None:
						if rc.count(prev_no) != 0:
							no = prev_no
						else:
							no = rc[0]
					else:
						no = rc[0]
				else:
					no = None

				curses_lock()
				try:
					s.winfo.addstr(0,0, " "*s.x, na )
				except:
					pass
				curses_unlock()

				if no != None:
					curses_lock()
					try:
						s.winfo.addstr(0, 0, unistr.encode('utf-8'), na)
						s.winfo.refresh()
					except:
						pass
					curses_unlock()

					s.select(no)
					prev_no = no
				else:
					curses_lock()
					try:
						s.winfo.addstr(0, 0, (u'!' + unistr).encode('utf-8'), na)
						s.winfo.refresh()
					except:
						pass
					curses_unlock()

			except:
				curses_lock()
				try:
					s.winfo.addstr(0, 0, (u'!' + unistr).encode('utf-8'), na)
					s.winfo.refresh()
				except:
					pass
				curses_unlock()

		curses_lock()
		try:
			s.winfo.addstr(0,0, " "*s.x)
			s.winfo.refresh()
		except:
			pass
		curses_unlock()


	def on_append(s):
		s.redraw()
		s.refresh()

	def on_change_track(s):
		s.redraw()
		s.refresh()
		
	def on_remove(s):
		if s.storage.nol == 0:
			s.on_fill()
			return
		if s.pos >= s.storage.nol:
			s.pos = s.storage.nol - 1
		s.select(s.pos)
		s.redraw()
		s.refresh()

	def on_fill(s):
		s.first_no = 0
		s.pos = 0
		s.cursor_pos =0
		if s.engine.visibility.is_set():
			s.redraw()
			s.refresh()

	def redraw(s):
		if not s.win:
			return
		curses_lock()
		try:
			s.win.erase()
		except:
			pass
		curses_unlock()

		if s.storage.is_empty():
			return
		if s.pos != s.first_no + s.cursor_pos:
			if s.pos < s.first_no:
				s.first_no = s.pos
			elif s.pos - s.first_no >= s.y:
				s.first_no = s.pos - s.y+1
				
		for i in range(0, min(s.y, s.storage.nol - s.first_no) ):
			l = s.storage.shorts[i + s.first_no]
			lm = s.storage.marked_elements[i + s.first_no]
			if s.pos - s.first_no == i:
				s.print_linecursor(i, l, lm)
				s.cursor_pos = i
			else:
				s.print_line(i, l, lm)

		s.print_playercursor()
		if s.yesno:
			s.yesno.draw()

		if s.progress:
			s.progress.redraw()

	def get_current_item_no(s):
		return s.pos

	def get_current_element(s):
		return s.storage.elements[s.pos]		

	def refresh(s):
		if s.engine.visibility.is_set():

			curses_lock()
			try:
				s.winp.noutrefresh()
				s.win.noutrefresh()
				s.winfo.noutrefresh()
				if s.yesno != None:
					s.yesno.win.noutrefresh()
				c.doupdate()
			except:
				pass
			curses_unlock()

	def hide_playercursors(s):
		curses_lock()
		try:
			s.win.vline(0,0,' ', s.y)
		except:
			pass
		curses_unlock()

	def print_playercursor(s):
		for cursor in s.storage.cursors:
			y = cursor.pos - s.first_no
			if y >= 0 and y < s.y:
				pos = s.storage[cursor.pos].get('depth',0)*2

				curses_lock()
				try:
					if s.pos == cursor.pos:
						s.win.addstr( y, pos, cursor.image.encode('utf-8'), ncargs(s.colors['cursor and player']) )
					else:
						s.win.addstr( y, pos, cursor.image.encode('utf-8'), ncargs(s.colors['player']) )
				except:
					pass
				curses_unlock()


	def scroll_by_y(s, y):
		try:
			nol = s.storage.nol
			if nol:
				step = (nol)/float(s.y)
				pos = y*step 
				if pos > 0:
					if y + 1== s.y:
						s.select(s.storage.nol - 1)
					elif pos < s.storage.nol:
						s.select( int2(pos) )
				else:
					s.select( 0 )
		except:
			pass

	def _print_scrollbar_full(s):
		if s.storage.engine.has_scroll():

			s.winp.addstr( 1, 0, u'╿'.encode('utf-8'), ncargs(s.colors['scrollbar']) )
			s.winp.addstr( s.y, 0, u'╽'.encode('utf-8'), ncargs(s.colors['scrollbar']) )
			for y in range(2, s.y):
				s.winp.addstr( y, 0, u'│'.encode('utf-8'), ncargs(s.colors['scrollbar']) )
	def _touch_scroll(s, pos):
		if pos == 0 :
			ico = config.scroll_bar_chars[0].encode('utf-8')
		elif pos == s.y-1 :
			ico = config.scroll_bar_chars[1].encode('utf-8')
		elif pos < s.y and pos > 0:
			ico = config.scroll_bar_chars[2].encode('utf-8')
		else:
			return
		try:
			s.winp.addstr( pos + 1, 0, ico, ncargs(s.colors['scrollbar']) )
		except:
			pass

	def _print_scrollbar(s):
		try:
			if not s.storage.engine.has_scroll():
				return
			nol = s.storage.nol
			if nol:
				s._touch_scroll(s.scroll_pos)

				step = (nol)/float(s.y)
				s.scroll_pos = (s.pos)/step
				s.scroll_pos = int(s.scroll_pos)
				if s.scroll_pos < s.y and s.scroll_pos >= 0:
					s.winp.addstr( s.scroll_pos + 1, 0, config.scroll_bar_chars[3].encode('utf-8'), ncargs(s.colors['scrollbar cursor']) )
		except:
			pass
	
	def _short_to_string(s, value):
		if type(value[0]) == list:
			v = ''
			for x in value[0]:
				v += x
		else:
			v = value[0]
		return v
		
	def print_linecursor(s, y, value, marked):

		curses_lock()
		try:
			s._print_scrollbar()
			v = s._short_to_string(value)
			s.win.addstr( y, 0, s.cursor, ncargs(s.colors['cursor']) )
			if marked:
				s.win.addstr( y, 1, v, ncargs(s.colors['cursor and marker']) )
			else:
				s.win.addstr( y, 1, v, ncargs(s.colors['cursor']) )
			s.win.addch ( y, s.x - 1, ' ', ncargs(s.colors['cursor']) )
		except:
			pass
		curses_unlock()

		if s.is_cursor_hide:
			s.print_line(y, value, marked)

	def update_line(s,no):
		pos = s.first_no + no
		if pos >= s.storage.nol:
			return
		if pos == s.pos:
			s.print_linecursor(no, s.storage.shorts[pos], s.storage.marked_elements[pos])
		else:
			s.print_line(no, s.storage.shorts[pos], s.storage.marked_elements[pos])
		s.refresh()
	def print_line(s, y, value, marked):

		curses_lock()
		try:
			if marked:
				v = s._short_to_string(value)
				s.win.addstr( y, 1, v, ncargs(s.colors['marker']) )
			else:
				if type(value[0]) == list:
					n = 1
					s.win.addstr( y, 1, value[0][0], ncargs(s.colors[value[1][0]]) )
					for v in value[0][1:]:
						s.win.addstr(v, ncargs(s.colors[value[1][n]]) )
						n = (n+1)%2
				else:
					s.win.addstr( y, 1, value[0], ncargs(s.colors[value[1]]) )
			s.win.addch ( y, s.x - 1, ' ', ncargs(s.colors['body']) )
		except Exception,e:
			pass

		curses_unlock()

	def get_current_item(s):
		if s.pos != None and s.pos < s.storage.nol:
			return s.storage.elements[s.pos]

	def select(s, no):
		if no >= s.storage.nol:
			return
		s.pos = no
		s.first_no = max(no - s.y/2, 0)
		if s.first_no > 0 and s.storage.nol - s.first_no < s.y:
			s.first_no = max(0, s.storage.nol - s.y)
			
		s.redraw()
		s.refresh()

	def mmark(s, pos):
		s.storage.marked_elements[pos] = not s.storage.marked_elements[pos]
		if pos == s.pos:
			s.print_linecursor(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
		else:
			s.redraw()
		s.refresh()

	def mark(s, direction = 0):
		s.storage.marked_elements[s.pos] = not s.storage.marked_elements[s.pos]
		if direction:
			s.up()
		else:
			s.down()
		
	def hide_cursor(s):
		s.is_cursor_hide = True
		try:
			if not s.storage.is_empty():
				s.print_line(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
				s.print_playercursor()
				s.head()
				s.refresh()
		except:
			pass

	def show_cursor(s):
		s.is_cursor_hide = False
		try:
			if not s.storage.is_empty():
				s.print_linecursor(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
				s.print_playercursor()
				s.head()
				s.refresh()
		except:
			pass
	def up(s):
		if s.yesno != None:
			s.yesno.left()
			return
		if s.storage.is_empty():
			return
		elif s.pos == 0:
			pass
		elif s.cursor_pos != 0:
			#clear cursor
			s.hide_playercursors()

			curses_lock()
			try:
				s.win.addstr(s.cursor_pos, 0, s.cursor)
			except:
				pass
			curses_unlock()

			s.print_line(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])

			#decrease positions
			s.cursor_pos -= 1
			s.pos -= 1
			#draw cursor
			s.print_linecursor(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
			s.print_playercursor()
		else:
			#decrease positions
			if s.first_no - s.y/2 < 0:
				s.first_no = 0
			else:
				s.first_no -= s.y/2
			s.pos -= 1
			s.redraw()
		s.refresh()

	def home(s):
		if s.yesno != None:
			return

		if not s.storage.is_empty():
			s.cursor_pos = 0
			s.pos = 0
			s.first_no = 0
			s.redraw()
			s.refresh()
	
	def end(s):
		if s.yesno != None:
			return

		if not s.storage.is_empty():
			s.pos = s.storage.nol - 1
			s.first_no = max(0, s.storage.nol - s.y)
			s.redraw()
			s.refresh()

	def page_up(s):
		if s.yesno != None:
			return

		if not s.storage.is_empty():
			s.pos = max(0,  s.pos - s.y)
			s.first_no = max(0, s.first_no - s.y)
			s.redraw()
			s.refresh()

	def page_down(s):
		if s.yesno != None:
			return

		if not s.storage.is_empty():
			s.first_no = max(0, min(s.storage.nol - s.y, s.storage.nol - 1, s.first_no + s.y ))
			s.pos = max(0, min(s.storage.nol - 1,  s.pos + s.y))
			s.redraw()
			s.refresh()

	def on_resize(s):
		if not s.storage.is_empty() and s.pos:
			if s.pos - s.first_no >= s.y:
				s.first_no = s.pos - s.y + 1

	def down(s):
		if s.yesno != None:
			s.yesno.right()
			return

		if s.storage.is_empty():
			return
			s.first_no = max(0, min(s.storage.nol - s.y, s.storage.nol - 1, s.first_no + s.y ))
		nol = s.storage.nol
		if nol == s.pos + 1:
			#redraw cursor
			s.hide_playercursors()
			s.print_linecursor(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
			s.print_playercursor()

		elif s.cursor_pos + 2 <= s.y:
			#clear cursor
			s.hide_playercursors()

			curses_lock()
			try:
				s.win.addstr(s.cursor_pos, 0, s.cursor)
			except:
				pass
			curses_unlock()

			s.print_line(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
			#increase positions
			s.cursor_pos += 1
			s.pos += 1
			#draw cursor
			s.print_linecursor(s.cursor_pos, s.storage.shorts[s.pos], s.storage.marked_elements[s.pos])
			s.print_playercursor()
		else:
			#s.first_no += 1
			if s.first_no + 3*s.y/2 > nol:
				s.first_no = nol - s.y
			else:
				s.first_no += s.y/2
			s.pos += 1
			s.redraw()
		s.refresh()

