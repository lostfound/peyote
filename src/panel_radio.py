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

from useful import unicode2, localise
from sets import config
from icecast import ShoutCast, Icecast, IcecastSearch
P_NAME = 'name'
P_TYPE = 'type'
P_STATUS = 'status'
P_DEPTH = 'depth'

_ = localise

class PRadio:
    def radio_init(s):
        s.radio_shoutcast = ShoutCast(1)
        s.radio_icecast = Icecast()
        s.icesearch = IcecastSearch()
        elements = []
        elements.append( {P_TYPE : 'submenu', P_STATUS : 0, 'name' : 'ShoutCast', 'menu-type' : 'shoutcast', P_DEPTH : 0} )
        elements.append( {P_TYPE : 'submenu', P_STATUS : 0, 'name' : 'IceCast', 'menu-type' : 'icecast', P_DEPTH : 0} )
        s.storage.fill( elements )

    def radio_deinit(s):
        del s.radio_shoutcast
        del s.radio_icecast
    
    def thread_shoutcast_show_more(s, item):
        s.busy.set()
        try:
            N = len( item['owner'].get('stations', []) )
            s.panel.process.print_text_message(_("Wait for a minute"))
            s.radio_shoutcast.receive_stations(item['owner'], s.panel.process, True)
            s.storage.insert(item['owner']['stations'][N:], s.panel.pos - 1)
        except Exception,e:
            pass
        try:
            s.print_info()
        except: pass
        try:
            s.panel.redraw()
            s.panel.refresh()
        except: pass
        s.busy.clear()
        
    def thread_shoutcast_receive_stations(s, item):
        s.busy.set()
        try:
            s.panel.process.print_text_message(_("Wait for a minute"))
            s.radio_shoutcast.receive_stations(item, s.panel.process)
            sm = {      P_TYPE : 'option'
                , 'name' : _('show more')
                , 'value' : ""
                , 'button-type' : 'shoutcast:show_more'
                , P_DEPTH : item[P_DEPTH] + 1
                , 'owner' : item
                }
            s.storage.insert(item['stations'] + [sm], s.panel.pos)
        except Exception, e:
            pass
        try:
            s.print_info()
        except: pass
        try:
            s.panel.redraw()
            s.panel.refresh()
        except: pass
        s.busy.clear()

    def thread_icecast_search_stations(s, item, more = 0):
        s.busy.set()
        sm = {      P_TYPE : 'option'
            , 'name' : _('show more')
            , 'value' : ""
            , 'button-type' : 'icecast:show_more'
            , P_DEPTH : item[P_DEPTH] + 1
            }
        try:
            s.panel.process.print_text_message(_("Wait for a minute"))
            if not more:
                stations = s.icesearch.search(item['value'], s.panel.process )
                s.storage.insert([sm], s.panel.pos)
                s.storage.insert(stations, s.panel.pos)
            else:
                more = s.icesearch.show_more(s.panel.process)
                s.storage.insert(more, s.panel.pos-1)
        except:
            pass
        try:
            s.print_info()
        except: pass
        try:
            s.panel.redraw()
            s.panel.refresh()
        except: pass
        s.busy.clear()

    def thread_shoutcast_search_stations(s, item):
        s.busy.set()
        try:
            s.panel.process.print_text_message(_("Wait for a minute"))
            s.radio_shoutcast.search_stations(item, s.panel.process )
            s.storage.insert(item['stations'], s.panel.pos)
        except:
            pass
        try:
            s.print_info()
        except: pass
        try:
            s.panel.redraw()
            s.panel.refresh()
        except: pass
        s.busy.clear()

    def thread_shoutcast_get_genres(s):
        s.busy.set()
        try:
            s.panel.process.print_text_message(_("Wait for a minute"))
            s.radio_shoutcast.receive_genres(s.panel.process)
            s.storage.insert(s.radio_shoutcast.genres, s.panel.pos)
            s.storage.insert( [{
                        P_TYPE : 'submenu'
                        , P_STATUS : 0
                        , P_DEPTH : 1
                        , 'name' : _('Search')
                        , 'value' : ""
                        , 'menu-type' : 'shoutcast:search'
                      }], s.panel.pos  )
        except:
            pass
        try:
            s.print_info()
        except: pass
        try:
            s.panel.redraw()
            s.panel.refresh()
        except: pass
        s.busy.clear()

    def radio_left(s):
        item = s.storage[s.panel.pos]
        if item[P_TYPE] == 'submenu' and item[P_STATUS] == 1:
            s.enter()
        elif item.get(P_DEPTH, 0) == 0 or s.panel.pos == 0:
            s.cd('locations://')
        else:
            D = item.get(P_DEPTH, 0)
            for pos in reversed( range(0, s.panel.pos) ):
                if D > s.storage[pos].get(P_DEPTH, 0):
                    break
            s.panel.pos = pos
            s.panel.redraw()
            s.panel.refresh()

    def radio_right(s):
        item = s.storage[s.panel.pos]
        if item[P_TYPE] == 'submenu' and item[P_STATUS] == 0:
            s.enter()
        elif item[P_TYPE] == 'submenu':
            D = item.get(P_DEPTH, 0)
            for pos in range(s.panel.pos + 1, s.storage.nol):
                if D >= s.storage[pos].get(P_DEPTH, 0):
                    break
            try:
                s.panel.pos = pos
                s.panel.redraw()
                s.panel.refresh()
            except:
                pass
        
    def enter(s):
        item = s.storage[s.panel.pos]
        if item[P_TYPE] == 'submenu' and item[P_STATUS] == 0:
            item[P_STATUS] = 1
            s.storage.reshort_no(s.panel.pos)
            if item['menu-type'] == 'shoutcast':
                if s.radio_shoutcast.check_genres():
                    s.storage.insert(s.radio_shoutcast.genres, s.panel.pos)
                    s.storage.insert( [{
                                P_TYPE : 'submenu'
                                , P_STATUS : 0
                                , P_DEPTH : 1
                                , 'name' : _('Search')
                                , 'value' : ""
                                , 'stations' : []
                                , 'menu-type' : 'shoutcast:search'
                              }], s.panel.pos  )
                    s.panel.redraw()
                    s.panel.refresh()
                else:
                    s.AddTask(s.thread_shoutcast_get_genres(), [])
            elif item['menu-type'] == 'icecast':
                s.radio_icecast.reload()
                item['tags'] = []
                for g in sorted(s.radio_icecast.gtree.keys()):
                    try:
                        tag = {      P_TYPE   : 'submenu'
                            , P_STATUS : 0
                            , P_DEPTH  : 1
                            , 'name'  : unicode2(g)
                            , 'stations' : s.radio_icecast.gtree[g]
                            , 'menu-type' : 'icecast:tag'
                            }
                    except:
                        continue
                    for stn in tag['stations']:
                        stn[P_DEPTH] = 2
                    item['tags'].append(tag)
                s.storage.insert(item['tags'], s.panel.pos)
                s.storage.insert( [{
                            P_TYPE : 'submenu'
                            , P_STATUS : 0
                            , P_DEPTH : 1
                            , 'name' : _('Search')
                            , 'value' : ""
                            , 'stations' : []
                            , 'menu-type' : 'icecast:search'
                          }], s.panel.pos  )
                s.panel.redraw()
                s.panel.refresh()
            elif item['menu-type'] == 'icecast:tag':
                s.storage.insert(item['stations'], s.panel.pos)
                s.panel.redraw()
                s.panel.refresh()
                    
            elif item['menu-type'] == 'genre':
                if item.get('children',[]) != []:
                    s.storage.insert(item['children'], s.panel.pos)
                elif item.get('stations',[]) != []:
                    sm = {      P_TYPE : 'option'
                        , 'name' : _('Show more')
                        , 'value' : ""
                        , 'button-type' : 'shoutcast:show_more'
                        , P_DEPTH : item[P_DEPTH] + 1
                        , 'owner' : item
                        }
                    s.storage.insert(item['stations'] + [sm], s.panel.pos)
                else:
                    s.stop_thread_flag = False
                    s.AddTask(s.thread_shoutcast_receive_stations, [item] )
                    return
                s.panel.redraw()
                s.panel.refresh()
            elif item['menu-type'] == 'shoutcast:search':
                offset = len(item[P_NAME]) +  item[P_DEPTH]*2 + 3
                param = item['value']
                if param == "":
                    param = u"The Beatles"
                new_param = s.panel.improved_input_line( offset, param)
                if not new_param:
                    item[P_STATUS] = 0
                    s.panel.show_cursor()
                    return
                try:
                    new_param = unicode2(new_param).rstrip().lstrip()
                except:
                    s.panel.redraw()
                    s.panel.refresh()
                    return
                if new_param == "":
                    s.panel.redraw()
                    s.panel.refresh()
                else:
                    item['value'] = new_param
                    s.storage.reshort_no(s.panel.pos)
                    s.panel.redraw()
                    s.panel.refresh()
                    s.AddTask(s.thread_shoutcast_search_stations, [item] )

            elif item['menu-type'] == 'icecast:search':
                offset = len(item[P_NAME]) +  item[P_DEPTH]*2 + 3
                param = item['value']
                if param == "":
                    param = u"Rock"
                new_param = s.panel.improved_input_line( offset, param)
                if not new_param:
                    item[P_STATUS] = 0
                    s.panel.show_cursor()
                    return
                try:
                    new_param = unicode2(new_param).rstrip().lstrip()
                except:
                    s.panel.redraw()
                    s.panel.refresh()
                    return
                if new_param == "":
                    s.panel.redraw()
                    s.panel.refresh()
                else:
                    item['value'] = new_param
                    s.storage.reshort_no(s.panel.pos)
                    s.panel.redraw()
                    s.panel.refresh()
                    s.AddTask(s.thread_icecast_search_stations, [item] )


        elif item[P_TYPE] == 'submenu' and item[P_STATUS] == 1:
            s.radio_hide_submenu(s.panel.pos)

        elif item[P_TYPE] == 'option': #show more
            if item['button-type'] == 'shoutcast:show_more':
                s.AddTask(s.thread_shoutcast_show_more, [item])

            elif item['button-type']  == 'icecast:show_more':
                s.AddTask(s.thread_icecast_search_stations, [item,1] )

        elif item[P_TYPE] == 'stream': # play_radio_now
            s.callback.play_track(item)

    def radio_hide_submenu(s,pos):
        current_entry = s.storage[pos]
        if current_entry[P_TYPE] == 'submenu' and current_entry[P_STATUS] == 1:
            current_entry[P_STATUS] = 0
            while pos + 1 < s.storage.nol:
                entry = s.storage[ pos + 1 ]
                if current_entry[P_DEPTH] >= entry[P_DEPTH]:
                    break
                s.storage.remove(pos + 1)

            s.storage.reshort_no(pos)
            s.panel.redraw()
            s.panel.refresh()



