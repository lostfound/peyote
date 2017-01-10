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

from subprocess import Popen, PIPE
from useful import unicode2, is_track, localise
from sorts import sorted2
import gettext, os
import gst,shlex
from sets import config, EncoderProfile, SongPrinter
from gobject import list_properties
from curses import COLOR_WHITE
from player import lastfm
from vk import GET_TOKEN

#  ** List of Classes **
#
#  BaseItem
#  Menu
#  Option
#  AddOption
#  BasePropertiesMenu
#   BasePropertyOption
#  CharsetOption
#  ISO8859Option
#  HideKeybarOption
#  cdnoOption
#  DefPlsOption
#  TerminalOption
#  AudioExtensionsMenu
#   AudioExtensionOption
#  TitleFormatMainMenu
#   TitleFormatMenu
#    TitleFormatOption
#  AudioPlayerMenu
#   +BaseAudioFiltersMenu
#   +AudioFilterHelper:
#   AudioPlayerRestartOption
#   AudioSinkMenu
#    AudioSinkOption
#    AudioSinkPropertiesMenu
#    AudioSinkPropertiesMenu2
#    AudioSinkPropertyOption
#   AudioFiltersMenu
#    +BaseAudioFilterMenu
#      AudioFilterStatusOption
#      AudioFilterOption
#   CrossfadeMenu
#    CrossfadeTimeOption
#    CrossfadeStatusOption
#  EncodersMenu
#   EncoderProfileMenu
#    EncoderNameOption
#    EncoderTagOption
#    EncoderPathOption
#    EncoderAudioFiltersMenu
#    EncoderEncoderMenu
#     EncoderEncoderNameOption
#     EncoderEncoderPropertiesMenu
#    EncoderMuxerMenu
#    EncoderMuxerNameOption
#    EncoderMuxerPropertiesMenu
#  PreferedApplicationsMenu
#   PreferedApplicationMenu
#    ApplicationOption
#    ExtensionOption
#  MixerMenu
#   MixerCurrentMixerOption
#    MixerOption
#   MixerPropsMenu
#    MixerPropOpt
#  AppearanceMenu
#   CurrentSkinOption
#   RenameSkinOption
#   IconsMenu
#   IconsDefaultsOption
#    IconsOption
#   CurrentSongMenu
#    CurrentSongOpt
#   PaletteMenu
#    ColorMenu
#     RGBOption
#    ColorName
#  ColorsMenu
#   ColorsSectionMenu
#   ColorsItemMenu
#    ItemBGOption
#    ItemFGOption
#    ItemBoldOption
#  AliasesMenu
#   TAliasesMenu
#    AliasOpt
#   AliasUsingMenu
#    AliasUsingOption
#  ShoutcastMenu
#   ShoutcastResults
#   ShoutcastSort
#  NotificationMenu
#   NotificationOption
#   DoNotifyOption
#  XspfMenu
#   XspfOpeningMenu
#   XspfSavingMenu
#    XspfOption
#  LastfmMenu
#   LastfmScrobblingOption
#   LastfmRadioScrobblingOption
#   LastfmUserOption
#   LastfmPassOption
#  AutopanelOption
#  AutopanelWidthOption
#  VpaleveMenu  
#   VpaleveToken
#  PConfig:




try:
    import pylast
except:
    pylast = None

_ = localise

P_NAME = 0
P_TYPE = 1
P_DEPTH= 2
P_VALUE= 3
P_STATUS=4
P_ICON = 5

EP_GETSTR      = 0x01
EP_NEW         = 0x02
EP_SWITCHP     = 0x04
EP_SELECT      = 0x08
EP_SWITCH      = 0x10
EP_RESHORTP    = 0x20
EP_REOPENP     = 0x40
EP_RESHORTN    = 0x80
class BaseItem:
    def __init__(s, name, depth):
        s.name = name
        s.depth = depth
        s.delable = False
        s.fakedel = False
        s.value = ''
        s.aux = u''

    def __getitem__(s, n):
        if n in ['name', P_NAME]:
            return s.get_name()

        if n in ['depth', P_DEPTH]:
            return s.depth

        if n in ['value', P_VALUE]:
            return s.get_value()

    def has_key(s, k):
        if k in ['value', P_VALUE]:
            if s.get_value():
                return True
            return False
        if k in ['name', P_NAME, 'type', P_TYPE, 'depth', P_DEPTH, 'value', P_VALUE]:
            return True
        return False
    
    def is_delable(s):
        return s.delable

    def get_name(s):
        return s.name
    def get_aux(s):
        return s.aux

class Menu (BaseItem):
    def __init__(s, name, depth):
        BaseItem.__init__(s, name, depth)
        s.menu_status = 0
        s.value = None


    def __getitem__(s, n):
        if n in ['type', P_TYPE]:
            return 'submenu'

        if n in ['status', P_STATUS]:
            return s.menu_status
        return BaseItem.__getitem__(s,n)

    def children(s):
        return []
    
    def __setitem__(s, k, v):
        if k in ['status', P_STATUS]:
            s.menu_status = v
    def get_value(s):
        return s.value

    def has_key(s, k):
        if k in ['status', P_STATUS]:
            return True
        return BaseItem.has_key(s, k)

    
class Option(BaseItem):
    def __init__(s, name, depth):
        BaseItem.__init__(s, name, depth)
        s.icon = config.config_chars[2]
        s.ep = EP_SWITCH
        s.offset = None
        s.process_it_anyway = False
    
    def __getitem__(s, n):
        if n in ['type', P_TYPE]:
            return 'option'

        if n in ['icon', P_ICON]:
            return s.get_icon()
        return BaseItem.__getitem__(s,n)
    def has_key(s, k):
        if k == 'icon':
            return True
        return BaseItem.has_key(s, k)

    def get_icon(s):
        return s.icon
    def get_value(s):
        return s.value
    
    def enter_policy(s):
        return s.ep

    def get_param(s):
        return s.get_value()
    
    def switch(s):
        pass

class BasePropertiesMenu(Menu):
    def __init__(s, depth):
        Menu.__init__(s, _(u'properties'), depth)

    def get_gst_plugin_name(s):
        return "pitch"
    def get_gst_plugin_params(s):
        return []
    def set_gst_plugin_params(s, v):
        pass

    def children(s):
        if s.get_gst_plugin_name() == None:
            return []
        elms = map ( lambda x: BasePropertyOption(x[0], x[1], s), s.get_gst_plugin_params() )
        elms.append( AddOption(_('[new]'), s.depth + 1, s) )
        return elms

    def get_new_param(s):
        return _get_any_property( s.get_gst_plugin_name(), map ( lambda x: x[0], s.get_gst_plugin_params() ) )

    def add_param(s, param):
        prm = _str_to_property(s.get_gst_plugin_name(), param)
        if not prm:
            return

        if prm[0] in map(lambda e: e[0], s.get_gst_plugin_params() ):
            return
        lst = s.get_gst_plugin_params()
        lst.append(prm)
        s.set_gst_plugin_params(lst)

        config.Save()
        return BasePropertyOption(prm[0], prm[1], s)

class BasePropertyOption(Option):
    def __init__(s, prm, val, parent):
        Option.__init__(s, None, parent.depth + 1 )
        s.ep = EP_GETSTR
        s.sprm = prm
        s.val = val
        s.offset = s.depth*2+1
        s.delable = True
        s.parent = parent
    
    def get_param(s):
        ret = '%s=' % s.sprm
        if type ( s.val ) == str:
            ret += s.val
        else:
            ret += repr(s.val)
        return ret

    def set_param(s, param):
        prm = _str_to_property(s.parent.get_gst_plugin_name(), param)
        if not prm:
            return
        if prm[0] != s.sprm:
            if prm[0] in map(lambda e: e[0], s.parent.get_gst_plugin_params()):
                return
        index = map(lambda e: e[0], s.parent.get_gst_plugin_params() ).index( s.sprm )
        s.parent.get_gst_plugin_params()[index] = prm
        s.sprm, s.val = prm
        config.Save()
    
    def on_delete(s):
        index = map(lambda e: e[0], s.parent.get_gst_plugin_params() ).index( s.sprm )
        lst = s.parent.get_gst_plugin_params()
        lst.pop(index)
        s.parent.set_gst_plugin_params(lst)
        config.Save()
        return True

    def get_name(s):
        return s.sprm
    def get_value(s):
        if type ( s.val ) == str:
            return s.val
        return repr(s.val)

#CHARSETS
class CharsetOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'secondary charset encoding'), 0)
        s.ep = EP_GETSTR

    def get_value(s):
        return config.secondary_encoding
    def set_param(s, param):
        try:
            param = str(param)
        except:
            return
        if _test_encoding(param):
            config.secondary_encoding = param
            config.Save()

class ISO8859Option(Option):
    def __init__(s):
        Option.__init__(s, _(u'iso8859-1 charset detection'), 0)
        if config.iso8859detection:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]

    def switch(s):
        config.iso8859detection = not config.iso8859detection
        config.Save()
        if config.iso8859detection:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]
    def get_value(s):
        return s.icon

    def get_aux(s):
        return _(u'It is useful for Russian users')

