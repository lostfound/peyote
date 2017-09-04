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
                                    

from __future__ import with_statement
import os, os.path, sys, getopt
import pickle
import codecs
from getopt import getopt, GetoptError
from gettext import lgettext
import random
import shutil
VERSION = [ 0, 10, 0 ]

from useful import localise, nullreplace
_ = localise
#Underline will be replaced by ./configure script. Don't edit it!
SHARE_DIR="/usr/local/share/peyote"
#Underline will be replaced by ./configure script. Don't edit it!
DEFAULT_TERMINAL="urxvt +sb -sh 30 -fadecolor gray -fade 5 -tint gray -tr -fg white -fn xft:monospace:size=10 -geometry 100x42 -e %peyote"

SKIN_POSTFIX = '.peyote.skin'
config = None

class Cmd:
    def __init__(s):
        s.cmd = {}

    def output_help_message(s):
        print "Peyote " + reduce(lambda x,y : "%s.%s" % (x,y) , VERSION )  +" (c) 2010 - 2017 (c) Peace and Love"
        print _(u"       is an audio player with friendly MC-like interface.")
        print _("       free software (GPL) without any warranty but with best wishes")
        print _("       website:"), "http://peyote.sourceforge.net"
        print _("Your terminal must display these unicode symbols:")
        print   "     ☮ ☸ ♺ ⚅ ☰  ♍ ☯ ♫ ⚐ ☐ ☒ ★ ☆ ☚ ☝ ☛ ↓ ↑ ⇝ ☺ ⚖ ☠ ○ ▸ ▾"
        print ""
        print _("usage:")
        print _("       peyote [option(s)] [location-1 [location-2 [...]]]")
        print ""
        print _("supported options:")
        print "       --encoding str     ", _("secondary character encoding  (!= utf-8) ["), s.secondary_encoding, ']'
        print "       --gst-sink str     ", _("audio output gstreamer plug-in ["), s.audio_player['audio_sink'], ']'
        print "       --skin str         ", _("Use this skin")
        print "       --help             ", _("print this message and exit")
        print ""
        print _("supported locations:")
        print "       playlist path"
        print "       directory path"
        print "       'equalizer://'"
        print ""


    def parse_commandline(s):
        gopts = ['help', 'encoding=', 'gst-sink=', 'skin=' ]
        try:
            optlist, args = getopt(sys.argv[1:], '', gopts)
        except GetoptError, err:
            print "I'm sorry but ", str(err)
            print 'Type "peyote --help" for more information.'
            sys.exit()

        if ('--help', '') in optlist:
            s.output_help_message()
            sys.exit()
        for val,arg in optlist:
            if val == '--encoding':
                try:
                    u"".decode(arg)
                except:
                    print "sorry, but character encoding", repr(arg), 'not recognized'
                    sys.exit(1)
                else:
                    s.cmd['secondary_encoding'] = arg

            elif val == '--gst-sink':
                s.cmd['audio_sink'] = arg

            elif val == '--skin':
                s.cmd['skin'] = arg
                skin_name = s.cmd['skin']
                if skin_name != "":
                    skins = s.list_skins()
                    for skin in skins:
                        if skin_name == skin.skin_name:
                            s.current_skin = skin
                            break
                    else:
                        s.current_skin = Skin(skin_name, s.peyote_skins_dir, s)

        if args :
            s.cmd[ 'locations' ] = args

class Skulls:
    def LoadSkulls(s):
        s.skulls = set()
        try:
            with codecs.open(s.skulls_file, "r",  'utf-8') as f:
                s.skulls = set(map ( lambda x: x.rstrip('\n'), f.readlines()) )
        except:
            pass

    def SaveSkulls(s):
        with codecs.open (s.skulls_file, "w",  'utf-8') as f:
            for skull in s.skulls:
                f.write(skull)
                f.write('\n')
            
    def is_cursed(s, addr):
        if addr in s.skulls:
            return True
        return False

    def IsCursed(s, track):
        if track['addr'] in s.skulls:
            track['cursed'] = True
            return True
        return False

    def Curse(s, addrs):
        s.LoadSkulls()
        for addr in addrs:
            s.skulls.add(addr)
        s.SaveSkulls()

    def Bless(s, addrs):
        s.LoadSkulls()
        for addr in addrs:
            s.skulls.discard(addr)
        s.SaveSkulls()
                

class EqualizerSettings:
    def __init__(s):
        s.equalizer_default = None
        s.equalizer_artists = {} #key = str(artist)
        s.equalizer_albums  = {} #key = [str(artist), str(album) ]
        s.equalizer_songs   = {} #key = [str(artist), str(album), str(title) ]

    def LoadEqualizer(s):
        pass
    def LoadEqualizers(s):
        try:
            with open(s.equalizer_file, "r") as f:
                s.equalizer_default = pickle.load(f)
                s.equalizer_artists = pickle.load(f)
                s.equalizer_albums  = pickle.load(f)
                s.equalizer_songs   = pickle.load(f)
        except:
            pass

    def GetEqualizer(s, track):
        artist = get_performer_alias (  track.get('performer', '' ), 6 )
        album = get_album_alias (  track.get('album', '' ), 6 )
        title = track.get('title', '' )
        eq = s.equalizer_songs.get( (artist, album, title), 
           s.equalizer_albums.get( (artist, album), 
           s.equalizer_artists.get( artist, 
           s.equalizer_default) ) )
        return eq
        
    def OnSaveEqualizer(s, eq, track, designed_for):
        try:
            artist = get_performer_alias (  track.get('performer', '' ), 6 )
            album = get_album_alias (  track.get('album', '' ), 6 )

            if designed_for == 0:
                s.equalizer_default = eq
            elif designed_for == 1:
                s.equalizer_artists[artist] = eq
            elif designed_for == 2:
                s.equalizer_albums[ (artist, album) ] = eq
            else:
                s.equalizer_songs[ (artist, album, track.get('title', '' ) ) ] = eq
            s.SaveEqualizers()
        except:
            pass
        
    def SaveEqualizers(s):
        try:    
            with open(s.equalizer_file, "w") as f:
                pickle.dump(s.equalizer_default, f)
                pickle.dump(s.equalizer_artists, f)
                pickle.dump(s.equalizer_albums, f)
                pickle.dump(s.equalizer_songs, f)

        except:
            pass

def _kbps(track):
    try:
        if track.has_key('bitrate'):
            return unicode(track['bitrate']/1000)
    except:
        pass
def _srate(track):
    try:
        if track.has_key('sample_rate'):
            return unicode(track['sample_rate'])
    except:
        pass

