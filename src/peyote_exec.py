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

from __future__ import with_statement
import os.path
from subprocess import Popen, PIPE
from Queue import Queue
from sets import config
import shlex

devnull = open(os.path.devnull, 'w')
q = Queue()

def stop():
    while not q.empty():
        q.get()
        q.task_done()
    q.join()

def check_programs():
    programs = []
    while not q.empty():
        program = q.get()
        if program.poll() == None:
            programs.append(program)
        q.task_done()
    for program in programs:
        q.put(program)
    return True

#def get_shell_child(pid):
#    prc = Popen([u"ps", "-ejH"], stdout = PIPE, shell=True)
#    lines = prc.stdout.readlines()
#    prc.wait()
#    del prc
#    is_child=False
#    for line in lines[1:]:
#        line_split = line.split()
#        if is_child:
#            return(int(line_split[0]))
#        elif int(line_split[0]) == pid:
#            is_child = True

def _check_pwd(pwd):
    if pwd and os.path.exists(pwd):
        return pwd
    return None

def execute_command(command, pwd=None):
    try:
        exc = Popen(command, stdout = devnull, stderr = devnull, stdin = PIPE,  shell=True, cwd = _check_pwd(pwd) )
    except:
        pass
    else:
        return exc

def background(command, pwd=None):
    global q
    p = execute_command( command, pwd )
    if p != None:
        q.put(p)

def execute(elm, pwd=None):
    cmd = None
    if elm['type'] == 'fsfile':
        if not elm.has_key('ext') or elm['ext'] == None:
            return
        ext = elm['ext'].lower()
        for exts,command in config.prefered_applications:
            if ext in exts:
                cmd = map( lambda s: s.decode('utf-8').replace('%file', elm['path']), shlex.split(command.encode('utf-8')) )
                break

        if cmd:
            try:
                exc = Popen(cmd, stdout = devnull, stderr = devnull, cwd = _check_pwd(pwd) )
                q.put(exc)
            except:
                pass