class HideKeybarOption(Option):
    def __init__(s, callback):
        Option.__init__(s, _('hide keybar'), 0)
        s.callback = callback
        if config.hide_keybar:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]

    def switch(s):
        config.hide_keybar = not config.hide_keybar
        config.Save()
        if config.hide_keybar:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]
        s.callback.redraw()

    def get_value(s):
        return s.icon

class cdnoOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'remove a disc number from an album name'), 0)
        if config.remove_cdno_from_album_name:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]

    def switch(s):
        config.remove_cdno_from_album_name = not config.remove_cdno_from_album_name
        config.Save()
        if config.remove_cdno_from_album_name:
            s.icon = config.config_chars[0]
        else:
            s.icon = config.config_chars[1]

    def get_value(s):
        return s.icon

class DefPlsOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'default playlist'), 0 )
        s.ep = EP_GETSTR

    def set_param(s, param):
        if _test_playlist(param):
            config.default_playlist = param
            config.Save()

    def get_value(s):
        return config.default_playlist

class TerminalOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'terminal'), 0)
        s.ep = EP_GETSTR
        s.value = unicode2(config.GetTerminal())
        s.delable = True
        s.fakedel = True

    def set_param(s, param):
        if not u"%peyote" in param:
            return
        config.SaveTerminal(param)
        s.value = config.GetTerminal()

    def get_aux(s):
        return _(u'hint: press DEL to reset to default')
    
    def on_delete(s):
        config.ResetTerminal()
        s.value = unicode2(config.GetTerminal())
        return False

        


class AddOption(Option):
    def __init__(s, name, depth, parent_menu, aux=u''):
        Option.__init__(s, name, depth)
        s.parent = parent_menu
        s.ep = EP_NEW
        s.value = ''
        s.aux = aux

    def get_param(s):
        return s.parent.get_new_param()
    def add_param(s, param):
        return s.parent.add_param(param)

class AudioExtensionsMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'audio extensions'), 0)
    def children(s):
        entries = map (lambda ext: AudioExtensionOption(ext), config.audio_extensions[0])
        entries += map (lambda ext: AudioExtensionOption(ext), config.audio_extensions[1])
        entries += map (lambda ext: AudioExtensionOption(ext), config.audio_extensions[2])
        entries.append(AddOption(_('[new]'), 1, s))
        return entries
    def get_new_param(s):
        return 'ext'

    def add_param(s, ext):
        if not ext:
            return None
        if ext in config.GetAudioExtensions() or ext in ['m3u', 'pls', 'cue', 'ext']:
            return None
        ext = ext.lower()
        
        config.audio_extensions[2].append(ext)
        config.audio_extensions[2].sort()
        config.Save()
        return AudioExtensionOption(ext)

        

class AudioExtensionOption(Option):
    def __init__(s, ext):
        Option.__init__(s, ext, 1 )
        s.icons = [ u'☺', u'⚖', u'☠', u'○' ]
        s.delable = True
    def get_category(s):
        for i in range(3):
            if s.name in config.audio_extensions[i]:
                return i
        return 3
        
    def get_icon(s):
        return s.icons[s.get_category()]

    def switch(s):
        n = s.get_category()
        if n == 3:
            return
        config.audio_extensions[n].remove(s.name)
        n = (n+1)%3
        config.audio_extensions[n].append(s.name)
        config.audio_extensions[n].sort()
        config.Save()
    def on_delete(s):
        n = s.get_category()
        if n != 3:
            config.audio_extensions[n].remove(s.name)
            config.Save()
        return True
#TITLE FORMAT
TF_PLAYLIST = 0
TF_FS       = 1
class TitleFormatMainMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'song title formats'), 0)
    def children(s):
        return [TitleFormatMenu(TF_PLAYLIST), TitleFormatMenu(TF_FS) ]

class TitleFormatMenu(Menu):
    def __init__(s, tp):
        s.tp = tp
        if s.tp == TF_PLAYLIST:
            Menu.__init__(s, _(u'playlist'), 1)
        else:
            Menu.__init__(s, _(u'file system'), 1) 

    def get_formats(s):
        if s.tp == TF_PLAYLIST:
            return config.playlist_title_formats
        elif s.tp == TF_FS:
            return config.fs_title_formats
    def children(s):
        s.cldr =  map( lambda no: TitleFormatOption(s.tp, no, s), 
                   range( len(s.get_formats()) )
                 )
        aux = u'status,cue,id,cdno,bitrate,sample_rate,channels,artist,album,title,basename,filename,file,ext,time,c1,c2,color1,color2'
        return s.cldr + [ AddOption(_('[new]'), 2, s, aux) ]

    def get_new_param(s):
        if s.tp == TF_PLAYLIST:
            return 'status,title|artist,date,album,time'
        return 'status,cue,id,title|artist,date,album,time'

    def add_param(s, param):
        try:
            param = str(param)
        except:
            return
        if not param:
            return None
        if '|' in param:
            fmt = tuple ( map( lambda p: s.convert_spart(p), param.split('|') ) )
        else:
            fmt = ( s.convert_spart(param), [] )
        s.get_formats().append(fmt)
        s.cldr.append( TitleFormatOption( s.tp, len(s.cldr), s ) )
        config.Save()
        return s.cldr[-1]
    def delete(s,no):
        if len(s.cldr) <= 1:
            return False
        for child in s.cldr[no:]:
            child.no -= 1
        del s.cldr[no]
        s.get_formats().pop(no)
        config.Save()
        return True

    def convert_spart(s, part):
        return filter( None, map( lambda c: c.strip().rstrip(), part.split(',') ) )

class TitleFormatOption(Option):
    def __init__(s, tp, no, parent):
        s.tp = tp
        s.no = no
        s.parent = parent
        fmt = s.get_format()
        Option.__init__(s, s.convert_part( fmt[0] ), 2 )
        s.value = s.convert_part( fmt[1] )
        s.delable = True
        s.ep = EP_GETSTR
        s.offset = 2*2 + 1

    def get_aux(s):
        return u'status,cue,id,cdno,bitrate,sample_rate,channels,artist,album,title,basename,filename,file,ext,time,c1,c2,color1,color2'
    
    def get_format(s):
        if s.tp == TF_PLAYLIST:
            return config.playlist_title_formats[s.no]
        elif s.tp == TF_FS:
            return config.fs_title_formats[s.no]

    def convert_part(s, part):
        l = len(part)
        if l == 0:
            return ''
        elif l == 1:
            return part[0]
        else:
            return reduce(lambda x,y: "%s,%s" % (x,y), part)

    def convert_spart(s, part):
        return filter( None, map( lambda c: c.strip().rstrip(), part.split(',') ) )

    def set_param(s, param):
        try:
            param = str(param)
        except:
            return

        fmt = s.get_format()
        if '|' in param:
            fmt = tuple ( map( lambda p: s.convert_spart(p), param.split('|') ) )
        else:
            fmt = ( s.convert_spart(param), [] )
        s.name, s.value = map( lambda p: s.convert_part(p), fmt )
        if s.tp == TF_PLAYLIST:
            config.playlist_title_formats[s.no] = fmt
        else:
            config.fs_title_formats[s.no] = fmt
        config.Save()

    def get_param(s):
        return reduce(lambda l,r: '%s|%s' % (s.convert_part(l), s.convert_part(r)),
                  s.get_format() 
                 )
    def on_delete(s):
        return  s.parent.delete(s.no) 

class AudioPlayerMenu(Menu):
    def __init__(s, player):
        Menu.__init__(s, _(u'audio player'), 0)
        s.player = player
    def children(s):
        return [AudioSinkMenu(), CrossfadeMenu(), AudioFiltersMenu(), AudioPlayerRestartOption(s.player)]

class AudioPlayerRestartOption(Option):
    def __init__(s, player):
        Option.__init__(s, _(u'[Restart audio player]'), 1 )
        s.player = player
    def switch(s):
        s.player.restart()

#Audio sink menu
class AudioSinkMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'gst audio sink'), 1)
    def children(s):
        return [AudioSinkOption(), AudioSinkPropertiesMenu()]

class AudioSinkOption(Option):
    def __init__(s):
        Option.__init__(s, None, 2 )
        s.ep = EP_GETSTR|EP_REOPENP
        s.offset = 5
    
    def get_param(s):
        return config.audio_player['audio_sink']

    def set_param(s, param):
        try:
            param = str(param)
        except:
            return

        if  _test_gst_sink(param):
            config.audio_player['audio_sink'] = param
            config.audio_player['audio_sink_params'] = []
            config.Save()
            return True
    
    def get_name(s):
        return config.audio_player['audio_sink']
        
def _str_to_property(plugin_name, prop_str):
    try:
        prm,val = map (lambda e: e.strip().rstrip(), str(prop_str).split('=', 1) )
    except:
        return
    if prm == '' or val == '' or prm == 'name':
        return
    V = _test_gst_sink_param(plugin_name, prm, val)
    if V != None:
        return (prm,V)