class SongPrinter:
    def __init__(s, alias_no = 4, template = u"$title"):
        s.template_str = template
        s.alias_no = alias_no

        s.cartridge = [ 
            ( lambda track: get_performer_alias ( track.get("performer"), s.alias_no ),
            ['artist'] )
            , ( lambda n: None if n == None else n if type(n) in [str, unicode] else unicode(n),
            ["id", "no"] )
            , ( lambda track: get_album_alias ( track.get("album"), s.alias_no ),
            ["album"] )
            , ( lambda track: track.get("date"),
            ['date', 'year'] )
            , ( lambda track: track.get("title") ,
            ['title'] )
            , ( lambda track: Dice() ,
            ['dice'] )
            , ( lambda track: s.Num(track['id'], 3) ,
            ['nnn'] )
            , ( lambda track: s.Num(track['id'], 2) ,
            ['nn'] )
            , ( lambda track: s.Num(track['id'], 1),
            ['n'] )
            , ( lambda track: s.Num(track['cdno'], 1) ,
            ['d'] )
            , ( lambda track: s.Num(track['cdno'], 2) ,
            ['dd'] )
            , ( lambda track: s.Num(track['cdno'], 3) ,
            ['ddd'] )
            , ( lambda track: track.get("ext"),
            ['ext'] )
            , ( lambda track: _kbps(track),
            ['bitrate'] )
            , ( _srate,
            ['srate'] )
            ]


    def Num(s,n,l):
        if n == None:
            return None
        elif type(n) in [str, unicode]:
            try:
                N = unicode(int(n))
            except:
                return None
            if l == 1 or len(N) >= l:
                return N

            return u"0"*(l-len(N)) + N

    def print_song(s, track, replace_f = lambda x: x):
        song_name = u""
        for v in s.template:
            if type(v) in [unicode, str]:
                song_name += v
            else:
                try:
                    thing = v[1]( track )
                except Exception,e:
                    continue
                if thing:
                    song_name += v[0]
                    song_name += replace_f(unicode(thing))
                    song_name += v[2]
        return song_name

    def init_printer(s, template_str):
        s.template_str = template_str
        tail = s.template_str
        s.template = []
        while True:
            dollar_idx = tail.find('$')
            pp_idx = tail.find('%')
            if dollar_idx == -1:
                s.template.append(tail)
                return True
            if dollar_idx < pp_idx or pp_idx == -1:
                spl = tail.split('$', 1)
                if spl[0] != u'':
                    s.template.append(spl[0])

                for ink,magic_words in s.cartridge:
                    for word in magic_words:
                        if spl[1].startswith(word):
                            s.template.append ( (u'', ink, u'') )
                            tail = spl[1][len(word):]
                            break
                    else: continue
                    break
                else:
                    return False
            else:
                ppspl = tail.split('%', 2)
                if len (ppspl) != 3:
                    return False
                if ppspl[0] != u'':
                    s.template.append(ppspl[0])
                spl = ppspl[1].split('$', 1)
                if len(spl) != 2:
                    return False

                tail = ppspl[2]
                for ink,magic_words in s.cartridge:
                    for word in magic_words:
                        if spl[1].startswith(word):
                            s.template.append ( ( spl[0], ink, spl[1][len(word):] ) )
                            break
                    else: continue
                    break
                else:
                    return False

        return True

class EncoderProfile(SongPrinter):
    def __init__(s):
        s.name = "profile_name"
        s.encoder = "encoder_name"
        s.encoder_opts =[]# [(optname, optvalue), ...]
        s.muxer = None
        s.muxer_opts = []
        s.filters = []# [(filter_name, on, [(optname, optvalue)]],...)
        s.tag_type = "id3"
        SongPrinter.__init__(s)


    def Save(s):
        ret = {}
        ret['name'] = s.name
        ret['encoder_name'] = s.encoder
        ret['encoder_args'] = s.encoder_opts
        ret['muxer_name'] = s.muxer
        ret['muxer_args'] = s.muxer_opts
        ret['filters'] = s.filters
        ret['path'] = s.template_str
        ret['tag'] = s.tag_type
        return ret

    def Load(s, inst):
        s.name = inst['name']
        s.encoder = inst['encoder_name']
        s.encoder_opts = inst['encoder_args']
        s.muxer = inst['muxer_name']
        s.muxer_opts = inst['muxer_args']
        s.filters = inst['filters']
        s.template_str = inst['path']
        s.tag_type = inst['tag']
        s.parse_file_template( s.template_str )

        
    def parse_file_template(s, template_str = u"%$artist%/%$date - %%$album%/%track $n - %$title.mp3"):
        return s.init_printer(template_str)

    def get_file_path(s, track):
        return s.print_song(track, replace_f = lambda x: x.replace('/', ':').replace('?', '') )

class Cheats:
    def LoadCheats(s):
        try:
            with open(os.path.join(s.peyote_config_dir, 'aerostat'), 'r') as f:
                pitch = f.read().strip()
                s.aerostat_pitch = float(pitch)
        except Exception,e:
            s.aerostat_cheat = False
        else:
            s.aerostat_cheat = True

def _mkdir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, 0700 )
        return True
    return False

class  Notification:
    def __init__(s):
        s.notification_string = u'notify-send "%title" "by %artist\\n%album"'
        s.do_notify = False
class Skin:
    def __init__(s, skin_name, skin_dir, cfg = config):
        s.skin_name = skin_name
        s.skin_file = skin_name + SKIN_POSTFIX
        if skin_dir == cfg.peyote_skins_dir:
            s.mode = "RW"
        else:
            s.mode = "RO"
        s.skin_dir = skin_dir
        s.skin_path = os.path.join(skin_dir, s.skin_file)
    def __eq__(s, e):
        if s.skin_path == e.skin_path:
            return True

        return False

