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

from useful import localise
from sets import config
from sorts import sorted2, sortedZ
_ = localise
ARTIST_KEY = 0
DEFAULT_KEY = -1
ALBUM_KEY = 1
TITLE_KEY = 2
DEPTH_KEY = 3
ISFAKE_KEY = 4
CHILDREN_KEY = 5
def create_eqtag(depth = 0, artist = None, album = None, title = None, isfake = False ):
    ret = {'type' : 'eq_tag'}
    ret[ARTIST_KEY] = artist
    ret[DEPTH_KEY] = depth
    ret[ALBUM_KEY] = album
    ret[TITLE_KEY] = title
    ret[CHILDREN_KEY] = []
    ret[ISFAKE_KEY] = isfake
    return ret
class EqTagsTree:
    tags = []
    tree = {}
    def __init__(s):
        s.update_tree()


    def _upalbum(s, artist, album, isfake = False):
        ab = s.tree.get(artist, None)
        if ab:
            for aa in ab[CHILDREN_KEY]:
                if aa[ALBUM_KEY] == album:
                    return aa
            ab[CHILDREN_KEY].append(create_eqtag(ALBUM_KEY, artist, album, isfake=isfake) )
        else:
            ab = create_eqtag( ARTIST_KEY, artist, isfake = True)
            ab[CHILDREN_KEY].append( create_eqtag(ALBUM_KEY, artist, album, isfake=isfake) )
            s.tree[artist] = ab

        return ab[CHILDREN_KEY][-1]
        
    def update_tree(s):
        s.tree = {}
        s.tags = []
        for artist in config.equalizer_artists.keys():
            s.tree[artist] = create_eqtag(ARTIST_KEY, artist)

        for artist,album in config.equalizer_albums.keys():
            s._upalbum(artist, album)

        for artist,album,title in config.equalizer_songs.keys():
            ab = s._upalbum(artist, album, isfake=True)
            ab[CHILDREN_KEY].append( create_eqtag(TITLE_KEY, artist, album, title ) )

        if config.equalizer_default:
            s.tags.append( create_eqtag(-1) )
        for artist in map( lambda name: s.tree[name], sorted2( s.tree.keys() ) ):
            s.tags.append(artist)
            artist[CHILDREN_KEY] = sortedZ(artist[CHILDREN_KEY], [ALBUM_KEY])
            for album in artist[CHILDREN_KEY]:
                s.tags.append(album)
                album[CHILDREN_KEY] = sortedZ(album[CHILDREN_KEY], [TITLE_KEY])
                for title in album[CHILDREN_KEY]:
                    s.tags.append(title)
        
    
