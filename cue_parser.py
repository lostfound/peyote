#!/usr/bin/env python3

import os.path
import re


class CueTrack:
    def __init__(s, p: "CueSheets: parent object", no: "int: track number", file: "filename"):
        s.title = None
        s.p = p
        s.idx = {}
        s.no = no
        s.dur = None
        s.artist = None
        s.file = file

    def add_index(s, no: "int: number", pos: "float: time"):
        s.idx[no] = pos

    def calc_duration(s, next_track):
        if next_track.file == s.file:
            try:
                begin = s.idx[1] if 1 in s.idx else s.idx[0]
                s.dur = next_track.idx[0] - begin
            except Exception as e:
                s.dur = None

    def __str__(s):
        ret = "№ {0} {1} [{2}]".format(s.no, s.title, s.artist)
        ret += "\n  FILE: {1}/{0}".format(s.file, s.p.path)
        if s.dur:
            ret += "\n  duration: {0} min".format(round(s.dur/60, 2))
        ret += "\n  IDX: {0}".format(s.idx)
        return ret


class CueSheets:
    __re_name_args       = re.compile("([\w]+)[\s]+(.*)")
    __re_rem             = re.compile('([A-Z]+)[\s]+("(.*)"$|(.*$))')
    __re_quotestrip      = re.compile('^"(.*)"$|(.*)')
    __re_file            = re.compile('^"(.*)"[\s]+([\w]+)')
    __re_track           = re.compile('^[0]*([\d]+)')
    __re_index           = re.compile('^[0]*([\d])+[\s]+[0]*([\d]+):[0]*([\d]+):[0]*([\d])')

    def __init__(s, file_path: "A cue path"):
        s.warnings = []
        try:
            with open(file_path) as f:
                content = f.read()
                s.codepage = "utf-8"
        except UnicodeDecodeError:
            with open(file_path, encoding="cp1251") as f:
                content = f.read()
                s.codepage = "cp1251"
                s.warnings.append("cp1251 Codepage")
        s.path = os.path.dirname(os.path.abspath(file_path))
        s.rem = {}
        s.album = None
        s.artist= None
        s.tracks = []
        artist = None
        title  = None
        track  = None
        file   = None

        for line in [x.rstrip().strip() for x in content.split('\n')]:
            rer = s.__class__.__re_name_args.match(line)
            if not rer: continue

            arg_name = rer.group(1).upper()
            arg_value = rer.group(2)
            if arg_name == "REM":
                rer = s.__class__.__re_rem.match(arg_value)
                if not rer:
                    continue
                s.rem[rer.group(1)] = rer.group(3) if rer.group(3) else rer.group(4)

            elif arg_name in ["PERFORMER", "TITLE"]:
                rer = s.__class__.__re_quotestrip.match(arg_value)
                if not rer:
                    s.warnings.append("invalid performer")
                    continue
                value = rer.group(1) if rer.group(1) else rer.group(2)
                if arg_name.startswith("P"):
                    artist = value
                else:
                    title = value

            elif arg_name == "FILE":
                rer = s.__class__.__re_file.match(arg_value)
                if not rer:
                    s.warnings.append("invalid file")
                    continue
                file = rer.group(1)

            elif arg_name == "TRACK":
                rer = s.__class__.__re_track.match(arg_value)
                if not rer:
                    s.warnings.append("invalid TRACK!!!")
                    continue
                no = int(rer.group(1))
                if not track:  # DISC NAME
                    s.album  = title
                    s.artist = artist
                else:
                    s._append_track(track, artist, title)

                track = CueTrack(s, no, file)

            elif arg_name == "INDEX":
                if not track:
                    s.warnings.append("index before TRACK")
                    continue
                rer = s.__class__.__re_index.match(arg_value)
                if not rer:
                    s.warnings.append("Invalid index")
                    continue
                no = int(rer.group(1))
                time = 0.0
                for g, m in zip(range(2, 5), [60, 1, 1/75]):
                    time += m*int(rer.group(g))

                track.add_index(no, time)

        s._append_track(track, artist, title)
        for i in range(len(s.tracks)-1):
            s.tracks[i].calc_duration(s.tracks[i+1])


    def _append_track(s, track: "CueTrack", artist: "performer", title: "title"):
        if track:
            track.title = title
            track.artist = artist
            s.tracks.append(track)

    def __str__(s):
        ret  = "{0}: {1} - {2}".format(s.__class__.__name__, s.artist, s.album)
        ret += "\n REM: {0}".format(s.rem)
        ret += "\n TRACKS:"
        for track in s.tracks:
            ret += "\n  {0}".format(str(track).replace("\n", "\n    "))
        if len(s.warnings):
            ret += "\n WARNINGS: {0}".format(s.warnings)
        return ret


if __name__ == '__main__':
    from os import listdir
    TEST_DATA_PATH = "test_data"
    for filename in filter(lambda x: x.endswith(".cue"), listdir(TEST_DATA_PATH)):
        cue = CueSheets(os.path.join(TEST_DATA_PATH, "{0}".format(filename)))
        print (cue)