class Directories:
    def list_skins(s):
        try:
            ret = map( lambda n: Skin( n[:-len(SKIN_POSTFIX)], s.peyote_skins_dir, s )
                , filter( lambda x: x.endswith(SKIN_POSTFIX), sorted(os.listdir(s.peyote_skins_dir)) )  )
        except:
            ret = []
        try:
            ret += map( lambda n: Skin( n[:-len(SKIN_POSTFIX)], s.preset_skins_dir, s )
                , filter( lambda x: x.endswith(SKIN_POSTFIX), sorted(os.listdir(s.preset_skins_dir)) ) )
        except:
            pass
        
        if s.current_skin not in ret:
            ret.append( s.current_skin )

        return ret

    def __init__(s):
        s.home_dir = unicode( os.getenv('HOME') )
        s.peyote_config_dir = os.path.join(s.home_dir, '.config/peyote')
        s.peyote_local_dir = os.path.join(s.home_dir, '.local/share/peyote')
        s.peyote_cache_dir = os.path.join(s.home_dir, '.cache/peyote')

        s.config_file = os.path.join(s.peyote_config_dir, 'config.pickle')
        s.terminal_file = os.path.join(s.peyote_config_dir, 'terminal.conf')
        s.lyrics_dir = os.path.join( s.peyote_cache_dir, 'lyrics' )
        s.peyote_skins_dir = os.path.join(s.peyote_local_dir, 'skins')
        s.preset_skins_dir = os.path.join(SHARE_DIR, 'skins')

        s.session_file = os.path.join(s.peyote_local_dir, 'session.data')
        s.equalizer_file = os.path.join(s.peyote_local_dir, 'equalizers.pickle')
        s.session_file = os.path.join(s.peyote_local_dir, 'session.data')
        s.skulls_file = os.path.join(s.peyote_local_dir, 'graveyard')
        s.locations_file = os.path.join(s.peyote_local_dir, 'locations')
        s.locations_bad_file = os.path.join(s.peyote_local_dir, 'locations.bad')
        s.crash_report_file = os.path.join(s.peyote_local_dir, 'crash-report')
        s.current_skin_name_file = os.path.join(s.peyote_local_dir, 'current_skin' )
        s.current_skin = Skin('default', s.peyote_skins_dir, s)

        s.aliases_file = os.path.join( s.peyote_local_dir, 'aliases.pickle' )
        if _mkdir(s.peyote_cache_dir):
            prev_conf_dir = os.path.join(s.home_dir, '.peyote')
            #copy lyrics
            for prev_lyrics_dir in [os.path.join(prev_conf_dir, 'lyrics'), os.path.join(s.peyote_local_dir, 'lyrics') ]:
                if os.path.exists( prev_lyrics_dir ) and not os.path.islink(prev_lyrics_dir):
                    try: shutil.copytree(prev_lyrics_dir, s.lyrics_dir)
                    except: pass
                    break

            prev_lyrics_dir = os.path.join( prev_conf_dir, 'lyrics')
            if os.path.exists( prev_lyrics_dir ):
                try:
                    os.remove( prev_lyrics_dir )
                except:
                    try: shutil.rmtree(prev_lyrics_dir)
                    except: pass
                try: os.symlink(s.lyrics_dir,  prev_lyrics_dir )
                except: pass

            prev_lyrics_dir = os.path.join(s.peyote_local_dir, 'lyrics')
            if os.path.exists( prev_lyrics_dir ):
                try: shutil.rmtree(prev_lyrics_dir)
                except: pass

    
        if _mkdir(s.peyote_config_dir):
            prev_conf_dir = os.path.join(s.home_dir, '.peyote')
            if os.path.exists( prev_conf_dir ):
                try: os.link( os.path.join(prev_conf_dir, 'config.pickle'), s.config_file )
                except: pass
                try: os.link( os.path.join(prev_conf_dir, 'terminal.conf'), s.terminal_file )
                except: pass
        if _mkdir(s.peyote_local_dir):
            _mkdir(s.peyote_skins_dir)
            prev_conf_dir = os.path.join(s.home_dir, '.peyote')
            if os.path.exists( prev_conf_dir ):
                try: os.link( os.path.join(prev_conf_dir, 'session.data'), s.session_file )
                except: pass
                try: os.link( os.path.join(prev_conf_dir, 'scheme.pickle'), s.current_skin.skin_path)
                except: pass
                try: os.link( os.path.join(prev_conf_dir, 'graveyard'), s.skulls_file )
                except: pass
                try: os.link( os.path.join(prev_conf_dir, 'aliases.pickle'), s.aliases_file )
                except: pass
                try: os.link( os.path.join(prev_conf_dir, 'locations'), s.locations_file )
                except: pass
        else:
            _mkdir(s.peyote_skins_dir)
        _mkdir(s.lyrics_dir)

