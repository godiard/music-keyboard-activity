# Copyright 2009 Simon Schampijer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import GdkPixbuf
import logging

from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics import style
from sugar3.activity.widgets import StopButton

from draw_piano import PianoKeyboard, LETTERS_TO_KEY_CODES
import math
import os

import time
import common.Util.Instruments
from common.Util import InstrumentDB
from common.Util.CSoundClient import new_csound_client
from KeyboardStandAlone import KeyboardStandAlone
from MiniSequencer import MiniSequencer
from Loop import Loop
import common.Config as Config


class SimplePianoActivity(activity.Activity):
    """SimplePianoActivity class as specified in activity.info"""

    def __init__(self, handle):
        """Set up the HelloWorld activity."""
        activity.Activity.__init__(self, handle)

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1

        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)

        toolbar_box.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        keybord_labels = RadioToolButton()
        keybord_labels.props.icon_name = 'q_key'
        keybord_labels.props.group = keybord_labels
        keybord_labels.connect('clicked', self.set_keyboard_labels_cb)
        toolbar_box.toolbar.insert(keybord_labels, -1)

        notes_labels = RadioToolButton()
        notes_labels.props.icon_name = 'do_key'
        notes_labels.props.group = keybord_labels
        notes_labels.connect('clicked', self.set_notes_labels_cb)
        toolbar_box.toolbar.insert(notes_labels, -1)

        german_labels = RadioToolButton()
        german_labels.props.icon_name = 'c_key'
        german_labels.props.group = keybord_labels
        german_labels.connect('clicked', self.set_german_labels_cb)
        toolbar_box.toolbar.insert(german_labels, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

        self.keyboard_letters = ['ZSXDCVGBHNJM', 'Q2W3ER5T6Y7U', 'I']

        notes = ['DO', 'DO#', 'RE', 'RE#', 'MI', 'FA', 'FA#', 'SOL',
                 'SOL#', 'LA', 'LA#', 'SI']
        self.notes_labels = [notes, notes, ['DO']]

        german_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G',
                        'G#', 'A', 'A#', 'B']

        self.german_labels = [german_notes, german_notes, ['C']]

        self.piano = PianoKeyboard(octaves=2, add_c=True,
                                   labels=self.keyboard_letters)

        # init csound
        self.instrumentDB = InstrumentDB.getRef()
        self.firstTime = False
        self.playing = False
        self.csnd = new_csound_client()
        self.timeout_ms = 50
        self.instVolume = 50
        self.drumVolume = 0.5
        self.instrument = 'piano'
        self.regularity = 0.75
        self.beat = 4
        self.reverb = 0.1
        self.tempo = Config.PLAYER_TEMPO
        self.beatDuration = 60.0 / self.tempo
        self.ticksPerSecond = Config.TICKS_PER_BEAT * self.tempo / 60.0
        #self.rythmInstrument = 'drum1kit'
        #self.csnd.load_drumkit(self.rythmInstrument)
        self.sequencer = MiniSequencer(self.recordStateButton,
                                       self.recordOverSensitivity)
        self.loop = Loop(self.beat, math.sqrt(self.instVolume * 0.01))

        self.muteInst = False
        self.csnd.setTempo(self.tempo)
        self.noteList = []
        time.sleep(0.001)  # why?
        for i in range(21):
            self.csnd.setTrackVolume(100, i)

        for i in range(10):
            r = str(i + 1)
            self.csnd.load_instrument('guidice' + r)

        self.volume = 100
        self.csnd.setMasterVolume(self.volume)

        self.enableKeyboard()
        self.setInstrument(self.instrument)

        self.connect('key-press-event', self.onKeyPress)
        self.connect('key-release-event', self.onKeyRelease)
        # finish csount init

        self.piano.connect('key_pressed', self.__key_pressed_cb)
        self.piano.connect('key_released', self.__key_released_cb)
        vbox = Gtk.VBox()
        vbox.set_homogeneous(False)
        self.load_instruments()
        vbox.pack_end(self.piano, True, True, 0)
        self.scrolled = Gtk.ScrolledWindow()
        vbox.pack_start(self.scrolled, False, False, 0)
        self.scrolled.add(self.instruments_iconview)
        vbox.show_all()
        self.set_canvas(vbox)
        piano_height = Gdk.Screen.width() / 2
        self.scrolled.set_size_request(
            -1, Gdk.Screen.height() - piano_height - style.GRID_CELL_SIZE)
        self.connect('size-allocate', self.__allocate_cb)

    def __allocate_cb(self, widget, rect):
        GLib.idle_add(self.resize, rect.width, rect.height)
        return False

    def resize(self, width, height):
        piano_height = width / 2
        self.scrolled.set_size_request(
            -1, height - piano_height - style.GRID_CELL_SIZE)
        return False

    def load_instruments(self):
        self._instruments_store = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)
        self._instruments_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.instruments_iconview = Gtk.IconView(self._instruments_store)
        self.instruments_iconview.set_text_column(2)
        self.instruments_iconview.set_pixbuf_column(1)

        # load the images
        images_path = os.path.join(activity.get_bundle_path(),
                                   'instruments')
        logging.error('Loading instrument images from %s', images_path)
        for file_name in os.listdir(images_path):
            image_file_name = os.path.join(images_path, file_name)
            logging.error('Adding %s', image_file_name)
            pxb = GdkPixbuf.Pixbuf.new_from_file_at_size(
                image_file_name, 75, 75)
            #instrument_name = image_file_name[image_file_name.rfind('/'):]
            instrument_name = image_file_name[image_file_name.rfind('/') + 1:]
            instrument_name = instrument_name[:instrument_name.find('.')]
            instrument_desc = \
                self.instrumentDB.instNamed[instrument_name].nameTooltip
            self._instruments_store.append([instrument_name, pxb,
                instrument_desc])
        self.instruments_iconview.connect(
            'selection-changed', self.__instrument_iconview_activated_cb)

    def __instrument_iconview_activated_cb(self, widget):
        item = widget.get_selected_items()[0]
        model = widget.get_model()
        instrument_name = model[item][0]
        self.setInstrument(instrument_name)

    def set_notes_labels_cb(self, widget):
        self.piano.font_size = 16
        self.piano.set_labels(self.notes_labels)

    def set_keyboard_labels_cb(self, widget):
        self.piano.font_size = 25
        self.piano.set_labels(self.keyboard_letters)

    def set_german_labels_cb(self, widget):
        self.piano.font_size = 25
        self.piano.set_labels(self.german_labels)

    def enableKeyboard(self):
        self.keyboardStandAlone = KeyboardStandAlone(
            self.sequencer.recording, self.sequencer.adjustDuration,
            self.csnd.loopGetTick, self.sequencer.getPlayState, self.loop)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def setInstrument(self, instrument):
        self.instrument = instrument
        self.keyboardStandAlone.setInstrument(instrument)
        self.csnd.load_instrument(instrument)

    def recordStateButton(self, button, state):
        pass
