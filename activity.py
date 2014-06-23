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
from gi.repository import GObject
from gi.repository import Pango
import logging

from sugar3.graphics.icon import Icon
from sugar3.graphics.xocolor import XoColor
from sugar3.graphics.palette import Palette

from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.palettemenu import PaletteMenuItem

from gettext import gettext as _

from sugar3.graphics.palette import ToolInvoker

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
import ttcommon.Util.Instruments
from ttcommon.Util import InstrumentDB
from ttcommon.Util.CSoundClient import new_csound_client
from KeyboardStandAlone import KeyboardStandAlone
from MiniSequencer import MiniSequencer
from Loop import Loop
import ttcommon.Config as Config

MAX_PALETTE_WIDTH = 5


def set_palette_list(instrument_list):
    text_label = instrument_list[0]['instrument_desc']
    file_name = instrument_list[0]['file_name']
    _menu_item = PaletteMenuItem(text_label=text_label,
                                 file_name=file_name)
    req2 = _menu_item.get_preferred_size()[1]
    menuitem_width = req2.width
    menuitem_height = req2.height

    palette_width = Gdk.Screen.width() - style.GRID_CELL_SIZE * 3
    palette_height = Gdk.Screen.height() - style.GRID_CELL_SIZE * 3

    nx = min(int(palette_width / menuitem_width), MAX_PALETTE_WIDTH)
    ny = min(int(palette_height / menuitem_height), len(instrument_list) + 1)
    if ny >= len(instrument_list):
        nx = 1
        ny = len(instrument_list)

    grid = Gtk.Grid()
    grid.set_row_spacing(style.DEFAULT_PADDING)
    grid.set_column_spacing(0)
    grid.set_border_width(0)
    grid.show()

    x = 0
    y = 0
    xo_color = XoColor('white')

    for item in sorted(instrument_list,
                       cmp=lambda x, y: cmp(x['instrument_desc'],
                                            y['instrument_desc'])):
        menu_item = PaletteMenuItem(text_label=item['instrument_desc'],
                                    file_name=item['file_name'])
        menu_item.connect('button-release-event', item['callback'], item)

        # menu_item.connect('button-release-event', lambda x: x, item)
        grid.attach(menu_item, x, y, 1, 1)
        x += 1
        if x == nx:
            x = 0
            y += 1

        menu_item.show()

    if palette_height < (y * menuitem_height + style.GRID_CELL_SIZE):
        # if the grid is bigger than the palette, put in a scrolledwindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(nx * menuitem_width,
                                         (ny + 1) * menuitem_height)
        scrolled_window.add_with_viewport(grid)
        return scrolled_window
    else:
        return grid