class Settings(Cmd, EqualizerSettings, Cheats, Skulls, Directories, Notification):
    def __init__(s):
        EqualizerSettings.__init__(s)
        Cmd.__init__(s)
        Directories.__init__(s) 
        Notification.__init__(s)
        try:
            with open(s.current_skin_name_file,"r") as f:
                skin = f.read()
            if skin != "":
                spl = skin.split('\n')
                if len(spl) == 1:
                    skin_name = skin
                    skin_mode = "RW"
                else:
                    skin_name,skin_mode = spl
                if skin_mode == "RW":
                    s.current_skin = Skin(skin_name, s.peyote_skins_dir, s)
                else:
                    s.current_skin = Skin(skin_name, s.preset_skins_dir, s)
        except:
            pass

        s.album_aliases = {}
        s.artist_aliases = {'The Mamas And The Papas'.lower() : 'The Mamas & The Papas',
                    'Mamas And Papas'.lower() : 'The Mamas & The Papas',
                    'Mamas And Papas'.lower() : 'The Mamas & The Papas',
                    'Beatles'.lower() : 'The Beatles' }
        s.title_aliases = {}

        s.alias_using = [True, #0 player
                 True, #1 fs
                 True, #2 playlist
                 True, #3 lyrics
                 True, #4 encoder
                 True, #5 d-bus
                 True, #6 equalizer
                 True] #7 last.fm
        s.song_title_formats = None
        s.audio_extensions = None
        s.secondary_encoding = None
        s.audio_player = {}
        s.default_playlist = None
        s.equalizer = None
        s.prefered_applications = None
        s.mixer = None
        s.iso8859detection = None
        s.remove_cdno_from_album_name = None
        s.shoutcast_RpP = None
        s.shoutcast_sort = None
        s.lastfm_user = None
        s.lastfm_md5 = None
        s.lastfm_scrobbler = False
        s.lastfm_scrobble_radio = True
        s.autopanel = False
        s.autopanel_width = 70

        s.alias_using_names = { 0: 'player',
                    1: 'fs',
                    2: 'playlist',
                    3: 'lyrics',
                    4: 'encoder',
                    5: 'd-bus',
                    6: 'equalizer',
                    7: 'last.fm'}
        s.encoder_profiles = None

        s.LoadSkulls()
        s.ResetIcons()
        s.color_scheme = ColorScheme()
        s.playing_track_left = SongPrinter(0)
        s.playing_track_right = SongPrinter(0)
        s.playing_track_bottom = SongPrinter(0)
        s.playing_track_left.init_printer(u"%♬ $title %")
        s.playing_track_right.init_printer(u'%☺ $artist %☸ %$year - %$album ☸')
        s.playing_track_bottom.init_printer(u'☀ $ext %$bitrate kbps%')
        s.hide_keybar = False
        #XSPF
        s.xspf_vlc_compatibility = False
        s.xspf_audacious_compatibility = False
        s.xspf_qmmp_compatibility = False
        s.xspf_check_http = True
        s.xspf_reload_file = True
        s.vk_token = u""
        #s.LoadScheme()
    
    def ResetIcons(s):
        s.equalizer_chars = [u'▨', u'□']
        s.track_status_chars = [u'☒', u'◻']
        s.progress_bar_chars = [u'◼', u'◻']
        s.playing_bar_chars = [u'◼', u'◻']
        s.audio_player_cursors = [u'♫', u'✈', u'↺']
        s.cue_char = u'☯'
        s.tree_chars = [u'▸', u'▾']
        s.config_chars = [u'◉', u'○', u'❖']
        s.bracelet_chars = [u'☮', u'☸']
        s.dice_chars =  [u'⚀', u'⚁', u'⚂', u'⚃', u'⚄', u'⚅']
        s.repeat_char = [u'♺']
        s.equalizer_holding_chars = [u'⚪' ,u'⚫']
        s.direction_chars = [ u'⇩', u'⇧', u'↯', u'⇨' ]
        s.keybar_navigation_chars = [u'☚', u'☝', u'☛']
        s.scroll_bar_chars = [u'╿', u'╽', u'│', u'|']
        s.curse_char = [u'☠']
        s.points_char = [u'…']

    def DoISO8859Check(s):
        return s.iso8859detection

    def ResetTerminal(s):
        try: os.unlink(s.terminal_file)
        except: pass

    def GetTerminal(s):
        try:
            with open (s.terminal_file, 'r') as f:
                terminal = f.read().strip('\n').rstrip('\n').split("=",1)[1].replace("${PEYOTE_BIN}", "%peyote")[1:-1].replace('\\"', '"').strip().rstrip()
        except:
            return DEFAULT_TERMINAL

        return terminal.replace("${PEYOTE_BIN}", "%peyote")

    def SaveTerminal(s, terminal):
        with open (s.terminal_file, 'w') as f:
            f.write( u'TERMX="%s"' % terminal.replace("%peyote", "${PEYOTE_BIN}").replace('"', '\\"' ) )

    def LoadAliases(s):
        try:
            with open (s.aliases_file, 'r') as f:
                s.artist_aliases = pickle.load(f)
                s.album_aliases  = pickle.load(f)
        except:
            pass
    def SaveAliases(s):
        with open (s.aliases_file, 'w') as f:
            pickle.dump(s.artist_aliases, f)
            pickle.dump(s.album_aliases, f)


    def Default(s):
        ret = True
        if not s.default_playlist:
            s.default_playlist = os.path.join( s.home_dir, 'peyote.xspf' )
            ret = False

        if not s.audio_player.has_key('audio_sink'):
            s.audio_player['audio_sink'] = 'autoaudiosink'
            s.audio_player['audio_sink_params'] = []
            ret = False
        if not s.audio_player.has_key('pre_sinks'):
            s.audio_player['pre_sinks'] = []
            ret = False

        if not s.audio_player.has_key('crossfade'):
            s.audio_player['crossfade'] = False
            s.audio_player['crossfade_time'] = 3.0
            s.audio_player['fade_in'] = 'Linear'
            s.audio_player['fade_out'] = 'Linear'
            ret = False

        if not s.secondary_encoding:
            s.secondary_encoding = 'cp1251'
            ret = False

        if not s.audio_extensions:
            s.audio_extensions = [ ["flac", "wav", "wave", "wv", "mpc"], [ "ogg", "oga" ], ["mp3", "wma", "ape", "m4a", 'aif', "mpa"] ]
            ret = False
        if not s.song_title_formats:
            s.song_title_formats = { "playlist" : [], "fs": [] }

        s.playlist_title_formats = s.song_title_formats['playlist']
        s.fs_title_formats = s.song_title_formats['fs']


        if not s.playlist_title_formats:
            s.playlist_title_formats.append( ( ['status', 'title'], ['artist', 'album', 'time'] ) )
            s.playlist_title_formats.append( ( ['status', 'title'], ['artist', 'time'] ) )
            s.playlist_title_formats.append( ( ['status', 'title'], ['date', 'album', 'time'] ) )
            s.playlist_title_formats.append( ( ['status', 'title'], ['time'] ) )
            ret = False
        if not s.fs_title_formats:
            s.fs_title_formats.append( ( ['status', 'cue', 'id', 'title'], ['time'] ) )
            s.fs_title_formats.append( ( ['status', 'cue', 'id', 'title'], ['artist', 'album', 'time'] ) )
            s.fs_title_formats.append( ( ['status', 'cue', 'id', 'title'], ['album', 'time'] ) )
            s.fs_title_formats.append( ( ['status', 'cue', 'id', 'title'], ['artist', 'time'] ) )
            ret = False
        if not s.prefered_applications:
            s.prefered_applications = [
                            ( ['jpg', 'jpeg', 'gif', 'png', 'tif', 'tiff', 'xcf', 'bmp'], u"geeqie %file" )
                           ,( ['mpg', 'mpeg', 'avi','ts', 'mpeg', 'mp4', 'vob', 'mkv'], u'mplayer -fs %file' )
                          ]
            ret = False
        if not s.mixer:
            s.mixer = {}
            s.mixer [ 'plugin' ] = 'alsamixer'
            s.mixer [ 'properties' ] = [ ]
            s.mixer [ 'track_no' ] = 0
            s.mixer [ 'step' ] = 1.0
            ret = False

        if s.shoutcast_RpP == None:
            s.shoutcast_RpP = 10
            ret = False

        if s.shoutcast_sort == None:
            s.shoutcast_sort = "bitrate"
            ret = False

        if len(s.alias_using) < 8:
            for i in range(8-len(s.alias_using)):
                s.alias_using.append(True)
            ret = False

        if s.encoder_profiles == None:
            s.encoder_profiles = {}
            enc = {}
            enc['name'] =u"mp3"
            enc['encoder_name'] = u"lamemp3enc"
            enc['encoder_args'] = [ ('cbr', True), ('target', 1), ('bitrate', 320) ]
            enc['muxer_name'] = None
            enc['muxer_args'] = []
            enc['filters'] = []
            enc['path'] = u"%$artist%/%$date - %%$album%/%track $n - %$title.mp3"
            enc['tag'] = 'id3'
            profile = EncoderProfile()
            profile.Load(enc)
            s.encoder_profiles[profile.name] = profile
            enc['name'] =u"oggvorbis"
            enc['encoder_name'] = u"vorvisenc"
            enc['encoder_args'] = [ ('quality', 0.7) ]
            enc['muxer_name'] = u"oggmux"
            enc['muxer_args'] = []
            enc['filters'] = []
            enc['path'] = u"%$artist%/%$date - %%$album%/%track $n - %$title.oga"
            enc['tag'] = 'oggvorbis'
            profile = EncoderProfile()
            profile.Load(enc)
            s.encoder_profiles[profile.name] = profile
            ret = False
        if s.iso8859detection == None:
            if s.secondary_encoding == 'cp1251':
                s.iso8859detection = True
            else:
                s.iso8859detection = False
            ret = False

        if s.remove_cdno_from_album_name == None:
            s.remove_cdno_from_album_name = False
            ret = False
 
        return ret
    
    def SaveCurrentSkinName(s):
        try:
            with open(s.current_skin_name_file, "w") as f:
                f.write("%s\n%s" % (s.current_skin.skin_name, s.current_skin.mode) )
        except:
            pass

    def SaveSchemeAs(s, skin_name):
        if s.current_skin.mode == "RW":
            os.unlink( s.current_skin.skin_path )
        s.current_skin = Skin(skin_name, s.peyote_skins_dir, s)
        s.SaveScheme()

    def SaveScheme(s):
        icons = { 'equalizer' : s.equalizer_chars,
              'track_status' : s.track_status_chars,
              'playing_bar' : s.playing_bar_chars,
              'audio_player_cursors' : s.audio_player_cursors,
              'cue' : s.cue_char,
              'tree' : s.tree_chars,
              'config' : s.config_chars,
              'friendship bracelet' : s.bracelet_chars,
              'equalizer holding' : s.equalizer_holding_chars,
              'dice' : s.dice_chars,
              'repeat' : s.repeat_char,
              'direction' : s.direction_chars,
              'keybar_navigation' : s.keybar_navigation_chars,
              'progress bar' : s.progress_bar_chars,
              'scroll bar': s.scroll_bar_chars,
              'curse': s.curse_char,
              'points' : s.points_char            }
        try:
            if s.current_skin.mode == "RO":
                s.current_skin = Skin(s.current_skin.skin_name, s.peyote_skins_dir,  s)
                s.SaveCurrentSkinName()

            with open(s.current_skin.skin_path, "w") as f:
                pickle.dump(s.color_scheme.Save(), f)
                pickle.dump( icons, f )
                pickle.dump(s.color_scheme.palette.Save(), f)
                pickle.dump( [ s.playing_track_left.template_str,
                    s.playing_track_right.template_str,
                    s.playing_track_bottom.template_str ], f )

        except Exception, e:
            pass

    def LoadScheme(s):
        if not os.path.exists(s.current_skin.skin_path):
            return False
        try:
            with open(s.current_skin.skin_path, "r") as f:
                s.color_scheme.Load( pickle.load(f) )
                try:
                    icons = pickle.load(f)
                    if len(icons['equalizer']) == len(s.equalizer_chars):
                        s.equalizer_chars = icons['equalizer']
                    if len(icons['track_status']) == len(s.track_status_chars):
                        s.track_status_chars = icons['track_status']
                    if len(icons['playing_bar']) == len(s.playing_bar_chars):
                        s.playing_bar_chars = icons['playing_bar']
                    if len(icons['audio_player_cursors']) == len(s.audio_player_cursors):
                        s.audio_player_cursors = icons['audio_player_cursors']
                    if len(icons['cue']) == len(s.cue_char):
                        s.cue_char = icons['cue']
                    if len(icons['tree']) == len(s.tree_chars):
                        s.tree_chars = icons['tree']
                    if len(icons['config']) == len(s.config_chars):
                        s.config_chars = icons['config']
                    if len(icons['friendship bracelet']) == len(s.bracelet_chars):
                        s.bracelet_chars = icons['friendship bracelet']
                    if len(icons['equalizer holding']) == len(s.equalizer_holding_chars):
                        s.equalizer_holding_chars = icons['equalizer holding']
                    if len(icons['dice']) == len(s.dice_chars):
                        s.dice_chars = icons['dice']
                    if len(icons['direction']) == len(s.direction_chars):
                        s.direction_chars = icons['direction']
                    if len(icons['keybar_navigation']) == len(s.keybar_navigation_chars):
                        s.keybar_navigation_chars = icons['keybar_navigation']
                    if len(icons['repeat']) == 1:
                        s.repeat_char = icons['repeat']
                    if len(icons['progress bar']) == len(s.progress_bar_chars):
                        s.progress_bar_char = icons['progress bar']
                    if len(icons['scroll bar']) == len(s.scroll_bar_chars):
                        s.scroll_bar_chars = icons['scroll bar']
                    if len(icons['curse']) == 1:
                        s.curse_char = icons['curse']
                    if len(icons['points']) == 1:
                        s.points_char = icons['points']

                except Exception,e:
                    pass
                try:
                    palette = pickle.load(f)
                except:
                    pass
                else:
                    try:
                        s.color_scheme.LoadPalette( palette )
                        s.color_scheme.generate_palette()
                    except:
                        pass
                try:
                    templates = pickle.load(f)
                except:
                    pass
                else:
                    try:
                        s.playing_track_left.init_printer(templates[0])
                    except:
                        s.playing_track_left.init_printer(u"%♬ $title %")
                    try:
                        s.playing_track_right.init_printer(templates[1])
                    except:
                        s.playing_track_right.init_printer(u'%☺ $artist %☸ %$year - %$album ☸')
                    try:
                        s.playing_track_bottom.init_printer(templates[2])
                    except:
                        s.playing_track_bottom.init_printer(u'☀ $ext %$bitrate kbps%')
        except:
            return

            
    def Save(s):
        with open(s.config_file, "w") as f:
            pickle.dump( ('secondary_encoding', s.secondary_encoding), f )
            pickle.dump( ('iso8859-1_detection', s.iso8859detection), f )
            pickle.dump( ('default_playlist', s.default_playlist), f )
            pickle.dump( ('audio_player', s.audio_player), f )
            pickle.dump( ('audio_extensions', s.audio_extensions), f )
            pickle.dump( ('song_title_formats', s.song_title_formats), f )
            pickle.dump( ('remove_cdno_from_album_name', s.remove_cdno_from_album_name), f )
            pickle.dump( ('prefered_applications', s.prefered_applications), f)
            pickle.dump( ('mixer', s.mixer), f)
            pickle.dump( ('alias using', s.alias_using), f)
            encoders = map( lambda k: s.encoder_profiles[k].Save(), s.encoder_profiles.keys() )
            pickle.dump( ('encoders', encoders), f)
            pickle.dump( ('hide keybar', s.hide_keybar ), f )
            shoutcast = { 'results_per_page' : s.shoutcast_RpP, 'sort' : s.shoutcast_sort }
            pickle.dump( ('shoutcast', shoutcast), f )
            pickle.dump( ('notification', (s.do_notify, s.notification_string)), f )
            pickle.dump( ('lastfm_scrobbler' , s.lastfm_scrobbler), f)
            pickle.dump( ('lastfm_scrobble_radio' , s.lastfm_scrobble_radio), f)
            pickle.dump( ('lastfm_user' , s.lastfm_user), f )
            pickle.dump( ('lastfm_md5' , s.lastfm_md5), f )
            pickle.dump( ('xspf_reload_file' , s.xspf_reload_file), f )
            pickle.dump( ('xspf_check_http' , s.xspf_check_http), f )
            pickle.dump( ('xspf_vlc_compatibility' , s.xspf_vlc_compatibility), f )
            pickle.dump( ('xspf_audacious_compatibility' , s.xspf_audacious_compatibility), f )
            pickle.dump( ('xspf_qmmp_compatibility' , s.xspf_qmmp_compatibility), f )
            pickle.dump( ('autopanel' , s.autopanel), f )
            pickle.dump( ('autopanel_width' , s.autopanel_width), f )
            pickle.dump( ('vk_token', s.vk_token), f )

            pickle.dump( ("END", {}), f )
    def Load(s):
        try:
            s.UnsafeLoad()
        except IOError:
            s.Default()
            s.Save()
        else:
            rc = s.Default()
            if not rc:
                s.Save()
        s.LoadAliases()
        s.LoadCheats()
    def UnsafeLoad(s):
        with open(s.config_file, "r") as f:
            while True:
                object_name, object_value = pickle.load(f)
                if object_name == 'END':
                    break
                if object_name == 'default_playlist':
                    s.default_playlist = object_value
                elif object_name == 'secondary_encoding':
                    s.secondary_encoding = object_value
                elif object_name == 'iso8859-1_detection':
                    s.iso8859detection = object_value
                elif object_name == 'audio_player':
                    s.audio_player = object_value
                elif object_name == 'audio_extensions':
                    s.audio_extensions = object_value
                elif object_name == 'song_title_formats':
                    s.song_title_formats = object_value
                elif object_name == 'prefered_applications':
                    s.prefered_applications = object_value
                elif object_name == 'mixer':
                    s.mixer = object_value
                elif object_name == 'alias using':
                    s.alias_using = object_value
                elif object_name == 'encoders':
                    s.encoder_profiles = {}
                    for e in object_value:
                        s.encoder_profiles[e['name']] = EncoderProfile()
                        s.encoder_profiles[e['name']].Load(e)
                elif object_name == 'remove_cdno_from_album_name':
                    s.remove_cdno_from_album_name = object_value
                elif object_name == 'hide keybar':
                    s.hide_keybar = object_value
                elif object_name == 'shoutcast':
                    s.shoutcast_RpP = object_value.get('results_per_page', 10)
                    s.shoutcast_sort = object_value.get('sort', 'bitrate')
                elif  object_name == 'notification':
                    s.do_notify = object_value[0]
                    s.notification_string = object_value[1]
                elif object_name == 'lastfm_scrobbler':
                    s.lastfm_scrobbler = object_value
                elif object_name == 'lastfm_scrobble_radio':
                    s.lastfm_scrobble_radio = object_value
                elif object_name == 'lastfm_user':
                    s.lastfm_user = object_value
                elif object_name == 'lastfm_md5':
                    s.lastfm_md5 = object_value
                elif object_name == 'xspf_audacious_compatibility':
                    s.xspf_audacious_compatibility = object_value
                elif object_name == 'xspf_vlc_compatibility':
                    s.xspf_vlc_compatibility = object_value
                elif object_name == 'xspf_qmmp_compatibility':
                    s.xspf_qmmp_compatibility = object_value
                elif object_name == 'xspf_reload_file':
                    s.xspf_reload_file = object_value
                elif object_name == 'xspf_check_http':
                    s.xspf_check_http = object_value
                elif object_name == 'autopanel':
                    s.autopanel = object_value
                elif object_name == 'autopanel_width':
                    s.autopanel_width = object_value
                elif object_name == 'vk_token':
                    s.vk_token = object_value


    def GetAudioExtensions(s):
        return s.audio_extensions[0] + s.audio_extensions[1] + s.audio_extensions[2]

    def GetSCEnc(s):
        if s.cmd.has_key('secondary_encoding'):
            return s.cmd['secondary_encoding']
        return s.secondary_encoding
    def DefaultPlaylist(s):
        if not os.path.isfile(s.default_playlist):
            open(s.default_playlist, "w").close()
        return s.default_playlist