class PEqualizer:
    def equalizer_init(s, showtags = False):
        s.tree = EqTagsTree()
        s.eq_track = s.callback.get_current_track()
        s.callback.subscribe(s.on_eq_next_track)
        s.eq_show_tags = showtags
        s.load_equalizer(2)

    def eq_switch_tagshowing(s):
        s.eq_show_tags = not s.eq_show_tags
        s.load_equalizer()

    def delete(s):
        elm = s.storage[s.panel.pos]
        if type(elm) == dict:
            if not elm[ISFAKE_KEY]:
                try:
                    if elm[DEPTH_KEY] == DEFAULT_KEY:
                        config.equalizer_default = None
                    elif elm[DEPTH_KEY] == ARTIST_KEY:
                        del config.equalizer_artists[ elm[ARTIST_KEY] ]
                    elif elm[DEPTH_KEY] == ALBUM_KEY:
                        del config.equalizer_albums[ ( elm[ARTIST_KEY], elm[ALBUM_KEY] ) ]
                    elif elm[DEPTH_KEY] == TITLE_KEY:
                        del config.equalizer_songs[ ( elm[ARTIST_KEY], elm[ALBUM_KEY], elm[TITLE_KEY] ) ]
                    config.SaveEqualizers()
                except:
                    pass
                s.tree.update_tree()
                s.load_equalizer(1)
    def load_equalizer(s, m=0):
        try:
            elm = s.storage[s.panel.pos]
            if type( elm ) != dict:
                del elm
                pos = s.panel.pos
            elif m == 1:
                elm[ISFAKE_KEY] = True
                for i in reversed(range(s.panel.pos)):
                    if type(s.storage[i]) == dict and not s.storage[i][ISFAKE_KEY]:
                        eelm = s.storage[i]
                        break
                    else:
                        eelm = s.storage[i]
                        break
        except:
            pass

        s.storage.fill(s.callback.get_equalizer().bands)
        if s.eq_show_tags:
            s.storage.append(s.tree.tags)
        if m == 2:
            return
        try:
            epos = s.storage.elements.index(elm)
            if epos > 0:
                s.panel.select(epos)
            elif not s.eq_show_tags:
                s.panel.select(s.storage.nol - 1 )
        except:
            if m == 1:
                try:
                    epos = s.storage.elements.index(eelm)
                    if epos > 0:
                        s.panel.select(epos)
                        return
                except:
                    pass
            try:
                if pos < s.storage.nol:
                    if type(s.storage[pos]) != dict:
                        s.panel.select(pos)
                
            except:
                if not s.eq_show_tags:
                    s.panel.select(s.storage.nol - 1 )
        

        
    def mark(s, mode=0):
        #mutex is needed
        if mode == 0:
            pos = s.panel.pos
            elm = s.storage[s.panel.pos]
            if type(elm) != dict:
                s.storage.marked_elements[pos] = not s.storage.marked_elements[pos]
                s.panel.redraw()
                s.panel.refresh()
        elif mode==1:
            for i in range(s.storage.nol):
                if type(s.storage[i]) in [unicode, str, dict]:
                    break
                s.storage.marked_elements[i] = not s.storage.marked_elements[i]

            s.panel.redraw()
            s.panel.refresh()


    def enter(s):
        elm = s.storage[s.panel.pos]
        if type( elm ) == dict:
            if not elm[ISFAKE_KEY]:
                eq = s.callback.get_equalizer() 
                if elm[DEPTH_KEY] == ARTIST_KEY:
                    eq.Load( config.equalizer_artists[elm[ARTIST_KEY]] )
                    s.load_equalizer()
                elif elm[DEPTH_KEY] == ALBUM_KEY:
                    eq.Load( config.equalizer_albums[( elm[ARTIST_KEY], elm[ALBUM_KEY] )] )
                    s.load_equalizer()
                elif elm[DEPTH_KEY] == TITLE_KEY:
                    eq.Load( config.equalizer_songs[( elm[ARTIST_KEY], elm[ALBUM_KEY], elm[TITLE_KEY] )] )
                    s.load_equalizer()
                elif elm[DEPTH_KEY] == DEFAULT_KEY:
                    eq.Load( config.equalizer_default )
                    s.load_equalizer()


    def equalizer_tags(s):
        s.storage.append(s.tree.tags)

    def equalizer_deinit(s):
        s.callback.unsubscribe(s.on_eq_next_track)

    def on_eq_next_track(s, track, equalizer):
        s.eq_track = track
        s.load_equalizer()
    
    def save_equalizer(s):
        s.equalizer_for_saving = ( s.storage[0].parent.Save(), s.eq_track )
        s.panel.run_yesno(_(" save equalizer "), [_("Select a target"),  ""], 
            [_("<Default>"), _("<Artist>"), _("<Album>"), _("<Song>"), _("<Nothing>")])
        s.question = True
        s.cmd = "save"
    def set_gain(s, gain):
        if  s.storage.marked_elements.count(True) != 0:
            for i in range(s.storage.nol):
                if s.storage.marked_elements[i]:
                    s.storage[i].set_gain(gain)
                    s.storage.reshort_no(i)
        else:
            s.storage[s.panel.pos].set_gain(gain)
            s.storage.reshort_no(s.panel.pos)
        s.panel.redraw()
        s.panel.refresh()
        pass

    def mouse_select(s, y, x):
        try:
            pos = s.panel.first_no + y
            if pos >= s.storage.nol:
                return

            if s.storage[pos].coord:
                start, l = s.storage[pos].coord
                p = 36./(l-1)
                xpos = x - start - 1
                if x < start:
                    return
                gain = xpos*p-24
                v = (gain*10//4)/10.
                gain =v*4
                s.storage[pos].set_gain(gain)
                s.storage.reshort_no(pos)
                s.panel.update_line(y)
        except:
            pass
        else:
            return True
        
    def resize_equalizer(s):
        nb = s.panel.input_line("Num-bands [3,64]:", "33")
        try:
            numbands = int(nb)
        except:
            return
        if numbands < 3 or numbands > 64:
            return
        eq = s.callback.get_equalizer()
        eq.generate_bands(numbands)
        s.load_equalizer()
    
    def equalizer_aftermove(s):
        s.storage.reshort()
        s.panel.redraw()
        s.panel.refresh()

    def right(s):
        if s.storage.marked_elements.count(True) != 0:
            for i in range(s.storage.nol):
                if s.storage.marked_elements[i]:
                    s.storage[i].increase(0.4)
        else:
            if type(s.storage[s.panel.pos]) == dict:
                s.enter()
                return
            s.storage[s.panel.pos].increase( 0.4 )

        s.storage.reshort()
        s.panel.redraw()
        s.panel.refresh()
    def left(s):
        if s.storage.marked_elements.count(True) != 0:
            for i in range(s.storage.nol):
                if s.storage.marked_elements[i]:
                    s.storage[i].increase(-0.4)
        else:
            s.storage[s.panel.pos].increase( -0.4 )
        s.storage.reshort()
        s.panel.redraw()
        s.panel.refresh()
    def question_enter(s):
        if s.cmd == "save":
            rc = s.panel.yesno.enter()
            s.panel.yesno = None
            s.panel.redraw()
            s.panel.refresh()
            s.question = False
            if rc == 4:
                del s.equalizer_for_saving
                return
            config.OnSaveEqualizer(s.equalizer_for_saving[0], s.equalizer_for_saving[1], rc)
            s.tree.update_tree()
            s.load_equalizer()
            del s.equalizer_for_saving
            return

