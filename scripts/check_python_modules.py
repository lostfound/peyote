#!/usr/bin/python

import sys

#configure: error: no suitable Python interpreter found
out = sys.stdout
err = sys.stderr

def print_fail_message(module_name, it_is_error=True):
	global out,err
	urls = {
		'mutagen' : 'http://code.google.com/p/mutagen/downloads/list'
		,'pygst' : 'http://gstreamer.freedesktop.org/modules/gst-python.html'
		,'pygobject' : 'http://www.pygtk.org/downloads.html'
		,'pyinotify' : 'https://github.com/seb-m/pyinotify/downloads'
		,'dbus-python' : 'http://www.freedesktop.org/wiki/Software/DBusBindings'
		,'pylast' : 'http://code.google.com/p/pylast/'
	 	}
	out.write("none\n")
	if it_is_error:
		err.write('configure: error: ' + module_name + ' not found!\n')
		err.write('  Please, install the ' + module_name + ' first. \n')
	else:
		err.write('configure: warning: ' + module_name + ' not found!!!\n\n')
		err.write("  It's be good if you could install %s\n" % module_name)
	if urls.has_key(module_name):
		err.write('  You can download the latest ' + module_name + ' sources directly\n  from "' + urls[module_name] + '"\n')
	if not it_is_error:
		err.write('\n')
		import time
		time.sleep(1.7)
	
	
try:
	out.write("checking for mutagen...")
	import mutagen
except:
	print_fail_message('mutagen')
	sys.exit(1)
else:
	out.write('yes\n')


try:
	out.write("checking for pygst...")
	import pygst
	if len(sys.argv) == 1 or sys.argv[1]=="yes":
		import gst
except:
	print_fail_message('pygst')
	sys.exit(1)
else:
	if len(sys.argv) == 1 or sys.argv[1]=="yes":
		for elm in ["autoaudiosink", "fakesink", "queue2", 'volume', "audioconvert", "playbin2", "equalizer-nbands"]:
			out.write(".")
			try:
				gst.element_factory_make( elm )
			except:
				out.write("no\n")
				err.write("'configure: error: " +  elm + " not found!\n")
				err.write("  Please, install the gstreamer0.10-plugins-* packages" )
	else:
		pass

	out.write('yes\n')

try:
	out.write("checking for pygobject...")
	import gobject
except:
	print_fail_message('pygobject')
	sys.exit(1)
else:
	out.write('yes\n')

try:
	out.write("checking for dbus python bindings...")
	import dbus
except:
	print_fail_message('dbus-python')
	sys.exit(1)
else:
	out.write('yes\n')
try:
	out.write("checking for pyinotify...")
	import pyinotify
except:
	print_fail_message('pyinotify', it_is_error=False)
else:
	out.write('yes\n')