import curses
from curses import COLOR_BLACK , COLOR_RED , COLOR_GREEN , COLOR_YELLOW , COLOR_BLUE , COLOR_MAGENTA , COLOR_CYAN , COLOR_WHITE , A_BOLD, A_UNDERLINE
c = curses

class DefaultColor:
    def __init__(s, no, f1, f2 = None, opts = None):
        if f2 == None:
            s._init2( no, f1)
        else:
            s.trio = (f1,f2,opts)
            s.duet = (no, opts)
            s.olo  = (f1,f2)
    def _init2(s, no, t):
        s.trio = (t.f, t.b, t.opts)
        s.duet = (no, t.opts)
        s.olo = (t.f, t.b)
    def get_colors(s):
        return s.olo
    def get_pair_no(s):
        return s.duet[0]
    def get_args(s):
        return s.duet[1]

#initialize color matrixs
id_color_matrix = { -1 : "transparent",
    COLOR_BLACK : "black", 
    COLOR_RED : "red",
    COLOR_GREEN : "green",
    COLOR_YELLOW : "yellow",
    COLOR_BLUE : "blue",
    COLOR_MAGENTA : "magenta",
    COLOR_CYAN : "cyan",
    COLOR_WHITE : "white" }
color_id_matrix = {}
for k in id_color_matrix.keys():
    v = id_color_matrix[k]
    color_id_matrix[v] = k