class FilterToolItem(Gtk.ToolButton):
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ([])), }

    def __init__(self, default_icon, default_label, palette_content):
        self._palette_invoker = ToolInvoker()
        Gtk.ToolButton.__init__(self)
        self._label = default_label

        self.set_is_important(False)
        self.set_size_request(style.GRID_CELL_SIZE, -1)

        self._label_widget = Gtk.Label()
        self._label_widget.set_alignment(0.0, 0.5)
        self._label_widget.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self._label_widget.set_max_width_chars(10)
        self._label_widget.set_use_markup(True)
        self._label_widget.set_markup(default_label)
        self.set_label_widget(self._label_widget)
        self._label_widget.show()

        self.set_widget_icon(icon_name=default_icon)

        self._hide_tooltip_on_click = True
        self._palette_invoker.attach_tool(self)
        self._palette_invoker.props.toggle_palette = True
        self._palette_invoker.props.lock_palette = True

        self.palette = Palette(_('Select Instrument'))
        self.palette.set_invoker(self._palette_invoker)

        self.props.palette.set_content(palette_content)

    def set_widget_icon(self, icon_name=None, file_name=None):
        if file_name is not None:
            icon = Icon(file=file_name,
                        icon_size=style.SMALL_ICON_SIZE,
                        xo_color=XoColor('white'))
        else:
            icon = Icon(icon_name=icon_name,
                        icon_size=style.SMALL_ICON_SIZE,
                        xo_color=XoColor('white'))
        self.set_icon_widget(icon)
        icon.show()

    def set_widget_label(self, label=None):
        # FIXME: Ellipsis is not working on these labels.
        if label is None:
            label = self._label
        """
        if len(label) > 10:
            label = label[0:7] + '...' + label[-7:]
        """
        self._label_widget.set_markup(label)
        self._label = label

    def __destroy_cb(self, icon):
        if self._palette_invoker is not None:
            self._palette_invoker.detach()

    def create_palette(self):
        return None

    def get_palette(self):
        return self._palette_invoker.palette

    def set_palette(self, palette):
        self._palette_invoker.palette = palette

    palette = GObject.property(
        type=object, setter=set_palette, getter=get_palette)

    def get_palette_invoker(self):
        return self._palette_invoker

    def set_palette_invoker(self, palette_invoker):
        self._palette_invoker.detach()
        self._palette_invoker = palette_invoker

    palette_invoker = GObject.property(
        type=object, setter=set_palette_invoker, getter=get_palette_invoker)

    def do_draw(self, cr):
        if self.palette and self.palette.is_up():
            allocation = self.get_allocation()
            # draw a black background, has been done by the engine before
            cr.set_source_rgb(0, 0, 0)
            cr.rectangle(0, 0, allocation.width, allocation.height)
            cr.paint()

        Gtk.ToolButton.do_draw(self, cr)

        if self.palette and self.palette.is_up():
            invoker = self.palette.props.invoker
            invoker.draw_rectangle(cr, self.palette)

        return False


