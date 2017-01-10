from __future__ import with_statement
import sys,os
from subprocess import Popen
from stat import S_IXOTH, S_IROTH, S_IXGRP, S_IRGRP, S_IRWXU

envnames = ['datarootdir', 'libdir', 'prefix', 'bindir', 'localedir', 'exec_prefix', 'version', 'Xterminal', 'PYTHON']
envirements = {}

def improved_getenv(env_name):
	env_value = os.getenv(env_name)
	if "${" in env_value and "}" in env_value:
		subenv_pos = env_value.find("${")+2
		subenv_len = env_value[subenv_pos:].find('}')
		subenv=improved_getenv(env_value[subenv_pos:][:subenv_len])
		env_value= "".join([env_value[:subenv_pos -2],subenv, env_value[subenv_pos+subenv_len+1:]])
	return env_value
		
for env_name in envnames:
	envirements[env_name] = improved_getenv(env_name)

peyote_py="src/peyote.py"
sets_py="src/sets.py"
def PatchSource(src_file, sp, dp ):
	sys.stdout.write(sys.argv[0] + ": patching " + src_file + " ")
	with open(src_file, "r") as f:
		code=f.readlines()

	sys.stdout.write("..")

	with open(src_file, "w") as f:
		for l in code:
			for SP,DP in zip(sp,dp):
				if l.startswith(SP):
					f.write(DP + '"\n')
					break
			else:
				f.write(l)

	sys.stdout.write("..")
	sys.stdout.write(" done\n")

def PatchSources():
	PatchSource(peyote_py, ["LOCALE_DIR"], ['LOCALE_DIR="' + envirements['localedir']])
	PatchSource(sets_py, ["SHARE_DIR", "DEFAULT_TERMINAL"], [
		'SHARE_DIR="' + os.path.join( envirements['datarootdir'], 'peyote'),
		'DEFAULT_TERMINAL="' + envirements['Xterminal']])

def CreateDesktopFiles():
	deskfile = "data/peyote.desktop"
	desk_template = "peyote.desktop.tmpl"

	sys.stdout.write(sys.argv[0] + ": creating " + deskfile + " ")

	with open(desk_template, "r") as f:
		desk_template=f.readlines()

	sys.stdout.write("..")

	with open(deskfile, "w") as f:
		f.write('[Desktop Entry]')
		f.write('\nVersion=')
		f.write(envirements['version'])
		f.write('\nExec=')
		f.write(envirements['bindir'] + '/xpeyote\n')
		for line in desk_template:
			f.write(line)

	sys.stdout.write("..")
	sys.stdout.write(" done\n")

	deskfile = "data/mescaline.desktop"
	desk_template = "mescaline.desktop.tmpl"

	sys.stdout.write(sys.argv[0] + ": creating " + deskfile + " ")

	with open(desk_template, "r") as f:
		desk_template=f.readlines()

	sys.stdout.write("..")

	with open(deskfile, "w") as f:
		f.write('[Desktop Entry]')
		f.write('\nVersion=')
		f.write(envirements['version'])
		f.write('\nExec=')
		f.write(envirements['PYTHON'] + ' ' + envirements['libdir'] + '/peyote/' + 'mescaline.py %F\n')
		for line in desk_template:
			f.write(line)

	sys.stdout.write("..")
	sys.stdout.write(" done\n")

peyote_bin = "scripts/peyote"
xpeyote_bin = "scripts/xpeyote"
mescaline_bin = "scripts/mescaline"

def CreateBinFiles():
	sys.stdout.write(sys.argv[0] + ": creating " + peyote_bin + " ")
	with open(peyote_bin, "w") as f:
		f.write('#!/bin/sh\n')
		f.write(envirements['PYTHON'] + ' ' + envirements['libdir'] + '/peyote/' + 'peyote.py $@ 2> /dev/null\n')
	sys.stdout.write("..")
	os.chmod(peyote_bin, S_IXOTH | S_IROTH | S_IXGRP | S_IRGRP | S_IRWXU)
	sys.stdout.write(".. done\n")

	sys.stdout.write(sys.argv[0] + ": creating " + mescaline_bin + " ")
	with open(mescaline_bin, "w") as f:
		f.write('#!/bin/sh\n')
		f.write(envirements['PYTHON'] + ' ' + envirements['libdir'] + '/peyote/' + 'mescaline.py $@\n')
	sys.stdout.write("..")
	os.chmod(mescaline_bin, S_IXOTH | S_IROTH | S_IXGRP | S_IRGRP | S_IRWXU)
	sys.stdout.write(".. done\n")

	sys.stdout.write(sys.argv[0] + ": creating " + xpeyote_bin + " ")
	with open(xpeyote_bin, "w") as f:
		f.write("""#!/bin/sh
PEYOTE_BIN="%s $*"
TERMX=""
test -f ~/.config/peyote/terminal.conf && . ~/.config/peyote/terminal.conf
test -z "$TERMX" && TERMX="%s"
$TERMX""" % ( os.path.join(envirements['bindir'], 'peyote'), envirements['Xterminal'].replace('"', '\\"').replace('%peyote', '${PEYOTE_BIN}') ) ) 
	sys.stdout.write("..")
	os.chmod(xpeyote_bin, S_IXOTH | S_IROTH | S_IXGRP | S_IRGRP | S_IRWXU)
	sys.stdout.write(".. done\n")

def CreateGmo():
	for lng in ['ru', 'pl']:
		po = 'po/%s.po' %lng
		gmo= 'po/%s.gmo' % lng
		sys.stdout.write(sys.argv[0] + ": creating " + gmo + " ")
		try:
			Popen( ['msgfmt', po, '-o', gmo ] ).wait()
		except:
			sys.stdout.write(".. fail\n")
		else:
			sys.stdout.write(".. done\n")

PatchSources()
CreateDesktopFiles()
CreateBinFiles()
CreateGmo()

print ""
print "*"*57
print "Installation:"
print "  Bin dir       = ", envirements['bindir']
print "  Locale dir    = ", envirements['localedir']
print "  Peyote dir    = ", envirements['libdir'] + "/peyote"
print "  Peyote skins  = ", envirements['datarootdir'] + '/peyote/skins'
print "  Python path   = ", envirements['PYTHON']
print "  Terminal      = ", envirements['Xterminal']
print "*"*57