additional_colors = {
    1 + COLOR_WHITE + COLOR_BLACK  : (0,0,0),
    1 + COLOR_WHITE + COLOR_RED    : (1000, 0, 0),
    1 + COLOR_WHITE + COLOR_GREEN  : (0, 1000, 0),
    1 + COLOR_WHITE + COLOR_YELLOW : (1000, 1000, 0),
    1 + COLOR_WHITE + COLOR_BLUE   : (0, 0, 1000),
    1 + COLOR_WHITE + COLOR_MAGENTA: (1000, 0, 1000),
    1 + COLOR_WHITE + COLOR_CYAN   : (0, 1000, 1000),
    1 + COLOR_WHITE + COLOR_WHITE  : (1000,1000,1000)
}

palette = None
config = None
class ColorTrio:
    def __init__(s, f, b, opts):
        global palette,config
        s.f = f
        s.b = b

        if palette and s.f not in palette.colors.keys():
            s.f = s.f - COLOR_WHITE - 1
        if palette and s.b not in palette.colors.keys():
            s.b = s.b - COLOR_WHITE - 1
        s.opts = opts

    def bg(s):
        try:
            return palette.colors[s.b].name
        except:
             return palette.colors[s.b - COLOR_WHITE - 1].name

    def fg(s):
        try:
            return palette.colors[s.f].name
        except:
            return palette.colors[s.f - COLOR_WHITE - 1].name

    def inc_bg(s):
        s.b+=1
        if s.b not in palette.colors.keys():
            s.b = -1
    def inc_fg(s):
        s.f+=1
        if s.f not in  palette.colors.keys():
            s.f = 0
    def bold(s):
        if s.opts&A_BOLD:
            return True
        else:
            return False
    def ch_bold(s):
        if s.opts&A_BOLD:
            s.opts = 0
        else:
            s.opts = A_BOLD
    def get_tuple(s):
        return (s.f, s.b, s.opts)
    