def _get_any_property(plugin_name, used_props):
    try:
        plug = gst.element_factory_make( plugin_name )
    except:
        return "name=value"
    propts = map(lambda p: [p.name, p.default_value], list( list_properties( plug ) ) )
    del plug
    blacklist=['name']
    if plugin_name.endswith('sink'):
        blacklist +=     ['preroll-queue-len', 'sync', 'max-lateness', 'qos', 'async'
                , 'ts-offset', 'enable-last-buffer', 'last-buffer', 'blocksize'
                , 'render-delay', 'buffer-time', 'latency-time', 'provide-clock'
                , 'slave-method', 'can-activate-pull', 'drift-tolerance', 'mute']
    valid_propts = []
    for p,o in propts:
        if p not in blacklist and p not in used_props:
            if type(o) not in [str, unicode]:
                o = repr(o)
            return u"%s=%s" % ( p , o )
    return "name=value"

class AudioSinkPropertiesMenu( BasePropertiesMenu):
    def __init__(s):
        BasePropertiesMenu.__init__(s, 2)

    def get_gst_plugin_name(s):
        return config.audio_player['audio_sink']
    def get_gst_plugin_params(s):
        return config.audio_player['audio_sink_params']
    def set_gst_plugin_params(s,v):
        config.audio_player['audio_sink_params'] = v

class AudioSinkPropertiesMenu2(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'properties'), 2)
    def children(s):
        elms = map ( lambda x: AudioSinkPropertyOption(x[0], x[1]), config.audio_player['audio_sink_params'] )
        elms.append( AddOption(_('[new]'), 3, s) )
        return elms

    def get_new_param(s):
        return _get_any_property( config.audio_player['audio_sink'], map ( lambda x: x[0], config.audio_player['audio_sink_params'] ) )

    def add_param(s, param):
        prm = _str_to_property(config.audio_player['audio_sink'], param)
        if not prm:
            return

        if prm[0] in map(lambda e: e[0], config.audio_player['audio_sink_params']):
            return
        config.audio_player['audio_sink_params'].append(prm)
        config.Save()
        return AudioSinkPropertyOption(prm[0], prm[1])

class AudioSinkPropertyOption(Option):
    def __init__(s, prm, val):
        Option.__init__(s, None, 3 )
        s.ep = EP_GETSTR
        s.sprm = prm
        s.val = val
        s.offset = 7
        s.delable = True
    
    def get_param(s):
        ret = '%s=' % s.sprm
        if type ( s.val ) == str:
            ret += s.val
        else:
            ret += repr(s.val)
        return ret

    def set_param(s, param):
        prm = _str_to_property(config.audio_player['audio_sink'], param)
        if not prm:
            return
        if prm[0] != s.sprm:
            if prm[0] in map(lambda e: e[0], config.audio_player['audio_sink_params']):
                return
        index = map(lambda e: e[0], config.audio_player['audio_sink_params'] ).index( s.sprm )
        config.audio_player['audio_sink_params'][index] = prm
        s.sprm, s.val = prm
        config.Save()
    
    def on_delete(s):
        index = map(lambda e: e[0], config.audio_player['audio_sink_params'] ).index( s.sprm )
        config.audio_player['audio_sink_params'].pop(index)
        config.Save()
        return True

    def get_name(s):
        return s.sprm
    def get_value(s):
        if type ( s.val ) == str:
            return s.val
        return repr(s.val)

# Audio Filters
class BaseAudioFiltersMenu(Menu):
    def __init__(s, depth):
        Menu.__init__(s, _(u'gst audio filters'), depth)
        s.chldns = []

    def get_new_param(s):
        return 'pitch'

    def add_param(s, param):
        if _test_gst_sink(param):
            s.get_presinks().append( [param, True, []] ) 
            s.chldns.append( BaseAudioFilterMenu( len(s.get_presinks()) - 1, s) )
            config.Save()
            return s.chldns[-1]

    def children(s):
        
        s.chldns = map( lambda no: BaseAudioFilterMenu(no, s), range( len( s.get_presinks() ) ) )
        return s.chldns + [ AddOption(_('[new]'), s.depth + 1, s) ]

    def delete(s, no):
        for c in s.chldns[no:]:
            c.no -= 1
        del s.chldns[no]
        s.get_presinks().pop(no)
        config.Save()
        return True
        

class AudioFiltersMenu(BaseAudioFiltersMenu):
    def __init__(s):
        BaseAudioFiltersMenu.__init__(s, 1)
        s.chldns = []

    def get_presinks(s):
        return config.audio_player['pre_sinks']

class AudioFilterHelper:
    def get_audio_filter_name(s, no):
        return s.p.get_presinks()[no][0]

    def get_audio_filter_params(s, no):
        return s.p.get_presinks()[no][2]

    def get_audio_filter_status(s, no):
        return s.p.get_presinks()[no][1]
    
    def get_presinks(s):
        return s.p.get_presinks()

class BaseAudioFilterMenu(Menu, AudioFilterHelper):
    def __init__(s, no, p):
        Menu.__init__(s, '', p.depth + 1 )
        s.p = p
        s.no = no
        s.delable = True
    def get_name(s):
        return s.get_audio_filter_name(s.no)
    
    def get_value(s):
        if s.get_audio_filter_status(s.no):
            return config.config_chars[0]
        return config.config_chars[1]

    def children(s):
        ret =  [ AudioFilterStatusOption(s) ]
        ret += map ( lambda p: AudioFilterOption(p[0], p[1], s), s.get_audio_filter_params(s.no) )
        ret.append(AddOption(_('[ add property ]'), s.depth + 1, s))
        return ret

    def on_delete(s):
        return s.p.delete(s.no)

    def get_new_param(s):
        return _get_any_property( s.get_audio_filter_name(s.no), map ( lambda x: x[0], s.get_audio_filter_params(s.no) ) )

    def add_param(s, param):
        prm = _str_to_property( s.get_audio_filter_name(s.no), param )
        if not prm:
            return

        if prm[0] in map(lambda e: e[0], s.get_audio_filter_params(s.no)):
            return
        s.p.get_presinks()[s.no][2].append(prm)
        config.Save()
        return AudioFilterOption(prm[0], prm[1], s)

class AudioFilterStatusOption(Option, AudioFilterHelper):
    def __init__(s, p):
        Option.__init__(s, '', p.depth + 1)
        s.p = p
        s.ep = EP_SWITCHP

    def get_icon(s):
        if s.get_audio_filter_status(s.p.no):
            return config.config_chars[0]
        return config.config_chars[1]

    def get_name(s):
        if s.get_audio_filter_status(s.p.no):
            return _('enabled')
        return _('disabled')

    def switch(s):
        s.p.get_presinks()[s.p.no][1] = not s.get_audio_filter_status(s.p.no)
        config.Save()

class AudioFilterOption(Option, AudioFilterHelper):
    def __init__(s, prm, val, p):
        Option.__init__(s, None, p.depth + 1 )
        s.ep = EP_GETSTR
        s.sprm = prm
        s.val = val
        s.offset = 7
        s.delable = True
        s.p = p
    
    def get_param(s):
        ret = '%s=' % s.sprm
        if type ( s.val ) == str:
            ret += s.val
        else:
            ret += repr(s.val)
        return ret

    def set_param(s, param):
        no = s.p.no
        prm = _str_to_property(s.get_audio_filter_name(no), param)
        if not prm:
            return
        if prm[0] != s.sprm:
            if prm[0] in map( lambda e: e[0], s.get_audio_filter_params(no) ):
                return

        index = map( lambda e: e[0], s.get_audio_filter_params(no) ).index( s.sprm )
        s.p.get_presinks()[no][2][index] = prm
        s.sprm, s.val = prm
        config.Save()
    
    def on_delete(s):
        no = s.p.no
        index = map( lambda e: e[0], s.get_audio_filter_params(no) ).index( s.sprm )
        del s.p.get_presinks()[no][2][index]
        config.Save()
        return True

    def get_name(s):
        return s.sprm
    def get_value(s):
        if type ( s.val ) == str:
            return s.val
        return repr(s.val)

#Crossfade submenu
class CrossfadeMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'crossfade effect'), 1)
    def children(s):
        return [CrossfadeStatusOption(), CrossfadeTimeOption()]

    def get_value(s):
        if config.audio_player['crossfade']:
            return config.config_chars[0]
        return config.config_chars[1]

class CrossfadeTimeOption(Option):
    def __init__(s):
        Option.__init__(s, _('time'), 2)
        s.ep = EP_GETSTR
    def get_value(s):
        return repr(config.audio_player['crossfade_time'])
    def set_param(s, param):
        try:
            tm = float(param)
        except:
            return
        if tm < 0:
            return
        config.audio_player['crossfade_time'] = tm
        config.Save()

class CrossfadeStatusOption(Option):
    def __init__(s):
        Option.__init__(s, '', 2)
        s.ep = EP_SWITCHP

    def get_icon(s):
        if config.audio_player['crossfade']:
            return config.config_chars[0]
        return config.config_chars[1]

    def get_name(s):
        if config.audio_player['crossfade']:
            return _('enabled')
        return _('disabled')

    def switch(s):
        config.audio_player['crossfade'] = not config.audio_player['crossfade']
        config.Save()
