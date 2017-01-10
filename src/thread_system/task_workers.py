#!/usr/bin/python2.5
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

from Queue import Queue, Empty
from threading import Thread, Event
import time

IMMEDIATE_TASK  = 0
TIMED_TASK = 1
STOP_TASK_THREAD_TASK = 100
class Task:
	def __init__(s, ttype, fx=None, args=[], tm=None):
		s.ttype = ttype
		if ttype == STOP_TASK_THREAD_TASK:
			return
		
		s.fx = fx
		s.args = args
		s.tm = tm
	def execute(s):
		s.fx(*s.args)
		
class TaskWorkers:
	def __init__(s, num_worker_threads=3):
		s.tasks = Queue()
		s.death = Event()
		s.q = Queue()
		s.timed_tasks = []
		s.timeout = None
		s.nwt = num_worker_threads
		s.maint = Thread(target=s.main_thread)
		s.workers = map( lambda x: Thread(target=s.worker_thread, args=[x]), range(s.nwt) )
		s.maint.start()
		for t in s.workers:
			t.start()

	def __del__(s):
		try: s.exit()
		except: pass

	def exit(s):
		s.stop()
		try:
			del s.q
			del s.tasks
		except:
			pass

	def add_timed_task(s, fx, args, start_time=0, delay = None):
		s.add_task( TIMED_TASK, fx, args, start_time if not delay else time.time() + delay )

	def add_immediate_task(s, fx, args):
		s.add_task(IMMEDIATE_TASK, fx, args)

	def add_task(s, ttype, fx, args, tm = None):
		if not s.death.is_set():
			s.tasks.put( Task(ttype, fx, args, tm) )

	def stop(s):
		if not s.death.is_set():
			#send stop signal to the sheduler
			s.tasks.put( Task(STOP_TASK_THREAD_TASK, None, None, None) )
			s.death.set()
			s.maint.join()  #wait

	def main_thread(s): # Scheduler

		while True:
			try:
				task = s.tasks.get(timeout=s.timeout)
			except Empty:
				#timeout
				Tsk = s.timed_tasks[0]
				task = s.timed_tasks.pop(0)
				if time.time() >= task.tm:
					s.q.put(task)
				else:
					s.timed_tasks.insert(0, task)
					s.timed_tasks.sort( key = lambda t: t.tm, reverse=False)
			else:
				s.tasks.task_done()
				if task.ttype == STOP_TASK_THREAD_TASK:
					#stop all threads
					for stop_command in [Task(STOP_TASK_THREAD_TASK, None, None, None)]*s.nwt:
						s.q.put(stop_command)
					del s.timed_tasks
					break

				elif task.ttype == IMMEDIATE_TASK: # start now!
					s.q.put(task)

				elif task.ttype == TIMED_TASK:
					if time.time() >= task.tm:
						s.q.put(task)
					else:
						s.timed_tasks.append(task)
						s.timed_tasks.sort( key = lambda t: t.tm, reverse=False )

			s.timeout = None if not s.timed_tasks else max(0, s.timed_tasks[0].tm - time.time())


		#wait for jobs to complete
		for t in s.workers:
			t.join()

		#drop all tasks
		while not s.tasks.empty():
			s.tasks.get()
			s.tasks.task_done()

		while not s.q.empty():
			s.q.get()
			s.q.task_done()
		s.q.join()
		s.tasks.join()


	def worker_thread(s, n):
		while not s.death.is_set():
			task = s.q.get()
			if task.ttype == STOP_TASK_THREAD_TASK:
				s.q.task_done()
				break
			try:
				task.execute()
			except:
				pass
			s.q.task_done()

