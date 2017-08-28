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

from Queue import Queue, Empty, Full
from threading import Thread, Semaphore, Event
import time

class WorkerThread():
	def __init__(s, p):
		s.p = p
		s.q = Queue(1)
		rt = Semaphore(0)
		Thread(target=s.run, args = [rt] ).start()
		rt.acquire()

	def add_task( s, fx, args = [], Q=None ):
		try:
			s.q.put([ fx, args ], False)
		except Full:
			return False
		if Q: # Register thread if it is new
			Q.put(s)

		return True
		
	def run(s, rt):
		rt.release()
		while True:
			task = s.q.get()

			if not task:
				s.q.task_done()
				break

			if not s.p.death.is_set():
				try:
					task[0](*task[1])
				except:
					pass
			s.q.task_done()
			if not s.p.death.is_set():
				s.p.q.put(s)
		try:
			s.q.get(False)
		except:
			pass
		else:
			s.q.task_done()
		s.q.join()
		del s.q
			
	
class ThreadPolls:
	def __init__( s ):
		s.q = Queue()    # Idle threads
		s.allq = Queue() # All threads
		s.death = Event()

	def Run(s, fx, args = []):
		if s.death.is_set():
			return

		try:
			thrd = s.q.get( False )
		except Empty: #Create thread for this task
			WorkerThread(s).add_task(fx, args, s.allq )
		else: #There is idle thread
			s.q.task_done()
			thrd.add_task(fx, args )

	def exit(s): #Stop all threads
		s.death.set()
		while not s.allq.empty():
			trd = s.allq.get()
			s.allq.task_done()
			try:
				trd.q.put(None)
			except:
				pass
		while not s.q.empty():
			s.q.get()
			s.q.task_done()
		s.q.join()
		s.allq.join()
		del s.allq
		del s.q
			
			

polls = ThreadPolls()