# Encoders
class EncodersMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'encoders'), 0)

    def children(s):
        encoders = map( lambda name: EncoderProfileMenu(name), sorted2(config.encoder_profiles.keys()) )
        encoders.append(AddOption(_('[ add encoder ]'), 1, s))
        return encoders

    def get_new_param(s):
        return "newencoder"

    def add_param(s, param):
        name = unicode2(param)
        if config.encoder_profiles.has_key(name):
            return
        profile = EncoderProfile()
        profile.name = name
        profile.parse_file_template()
        config.encoder_profiles[name] = profile
        config.Save()
        return  EncoderProfileMenu(name)

class EncoderProfileMenu(Menu):
    def __init__(s, name):
        Menu.__init__(s, name, 1)
        s.profile_name = name
        s.slaves = []
        s.delable = True
    def get_name(s):
        return s.profile_name
    def children(s):
        slaves = [EncoderNameOption(s), 
            EncoderTagOption(s),
            EncoderPathOption(s),
            EncoderAudioFiltersMenu(s),
            EncoderEncoderMenu(s),
            EncoderMuxerMenu(s) ]
        return slaves
    def on_delete(s):
        del config.encoder_profiles[s.profile_name]
        config.Save()
        return True

class EncoderNameOption(Option):
    def __init__(s, parent):
        Option.__init__(s, _(u'profile name'), 2)
        s.parent = parent
        s.ep = EP_GETSTR | EP_RESHORTP

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]
    
    def get_value(s):
        return s.parent.profile_name
    
    def set_param(s, param):
        value = unicode2(param)
        if value in config.encoder_profiles.keys():
            return False

        profile = s._get_encoder_profile()
        del config.encoder_profiles[s.parent.profile_name]
        config.encoder_profiles[value] = profile
        profile.name = value
        s.parent.profile_name = value
        config.Save()
    
        return True

        
class EncoderTagOption(Option):
    def __init__(s, parent):
        Option.__init__(s, _(u'tag type'), 2)
        s.parent = parent
        s.ep = EP_SWITCHP
    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]

    def get_value(s):
        profile = s._get_encoder_profile()
        return profile.tag_type
    
    def switch(s):
        profile = s._get_encoder_profile()
        tags = ['id3', 'wavpack', 'ape', 'oggvorbis', 'flac', "oggflac", "none"]
        tags_len = len(tags)
        i = tags.index( profile.tag_type ) + 1
        if i >= tags_len:
            i = 0
        profile.tag_type = tags[i]
        config.Save()

class EncoderPathOption(Option):
    def __init__(s, parent):
        Option.__init__(s, _(u'destination'), 2)
        s.parent = parent
        s.ep = EP_GETSTR

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]

    def get_value(s):
        profile = s._get_encoder_profile()
        return profile.template_str

    def set_param(s, param):
        profile = s._get_encoder_profile()
        value = unicode2(param)
        prev_value = profile.template_str
        if profile.parse_file_template(value) != True:
            profile.parse_file_template(prev_value)
            return False
        config.Save()
        return True

    def get_aux(s):
        return u'artist, album, title, date, n, nn, nnn, d, dd, ddd'

class EncoderAudioFiltersMenu(BaseAudioFiltersMenu):
    def __init__(s, parent):
        BaseAudioFiltersMenu.__init__(s, 2)
        s.parent = parent
        s.chldns = []

    def get_presinks(s):
        return config.encoder_profiles[s.parent.profile_name].filters

class EncoderEncoderMenu(Menu):
    def __init__(s, parent):
        Menu.__init__(s, _(u'gst encoder'), 2)
        s.parent = parent

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]
        
    def children(s):
        return [ EncoderEncoderNameOption(s.parent),
             EncoderEncoderPropertiesMenu(s.parent) ]

class EncoderEncoderNameOption(Option):
    def __init__(s, parent):
        Option.__init__(s, u'', 3)
        s.parent = parent
        s.ep = EP_GETSTR|EP_REOPENP
        s.offset = 7

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]

    def get_name(s):
        profile = s._get_encoder_profile()
        return profile.encoder
    
    def get_param(s):
        profile = s._get_encoder_profile()
        return profile.encoder

    def set_param(s, param):
        profile = s._get_encoder_profile()
        value = unicode2(param)
        if _test_gst_sink(value):
            profile.encoder = value
            profile.encoder_opts = []
            config.Save()
            return True
        return False

class EncoderEncoderPropertiesMenu( BasePropertiesMenu):
    def __init__(s, parent):
        BasePropertiesMenu.__init__(s, 3)
        s.parent = parent

    def get_gst_plugin_name(s):
        return config.encoder_profiles[s.parent.profile_name].encoder
    def get_gst_plugin_params(s):
        return config.encoder_profiles[s.parent.profile_name].encoder_opts
    def set_gst_plugin_params(s,v):
        config.encoder_profiles[s.parent.profile_name].encoder_opts = v

class EncoderMuxerMenu(Menu):
    def __init__(s, parent):
        Menu.__init__(s, _(u'gst muxer'), 2)
        s.parent = parent

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]
        
    def children(s):
        return [ EncoderMuxerNameOption(s.parent),
             EncoderMuxerPropertiesMenu(s.parent) ]

class EncoderMuxerNameOption(Option):
    def __init__(s, parent):
        Option.__init__(s, u'', 3)
        s.parent = parent
        s.ep = EP_GETSTR|EP_REOPENP
        s.offset = 7
        s.delable = True
        s.fakedel = True

    def _get_encoder_profile(s):
        return config.encoder_profiles[s.parent.profile_name]

    def get_name(s):
        profile = s._get_encoder_profile()
        if profile.muxer:
            return profile.muxer
        return "nothing"
    
    def get_param(s):
        profile = s._get_encoder_profile()
        if profile.muxer:
            return profile.muxer
        return "nothing"

    def on_delete(s):
        profile = s._get_encoder_profile()
        profile.muxer = None
        profile.muxer_opts = []
        config.Save()
        return False

    def set_param(s, param):
        profile = s._get_encoder_profile()
        value = unicode2(param)
        if value == 'nothing':
            profile.muxer = None
            profile.muxer_opts = []
            config.Save()
            return True
        if _test_gst_sink(value):
            profile.muxer = value
            profile.muxer_opts = []
            config.Save()
            return True
        return False

class EncoderMuxerPropertiesMenu( BasePropertiesMenu):
    def __init__(s, parent):
        BasePropertiesMenu.__init__(s, 3)
        s.parent = parent

    def get_gst_plugin_name(s):
        return config.encoder_profiles[s.parent.profile_name].muxer
    def get_gst_plugin_params(s):
        return config.encoder_profiles[s.parent.profile_name].muxer_opts
    def set_gst_plugin_params(s,v):
        config.encoder_profiles[s.parent.profile_name].muxer_opts = v
# Prefered Applications
class PreferedApplicationsMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'prefered applications'), 0)
        s.chldrn = []
    def children(s):
        ret = map(lambda n: PreferedApplicationMenu(n, s), range( len(config.prefered_applications) ) )
        s.chldrn = ret
        return ret + [AddOption(_('[new]'), 1, s)]
    def get_new_param(s):
        return u'program -opt %file'
    def add_param(s, param):
        param.strip()
        if not param:
            return
        config.prefered_applications.append( ([], param) )
        config.Save()
        s.chldrn.append( PreferedApplicationMenu( len(config.prefered_applications) - 1, s ) )
        return s.chldrn[-1]
    def delete( s, no ):
        for c in s.chldrn[no:]:
            c.no -= 1
        config.prefered_applications.pop(no)
        config.Save()
        s.chldrn.pop(no)
        return True
        

class PreferedApplicationMenu(Menu):
    def __init__(s, no, p):
        Menu.__init__(s, _(u''), 1)
        s.p = p
        s.no= no
        s.delable = True
    def get_name (s):
        pa = config.prefered_applications[s.no]
        return shlex.split( pa[1].encode('utf-8') )[0]

    def children(s):
        pa = config.prefered_applications[s.no]
        ret = [ApplicationOption(s)] + map(lambda e: ExtensionOption(e, s), pa[0])
        ret.append(AddOption(_('[ add extension ]'), 2, s))
        return ret
    def on_delete(s):
        return s.p.delete(s.no)

    def get_new_param(s):
        return u'ext'

    def add_param(s, param):
        ext = param.lower()
        pa = config.prefered_applications[s.no]
        if ext not in pa[0]:
            pa[0].append(ext)
            pa[0].sort()
            config.Save()
            return ExtensionOption(ext, s)

class ApplicationOption(Option):
    def __init__(s, p):
        Option.__init__(s, _('command'), 2)
        s.p = p
        s.ep = EP_GETSTR | EP_RESHORTP
    def get_value(s):
        pa = config.prefered_applications[s.p.no]
        return pa[1]

    def set_param(s, param):
        pa = config.prefered_applications[s.p.no]
        config.prefered_applications[s.p.no] = (pa[0], param)
        config.Save()
        return True