class SimplePianoActivity(activity.Activity):
    """SimplePianoActivity class as specified in activity.info"""

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self._what_list = []

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1

        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        toolbar_box.toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)

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

        ti_notes_labels = RadioToolButton()
        ti_notes_labels.props.icon_name = 'ti_key'
        ti_notes_labels.props.group = keybord_labels
        ti_notes_labels.connect('clicked', self.set_ti_notes_labels_cb)
        toolbar_box.toolbar.insert(ti_notes_labels, -1)

        german_labels = RadioToolButton()
        german_labels.props.icon_name = 'c_key'
        german_labels.props.group = keybord_labels
        german_labels.connect('clicked', self.set_german_labels_cb)
        toolbar_box.toolbar.insert(german_labels, -1)

        no_labels = RadioToolButton()
        no_labels.props.icon_name = 'edit-clear'
        no_labels.props.group = keybord_labels
        no_labels.connect('clicked', self.set_keyboard_no_labels_cb)
        toolbar_box.toolbar.insert(no_labels, -1)
        self._what_widget = Gtk.ToolItem()
        self._what_search_button = FilterToolItem(
            'view-type', _('Piano'), self._what_widget)
        self._what_widget.show()
        separator = Gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        toolbar_box.toolbar.insert(self._what_search_button, -1)
        self._what_search_button.show()
        self._what_search_button.set_is_important(True)
        self._what_widget_contents = None

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        # toolbar_box.insert()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

        self.keyboard_letters = ['ZSXDCVGBHNJM', 'Q2W3ER5T6Y7U', 'I']

        notes = ['DO', ['DO#', 'REb'], 'RE', ['RE#', 'MIb'], 'MI', 'FA',
                 ['FA#', 'SOLb'], 'SOL',
                 ['SOL#', 'LAb'], 'LA', ['LA#', 'SIb'], 'SI']
        self.notes_labels = [notes, notes, ['DO']]

        # some countries use TI instead of SI
        ti_notes = ['DO', ['DO#', 'REb'], 'RE', ['RE#', 'MIb'], 'MI', 'FA',
                    ['FA#', 'SOLb'], 'SOL',
                    ['SOL#', 'LAb'], 'LA', ['LA#', 'TIb'], 'TI']
        self.ti_notes_labels = [ti_notes, ti_notes, ['DO']]

        german_notes = ['C', ['C#', 'Db'], 'D', ['D#', 'Eb'], 'E', 'F',
                        ['F#', 'Gb'], 'G',
                        ['G#', 'Ab'], 'A', ['A#', 'Bb'], 'B']

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
        # self.rythmInstrument = 'drum1kit'
        # self.csnd.load_drumkit(self.rythmInstrument)
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
        self._event_box = Gtk.EventBox()
        self._event_box.modify_bg(
            Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())
        vbox.pack_start(self._event_box, False, False, 0)
        vbox.pack_end(self.piano, True, True, 0)
        vbox.show_all()
        self.set_canvas(vbox)
        piano_height = Gdk.Screen.width() / 2
        self._event_box.set_size_request(
            -1, Gdk.Screen.height() - piano_height - style.GRID_CELL_SIZE)
        self.connect('size-allocate', self.__allocate_cb)

    def __allocate_cb(self, widget, rect):
        GLib.idle_add(self.resize, rect.width, rect.height)
        return False

    def resize(self, width, height):
        logging.error('activity.py resize......')
        piano_height = width / 2
        self._event_box.set_size_request(
            -1, height - piano_height - style.GRID_CELL_SIZE)
        return False

    def load_instruments(self):
        self._instruments_store = []

        # load the images
        images_path = os.path.join(activity.get_bundle_path(),
                                   'instruments')
        logging.error('Loading instrument images from %s', images_path)
        for file_name in os.listdir(images_path):
            image_file_name = os.path.join(images_path, file_name)
            logging.error('Adding %s', image_file_name)
            pxb = GdkPixbuf.Pixbuf.new_from_file_at_size(
                image_file_name, 75, 75)
            # instrument_name = image_file_name[image_file_name.rfind('/'):]
            instrument_name = image_file_name[image_file_name.rfind('/') + 1:]
            instrument_name = instrument_name[:instrument_name.find('.')]
            instrument_desc = \
                self.instrumentDB.instNamed[instrument_name].nameTooltip

            file_path = os.path.join(images_path, file_name)

            # set the default icon
            if (instrument_name == 'piano'):
                self._what_search_button.set_widget_icon(
                    file_name=file_path)

            self._instruments_store.append(
                {"instrument_name": instrument_name,
                 "pxb": pxb,
                 "instrument_desc": instrument_desc,
                 "file_name": file_path,
                 "callback": self.__instrument_iconview_activated_cb})

        self._what_widget_contents = set_palette_list(self._instruments_store)
        self._what_widget.add(self._what_widget_contents)
        self._what_widget_contents.show()

    def __instrument_iconview_activated_cb(self, widget, event, item):
        self.setInstrument(item['instrument_name'])
        self._what_search_button.set_widget_icon(file_name=item['file_name'])
        self._what_search_button.set_widget_label(
            label=item['instrument_desc'])

    def set_notes_labels_cb(self, widget):
        self.piano.font_size = 16
        self.piano.set_labels(self.notes_labels)

    def set_ti_notes_labels_cb(self, widget):
        self.piano.font_size = 16
        self.piano.set_labels(self.ti_notes_labels)

    def set_keyboard_labels_cb(self, widget):
        self.piano.font_size = 25
        self.piano.set_labels(self.keyboard_letters)

    def set_german_labels_cb(self, widget):
        self.piano.font_size = 25
        self.piano.set_labels(self.german_labels)

    def set_keyboard_no_labels_cb(self, widget):
        self.piano.font_size = 25
        self.piano.set_labels(None)

    def enableKeyboard(self):
        self.keyboardStandAlone = KeyboardStandAlone(
            self.sequencer.recording, self.sequencer.adjustDuration,
            self.csnd.loopGetTick, self.sequencer.getPlayState, self.loop)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def setInstrument(self, instrument):
        logging.error("Set Instrument: %s" % instrument)
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
        # self._recordToolbar.keyboardRecOverButton.set_sensitive( state )

    def __key_pressed_cb(self, widget, octave_clicked, key_clicked, letter):
        logging.debug(
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