colors = {}
class Color:
    r = 0
    g = 0
    b = 0
    default = False
    
    def __init__(s, no, name = u''):
        s.no = no
        if s.no <= COLOR_WHITE:
            s.name = id_color_matrix[s.no]
            s.default = True
        else:
            s.name = _(id_color_matrix[s.no - COLOR_WHITE - 1]) + "(2)"
        try:
            s.get_rgb()
        except:
            pass

    def get_rgb(s):
        if s.no == -1:
            return (0,0,0)
        s.r, s.g, s.b = curses.color_content(s.no)
        return( s.r, s.g, s.b )

    def change_rgb(s, r=None, g=None, b=None):
        if r != None:
            s.r = r

        if g != None:
            s.g = g

        if b != None:
            s.b = b

        if curses.can_change_color():
            curses.init_color(s.no, s.r, s.g, s.b)
    def save(s):
        return (s.name, s.r, s.g, s.b)

    def init_color(s):
        if curses.can_change_color():
            curses.init_color(s.no, s.r, s.g, s.b)

class Palette:
    def __init__(s, sets = None):
        s.colors = {}
        for no in range(-1, COLOR_WHITE+1):
            s.colors[no] = Color(no)
        s.can_change_color = curses.can_change_color()
        if s.can_change_color and curses.COLORS >= 2*(COLOR_WHITE + 1):
            for no in range(COLOR_WHITE+1, 2*(COLOR_WHITE + 1)):
                s.colors[no] = Color(no)
        if sets:
            for no in sets.keys():
                try:
                    s.colors[no].name = sets[no][0]
                    s.colors[no].change_rgb(r = sets[no][1], g = sets[no][2], b =  sets[no][3] )
                except:
                    pass
        elif s.can_change_color and curses.COLORS >= 2*(COLOR_WHITE + 1):
            for no in range(COLOR_WHITE+1, 2*(COLOR_WHITE + 1)):
                rgb = additional_colors[no]
                s.colors[no].change_rgb( r = rgb[0], g = rgb[1], b = rgb[2] )

        s.length = len( s.colors.keys() )

    def Save(s):
        ret = {}
        for no in s.colors.keys():
            ret[no] = s.colors[no].save()
        return ret
    