class ExtensionOption(Option):
    def __init__(s, name, p):
        Option.__init__(s, name, 2)
        s.p = p
        s.delable = True
        s.ep = EP_GETSTR
        s.offset = 5
    def on_delete(s):
        pa = config.prefered_applications[s.p.no]
        if s.name in pa[0]:
            index = pa[0].index(s.name)
            pa[0].pop(index)
            config.Save()
            return True
    def get_param(s):
        return s.name

    def set_param(s, param):
        ext = param.strip().lower()
        pa = config.prefered_applications[s.p.no]
        if ext in pa[0]:
            return False
        index = pa[0].index(s.name)
        pa[0][index] = ext
        s.name = ext
        config.Save()
        return True
# Gst Mixer
class MixerMenu(Menu):
    def __init__(s, callback):
        s.callback = callback
        Menu.__init__(s, _('gst mixer'), 0 )

    def children (s):
        cldrn = []
        return [  MixerOption(s), MixerPropsMenu(s), MixerCurrentMixerOption(s) ]

class MixerCurrentMixerOption( Option ):
    def __init__(s, p):
        s.p = p
        Option.__init__(s, None, 1 )
        s.ep = EP_SELECT
    def get_name(s):
        return s.p.callback.get_mixer_label()

    def get_value(s):
        return ''
    
    def get_yesno(s):
        mixers = s.p.callback.mixers()
        if mixers and mixers != []:
            s.mixers = mixers
            return [ _('mixer'), [_('select mixer'), "" ], map ( lambda m: u'<%s>' % (m[1]), s.p.callback.mixers() ) ]
    
    def answer(s, rc):
        config.mixer['track_no'] = s.mixers[rc][0]
        config.Save()

    
class MixerOption( Option ):
    def __init__(s, p):
        s.p = p
        Option.__init__(s, None, 1 )
        s.ep = EP_GETSTR|EP_REOPENP

    def get_name(s):
        return config.mixer['plugin']

    def get_value(s):
        return ''

    def get_param(s):
        return config.mixer['plugin']

    def set_param(s, param):
        try:
            param = str(param)
        except:
            return

        if  _test_gst_mixer(param):
            config.mixer['plugin'] = param
            config.mixer['properties'] = []
            s.p.callback.restart_mixer()
            config.Save()
            return True

class MixerPropsMenu( Menu ):
    def __init__(s, p):
        Menu.__init__(s, _('properties'), 1 )
        s.p = p
    def children(s):
        return map ( lambda pv: MixerPropOpt(pv[0], pv[1], s.p), config.mixer['properties'] ) + [ AddOption(_('[new]'), 2, s) ]

    def get_new_param(s):
        return _get_any_property( config.mixer['plugin'], map ( lambda x: x[0], config.mixer['properties'] ) )

    def add_param(s, param):
        prm = _str_to_property(  config.mixer['plugin'], param)
        if not prm:
            return

        if prm[0] in map( lambda e: e[0], config.mixer['properties'] ):
            return

        config.mixer['properties'].append(prm)
        config.Save()
        return MixerPropOpt(prm[0], prm[1], s.p)

class MixerPropOpt( Option ):
    def __init__(s, prm, val, p):
        Option.__init__(s, None, 2)
        s.ep = EP_GETSTR
        s.sprm = prm
        s.val = val
        s.offset = 5
        s.delable = True
        s.p = p
    
    def get_param(s):
        ret = '%s=' % s.sprm
        if type ( s.val ) == str:
            ret += s.val
        else:
            ret += repr(s.val)
        return ret

    def set_param(s, param):
        prm = _str_to_property(config.mixer['plugin'], param)
        if not prm:
            return
        if prm[0] != s.sprm:
            if prm[0] in map( lambda e: e[0], config.mixer['properties'] ):
                return

        index = map( lambda e: e[0], config.mixer['properties'] ).index( s.sprm )
        config.mixer['properties'][index] = prm
        s.sprm, s.val = prm
        config.Save()
    
    def on_delete(s):
        index = map( lambda e: e[0], config.mixer['properties'] ).index( s.sprm )
        del config.mixer['properties'][index]
        config.Save()
        return True

    def get_name(s):
        return s.sprm

    def get_value(s):
        if type ( s.val ) == str:
            return s.val
        return repr(s.val)

#Appearance
class AppearanceMenu(Menu):
    def __init__(s, callback):
        Menu.__init__(s, _(u'appearance'), 0)
        s.callback = callback

    def children(s):
        return [ CurrentSkinOption(s.callback), RenameSkinOption(s.callback),
            IconsMenu(s.callback), PaletteMenu(), ColorsMenu (s.callback),
            CurrentSongMenu() ]

class CurrentSkinOption(Option):
    def __init__(s, callback):
        Option.__init__(s, _(u'current skin'), 1)
        s.ep = EP_SWITCH|EP_REOPENP
        s.callback = callback

    def get_value(s):
        if config.current_skin.mode == "RO":
            return u'(*)' + config.current_skin.skin_name
        return config.current_skin.skin_name

    def switch(s):
        skins = config.list_skins()
        l = len(skins)
        if l <= 1:
            return
        n = skins.index(config.current_skin)
        if n >= l - 1:
            config.current_skin = skins[0]
        else:
            config.current_skin = skins[n+1]
        config.LoadScheme()
        config.color_scheme.generate_palette()
        config.color_scheme.generate_colors()
        s.callback.redraw()
        config.SaveCurrentSkinName()

class RenameSkinOption(Option):
    def __init__(s, callback):
        Option.__init__(s, '', 1)
        s.ep = EP_GETSTR|EP_RESHORTN
        s.reshort_offset = -1
        s.callback = callback
        s.process_it_anyway = True
        s.delable = True
        s.fakedel = True
    
    def get_aux(s):
        if config.current_skin.mode == "RW":
            return _(u"hint: press DEL to delete the skin")
        return ""
    def get_name(s):
        if config.current_skin.mode == "RO":
            return _(u'clone')
        else:
            return _(u"rename")

    def get_value(s):
        return config.current_skin.skin_name

    def set_param(s, param):
        try:
            v = unicode2(param)
            if v == "":
                return
        except:
            return
        
        config.SaveSchemeAs(v)
        return True

    def on_delete(s):
        if config.current_skin.mode == "RO":
            return
        skin_path = config.current_skin.skin_path
        skins = config.list_skins()
        l = len(skins)
        if l <= 1:
            return
        n = skins.index(config.current_skin)
        if n >= l - 1:
            config.current_skin = skins[0]
        else:
            config.current_skin = skins[n+1]
        config.LoadScheme()
        config.color_scheme.generate_palette()
        config.color_scheme.generate_colors()
        s.callback.redraw()
        config.SaveCurrentSkinName()
        os.unlink(skin_path)
        return False

# Icons
def _equalizer_icons():
    return config.equalizer_chars

def _playing_bar():
    return config.playing_bar_chars

def _audio_cursors():
    return config.audio_player_cursors

def _song_status():
    return config.track_status_chars
def _cue():
    return config.cue_char

def _tree():
    return config.tree_chars

def _config():
    return config.config_chars

def _bracelet():
    return config.bracelet_chars

def _holding():
    return config.equalizer_holding_chars

def _dice():
    return config.dice_chars

def _repeat():
    return config.repeat_char

def _direction():
    return config.direction_chars

def _keybar_navigation():
    return config.keybar_navigation_chars

def _progress_bar():
    return config.progress_bar_chars

def _scroll_bar():
    return config.scroll_bar_chars

def _curse():
    return config.curse_char

def _points():
    return config.points_char

class IconsMenu(Menu):
    def __init__(s, callback):
        Menu.__init__(s, _(u'icons'), 1)
        s.callback = callback

    def children(s):
        return    [     IconsOption ( _('equalizer'), _equalizer_icons, s.callback )
                ,IconsOption ( _('playing bar'), _playing_bar, s.callback )
                ,IconsOption ( _('audio cursors'), _audio_cursors, s.callback )
                ,IconsOption ( _('song status'), _song_status, s.callback )
                ,IconsOption ( _('cue'), _cue, s.callback )
                ,IconsOption ( _('tree'), _tree, s.callback )
                ,IconsOption ( _('config'), _config, s.callback )
                ,IconsOption ( _('friendship bracelet'), _bracelet, s.callback )
                ,IconsOption ( _('equalizer holding'), _holding, s.callback )
                ,IconsOption ( _('dice'), _dice, s.callback )
                ,IconsOption ( _('repeat'), _repeat, s.callback )
                ,IconsOption ( _('direction'), _direction, s.callback )
                ,IconsOption ( _('keybar navigation'), _keybar_navigation, s.callback )
                ,IconsOption ( _('progress bar'), _progress_bar, s.callback )
                ,IconsOption ( _('scroll bar'), _scroll_bar, s.callback )
                ,IconsOption ( _('cursed song'), _curse, s.callback )
                ,IconsOption ( _('points'), _points, s.callback )
                ,IconsDefaultsOption(s.callback)
            ]

