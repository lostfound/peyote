#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from useful import unicode2
import codecs
import traceback
df = codecs.open(os.path.join(os.getenv('HOME'), '.local', 'share', 'peyote', 'debug'), 'w', 'utf-8' )
def trace():
    traceback.print_exc(file=df)
def debug(*args):
        if __name__ == '__main__':
            s = u""
            for p in args:
                s += repr(p) + ' '
            print s
        else:
            global df
            if not df:
                return
            s = u""
            for p in args:
                if type(p) in [ unicode, str ]:
                    s += unicode2(p) + ' '
                else:
                    s += repr(p) + ' '
            df.write(s+'\n')
            df.flush()
