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

from useful import unicode2, localise
from threading import Semaphore
import gettext
from lyrics.lyrics import search_lyrics
from thread_system.thread_polls import polls
from sets import config, get_performer_alias

_ = localise
HELP=[]
HELP.append( {"status": 0, "name": _("Keyboard control"), "type": "submenu", "en": """  KEYBOARD CONTROL
================================================================

PLAYER
  0          - increase volume
  9          - decrease volume
  8          - increase pitch
  7          - decrease pitch
  4          - increase crossfade time
  3          - decrease crossfade time
  s          - random
  r          - repeat
  e/E        - hold the EQ
  x          - play songs backward/forwards
  space      - play/pause
  (/)
  shift +
  left/right - seek backward/forward 10 seconds
  n          - next
  w          - redraw
  q          - save the current session and exit
  ctrl+c     - exit

PANEL ==========================================================
  tab       - change the current panel
  >
  <         - next/prev tab
  up/down   - move the selection bar
  home/end  - move the selection bar to the first/last entry
  page up
  page down - move the selection bar one page up/down
  insert    - tag/untag the entry
  *         - tag/untag all entries
  -         - untag all tagged entries
  i/I       - move the selection bar to next/prev tagged entry
  shift +
  up/down   - move the currently selected entry or the tagged entries
  c         - change the location in the current panel
              You able to enter 'equaliser://'
  1
  2         - increase/decrease the panel width
  t         - create a new panel
  h         - open an help in a new tab
  y         - close a current panel
  backspace - go to a next or a current song
  /         - quick search
  .         - realign the cursor at center, top or bottom of the panel
  p         - display only one panel or back to the two panels mode
  ~         - move the selection bar to random entry

FS =============================================================
  enter
  right - open (play) the the currently selected directory or
          playlist(song)
  left  - go to the parent directory
  del
  F8    - delete the currently selected entry or the tagged entries
  F9    - rename the currently selected file or the tagged entries
  F7    - create a playlist or a directory

  F5    - copy an entry(es) to a unselected panel
  F4    - copy an entry(es) to directory which was opened and was 
          under an inactive cursor.
          add entry(ies) to a playlist after the inactive cursor
        
  F6    - move an entry or tagged entries to the currently 
          unselected panel
  F3    - mp3encode the song or tagged songs to the unselected panel
  !     - execute a shell command
  ?     - search a song
  d     - calculate a size of the tagged directories
  f     - show/hide an ordinary files
  m     - switch the displaying mode
  u     - mark the current song or the tagged songs played
  U     - mark the current song or the tagged songs played
  _     - mark all played songs
  \     - enter in the tree mode ( leave the tree mode)
  +     - tab group of songs
  k     - curse the currently selected song.
  K     - uncurse the currently selected song.

PLAYLIST =======================================================
  m     - switch the displaying mode
  rigth - set a next song
  enter - play the selected song
  left  - go to the parent directory
  del
  F8    - delete the selected song or the tagged songs
  F4    - edit path of song in the playlist
  F2    - save a playlist
  u     - mark the selected song or the tagged songs unplayed
  U     - mark the selected song or the tagged songs played
  _     - mark all played songs
  f7    - add a song url to the playlist.
  +     - tab group of songs
  ]     - sort the playlist
  }     - shuffle the playlist
  {     - sort the playlist in chronological order
  k     - curse the currently selected song.
  K     - uncurse the currently selected song.

equalizer:// ===================================================
  F2    - save

locations:// ===================================================
  F7        - Add new location 
  del, F8   - Delete the current location or tagged locations
  F9        - Rename the current location

config:// ======================================================
  del, F8   - Delete
""", "ru": """ КНОПОЧКИ
================================================================

ПЛЕЕР ==========================================================
  0         - увеличить громкость
  9         - уменьшить громкость
  8         - увеличить pitch
  7         - уменьшить pitch
  4         - Увеличить время плавного перехода
  3         - Заменьшить время плавного перехода
  s         - вкл/выкл случайный порядок проигрывания
  r         - вкл/выкл повторы
  x         - задом наперёд/обычно
  h         - зафиксировать эволайзер
  space     - Пауза/продолжить

  (/)
  shift +
  left/right- перемотка туда/сюда на 10 секунд

  n/p- следующая/предыдущая песенка
  w         - перерисовать скрин
  q         - сохранить текущею сессию и выйти
  ctrl+c    - выйти без сохраненья
  e/E       - зафиксировать Эволайзер

ПАНЕЛЬКА =======================================================
  tab       - поменять панель

  >/<         - Табы: следующий/предыдущий

  up/down   - Курсор вверх/вниз
  home/end  - Курсор в самое начало/конец

  page up
  page down - Курсор на страницу вверх/вниз

  insert    - выделить/снять выделение
  *         - выделить/снять выделение со всех элементов в панельке
  -         - снять выделение со всего выделенного
  i/I       - Курсор с следующей/предыдущей пометочке

  shift +
  up/down   - Двигать выделеное или то что под курсором вверх/вниз
  backspace - перевести курсор к тому что играет/будет играть
  c         - изменить локацию в текущей панели
            можно ввести 'equaliser://', 'help://'
  1
  2     - увеличить/уменьшить ширину панели
  h     - открыть HELP в новом табе
  t     - создать новую панель
  y     - закрыть текущею панель
  /     - быстрый поиск
  .     - отобразить курсор в центре, внизу или вверху панельки
  p     - показывать одну или две панельки
  ~     - курсор на произвольный элемент

ФАЙЛОВАЯ СИСТЕМА ===============================================

  enter
  right - Если под курсором директория/поейлист-она откроется,
          если песенка - начнёт играться
  left  - выйти на директорию выше

  del
  F8    - Удалить всё выделеное или то что под курсором
  F9    - переименовать выделеные файлы, или файл под курсором
  F7    - создать новый плейлист или же папочку
  F4/F5 - копировать в невыделеную панель
          (F4 под курсор - если в плейлист, 
          воткрытую папку если дерево)
  F6    - переместить
  F3    - энкодировать песенки в mp3
  !     - выполнить шел комманду
  ?     - поиск песенки/песенок
  d     - вычислить размер выделенных папочек
  f     - прятать/показывать файлы-не песенки
  m     - меняет режим отображения песенок
  u     - пометить песенку или выделенные песенки как неигранное
  U     - пометить песенку или выделенные песенки как отиграное
  _     - пометить отыгранные песенки
  \     - войти/покинуть режим дерева
  +     - пометить группу песенок
  k     - проклясть песенку
  K     - снять проклятие с песенки

ПЛЕЙЛИСТ =======================================================
  m     - очень классная кнопочка(меняет режим отображения песенок)
  rigth - назначить эту песенку следующей
  enter - играть то что под курсором
  left  - выйти из плейлиста
  del
  F8    - удалить выделеные песенки или песенку под курсором из плейлиста
  F4    - редактировать путь выбраной(ых) песенок
  F2    - сохранить изменения в плейлисте
  u     - пометить все песенки как непроигранные
  f7    - добавить урл песенки в конец плейлиста
  u     - пометить песенку или выделенные песенки как неигранное
  U     - пометить песенку или выделенные песенки как отиграное
  _     - пометить отыгранные песенки
  +     - пометить группу песенок
  ]     - упорядочить плейлист
  }     - перемешать плейлист
  {     - Сортировать плейлист в хронологическом подядке
  k     - проклясть песенку
  K     - снять проклятие с песенки

equalizer:// ===================================================
  F2    - Сохранить
  f     - Показывать/прятать пресеты
  ]     - Установить на 0Db

locations:// ===================================================
  F7        - Добавить локацию
  del, F8   - Удалить
  F9        - Переименовать

config:// ======================================================
  del, F8   - Удалить
"""} ) #HELP.append