class IconsDefaultsOption(Option):
    def __init__(s, callback):
        Option.__init__(s, _(u"reset to defaults"), 2)
        s.callback = callback

    def switch(s):
        config.ResetIcons()
        config.SaveScheme()
        s.callback.redraw()

class IconsOption(Option):
    def __init__(s, name, get_icons, callback):
        s.callback = callback
        s.get_icons = get_icons
        Option.__init__(s, name, 2)
        s.ep = EP_GETSTR

    def get_value(s):
        return s.get_param()

    def get_param(s):
        icons = s.get_icons()
        if type(icons) == list:
            v = u""
            for i in icons:
                v+=i
        else:
            v = icons
        return v

    def set_param(s, param):
        icons = s.get_icons()
        try:
            v = unicode2(param)
            if len(v) != len(icons):
                return

            if type(icons) != list:
                config.cue_char = v
                config.SaveScheme()
                return True

            for i in range( len(icons) ):
                icons[i] = v[i]
        except:
            return
        
        config.SaveScheme()
        s.callback.redraw()
        return True

class CurrentSongMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'playing song description'), 1)

    def children(s):
        return map ( lambda x: CurrentSongOpt(x), range(3) )

class CurrentSongOpt(Option):
    def __init__(s, n):
        Option.__init__(s, u'', 2)
        s.n = n
        s.ep = EP_GETSTR 
        if s.n == 0:
            s.name = _(u'left')
        elif s.n == 1:
            s.name = _(u'right')
        else:
            s.name = _(u'bottom')
    
    def get_value(s):
        if s.n == 0:
            return config.playing_track_left.template_str
        elif s.n == 1:
            return config.playing_track_right.template_str
        else:
            return config.playing_track_bottom.template_str

    def get_param(s):
        return s.get_value()
    
    def set_param(s, param):
        try:
            param = unicode(param)
        except:
            return
        sp = SongPrinter()
        try:
            rc = sp.init_printer(param)
        except:
            rc = False
        if rc:
            if s.n == 0:
                config.playing_track_left.init_printer(param)
            elif s.n == 1:
                config.playing_track_right.init_printer(param)
            else:
                config.playing_track_bottom.init_printer(param)
            config.SaveScheme()
            
        return True

# Palette
class PaletteMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _(u'palette'), 1)
        if not config.color_scheme.palette.can_change_color:
            s.aux = _("This terminal can't change color")

    def children(s):
        if config.color_scheme.palette.can_change_color:
            return map(lambda x: ColorMenu(x), sorted(config.color_scheme.palette.colors.keys()) )
        else:
            return []
    
    

class ColorMenu(Menu):
    def __init__(s, no):
        s.no = no
        Menu.__init__(s, u'', 2)
    def get_name (s):
        if config.color_scheme.palette.colors[s.no].default:
            return _(config.color_scheme.palette.colors[s.no].name)
        else:
            return config.color_scheme.palette.colors[s.no].name

    def children(s):
        if s.no == -1:
            return []
        if s.no <= COLOR_WHITE:
            return map ( lambda x: RGBOption(s.no, x), range(3) )
        return [ColorName(s.no)] + map ( lambda x: RGBOption(s.no, x), range(3) )

class ColorName(Option):
    def __init__(s, no):
        Option.__init__(s, u'', 3)
        s.no = no
        s.ep = EP_GETSTR | EP_RESHORTP
    
    def get_name(s):
        return config.color_scheme.palette.colors[s.no].name
    
    def get_param(s):
        return s.get_name()
    
    def set_param(s, param):
        try:
            name = unicode(param)
        except:
            return

        config.color_scheme.palette.colors[s.no].name = name
        config.SaveScheme()
        return True

class RGBOption(Option):
    def __init__(s, no, rgb):
        Option.__init__(s, u'', 3)
        s.no = no
        s.rgb = rgb
        s.ep = EP_GETSTR
        s.aux = _(u'value must be between 0 and 1000')

    def get_name(s):
        if s.rgb == 0:
            return 'R'
        elif s.rgb == 1:
            return 'G'
        return 'B'

    def get_value(s):
        return str(config.color_scheme.palette.colors[s.no].get_rgb()[s.rgb])
    
    def get_param(s):
        return s.get_value()

    def set_param(s, param):
        try:
            c = int(str(param))
        except:
            return

        if c < 0 or c > 1000:
            return

        if s.rgb == 0:
            config.color_scheme.palette.colors[s.no].r = c
        elif s.rgb == 1:
            config.color_scheme.palette.colors[s.no].g = c
        else:
            config.color_scheme.palette.colors[s.no].b = c

        config.color_scheme.palette.colors[s.no].init_color()
        config.SaveScheme()

# Colors
class ColorsMenu(Menu):
    def __init__(s, callback):
        s.callback = callback
        Menu.__init__(s, _(u'colors'), 1)

    def children(s):
        return [ColorsSectionMenu(u'panel', s.callback), ColorsSectionMenu(u'pop-up window', s.callback), ColorsSectionMenu('player', s.callback), ColorsSectionMenu('key bar', s.callback) ]

class ColorsSectionMenu(Menu):
    def __init__(s, section, callback):
        Menu.__init__(s, _(section), 2)
        s.callback = callback
        s.section = section

    def children(s):
        return map ( lambda k: ColorsItemMenu(s.section, k, s.callback), config.color_scheme.get_seq(s.section) )

class ColorsItemMenu(Menu):
    def __init__(s, section, item, callback):
        Menu.__init__(s, _(item), 3)
        s.item = item
        s.section = section
        s.callback = callback
    def children(s):
        return [ItemBGOption(s.section, s.item), ItemFGOption(s.section, s.item), ItemBoldOption(s.section, s.item, s.callback)]

class ItemBGOption(Option):
    def __init__(s, section, item):
        Option.__init__(s, '', 4)
        s.ep = EP_SWITCHP
        s.section = section
        s.item = item
    def get_name(s):
        return _('background')

    def get_value(s):
        return _(config.color_scheme[s.section][s.item].bg())

    def switch(s):
        config.color_scheme[s.section][s.item].inc_bg()
        config.color_scheme.generate_colors()
        config.SaveScheme()

class ItemFGOption(Option):
    def __init__(s, section, item):
        Option.__init__(s, '', 4)
        s.ep = EP_SWITCHP
        s.section = section
        s.item = item
    def get_name(s):
        return _('foreground')
    def get_value(s):
        return _(config.color_scheme[s.section][s.item].fg())
    def switch(s):
        config.color_scheme[s.section][s.item].inc_fg()
        config.color_scheme.generate_colors()
        config.SaveScheme()

class ItemBoldOption(Option):
    def __init__(s, section, item, callback):
        Option.__init__(s, '', 4)
        s.ep = EP_SWITCHP
        s.section = section
        s.item = item
        s.callback = callback

    def get_name(s):
        return _('bold')

    def get_icon(s):
        if config.color_scheme[s.section][s.item].bold():
            return config.config_chars[0]
        return config.config_chars[1]

    def switch(s):
        config.color_scheme[s.section][s.item].ch_bold()
        config.color_scheme.generate_colors()
        config.SaveScheme()
        s.callback.redraw()

#Aliases Menu
class AliasesMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _('aliases'), 0)
    def children(s):
        return [AliasUsingMenu(), TAliasesMenu('artist'), TAliasesMenu('album')]

class TAliasesMenu(Menu):
    def __init__(s, target):
        Menu.__init__(s, _('%ss' % target), 1)
        s.target = target

    def _get_atree(s):
        if s.target == 'artist':
            return config.artist_aliases
        else:
            return config.album_aliases

    def children(s):
        inverted_aliases = {}
        alias_names = []
        aliases = s._get_atree()
            
        for k,v in aliases.items():
            if inverted_aliases.has_key(v):
                inverted_aliases[v].append(k)
            else:
                inverted_aliases[v] = [k]
                alias_names.append(v)
        alias_names = sorted2(alias_names)
        ret = []
        for a in alias_names:
            for n in sorted2(inverted_aliases[a]):
                ret.append(AliasOpt(a,n, s.target))
        ret.append(AddOption(_('[new]'), 2, s))
        return ret

    def get_new_param(s):
        return "alias=%s name" % s.target

    def add_param(s, param):
        try:
            a,v = map ( lambda x: unicode2(x), param.split('=', 1))
            v = v.lower()
            tree = s._get_atree()
            if a.strip() == '' or v.strip() == '':
                return
            if tree.has_key(v):
                return
            tree[v] = a
            
            config.SaveAliases()
            return AliasOpt(a, v, s.target)
        except:
            pass

class AliasOpt( Option ):
    def __init__(s, alias, name, target):
        Option.__init__(s, None, 2)
        s.ep = EP_GETSTR
        s.alias = alias
        s.offset = 5
        s.name = name
        s.target = target
        s.delable = True
    
    def _get_atree(s):
        if s.target == 'artist':
            return config.artist_aliases
        else:
            return config.album_aliases

    def get_param(s):
        ret = '%s=%s' % (s.alias, s.name)
        return ret

    def set_param(s, param):
        try:
            a,v = map ( lambda x: unicode2(x), param.split('=', 1))
            tree = s._get_atree()
            v = v.lower()
            if a.strip() == '' or v.strip() == '':
                return
            del tree[s.name]
            tree[v] = a
            s.alias = a
            s.name = v
            config.SaveAliases()
            return True
        except:
            pass
                
    def on_delete(s):
        del s._get_atree()[s.name]
        config.SaveAliases()
        return True

    def get_name(s):
        return s.alias

    def get_value(s):
        return s.name

