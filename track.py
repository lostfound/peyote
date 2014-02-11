from mutagenx import File
import os.path
from pprint import pprint

_lyrics_tag_keys = [b'\xa9lyr']
_diskno_tak_keys = []


class AudioTags:
    __key_funk_dict = None
    warnings = set()

    def __init__(s, path):
        if not AudioTags.__key_funk_dict:
            AudioTags.__key_funk_dict = {
                 b'\xa9lyr':  AudioTags.__set_lyrics
                ,b'\xa9alb':  AudioTags.__set_album
                ,b'\xa9art':  AudioTags.__set_artist
                ,b'\xa9nam':  AudioTags.__set_title
                ,b'\xa9gen':  AudioTags.__set_genre
                ,b'\xa9day':  AudioTags.__set_date
                ,b'disk'   :  AudioTags.__set_diskno
                ,b'trkn'   :  AudioTags.__set_no
            }
        try:
            s.ext = path.rsplit('.', 1)[-1].lower()
        except IndexError:
            s.ext = ''


        tag = File(path)
        s.info = tag.info
        s.duration = tag.info.length
        s._prepare_tags(tag.tags)

    def _prepare_tags(s, tags: 'mutagen File(path)'):
        s.lyrics = None
        s.artist = None
        s.album  = None
        s.diskno = None
        s.date   = None
        s.genre  = None
        s.title  = None
        s.no     = None

        for key in tags.keys():
            fx = AudioTags.__key_funk_dict.get(key.lower())
            if fx: fx(s, key, tags.get(key))

    @staticmethod
    def __mg_get_sting(key, value):
        if type(value) == list:
            if len(value) != 1:
                AudioTags.warnings.add("{0}: len!=1".format(key))
            v = value[0]
            if type(v) == str: return value[0]
            AudioTags.warnings.add("{0}: type is: [{1}]".format(key, type(v)))
        else:
            AudioTags.warnings.add("{0}: type is: {1}".format(key, type(value)))

    @staticmethod
    def __mg_get_tupleint(key, value):
        if type(value) == list:
            if len(value) != 1:
                AudioTags.warnings.add("{0}: len!=1".format(key))
            v = value[0]
            if type(v) == tuple:
                if len(v) != 2:
                    AudioTags.warnings.add("{0}: len(tuple)!=2".format(key))
                    return
                if type(v[0]) != int and type(v[1]) != int:
                    AudioTags.warnings.add("{0}: invalid types [({0}, {1})]".format(type(v[0]), type(v[1])))
                    return


                return value[0]
            AudioTags.warnings.add("{0}: type is: [{1}]".format(key, type(v)))
        else:
            AudioTags.warnings.add("{0}: type is: {1}".format(key, type(value)))

    def __set_lyrics(s, key, value):
        s.lyrics = AudioTags.__mg_get_sting(key, value)

    def __set_artist(s, key, value):
        s.artist = AudioTags.__mg_get_sting(key, value)

    def __set_album(s, key, value):
        s.album = AudioTags.__mg_get_sting(key, value)

    def __set_diskno(s, key, value):
        tpl = AudioTags.__mg_get_tupleint(key, value)
        if tpl:
            no,mx = tpl
            if mx != 1:
                s.diskno = no

    def __set_date(s, key, value):
        s.date = AudioTags.__mg_get_sting(key, value)

    def __set_genre(s, key, value):
        s.genre = AudioTags.__mg_get_sting(key, value).lower()

    def __set_title(s, key, value):
        s.title = AudioTags.__mg_get_sting(key, value)

    def __set_no(s, key, value):
        tpl = AudioTags.__mg_get_tupleint(key, value)
        if tpl:
            s.no = tpl[0]


class Song:
    def __init__(s, path):
        pass

if __name__ == '__main__':
    from os import listdir
    TEST_DATA_PATH = "test_data"
    for filename in filter(lambda x: x.endswith(".m4a"), listdir(TEST_DATA_PATH)):
        at = AudioTags(os.path.join(TEST_DATA_PATH, filename))
        print (filename)
        tag = File(os.path.join(TEST_DATA_PATH, filename))
        pprint (dir(tag.info))
        pprint (list(tag.tags.keys()))
        print (tag.tags.get(b'\xa9lyr'))


