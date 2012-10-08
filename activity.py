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
from gi.repository import Gdk
import logging

from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.activity.widgets import StopButton

from draw_piano import PianoKeyboard
import math

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

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

        self.keyboard_letters = ['Q2W3ER5T6Y7UI', 'ZSXDCVGBHNJM', ',']

        notes = ['DO', 'DO#', 'RE', 'RE#', 'MI', 'FA', 'FA#', 'SOL',
                        'SOL#', 'LA', 'LA#', 'SI']
        self.notes_labels = [notes, notes, ['DO']]

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
        self.beatDuration = 60.0/self.tempo
        self.ticksPerSecond = Config.TICKS_PER_BEAT*self.tempo/60.0
        #self.rythmInstrument = 'drum1kit'
        #self.csnd.load_drumkit(self.rythmInstrument)
        self.sequencer= MiniSequencer(self.recordStateButton,
                self.recordOverSensitivity)
        self.loop = Loop(self.beat, math.sqrt(self.instVolume * 0.01))

        self.muteInst = False
        self.csnd.setTempo(self.tempo)
        self.noteList = []
        time.sleep(0.001) # why?
        for i in range(21):
            self.csnd.setTrackVolume( 100, i )

        for i in  range(10):
            r = str(i+1)
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
        self.piano.show()
        self.set_canvas(self.piano)

    def set_notes_labels_cb(self, widget):
        self.piano.font_size = 14
        self.piano.set_labels(self.notes_labels)

    def set_keyboard_labels_cb(self, widget):
        self.piano.font_size = 20
        self.piano.set_labels(self.keyboard_letters)

    def enableKeyboard(self):
        self.keyboardStandAlone = KeyboardStandAlone(self.sequencer.recording,
                self.sequencer.adjustDuration, self.csnd.loopGetTick,
                self.sequencer.getPlayState, self.loop)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def setInstrument(self , instrument):
        self.instrument = instrument
        self.keyboardStandAlone.setInstrument(instrument)
        self.csnd.load_instrument(instrument)

    def recordStateButton( self, button, state ):
        pass
#        if button == 1:
#            self._recordToolbar.keyboardRecButton.set_active( state )
#        else:
#            self._recordToolbar.keyboardRecOverButton.set_active( state )

    def recordOverSensitivity( self, state ):
        pass
        #self._recordToolbar.keyboardRecOverButton.set_sensitive( state )

    def __key_pressed_cb(self, widget, octave_clicked, key_clicked, letter):
        logging.debug('Pressed Octave: %d Key: %d Letter: %s' %
            (octave_clicked, key_clicked, letter))

        if key_clicked >= 9:
            key = key_clicked - 9
            octave = octave_clicked + 1
        else:
            key = key_clicked + 3
            octave = octave_clicked
        freq = 440 * math.pow(2.0, octave + (key - 12.0) / 12.0)
        logging.debug('Vales Octave: %d Key: %d Freq: %s' % (octave, key,
                freq))
        self.tone_generator.set_values(freq, 1)
        self.tone_generator.start()

    def __key_released_cb(self, widget, octave_clicked, key_clicked, letter):
        self.tone_generator.stop()

    def onKeyPress(self, widget, event):

        if event.hardware_keycode == 37:
            if self.muteInst:
                self.muteInst = False
            else:
                self.muteInst = True

        self.keyboardStandAlone.onKeyPress(widget, event,
                math.sqrt(self.instVolume * 0.01))

    def onKeyRelease(self, widget, event):
        self.keyboardStandAlone.onKeyRelease(widget, event)