class AliasUsingMenu(Menu):
    def __init__(s):
        Menu.__init__(s, _('using'), 1)

    def children(s):
        return map( lambda no: AliasUsingOption(no), range(len(config.alias_using)) )

class AliasUsingOption(Option):
    def __init__(s, aid ):
        Option.__init__(s, _(config.alias_using_names[aid]), 2)
        s.ep = EP_SWITCHP
        s.aid =aid

    def get_icon(s):
        if config.alias_using[s.aid]:
            return config.config_chars[0]
        return config.config_chars[1]

    def switch(s):
        config.alias_using[s.aid] = not config.alias_using[s.aid]
        config.Save()

#RADIO
class ShoutcastMenu(Menu):
    def __init__(s, d = 0):
        Menu.__init__(s, 'shoutcast', d)
    
    def children(s):
        return [ShoutcastResults(s.depth + 1), ShoutcastSort(s.depth + 1)]

class ShoutcastResults(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _('number of results'), d)
        s.ep = EP_GETSTR

    def set_param(s, param):
        try:
            n = int(param)
            if n <3 or n > 1000:
                return
            config.shoutcast_RpP = n
            config.Save()
            return True
        except:
            pass

    def get_value(s):
        return str(config.shoutcast_RpP)

class ShoutcastSort(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _('sort by'), d)
        s.ep = EP_SWITCH
    
    def get_value(s):
        return _(config.shoutcast_sort)
    
    def switch(s):
        if config.shoutcast_sort == "bitrate":
            config.shoutcast_sort = 'popularity'
        else:
            config.shoutcast_sort = 'bitrate'
        config.Save()
#NOTIFICATION
class NotificationMenu(Menu):
    def __init__(s, d = 0):
        Menu.__init__(s, _('notifications'), d)
    
    def children(s):
        return [DoNotifyOption(s.depth + 1), NotificationOption(s.depth + 1)]

    def get_value(s):
        if config.do_notify:
            return config.config_chars[0]
        return config.config_chars[1]

class NotificationOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _('command'), d)
        s.ep = EP_GETSTR
        s.aux = u'%title, %artist, %album, %path'

    def set_param(s, param):
        try:
            p = unicode(param)
            config.notification_string = p
            config.Save()
            return True
        except:
            pass

    def get_value(s):
        return unicode(config.notification_string)

class DoNotifyOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, '', d)
        s.ep = EP_SWITCHP

    def get_icon(s):
        if config.do_notify:
            return config.config_chars[0]
        return config.config_chars[1]

    def get_name(s):
        if config.do_notify:
            return _('enabled')
        return _('disabled')

    def switch(s):
        config.do_notify = not config.do_notify
        config.Save()

#XSPF
class XspfMenu(Menu):
    def __init__(s, d = 0):
        Menu.__init__(s, _('XSPF playlist'), d)

    def children(s):
        return [XspfOpeningMenu(s.depth+1), XspfSavingMenu(s.depth+1)]

class XspfOpeningMenu(Menu):
    def __init__(s, d = 1):
        Menu.__init__(s, _('opening'), d)

    def children(s):
        return map(lambda no: XspfOption(s.depth+1, no), range(2))

class XspfSavingMenu(Menu):
    def __init__(s, d = 1):
        Menu.__init__(s, _('saving'), d)

    def children(s):
        return map(lambda no: XspfOption(s.depth+1, no), range(2,5))


class XspfOption(Option):
    def __init__(s, d = 1, ono = 0):
        s.ono = ono
        s.ep = EP_SWITCHP

        if ono == 0:
            Option.__init__(s, _('Check http links'), d)
        elif ono == 1:
            Option.__init__(s, _('Reload files'), d)
        elif ono == 2:
            Option.__init__(s, _('VLC compatibility'), d)
        elif ono == 3:
            Option.__init__(s, _('Audacious compatibility'), d)
        elif ono == 4:
            Option.__init__(s, _('QMMP compatibility'), d)
            s.aux = _("conflict with VLC & Audacious")

    def get_icon(s):
        if s.ono == 0:
            if config.xspf_check_http:
                return config.config_chars[0]
            return config.config_chars[1]
        if s.ono == 1:
            if config.xspf_reload_file:
                return config.config_chars[0]
            return config.config_chars[1]
        if s.ono == 2:
            if config.xspf_vlc_compatibility:
                return config.config_chars[0]
            return config.config_chars[1]
        if s.ono == 3:
            if config.xspf_audacious_compatibility:
                return config.config_chars[0]
            return config.config_chars[1]
        if s.ono == 4:
            if config.xspf_qmmp_compatibility:
                return config.config_chars[0]
            return config.config_chars[1]
        
    def switch(s):
        if s.ono == 0:
            config.xspf_check_http = not config.xspf_check_http
        elif s.ono == 1:
            config.xspf_reload_file = not config.xspf_reload_file
        elif s.ono == 2:
            config.xspf_vlc_compatibility = not config.xspf_vlc_compatibility
        elif s.ono == 3:
            config.xspf_audacious_compatibility = not config.xspf_audacious_compatibility
        elif s.ono == 4:
            config.xspf_qmmp_compatibility = not config.xspf_qmmp_compatibility
        config.Save()

#VPALEVE
class VpaleveMenu(Menu):
    def __init__(s, d = 0):
        Menu.__init__(s, _('vk.com'), d)
    def children(s):
        return [VpaleveToken()]

class VpaleveToken(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _(u'token'), d)
        s.ep = EP_GETSTR
    
    def get_aux(s):
        return GET_TOKEN
    def get_value(s):
        if config.vk_token:
            return config.vk_token
        return u""
    
    def set_param(s, param):
        try:
            name = unicode(param)
        except:
            return

        config.vk_token = name
        config.Save()
        lastfm.reconnect()
        return True

#LASTFM
class LastfmMenu(Menu):
    def __init__(s, d = 0):
        Menu.__init__(s, 'last.fm', d)
    
    def children(s):
        if pylast:
            return [LastfmScrobblingOption(s.depth + 1), LastfmRadioScrobblingOption(s.depth + 1), \
                LastfmUserOption(s.depth + 1), LastfmPassOption(s.depth + 1)]
        return []

class LastfmScrobblingOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, 'scrobbling', d)
        s.ep = EP_SWITCHP

    def get_icon(s):
        if config.lastfm_scrobbler:
            return config.config_chars[0]
        return config.config_chars[1]

    def get_value(s):
        if config.lastfm_scrobbler:
            return _('enabled')
        return _('disabled')

    def switch(s):
        config.lastfm_scrobbler = not config.lastfm_scrobbler
        config.Save()
        lastfm.reconnect()

class LastfmRadioScrobblingOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _('radio scrobbling'), d)
        s.ep = EP_SWITCHP

    def get_icon(s):
        if config.lastfm_scrobble_radio:
            return config.config_chars[0]
        return config.config_chars[1]

    def get_value(s):
        if config.lastfm_scrobble_radio:
            return _('enabled')
        return _('disabled')

    def switch(s):
        config.lastfm_scrobble_radio = not config.lastfm_scrobble_radio
        config.Save()


class LastfmUserOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _(u'login'), d)
        s.ep = EP_GETSTR
    
    def get_value(s):
        if config.lastfm_user:
            return config.lastfm_user
        return u""
    
    def set_param(s, param):
        try:
            name = unicode(param)
        except:
            return

        config.lastfm_user = name
        config.Save()
        lastfm.reconnect()
        return True

class LastfmPassOption(Option):
    def __init__(s, d = 1):
        Option.__init__(s, _(u'password'), d)
        s.ep = EP_GETSTR
    
    def get_value(s):
        if config.lastfm_md5:
            return u"***"
        return _(u"none")
    
    def set_param(s, param):
        try:
            name = unicode(param)
        except:
            return

        config.lastfm_md5 = pylast.md5(param)
        config.Save()
        lastfm.reconnect()
        return True
#AUTOPANEL
class AutopanelOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'auto hide unselected panel'), 0)
        s.ep = EP_SWITCH|EP_RESHORTN
        s.reshort_offset = 1

    def get_value(s):
        if config.autopanel:
            return config.config_chars[0]
        return config.config_chars[1]

    def get_icon(s):
        if config.autopanel:
            return config.config_chars[0]
        return config.config_chars[1]

    def switch(s):
        config.autopanel = not config.autopanel
        config.Save()

class AutopanelWidthOption(Option):
    def __init__(s):
        Option.__init__(s, _(u'hide it when width less then'), 0)
        s.ep = EP_GETSTR

    def get_value(s):
        return unicode(config.autopanel_width)

    def get_icon(s):
        if config.autopanel:
            return config.config_chars[0]
        return config.config_chars[1]

    def set_param(s, param):
        try:
            v = int(param)
        except:
            return
        if v < 0:
            return False

        config.autopanel_width = v
        config.Save()
        return True