HELP.append( {"status": 0, "name": _("Mouse control"), "type": "submenu", "en": """  MOUSE CONTROL
================================================================
  button         element          behavior
  
  *********************** Panel **********************
  left           entry            select a entry
  right          entry            mark(unmark) an entry
  double         song             immediately play a song
  double         directory        open a directory
  double         playlist         open a playlist
  left           header           open a directory
  left           ☐/☒              mark as (un)played
  *********************** Player **********************
  left           ♺,⚅              toggle the shuffle play order
  left           ☐,☒              toggle the repeat play order
  left           ↑,↓              playing backward/forwards
  left           other space      pause/resume playing
  ********************* Equalizer *********************
  left           ▨/□              hold EQ
  *********************** Key Bar *********************
  left           ☚/☛              scrolling
  left           ☝,☟              change the key bar
  left           Key              press key
  left           button           press button
""", "ru": """ Мышка
================================================================
  кнопочка       элемент          результатик
  
  *********************** Панель *********************
  левая          линия            select a entry
  правая         линия            выделить(развыделить)
                                  эту линию
  дабл-клик      песенка          немедлено играть
  дабл-клик      папочка          войти в папочку

  дабл-клик      плейлист         открыть плейлист
  левая          заголовок        перейти к директории
  левая          ☐/☒              пометить трек как
                                  (не)отыгранный

  *********************** Плеер ***********************
  левая          ♺,⚅              переключить произвольный
                                  выбор трек
  левая          ☐,☒              переключить повтор треков
  левая          ↑,↓              задом наперёд/обычно
  левая          другое место     пауза/продолжить

  ********************* Эквалайзер ********************
  левая          ▨/□              Менять децебельчики

  ****************** кнопочная панель *****************
  левая          ☚/☛              скролить
  левая          ☝,☟              менять кнопочную панель
  левая          кнопка           нажать
  левая          кнопка           нажать
"""
} ) #HELP.append

class PHelp:

    def init_help(s):
        s.busy.set()
        s.language = _(u"_en").replace("_","")
        s.article = None
        s.storage.clear()
        s.main_page()
        s.busy.clear()

    def destroy_help(s):
        s.article  = None
        s.language = None

    def main_page(s):
        s.storage.fill( [_(u"Table of contents"), u""] + HELP )
        if s.article: s.panel.pos = HELP.index(s.article) + 2
        s.panel.redraw()
        s.panel.refresh()

    def left(s):
        if s.article:
            s.busy.set()

            s.main_page()
            s.article = None

            s.busy.clear()
        else:
            s.cd("locations://")

    def enter(s):
        obj = s.storage[s.panel.pos]
        if type(obj) == dict:
            s.busy.set()
            s.storage.fill( [unicode2( l ) for l in obj.get(s.language,obj["en"]).split("\n") ] )
            s.article = obj
            s.panel.redraw()
            s.panel.refresh()
            s.busy.clear()

