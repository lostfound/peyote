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
import curses,curses.panel
import locale
from useful import get_id
from random import sample
from sorts import sortedT, sortedC


def element_to_line(elm):
    if type(elm) == unicode:
        return elm
    else: return u'unknown'

def line_to_short(line, length):
    return line[:length]    

class storage:
    event    = None
    line_to_short = line_to_short
    e_to_line= element_to_line
    length = 20
    def __init__(s, engine):
        s.elements = []
        s.shorts   = []
        s.types    = []
        s.nol       = 0
        s.marked_elements = []
        s.engine   = engine
        s.cursors  = []
    


    def current_element(s):
        try:
            return s.elements[s.engine.panel.pos]
        except:
            return None
    def search_keyval(s, k, v):
        if v==None:
            return -1
        for n,elm in enumerate( s.elements ):
            if elm.get(k, None) == v:
                return n
        return -1

                
    def is_empty(s):
        if s.elements == []:
            return True
        return False

    def get_enumerated_marked_elements(s):
        ret = []
        for mrk in enumerate(s.marked_elements):
            if mrk[1] == True:
                ret.append( ( mrk[0], s.elements[mrk[0]] ) )
        return ret

    def sort(s, sort_no = 0):
        #4 playlist
        if s.nol in [1,0,None]:
            return

        if s.cursors and s.cursors != []:
            s.cursors[0].pc.lock()

        shl = zip(s.elements, s.marked_elements, s.shorts, range(s.nol) )
        for e,sh in zip(s.elements, shl):
            e['temp'] = sh

        if sort_no == 0:
            shl = map(lambda x: x.pop('temp'), sortedT(s.elements, 2) )
        else:
            shl = map(lambda x: x.pop('temp'), sortedC(s.elements, 2)  )

        s.elements = map(lambda em: em[0], shl)
        s.marked_elements = map(lambda em: em[1], shl)
        s.shorts = map(lambda em: em[2], shl)
        cursors = list(s.cursors)

        pos = s.engine.panel.pos
        for n,f in enumerate(map(lambda em: em[3], shl)):
            if f == pos:
                s.engine.panel.pos = n
                pos = -1

            shooted=[]
            for cursor in cursors:
                if cursor.pos == f:
                    cursor.pos = n
                    shooted.append(cursor)
            for cursor in shooted:
                cursors.remove(cursor)

        if s.cursors and s.cursors != []:
            s.cursors[0].pc.unlock()
        if s.engine:
            s.engine.on_shuffle()

    def shuffle(s):
        #4 playlist
        if s.nol in [1,0,None]:
            return
        if s.cursors and s.cursors != []:
            s.cursors[0].pc.lock()

        shl = sample(zip(s.elements, s.marked_elements, s.shorts, range(s.nol) ), s.nol)
        s.elements = map(lambda em: em[0], shl)
        s.marked_elements = map(lambda em: em[1], shl)
        s.shorts = map(lambda em: em[2], shl)
        cursors = list(s.cursors)

        pos = s.engine.panel.pos
        for n,f in enumerate(map(lambda em: em[3], shl)):
            if f == pos:
                s.engine.panel.pos = n
                pos = -1

            shooted=[]
            for cursor in cursors:
                if cursor.pos == f:
                    cursor.pos = n
                    shooted.append(cursor)
            for cursor in shooted:
                cursors.remove(cursor)

        if s.cursors and s.cursors != []:
            s.cursors[0].pc.unlock()
        if s.engine:
            s.engine.on_shuffle()

    def get_marks(s):
        ret = []
        for n,mrk in enumerate(s.marked_elements):
            if mrk:
                ret.append(n)
        return ret

    def get_marked_elements(s):
        ret = []
        for mrk in enumerate(s.marked_elements):
            if mrk[1] == True:
                ret.append(s.elements[mrk[0]])
        return ret

    def pop_marked_elements(s):
        ret = []
        while s.marked_elements.count(True) != 0:
            no = s.marked_elements.index(True)
            ret.append(s.elements[no])
            s.marked_elements[no] = False
        return ret

    def get_storage_length(s):
        return s.nol

    def clear(s):
        del s.elements
        del s.shorts
        del s.types
        s.elements = []
        s.shorts   = []
        s.types    = []
        s.nol       = 0
        s.marked_elements = []
        for cursor in s.cursors:
            cursor.destroy()
        s.cursors = []


    def __getitem__(s, no):
        return s.elements[no]

    def reshort(s):
        del s.shorts
        s.shorts = []
        for elm in s.elements:
            s.shorts.append( s.engine.element_to_short( elm ) )
    def reshort_no(s, no):
        try:
            if no >=0 and no < s.nol:
                s.shorts[no] = s.engine.element_to_short( s.elements[no] )
        except:
            pass

    def disconnect_cursor(s, cursor):
        if s.cursors.count(cursor) != 0:
            s.cursors.remove(cursor)
            s.engine.panel.on_change_track()


    def insert(s, elements, after):
        pos = after+1
        update_pos = False
        for cursor in s.cursors:
            if cursor.pos > after:
                cursor.pos += len(elements)
                update_pos = True

        for elm in reversed(elements):
            short = s.engine.element_to_short( elm )
            s.elements.insert(pos, elm)
            s.shorts.insert(pos, short)
            s.marked_elements.insert(pos, False)
            s.nol+=1

        if update_pos:
            s.engine.panel.on_change_track()
            pass
    def fill(s, elements):
        s.clear()
        for elm in elements:
            s.elements.append(elm)
            s.shorts.append( s.engine.element_to_short( elm ) )
        s.nol = len(s.elements)
        s.marked_elements = [False]*s.nol
        if s.engine:
            s.engine.on_fill()
    
    def remove_marked(s):
        while s.marked_elements.count(True) != 0:
            no = s.marked_elements.index(True)
            s.shorts.pop(no)
            s.marked_elements.pop(no)
            s.elements.pop(no)
            s.nol -= 1
            s.when_remove(no)
        s.engine.panel.on_change_track()

    def remember_cursors(s):
        s.rcurs = [None, None]
        s.rpc = None
        for cursor in s.cursors:
            if cursor == cursor.pc.ctrack:
                n = 0
            else:
                n = 1
            s.rpc =  cursor.pc
            s.rcurs[n] = get_id(s.elements[cursor.pos])

    def restore_cursors(s):
        curs = s.rcurs
        rpc = s.rpc
        del s.rcurs
        del s.rpc
        if rpc:
            rpc.set_cursors(s, curs)

    def when_remove(s, no):
        update_pos = False
        destroyed = []
        for cursor in s.cursors:
            if cursor.pos > no:
                cursor.pos -= 1
            elif cursor.pos == no:
                if s.engine.type not in ['fs', 'radio']:
                    if cursor.get_type() == 0:
                        cursor.destroy()
                        destroyed.append(cursor)

                    elif cursor.pos == no and s.nol == no:
                        if no != 0:
                            cursor.pos -= 1
                        else:
                            cursor.destroy()
                            destroyed.append(cursor)
                else:
                    cursor.destroy()
                    destroyed.append(cursor)
                    
        for csr in destroyed:
            s.cursors.remove(csr)


    def pcursorup(s):
        s.engine.panel.on_change_track()

    def remove(s, no):
        if type(no) != int:
            return
        if no >= s.nol:
            return
        s.shorts.pop(no)
        s.marked_elements.pop(no)
        s.elements.pop(no)
        s.nol -= 1
        if s.event:
            s.event.on_remove()
        s.when_remove(no)
        s.engine.panel.on_change_track()


    def eq_imdown(s, pos):
        nol = s.nol
        for i in range(pos, s.nol):
            if type(s.elements[i]) in [dict, unicode, str]:
                nol = i
                break
        if pos + 1 == nol:
            return

        s.elements[pos].substitution( s.elements[pos+1] )

        for lst in [s.shorts, s.marked_elements]:
            lst.insert( pos + 1, lst.pop(pos) )

    def imdown(s,  pos):
        if pos + 1 == s.nol:
            return
        for lst in [s.elements, s.shorts, s.marked_elements]:
            lst.insert( pos + 1, lst.pop(pos) )
        update_pos = False

        for cursor in s.cursors:
            if cursor.pos == pos:
                cursor.pos += 1
                update_pos = True
            elif cursor.pos == pos + 1:
                cursor.pos -= 1

        if update_pos:
            s.engine.panel.on_change_track()


    def eq_imup(s, pos):
        if pos == 0:
            return

        s.elements[pos-1].substitution( s.elements[pos] )

        for lst in [s.shorts, s.marked_elements]:
            lst.insert( pos - 1, lst.pop(pos) )

        
    def imup(s,  pos):
        if pos == 0:
            return
        for lst in [s.elements, s.shorts, s.marked_elements]:
            lst.insert( pos - 1, lst.pop(pos) )

        update_pos = False

        for cursor in s.cursors:
            if cursor.pos == pos:
                cursor.pos -= 1
                update_pos = True
            elif cursor.pos == pos - 1:
                cursor.pos += 1
                update_pos = True

        if update_pos:
            s.engine.panel.on_change_track()
    def tmdown(s, pos):
        if pos == s.nol-1:
            return
        N = None
        depth = s.elements[pos].get('depth', 0)
        for n in range(pos+1, s.nol):
            if s.elements[n].get('depth', 0) <= depth:
                E = n - 1
                if not s.elements[n].get('opened'):
                    N = n
                    break
                else:
                    N = s.nol - 1
                    for i in range(n+1, s.nol):
                        if s.elements[i].get('depth', 0) <= depth:
                            N = i - 1
                            break
                break
        if N == None:
            return
        if s.elements[N].get('depth',0) < depth:
            return

        update_pos = False
        ret = pos
        posid = get_id(s.elements[pos])
        cursors = map( lambda cursor: get_id(s.elements[cursor.pos]), s.cursors)
        for lst in [s.elements, s.shorts, s.marked_elements]:
            for i in reversed(range(pos, E+1)):
                lst.insert( N, lst.pop(pos) )

        for i in range(pos, s.nol):
            if get_id(s.elements[i]) == posid:
                ret = i
                break
        for i in range(pos, s.nol):
            for j,cid in enumerate(cursors):
                if get_id(s.elements[i]) == cid:
                    try:
                        s.cursors[j].pos = i
                        update_pos = True
                    except:
                        pass
            
        if update_pos:
            s.engine.panel.on_change_track()
        return ret
    def tmup(s, pos):
        if pos == 0:
            return
        N = None
        depth = s.elements[pos].get('depth', 0)
        for n in reversed(range(0, pos)):
            if s.elements[n].get('depth', 0) == depth:
                N = n
                break
            elif s.elements[n].get('depth', 0) < depth:
                break
        if N == None:
            return
        E = s.nol - 1
        for n in range(pos+1, s.nol):
            if s.elements[n].get('depth', 0) <= depth:
                E = n - 1
                break

        update_pos = False
        ret = pos
        posid = get_id(s.elements[pos])
        cursors = map( lambda cursor: get_id(s.elements[cursor.pos]), s.cursors)
        for lst in [s.elements, s.shorts, s.marked_elements]:
            for i in  range(0, E + 1 - pos):
                lst.insert( N+i, lst.pop(pos+i) )

        for i in reversed(range(0, pos)):
            if get_id(s.elements[i]) == posid:
                ret = i
                break
        for i in reversed(range(0, E +1)):
            for j,cid in enumerate(cursors):
                if get_id(s.elements[i]) == cid:
                    try:
                        s.cursors[j].pos = i
                        update_pos = True
                    except:
                        pass
            
        if update_pos:
            s.engine.panel.on_change_track()
        return ret

    def treemove(s, pos, direction):
        rc = None
        M = s.marked_elements.count(True)
        if not M:
            if direction == 'down':
                rc = s.tmdown(pos)
            elif direction == 'up':
                rc = s.tmup(pos)
            if rc == None:
                return
                
            s.engine.down(rc)
        elif direction == 'up':
            for n in range(0,M):
                numbers = map (lambda y: y[0], filter(lambda x: True if x[1] else False, enumerate(s.marked_elements) ) )
                mpos = numbers[n]
                s.tmup(mpos)
        elif direction == 'down':
            for n in reversed(range(0,M)):
                numbers = map (lambda y: y[0], filter(lambda x: True if x[1] else False, enumerate(s.marked_elements) ) )
                mpos = numbers[n]
                s.tmdown(mpos)
                
                
        s.engine.panel.redraw()
        s.engine.panel.refresh()

    def move(s, pos, direction, eq=False):
        if s.marked_elements.count(True) != 0:
            numbers = map (lambda y: y[0], filter(lambda x: True if x[1] else False, enumerate(s.marked_elements) ) )
            if direction == "up":
                for no in numbers:
                    if not eq:
                        s.imup(no)
                    else:
                        s.eq_imup(no)
            elif direction == "down":
                numbers.reverse()
                for no in numbers:
                    if not eq:
                        s.imdown(no)
                    else:
                        s.eq_imdown(no)
            s.engine.on_move()
                    
        else:
            if direction == "up":
                if not eq:
                    s.imup(pos)
                else:
                    s.eq_imup(pos)
                s.engine.up()
            if direction == "down":
                if not eq:
                    s.imdown(pos)
                else:
                    s.eq_imdown(pos)
                s.engine.down()

    def append(s, elements):
        s.elements += elements
        for elm in elements:
            s.shorts.append( s.engine.element_to_short( elm ) )
            s.nol += 1
            s.marked_elements.append(False)
        if s.engine:
            s.engine.on_append()
        