#THE CONFIG PANEL
class PConfig:
    def init_config(s):
        entries = []
        entries.append( CharsetOption() )
        entries.append( ISO8859Option() )
        entries.append( DefPlsOption() )
        entries.append( AudioPlayerMenu(s.callback) )
        entries.append( EncodersMenu() )
        entries.append( MixerMenu(s.callback) )
        entries.append( AudioExtensionsMenu() )
        entries.append( TitleFormatMainMenu() )
        entries.append( ShoutcastMenu() )
        entries.append( LastfmMenu() )
        #entries.append( VpaleveMenu())
        entries.append( XspfMenu() )

        entries.append( PreferedApplicationsMenu() )
        entries.append( AppearanceMenu(s.callback) )
        entries.append( AliasesMenu() )
        entries.append( NotificationMenu() )
        entries.append( cdnoOption() )
        entries.append( HideKeybarOption(s.callback) )
        entries.append( AutopanelOption() )
        entries.append( AutopanelWidthOption() )
        entries.append( TerminalOption() )
        s.storage.fill(entries)

    def question_enter(s):
        rc = s.panel.yesno.enter()
        s.panel.yesno = None

        try:
            s.storage[s.panel.pos].answer(rc)
        except:
            pass
        else:
            s.storage.reshort_no ( s.panel.pos )

        s.panel.redraw()
        s.panel.refresh()

        s.question = False
        s.cmd = None

    def _get_parent_pos(s):
        depth = s.storage[s.panel.pos].depth
        for n in range(s.panel.pos, -1, -1):
            if s.storage[n].depth < depth:
                return n
        return None

    def _process_flags(s, current_entry):
        if current_entry.enter_policy()&EP_REOPENP:
            dp = current_entry.depth
            for pos in range(s.panel.pos, s.storage.nol):
                if dp > s.storage[pos].depth:
                    break
                if s.storage[pos][P_TYPE] == 'submenu' and s.storage[pos][P_STATUS] == 1:
                    s.hide_submenu(pos)
                    break
        elif current_entry.enter_policy()&EP_RESHORTP:
            dp = current_entry.depth
            for pos in reversed(range(s.panel.pos)):
                if dp > s.storage[pos].depth and s.storage[pos][P_TYPE] == 'submenu':
                    s.storage.reshort_no(pos)
                    break
        if current_entry.enter_policy()&EP_RESHORTN:
            s.storage.reshort_no(s.panel.pos + current_entry.reshort_offset)
    def enter(s):
        current_entry = s.storage[s.panel.pos]
        offset = len(current_entry[P_NAME]) +  current_entry.depth*2
        if current_entry.depth:
            offset += 2

        if current_entry[P_TYPE] == 'option':
            if current_entry.offset != None:
                offset = current_entry.offset
            if current_entry.enter_policy()&EP_GETSTR:
                param = current_entry.get_param()
                new_param = s.panel.improved_input_line( offset, param)
                if not new_param or ( new_param == param and not current_entry.process_it_anyway):
                    s.panel.redraw()
                    s.panel.refresh()
                    return
                if current_entry.set_param(new_param):
                    s._process_flags(current_entry)

            elif current_entry.enter_policy()&EP_SWITCH:
                current_entry.switch()
                s._process_flags(current_entry)

            elif current_entry.enter_policy() == EP_SELECT:
                yesno =  current_entry.get_yesno()
                if yesno:
                    s.panel.run_yesno(yesno[0], yesno[1], yesno[2])
                    s.cmd="mixer"
                    s.question = True

            elif current_entry.enter_policy() == EP_SWITCHP:
                current_entry.switch()
                depth = current_entry.depth
                for pos in reversed(range(s.panel.pos)):
                    if depth > s.storage[pos].depth:
                        s.storage.reshort_no(pos)
                        break
            elif current_entry.enter_policy() == EP_NEW:
                param = current_entry.get_param()
                new_param = s.panel.improved_input_line( offset, param)
                if new_param:
                    entry = current_entry.add_param(new_param)
                    if entry:
                        s.storage.insert([entry], s.panel.pos-1)
                s.panel.redraw()
                s.panel.refresh()
                return
            s.storage.reshort_no(s.panel.pos)
            s.panel.redraw()
            s.panel.refresh()
            return
        elif current_entry[P_TYPE] == 'submenu':
            if current_entry[P_STATUS] == 0:
                current_entry[P_STATUS] = 1
                entries = current_entry.children()
                if entries != []:
                    s.storage.insert(entries, s.panel.pos)
            else:
                s.hide_submenu(s.panel.pos)
            s.storage.reshort_no(s.panel.pos)
            s.panel.redraw()
            s.panel.refresh()

    def left(s):
        current_entry = s.storage[s.panel.pos]
        if current_entry[P_TYPE] == 'submenu' and current_entry[P_STATUS] == 1:
                s.hide_submenu(s.panel.pos)
        elif current_entry.depth > 0:
            d = current_entry.depth
            for i in reversed(range(0, s.panel.pos)):
                if s.storage[i].depth < d:
                    s.panel.select(i)
                    break
        else:
            s.cd('locations://')
    def right(s):
        current_entry = s.storage[s.panel.pos]
        if current_entry[P_TYPE] == 'submenu' and current_entry[P_STATUS] == 0:
            s.enter()
        elif s.panel.pos + 1 == s.storage.nol:
            return
        else:
            if current_entry[P_TYPE] == 'submenu': tp = 1
            else: tp = 0

            d = current_entry.depth
            for i in range(s.panel.pos+1, s.storage.nol):
                if tp and s.storage[i].depth <= d:
                    s.panel.select(i)
                    break
                elif tp == 0 and s.storage[i].depth < d:
                    s.panel.select(i)
                    break
            else:
                s.panel.select(s.storage.nol-1)

    def delete(s):
        current_entry = s.storage[s.panel.pos]
        if current_entry[P_TYPE] == 'option':
            if not current_entry.is_delable():
                return
            if current_entry.on_delete():
                s.storage.remove(s.panel.pos)
                s.panel.redraw()
                s.panel.refresh()
            elif current_entry.fakedel:
                if current_entry.enter_policy()&EP_REOPENP:
                    dp = current_entry.depth
                    for pos in range(s.panel.pos, s.storage.nol):
                        if dp > s.storage[pos].depth:
                            break
                        if s.storage[pos][P_TYPE] == 'submenu' and s.storage[pos][P_STATUS] == 1:
                            s.hide_submenu(pos)
                            break
                elif current_entry.enter_policy()&EP_RESHORTN:
                    s.storage.reshort_no(s.panel.pos + current_entry.reshort_offset)
                s.storage.reshort_no(s.panel.pos)
                s.panel.redraw()
                s.panel.refresh()
        elif  current_entry[P_TYPE] == 'submenu':
            if not current_entry.is_delable():
                return
            s.hide_submenu(s.panel.pos)
            s.storage[s.panel.pos].on_delete()
            s.storage.remove(s.panel.pos)
            s.panel.redraw()
            s.panel.refresh()
                
    def move(s, direction):
        pass

    def hide_submenu(s,pos):
        current_entry = s.storage[pos]
        if current_entry[P_TYPE] == 'submenu' and current_entry[P_STATUS] == 1:
            current_entry[P_STATUS] = 0
            while pos + 1 < s.storage.nol:
                entry = s.storage[ pos + 1 ]
                if current_entry.depth >= entry.depth:
                    break
                s.storage.remove(pos + 1)

            s.storage.reshort_no(pos)
            s.storage.reshort_no(pos)
            s.panel.redraw()
            s.panel.refresh()

_icons = [ u'☺', u'⚖', u'☠' ]

def _test_gst_sink(audio_sink):
    try:
        asink = gst.element_factory_make( audio_sink )
    except:
        return False
    del asink
    return True

def _test_gst_mixer(mixer_name):
    try:
        mx = gst.element_factory_make( mixer_name )
        dir ( mx.list_tracks )
    except:
        return False
    del mx
    return True

def _test_gst_sink_param(audio_sink, param, value_str):
    try:
        asink = gst.element_factory_make( audio_sink )
    except:
        return None
    value = None
    if value_str.lower() in ['true', 'false']:
        vtype = bool
        value = True if value_str.lower() == 'true' else False

    if value == None:
        try:
            value = int(value_str)
            vtype = int
        except:
            value = None
    if value == None:
        try:
            value = float(value_str)
            vtype = float
        except:
            value = None
    if value == None:
        value = value_str
        vtype = str
    try:
        asink.set_property(param, value)
    except:
        if vtype == int:
            vtype = float
            value = float(value_str)
            try:
                asink.set_property(param, value)
            except:
                del asink
                return None
        else:
            del asink
            return None
    else:
        del asink
        return value

def _test_playlist(path):
    if os.path.isfile(path):
        return True
    try:
        open(path, "w").close()
    except:
        return False
    return True

def _test_encoding(encoding):
    try:
        ''.encode(encoding)
    except:
        return False
    return True