class ColorScheme:
    def __getitem__(s, name):
        if name == 'panel':
            return s.panel
        if name == 'player':
            return s.player
        if name == 'pop-up window':
            return s.popup
        return s.key_bar
    
    def Save(s):
        scheme = {}
        scheme['panel']        = map( lambda k: [ k, s.panel[k].get_tuple() ], s.get_seq('panel'))
        scheme['player']    = map( lambda k: [ k, s.player[k].get_tuple() ], s.get_seq('player'))
        scheme['pop-up window']    = map( lambda k: [ k, s.popup[k].get_tuple() ], s.get_seq('pop-up window'))
        scheme['key bar']    = map( lambda k: [ k, s.key_bar[k].get_tuple() ], s.get_seq('key bar'))
        return scheme
    def LoadPalette(s, dct):
        s.palette_sets = dct

    def Load(s, dct):
        for ss in dct.keys():
            part = s[ss]
            for k in dct[ss]:
                if part.has_key ( k[0] ):
                    part[ k[0] ] = ColorTrio ( k[1][0], k[1][1], k[1][2] )

    def get_seq(s, name):
        if name == 'panel':
            return [ 'body', 'border', 'active header', 'passive header',
                'cursor', 'pointer', 'pointer & cursor', 'tagged item',
                'directory', 'song1', 'song1(c2)', 'song2', 'song2(c2)', 'song3', 'song3(c2)', 'stream',
                'broken link', 'broken link(c2)', 'playlist', 'file', 'location1', 'location2',
                'lyrics', 'inputbox', 'inputbox cursor', 'scrollbar', 'scrollbar cursor', 
                'equalizer tag1', 'equalizer tag2', 'progress' ]
        if name == 'player':
            return [ 'body', 'time']
        if name == 'pop-up window':
            return ['body', 'active button', 'progress', 'inputbox', 'inputbox cursor' ]
        if name == 'key bar':
            return ['name', 'key']

    def __init__(s, BG=COLOR_BLUE):
        s.palette_sets = None
        s.palette = None
        s.panel    = {}
        s.popup   = {}
        s.player  = {}
        s.key_bar = {}

        s.panel['body'] = ColorTrio(COLOR_WHITE, BG, 0)
        s.panel['border'] = ColorTrio(COLOR_WHITE, BG, 0)
        s.panel['active header'] = ColorTrio(COLOR_WHITE, BG, A_BOLD)
        s.panel['passive header'] = ColorTrio(COLOR_WHITE, BG, 0)
        s.panel['cursor'] = ColorTrio(COLOR_BLACK, COLOR_CYAN, 0)
        s.panel['pointer'] = ColorTrio(COLOR_CYAN, BG, A_BOLD)
        s.panel['pointer & cursor'] = ColorTrio(COLOR_YELLOW, COLOR_CYAN, A_BOLD)
        s.panel['tagged item'] = ColorTrio(COLOR_YELLOW, BG, A_BOLD)
        s.panel['directory'] = ColorTrio(COLOR_WHITE, BG, A_BOLD)
        s.panel['song1'] = ColorTrio(COLOR_WHITE, BG, 0)
        s.panel['song2'] = ColorTrio(c.COLOR_GREEN, BG, 0)
        s.panel['song3'] = ColorTrio(COLOR_CYAN, BG, 0)
        s.panel['broken link'] = ColorTrio(COLOR_RED, BG, A_BOLD)
        s.panel['song1(c2)'] = ColorTrio(COLOR_WHITE, BG, A_BOLD)
        s.panel['song2(c2)'] = ColorTrio(c.COLOR_GREEN, BG, A_BOLD)
        s.panel['song3(c2)'] = ColorTrio(COLOR_CYAN, BG, A_BOLD)
        s.panel['broken link(c2)'] = ColorTrio(COLOR_RED, BG, A_BOLD)
        s.panel['stream'] = ColorTrio(COLOR_MAGENTA, BG, 0)
        s.panel['playlist'] = ColorTrio(COLOR_WHITE, BG, A_BOLD)
        s.panel['file'] = ColorTrio(COLOR_MAGENTA, BG, A_BOLD)
        s.panel['location1'] = ColorTrio(COLOR_GREEN, BG, A_BOLD)
        s.panel['location2'] = ColorTrio(COLOR_CYAN, BG, 0)
        s.panel['lyrics'] = ColorTrio(COLOR_WHITE, BG, A_BOLD)
        s.panel['inputbox'] = ColorTrio(COLOR_BLACK, COLOR_CYAN, 0)
        s.panel['inputbox cursor'] = ColorTrio(COLOR_CYAN, COLOR_BLACK, 0)
        s.panel['scrollbar'] = ColorTrio(COLOR_YELLOW, COLOR_BLUE, 0)
        s.panel['scrollbar cursor'] = ColorTrio(COLOR_YELLOW, COLOR_BLUE, A_BOLD)
        s.panel['equalizer tag1'] = ColorTrio(COLOR_WHITE, COLOR_BLUE, 0 )
        s.panel['equalizer tag2'] = ColorTrio(COLOR_CYAN, COLOR_BLUE, 0 )
        s.panel['progress'] = ColorTrio(COLOR_WHITE, COLOR_MAGENTA, A_BOLD )

        s.player['body'] = ColorTrio(COLOR_WHITE, COLOR_BLACK, 0)
        s.player['time'] = ColorTrio(COLOR_WHITE, COLOR_BLACK, 0)

        s.popup['body'] = ColorTrio(COLOR_WHITE, COLOR_MAGENTA, A_BOLD )
        s.popup['active button'] = ColorTrio(COLOR_BLACK, COLOR_GREEN, A_BOLD )
        s.popup['progress'] = ColorTrio(COLOR_BLACK, COLOR_CYAN, A_BOLD )
        s.popup['inputbox'] = ColorTrio(COLOR_WHITE, COLOR_BLACK, 0 )
        s.popup['inputbox cursor'] = ColorTrio (COLOR_BLACK, COLOR_WHITE,  0 )

        s.key_bar['name'] = ColorTrio(COLOR_WHITE, COLOR_BLACK, 0 )
        s.key_bar['key'] = ColorTrio(COLOR_WHITE, COLOR_BLACK, A_BOLD )

    def generate_palette(s):
        s.palette = Palette(s.palette_sets)
        global palette
        palette = s.palette

    def generate_colors(s):
        global colors
        colors['body']            = DefaultColor( 1, s.panel['body'] )
        colors['border']        = DefaultColor( 2, s.panel['border'] )

        colors['active header']        = DefaultColor( 3, s.panel['active header'] )
        colors['header']        = DefaultColor( 4, s.panel['passive header'] )

        colors['cursor']        = DefaultColor( 5, s.panel['cursor'].f, s.panel['cursor'].b, s.panel['cursor'].opts|A_UNDERLINE )
        colors['marker']        = DefaultColor( 6, s.panel['tagged item'] )
        colors['player']        = DefaultColor(31, s.panel['pointer'] )
        colors['cursor and marker']    = DefaultColor( 7, s.panel['tagged item'].f, s.panel['cursor'].b, s.panel['tagged item'].opts|A_UNDERLINE )
        colors['cursor and player']    = DefaultColor( 8, s.panel['pointer & cursor'] )

        colors['elm is dir']        = DefaultColor( 9, s.panel['directory'] )
        colors['elm is symdir']     = DefaultColor(10, s.panel['directory'] )
        colors['elm is media1']        = DefaultColor(11, s.panel['song1'] )
        colors['elm is media2']        = DefaultColor(12, s.panel['song2'] )
        colors['elm is media3']        = DefaultColor(13, s.panel['song3'] )
        colors['elm is playlist']    = DefaultColor(14, s.panel['playlist'] )
        colors['elm is fsfile']        = DefaultColor(15, s.panel['file'] )
        colors['system_location']    = DefaultColor(16, s.panel['location1'] )
        colors['user_location']        = DefaultColor(17, s.panel['location2'] )
        colors['lyrics']        = DefaultColor(18, s.panel['lyrics'] )

        colors['panel inputline']    = DefaultColor(19, s.panel['inputbox'] )
        colors['panel inputline cursor']= DefaultColor(20, s.panel['inputbox cursor'] )
        colors['fast search']         = DefaultColor(21, s.panel['inputbox'] )

        colors['scrollbar']         = DefaultColor(32, s.panel['scrollbar'] )
        colors['scrollbar cursor']    = DefaultColor(33, s.panel['scrollbar cursor'] )
        colors['equalizer tag1']    = DefaultColor(34, s.panel['equalizer tag1'] )
        colors['equalizer tag2']    = DefaultColor(35, s.panel['equalizer tag2'] )


        colors['player body']        = DefaultColor(22, s.player['body'] )
        colors['player time']        = DefaultColor(23, s.player['time'] )


        colors['yesno']            = DefaultColor(24, s.popup['body'] )
        colors['yesno active button']    = DefaultColor(25, s.popup['active button'] )
        colors['progress']        = DefaultColor(26, s.popup['progress'] )
        colors['textpad']        = DefaultColor(27, s.popup['inputbox'] )
        colors['textpad cursor']    = DefaultColor(28, s.popup['inputbox cursor'] )

        colors['button']        = DefaultColor(29, s.key_bar['name'])
        colors['button key']        = DefaultColor(30, s.key_bar['key'])
        #cur = 42
        colors['elm is media1(c2)']        = DefaultColor(36, s.panel['song1(c2)'] )
        colors['elm is media2(c2)']        = DefaultColor(37, s.panel['song2(c2)'] )
        colors['elm is media3(c2)']        = DefaultColor(38, s.panel['song3(c2)'] )
        colors['panel progress']        = DefaultColor(39, s.panel['progress'])
        colors['stream']            = DefaultColor(40, s.panel['stream'])
        colors['broken link']            = DefaultColor(41, s.panel['broken link'])
        colors['broken link(c2)']        = DefaultColor(42, s.panel['broken link(c2)'])
        generate_pair(colors)
        return colors

def Dice():
    return random.choice( config.dice_chars )

def generate_pair(colors):
    pair = dict()
    for name in colors.keys():
        try:
            c.init_pair(colors[name].get_pair_no(), colors[name].get_colors()[0], colors[name].get_colors()[1])
        except:
            c0 = colors[name].get_colors()[0]
            c1 = colors[name].get_colors()[1]
            if c0 > COLOR_WHITE:
                c0 = c0 - COLOR_WHITE - 1
            if c1 > COLOR_WHITE:
                c1 = c1 - COLOR_WHITE - 1
            c.init_pair(colors[name].get_pair_no(), c0, c1)
        pair[name] =  colors[name].get_pair_no()
    return pair

config = Settings()

def get_performer_alias(name, n):
    if not config.alias_using[n]:
        return name

    lname = name.lower()
    if config.artist_aliases.has_key(lname):
        return config.artist_aliases[lname]
    else:
        return name

def get_album_alias(name, n):
    if not config.alias_using[n]:
        return name
    lname = name.lower()
    if config.album_aliases.has_key(lname):
        return config.album_aliases[lname]
    else:
        return name

