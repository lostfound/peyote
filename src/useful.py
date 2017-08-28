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


import urllib, os, gettext
import fs.auto

def nullreplace(string, char):
    replaced_string = string.replace(char, '')
    if replaced_string != '':
        return replaced_string
    return string

def time2str(sec):
    def int2(i):
        r = repr(i)
        if len(r)==1:
            return '0' + r
        else:
            return r
    if sec == None:
        return " --:--s "
    h = int(sec/3600)
    m2 = int(sec/60)
    m = m2%60
    s = int(sec)%60
    if h > 0:
        if m2 <100:
            return '%sm : %ss' % ( int2(m2), int2(s) )
        else:
            d = int(h/24)
            if d == 0:
                return '%sh : %sm' % ( int2(h), int2(m) )
            h = h%24
            return '%sd : %sh : %sm' % ( int2(d), int2(h), int2(m) )
    else:
        return '%sm : %ss' % ( int2(m), int2(s) )
def localise(s):
    return unicode2(gettext.lgettext(s))

get_id = lambda elm: elm.get('addr', elm.get('path', elm.get('name') ) )

def is_track(entry):
    if entry['type'] in ['file', 'cue', 'http', 'stream']:
        return True
    return False

def is_track2(entry):
    if is_track(entry):
        if not entry.get('cursed') and not entry.get('broken'):
            return True
    return False


def unicode2(s):
    if type(s) == str:
        return unicode(s.decode('utf-8'))
    elif type(s) == unicode:
        return s
    else:
        return unicode(s)

def quote(addr):
    if "%" not in addr:
        if type(addr) == str:
            try:
                return urllib.quote( unicode2(addr).encode('utf-8') )
            except:
                return urllib.quote(addr.encode('utf-8'))
        else:
            return urllib.quote(addr.encode('utf-8'))
    else:
        return addr
def quote_http(addr):
    try:
        serv, path = addr[7:].split('/',1)
    except:
        return unicode(addr)
    return 'http://' + os.path.join(serv, quote(path))

def get_human_readable(b):
    if b > 10737418240:
        _bytes = unicode(b//1073741824)
        scale = "GB"
    elif b > 10485760:
        _bytes = unicode(b//1048576)
        scale = "MB"
    elif b > 10240:
        _bytes = unicode(b//1024)
        scale = "KB"
    else:
        _bytes = unicode(b)
        scale = "B"
    return unicode(_bytes) + ' ' + scale

def compare_names(a, b):
    A = a.lower().split()
    B = b.lower().split()

    for i in range(A.count('the')):
        A.remove('the')

    for i in range(B.count('the')):
        B.remove('the')
    
    return  A == B

def unquote_uri(uri):
    uri_spl = uri.split('%')
    if uri_spl <= 1:
        return uri
    for x in uri_spl[1:]:
        try:
            x[:2].decode('hex')
        except:
            return uri
    return unicode2(urllib.unquote(uri.encode('utf-8')))

def quote_uri(location, parent=None):
    native_addr = location
    spl_addr = native_addr.rsplit('://',1)
    postfix = u""

    if len(spl_addr) == 1:
        prefix = u""
        addr = spl_addr[0]
    else:
        prefix = spl_addr[0] + u'://'
        addr = spl_addr[1]

    if 'cue://' in prefix.lower() and '#' in addr:
        addr,postfix = addr.rsplit('#')
        postfix = u"#" + postfix

    addr = unicode2(addr)
    if 'http://' in prefix.lower():
        addr_spl = addr.split('/',1)
        if len(addr_spl) == 1:
            server = addr
            addr = ""
        else:
            addr =addr_spl[1]
            server = addr_spl[0] + '/'
        addr = prefix + server + quote(addr.encode('utf-8')) + postfix
    elif parent:
        prefix = prefix.lower().replace('file://', '')
        addr = prefix + quote(fs.auto.relative(parent, addr)) + postfix
    else:
        addr = prefix + quote(addr.encode('utf-8')) + postfix

    return addr