#        if button == 1:
#            self._recordToolbar.keyboardRecButton.set_active( state )
#        else:
#            self._recordToolbar.keyboardRecOverButton.set_active( state )

    def recordOverSensitivity(self, state):
        pass
        #self._recordToolbar.keyboardRecOverButton.set_sensitive( state )

    def __key_pressed_cb(self, widget, octave_clicked, key_clicked, letter):
        logging.error(
            'Pressed Octave: %d Key: %d Letter: %s' %
            (octave_clicked, key_clicked, letter))
        if letter in LETTERS_TO_KEY_CODES.keys():
            self.keyboardStandAlone.do_key_press(
                LETTERS_TO_KEY_CODES[letter], None,
                math.sqrt(self.instVolume * 0.01))

    def __key_released_cb(self, widget, octave_clicked, key_clicked, letter):
        if letter in LETTERS_TO_KEY_CODES.keys():
            self.keyboardStandAlone.do_key_release(
                LETTERS_TO_KEY_CODES[letter])

    def onKeyPress(self, widget, event):

        if event.hardware_keycode == 37:
            if self.muteInst:
                self.muteInst = False
            else:
                self.muteInst = True
        self.piano.physical_key_changed(event.hardware_keycode, True)
        self.keyboardStandAlone.onKeyPress(
            widget, event, math.sqrt(self.instVolume * 0.01))

    def onKeyRelease(self, widget, event):
        self.keyboardStandAlone.onKeyRelease(widget, event)
        self.piano.physical_key_changed(event.hardware_keycode, False)
