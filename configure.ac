AC_PREREQ([2.67])

AC_INIT([peyote], [0.9.11], [platonny at ngs.ru])
AC_PROG_INSTALL
AM_INIT_AUTOMAKE([1.8])

AC_CONFIG_SRCDIR([src/pygsthack.c])
AC_CONFIG_HEADERS([config.h])

default_xterminal="urxvt +sb -sh 30 -fadecolor gray -fade 5 -tint gray -tr -fg white -fn xft:monospace:size=10 -geometry 100x42 -e %peyote"
AC_ARG_WITH([terminal],
            [AC_HELP_STRING([--with-terminal=STRING],
                            [Peyote execution string. Used by bin/xpeyote.
			     default: "urxvt ...some options.. %peyote"])],
            [XTERMINAL_STRING="$withval"],
            [XTERMINAL_STRING="$default_xterminal"])
AC_SUBST([XTERMINAL_STRING])
RC=`echo "$XTERMINAL_STRING" | grep %peyote`
if test "$RC" == "" ; then
	echo "Error: the --with-terminal option must contain the word %peyote"
	exit 1
fi

# Checks for programs.
#LT_INIT
#AC_PROG_CC
#AC_PROG_LIBTOOL

AM_PATH_PYTHON([2.6])
if test "$PYTHON" = ":"; then
	AC_MSG_ERROR([Python not found])
fi
if test "`scripts/get_major_version $PYTHON_VERSION`"  != "2" ; then
	AC_MSG_ERROR(
[Peyote requires 2.6 <= python-$PYTHON_VERSION < 3
if You have this version of python, then try to type 'PYTHON=/path/to/python ./configure'
])
fi
AC_ARG_ENABLE(gst-plugins-check,[  --disable-gst-plugins-check   (default enabled)], [gstplugins="no"], [gstplugins="yes"])
dnl a macro to check for ability to create python extensions
dnl dnl  AM_CHECK_PYTHON_HEADERS([ACTION-IF-POSSIBLE], [ACTION-IF-NOT-POSSIBLE])
dnl dnl function also defines PYTHON_INCLUDES
#AC_DEFUN([AM_CHECK_PYTHON_HEADERS],
# [AC_REQUIRE([AM_PATH_PYTHON])
# AC_MSG_CHECKING(for headers required to compile python extensions)
# dnl deduce PYTHON_INCLUDES
# py_prefix=`$PYTHON -c "import sys; print sys.prefix"`
# py_exec_prefix=`$PYTHON -c "import sys; print sys.exec_prefix"`
# PYTHON_INCLUDES="-I${py_prefix}/include/python${PYTHON_VERSION}"
# if test "$py_prefix" != "$py_exec_prefix"; then
#  PYTHON_INCLUDES="$PYTHON_INCLUDES -I${py_exec_prefix}/include/python${PYTHON_VERSION}"
# fi
# AC_SUBST(PYTHON_INCLUDES)
# dnl check if the headers exist:
# save_CPPFLAGS="$CPPFLAGS"
# CPPFLAGS="$CPPFLAGS $PYTHON_INCLUDES"
# AC_TRY_CPP([#include <Python.h>],dnl
#   [AC_MSG_RESULT(found)
#   $1],dnl
#   [AC_MSG_RESULT(not found)
#   $2])
#   CPPFLAGS="$save_CPPFLAGS"
#   ])
#AM_CHECK_PYTHON_HEADERS([build_python_plugin="yes"], [build_python_plugin="no"] )
#if test "$build_python_plugin" != "yes"; then
#	AC_MSG_ERROR(Python.h is required)
#fi


if ! $PYTHON scripts/check_python_modules.py "$gstplugins"; then
	AC_MSG_ERROR(Shit happens)
fi
#PKG_CHECK_MODULES([pygobject], [pygobject-2.0])
PKG_CHECK_MODULES([gstreamer], [gstreamer-1.0])

AC_CHECK_PROGS([UPDATE_DESKTOP_DATABASE],[update-desktop-database],:)
AC_CHECK_PROGS([UPDATE_MENUS],[update-menus],:)

AC_CONFIG_FILES([Makefile src/Makefile po/Makefile.in data/Makefile data/icons/Makefile])

AM_PO_SUBDIRS()

DESKDIR=/usr/share/applications
ICONSDIR=/usr/share/icons
AC_SUBST(SRCDIR)
AC_SUBST(ICONSDIR)
AC_SUBST(DESKDIR)


peyotedir=${libdir}/peyote
AC_SUBST(peyotedir)

AC_OUTPUT
datarootdir=${datarootdir} \
libdir=${libdir} \
prefix=${prefix} \
bindir=${bindir} \
localedir=${localedir} \
exec_prefix=${exec_prefix} \
version=${VERSION} \
Xterminal=${XTERMINAL_STRING} \
PYTHON=${PYTHON} \
${PYTHON} scripts/config.py

exit

