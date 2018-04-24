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
from __future__ import division

from gettext import gettext as _
import logging
import json
import time
import math
import os
import tempfile

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Pango

from sugar3.activity import activity
from sugar3.datastore import datastore
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton
from sugar3.graphics.icon import Icon
from sugar3.graphics.xocolor import XoColor
from sugar3.graphics.palette import Palette
from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.graphics.palette import ToolInvoker
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics import style
from sugar3.graphics.alert import NotifyAlert

from ttcommon.Util.NoteDB import Note
import ttcommon.Util.NoteDB as NoteDB
# Instruments is needed to find the percussion sets
import ttcommon.Util.Instruments  # noqa: F401
from ttcommon.Util import InstrumentDB
from ttcommon.Util.CSoundClient import new_csound_client
from ttcommon.Config import imagefile
import ttcommon.Config as Config

from Loop import Loop
from Fillin import Fillin
from KeyboardStandAlone import KeyboardStandAlone
from MiniSequencer import MiniSequencer
from RythmGenerator import generator

from draw_piano import PianoKeyboard, LETTERS_TO_KEY_CODES

DRUMCOUNT = 6
PLAYER_TEMPO = 95
PLAYER_TEMPO_LOWER = 30
PLAYER_TEMPO_UPPER = 150
PLAYER_TEMPO_STEP = int((160 - 30) / 10)


class IntensitySelector(Gtk.ToolItem):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ([])), }

    def __init__(self, value_range, default_value, default_image):

        Gtk.ToolItem.__init__(self)
        self._palette_invoker = ToolInvoker()

        self.palette = None
        self._values = value_range
        self._palette_invoker.attach_tool(self)

        # theme the buttons, can be removed if add the style to the sugar css
        # these are the same values used in gtk-widgets.css.em
        if style.zoom(100) == 100:
            subcell_size = 15
            default_padding = 6
        else:
            subcell_size = 11
            default_padding = 4

        hbox = Gtk.HBox()
        vbox = Gtk.VBox()
        self.add(vbox)
        # add a vbox to set the padding up and down
        vbox.pack_start(hbox, True, True, default_padding)

        self._size_down = ToolButton('go-previous-paired')
        self._palette_invoker.attach_tool(self._size_down)

        self._size_down.set_can_focus(False)
        self._size_down.connect('clicked', self.__value_changed_cb, False)
        hbox.pack_start(self._size_down, False, False, 5)

        # TODO: default?
        self._default_value = default_value
        self._value = self._default_value

        self.image_wrapper = Gtk.EventBox()
        self._intensityImage = Gtk.Image()
        self.image_wrapper.add(self._intensityImage)
        self.image_wrapper.show()
        self._intensityImage.set_from_file(default_image)
        self._intensityImage.show()
        self._palette_invoker.attach_widget(self.image_wrapper)

        hbox.pack_start(self.image_wrapper, False, False, 10)

        self._size_up = ToolButton('go-next-paired')

        self._palette_invoker.attach_tool(self._size_up)

        self._size_up.set_can_focus(False)
        self._size_up.connect('clicked', self.__value_changed_cb, True)
        hbox.pack_start(self._size_up, False, False, 5)

        radius = 2 * subcell_size
        theme_up = "GtkButton {border-radius:0px %dpx %dpx 0px;}" % (radius,
                                                                     radius)
        css_provider_up = Gtk.CssProvider()
        css_provider_up.load_from_data(theme_up)

        style_context = self._size_up.get_style_context()
        style_context.add_provider(css_provider_up,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

        theme_down = "GtkButton {border-radius: %dpx 0px 0px %dpx;}" % (radius,
                                                                        radius)
        css_provider_down = Gtk.CssProvider()
        css_provider_down.load_from_data(theme_down)
        style_context = self._size_down.get_style_context()
        style_context.add_provider(css_provider_down,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.show_all()

    def __destroy_cb(self, **args):
        if self._palette_invoker is not None:
            self._palette_invoker.detach()

    def __value_changed_cb(self, button, increase):
        if self._value in self._values:
            i = self._values.index(self._value)
            if increase:
                if i < len(self._values) - 1:
                    i += 1
            else:
                if i > 0:
                    i -= 1
        else:
            i = self._values.index(self._default_value)

        self._value = self._values[i]
        self._size_down.set_sensitive(i != 0)
        self._size_up.set_sensitive(i < len(self._values) - 1)
        self.emit('changed')

    def set_value(self, val):
        if val not in self._values:
            # assure the val assigned is in the range
            # if not, assign one close.
            for v in self._values:
                if v > val:
                    val = v
                    break
            if val > self._values[-1]:
                size = self._values[-1]

        self._value = size
        self._size_label.set_text(str(self._value))

        # update the buttons states
        i = self._values.index(self._value)
        self._size_down.set_sensitive(i != 0)
        self._size_up.set_sensitive(i < len(self._value) - 1)
        self.emit('changed')

    def set_tooltip(self, tooltip):
        """ Set a simple palette with just a single label.
        """
        if self.palette is None or self._tooltip is None:
            self.palette = Palette(tooltip)
        elif self.palette is not None:
            self.palette.set_primary_text(tooltip)

        self._tooltip = tooltip

    def get_hide_tooltip_on_click(self):
        return self._hide_tooltip_on_click

    def set_hide_tooltip_on_click(self, hide_tooltip_on_click):
        if self._hide_tooltip_on_click != hide_tooltip_on_click:
            self._hide_tooltip_on_click = hide_tooltip_on_click

    hide_tooltip_on_click = GObject.property(
        type=bool, default=True, getter=get_hide_tooltip_on_click,
        setter=set_hide_tooltip_on_click)

    def get_tooltip(self):
        return self._tooltip

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
        Gtk.ToolButton.do_draw(self, cr)

        if self.palette and self.palette.is_up():
            invoker = self.palette.props.invoker
            invoker.draw_rectangle(cr, self.palette)

        return False

    def do_clicked(self):
        if self._hide_tooltip_on_click and self.palette:
            self.palette.popdown(True)

    def set_image(self, image):
        self._intensityImage.set_from_file(image)

    def get_value(self):
        return self._value


def xfrange(start, stop, step):

    old_start = start  # backup this value

    digits = int(round(math.log(10000, 10))) + 1  # get number of digits
    magnitude = 10 ** digits
    stop = int(magnitude * stop)  # convert from
    step = int(magnitude * step)  # 0.1 to 10 (e.g.)

    if start == 0:
        start = 10 ** (digits - 1)
    else:
        start = 10 ** (digits) * start

    data = []  # create array

    # calc number of iterations
    end_loop = int((stop - start) // step)
    if old_start == 0:
        end_loop += 1

    acc = start

    for i in xrange(0, end_loop):
        data.append(acc / magnitude)
        acc += step

    return data


class FilterToolItem(Gtk.ToolButton):
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ([])), }

    def __init__(self, tagline, default_icon, default_label, palette_content):
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

        self.palette = Palette(tagline)
        self.palette.set_invoker(self._palette_invoker)

        self.props.palette.set_content(palette_content)

    def set_widget_icon(self, icon_name=None, file_name=None):
        if file_name is not None:
            icon = Icon(file=file_name,
                        pixel_size=style.SMALL_ICON_SIZE,
                        xo_color=XoColor('white'))
        else:
            icon = Icon(icon_name=icon_name,
                        pixel_size=style.SMALL_ICON_SIZE,
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


class SimplePianoActivity(activity.Activity):
    """SimplePianoActivity class as specified in activity.info"""

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        Gst.init(None)
        self._what_list = []

        self.play_recording_thread = None

        self.playing_recording = False
        self.firstTime = False
        self.playing = False
        self.regularity = 0.7
        self._drums_store = []
        self.recording = False
        self.recorded_keys = []
        self.is_valid_recording = False

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1
        self.csnd = new_csound_client()
        self.rythmInstrument = 'drum1kick'
        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()
        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        toolbar_box.toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)

        self.play_index = 0

        self.play_recording_button = ToolButton(
            icon_name='media-playback-start')
        self.play_recording_button.set_property('can-default', True)
        self.play_recording_button.show()
        self.record_button = ToggleToolButton(icon_name='media-record')
        self.record_button.set_property('can-default', True)
        self.record_button.show()
        self.play_recording_button.set_sensitive(False)

        self.record_button.connect('clicked', self.__record_button_click_cb)

        self.play_recording_button.connect('clicked',
                                           self.handlePlayRecordingButton)

        toolbar_box.toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)

        # TODO: disabe until is implemented with csnd6
        # self.createPercussionToolbar(toolbar_box)

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
        self._what_search_button = FilterToolItem(_('Select Instrument'),
                                                  'view-type',
                                                  _('Piano'),
                                                  self._what_widget)
        self._what_widget.show()
        toolbar_box.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar_box.toolbar.insert(self._what_search_button, -1)
        self._what_search_button.show()
        self._what_search_button.set_is_important(True)
        self._what_widget_contents = None
        self._what_drum_widget_contents = None

        separator = Gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)

        toolbar_box.toolbar.insert(self.record_button, -1)
        toolbar_box.toolbar.insert(self.play_recording_button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self._save_as_audio_bt = ToolButton(icon_name='save-as-audio')
        self._save_as_audio_bt.props.tooltip = _('Save as audio')
        self._save_as_audio_bt.connect('clicked', self._save_ogg_cb)
        self._save_as_audio_bt.show()
        self._save_as_audio_bt.set_sensitive(False)
        activity_button.page.insert(self._save_as_audio_bt, -1)

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
        self.timeout_ms = 50
        self.instVolume = 50
        self.drumVolume = 0.5
        self.instrument = 'piano'
        self.beat = 4
        self.reverb = 0.1
        self.tempo = PLAYER_TEMPO
        self.beatDuration = 60.0 / self.tempo
        self.ticksPerSecond = Config.TICKS_PER_BEAT * self.tempo / 60.0

        self.sequencer = MiniSequencer(self.recordStateButton,
                                       self.recordOverSensitivity)
        self.loop = Loop(self.beat, math.sqrt(self.instVolume * 0.01))

        self.drumFillin = Fillin(self.beat,
                                 self.tempo,
                                 self.rythmInstrument,
                                 self.reverb,
                                 self.drumVolume)

        self.muteInst = False
        self.csnd.setTempo(self.tempo)
        self.noteList = []
        for i in range(21):
            self.csnd.setTrackVolume(100, i)

        # TODO commented because apparently are not used in the activity
        # for i in range(10):
        #     self.csnd.load_instrument('guidice' + str(i + 1))

        self.volume = 100
        self.csnd.setMasterVolume(self.volume)

        self.enableKeyboard()
        self.setInstrument(self.instrument)

        self.connect('key-press-event', self.onKeyPress)
        self.connect('key-release-event', self.onKeyRelease)

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

        # TODO: disabe until is implemented with csnd6
        # GObject.idle_add(self.initializePercussion)

    def createPercussionToolbar(self, toolbar_box):

        self.beats_pm_button = IntensitySelector(range(2, 13),
                                                 4,
                                                 imagefile('beat3.svg'))
        self.tempo_button = \
            IntensitySelector(range(PLAYER_TEMPO_LOWER,
                                    PLAYER_TEMPO_UPPER + 1, PLAYER_TEMPO_STEP),
                              PLAYER_TEMPO, imagefile('tempo5.png'))

        self.complexity_button = IntensitySelector(xfrange(0, 1, 0.1),
                                                   self.regularity,
                                                   imagefile('complex6.svg'))

        self._play_percussion_btn = ToolButton(
            icon_name='media-playback-start')
        self._play_percussion_btn.set_property('can-default', True)
        self._play_percussion_btn.show()
        self._play_percussion_btn.connect('clicked', self.handlePlayButton)

        beats_toolbar = ToolbarBox()
        beats_toolbar.toolbar.insert(self._play_percussion_btn, -1)

        self._what_drum_widget = Gtk.ToolItem()
        self._what_drum_search_button = FilterToolItem(
            _('Select Drum'), 'view-type', _('Jazz / Rock Kit'),
            self._what_drum_widget)
        self._what_drum_search_button.set_widget_icon(
            file_name=imagefile("drum1kit.svg"))

        self._what_drum_widget.show()
        beats_toolbar.toolbar.insert(self._what_drum_search_button, -1)
        self._what_drum_search_button.show()
        self._what_drum_search_button.set_is_important(True)

        beats_toolbar.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        beats_toolbar.toolbar.insert(self.complexity_button, -1)
        beats_toolbar.toolbar.insert(self.beats_pm_button, -1)
        beats_toolbar.toolbar.insert(self.tempo_button, -1)

        beats_toolbar_button = ToolbarButton(icon_name='toolbar-drums',
                                             page=beats_toolbar)
        beats_toolbar_button.show()

        toolbar_box.toolbar.insert(beats_toolbar_button, 1)

        self.beats_pm_button.set_tooltip(_("Beats per bar"))
        self.beats_pm_button.show()
        self.beats_pm_button.connect('changed', self.beatSliderChange, True)
        self.tempo_button.connect('changed', self.tempoSliderChange, True)
        self.complexity_button.connect('changed',
                                       self.handleComplexityChange,
                                       True)
        self.complexity_button.set_tooltip(_("Beat complexity"))
        self.tempo_button.show()
        self.tempo_button.set_tooltip(_('Tempo'))
        self.complexity_button.show()

    def initializePercussion(self):
        self.rythmInstrument = 'drum1kit'
        self.csnd.load_drumkit(self.rythmInstrument)
        self.csnd.setTempo(self.tempo)
        self.beatPickup = False

        def flatten(ll):
            rval = []
            for l in ll:
                rval += l
            return rval

        noteOnsets = []
        notePitchs = []

        i = 0
        self.noteList = []
        self.csnd.loopClear()
        for x in flatten(
            generator(self.rythmInstrument, self.beat,
                      0.8, self.regularity, self.reverb)):
            x.amplitude = x.amplitude * self.drumVolume
            noteOnsets.append(x.onset)
            notePitchs.append(x.pitch)
            n = Note(0, x.trackId, i, x)
            self.noteList.append((x.onset, n))
            i = i + 1
            self.csnd.loopPlay(n, 1)                    # add as active

        self.csnd.loopSetNumTicks(self.beat * Config.TICKS_PER_BEAT)
        self.drumFillin.unavailable(noteOnsets, notePitchs)

        if self.playing:
            self.csnd.loopStart()

    def __allocate_cb(self, widget, rect):
        GLib.idle_add(self.resize, rect.width, rect.height)
        return False

    def resize(self, width, height):
        logging.debug('activity.py resize......')
        piano_height = width / 2
        self._event_box.set_size_request(
            -1, Gdk.Screen.height() - piano_height - style.GRID_CELL_SIZE)
        return False

    def load_instruments(self):
        self._instruments_store = []

        # load the images
        images_path = os.path.join(activity.get_bundle_path(),
                                   'instruments')
        logging.error('Loading instrument images from %s', images_path)
        for file_name in os.listdir(images_path):
            image_file_name = os.path.join(images_path, file_name)
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

        # TODO: disabe until is implemented with csnd6
        """
        for drum_number in range(0, DRUMCOUNT):
            drum_name = 'drum%dkit' % (drum_number + 1)
            self._drums_store.append({
                "instrument_name": drum_name,
                "file_name": imagefile(drum_name + '.svg'),
                "instrument_desc":
                    self.instrumentDB.instNamed[drum_name].nameTooltip,
                "callback": self.__drum_iconview_activated_cb
            })

        self._what_drum_widget_contents = set_palette_list(self._drums_store)
        self._what_drum_widget.add(self._what_drum_widget_contents)
        self._what_drum_widget_contents.show()
        """

    def __drum_iconview_activated_cb(self, widget, event, item):
        data = item['instrument_name']
        self.rythmInstrument = data
        self.csnd.load_drumkit(data)
        instrumentId = self.instrumentDB.instNamed[data].instrumentId
        for (o, n) in self.noteList:
            self.csnd.loopUpdate(n, NoteDB.PARAMETER.INSTRUMENT,
                                 instrumentId, -1)
        self.drumFillin.setInstrument(self.rythmInstrument)
        self._what_drum_search_button.set_widget_label(
            label=item['instrument_desc'])
        self._what_drum_search_button.set_widget_icon(
            file_name=item['file_name'])

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

    def beatSliderChange(self, widget, event):
        self.beat = int(self.beats_pm_button.get_value())
        self.sequencer.beat = self.beat
        self.loop.beat = self.beat
        self.drumFillin.setBeats(self.beat)
        img = int(self.scale(self.beat, 2, 12, 1, 11))
        self.beats_pm_button.set_image(imagefile('beat' + str(img) + '.svg'))
        self.beatPickup = False
        self.regenerate()
        self.beatPickup = True

    def regenerate(self):
        def flatten(ll):
            rval = []
            for l in ll:
                rval += l
            return rval
        noteOnsets = []
        notePitchs = []
        i = 0
        self.noteList = []
        self.csnd.loopClear()
        for x in flatten(
            generator(self.rythmInstrument,
                      self.beat, 0.8, self.regularity,
                      self.reverb)):
            x.amplitude = x.amplitude * self.drumVolume
            noteOnsets.append(x.onset)
            notePitchs.append(x.pitch)
            n = Note(0, x.trackId, i, x)
            self.noteList.append((x.onset, n))
            i = i + 1
            self.csnd.loopPlay(n, 1)                    # add as active
        self.csnd.loopSetNumTicks(self.beat * Config.TICKS_PER_BEAT)
        self.drumFillin.unavailable(noteOnsets, notePitchs)
        self.recordOverSensitivity(False)
        if self.playing:
            self.csnd.loopStart()

    def handlePlayRecordingButton(self, val):
        if not self.playing_recording:
            self.playing_recording = True
            self.play_recording_button.props.icon_name = 'media-playback-stop'
            self.play_recording_thread = \
                GObject.timeout_add(100, self._play_recorded_keys)
        else:
            self.playing_recording = False
            self.play_recording_button.props.icon_name = 'media-playback-start'

    def _save_ogg_cb(self, widget):
        self._wav_tempfile = tempfile.NamedTemporaryFile(
            mode='w+b', suffix='.wav', dir='/tmp/')
        self.csnd.inputMessage(Config.CSOUND_RECORD_PERF %
                               self._wav_tempfile.name)

        self.playing_recording = True
        self.play_recording_thread = \
            GObject.timeout_add(100, self._play_recorded_keys,
                                self._save_ogg_end_cb)

    def _save_ogg_end_cb(self):
        self.csnd.inputMessage(Config.CSOUND_STOP_RECORD_PERF %
                               self._wav_tempfile.name)

        self._ogg_tempfile = tempfile.NamedTemporaryFile(
            mode='w+b', suffix='.ogg', dir='/tmp/')

        line = 'filesrc location=%s ! ' \
            'wavparse ! audioconvert ! vorbisenc ! oggmux ! ' \
            'filesink location=%s' % (self._wav_tempfile.name,
                                      self._ogg_tempfile.name)
        pipe = Gst.parse_launch(line)
        pipe.get_bus().add_signal_watch()
        pipe.get_bus().connect('message::eos', self._save_ogg_eos_cb, pipe)
        pipe.set_state(Gst.State.PLAYING)

    def _save_ogg_eos_cb(self, bus, message, pipe):
        bus.remove_signal_watch()
        pipe.set_state(Gst.State.NULL)

        title = '%s saved as audio' % self.metadata['title']

        jobject = datastore.create()
        jobject.metadata['title'] = title
        jobject.metadata['keep'] = '0'
        jobject.metadata['mime_type'] = 'audio/ogg'
        jobject.file_path = self._ogg_tempfile.name
        datastore.write(jobject)

        self._wav_tempfile.close()
        self._ogg_tempfile.close()

        alert = NotifyAlert(10)
        alert.props.title = _('Audio recorded')
        alert.props.msg = _('The audio file was saved in the Journal')
        alert.connect('response', self.__alert_response_cb)
        self.add_alert(alert)

        return False

    def __alert_response_cb(self, alert, result):
        self.remove_alert(alert)

    def __record_button_click_cb(self, button):
        if not self.recording:
            self.play_recording_button.set_sensitive(False)
            self._save_as_audio_bt.set_sensitive(False)
            self.recorded_keys = []
            self.recording = True
            icon = Icon(icon_name='media-record', fill_color='#ff0000')
            icon.show()
            self.record_button.set_icon_widget(icon)
        else:
            self.recording = False
            icon = Icon(icon_name='media-record', fill_color='#ffffff')
            icon.show()
            self.record_button.set_icon_widget(icon)
            if len(self.recorded_keys) != 0:
                self.play_recording_button.set_sensitive(True)
                self._save_as_audio_bt.set_sensitive(True)

    def tempoSliderChange(self, widget, event):
        self._updateTempo(self.tempo_button.get_value())
        img = int(self.scale(self.tempo, PLAYER_TEMPO_LOWER,
                             PLAYER_TEMPO_UPPER, 1, 9))
        self.tempo_button.set_image(imagefile('tempo' + str(img) + '.png'))

    def _updateTempo(self, val):
        self.tempo = val
        self.beatDuration = 60.0 / self.tempo
        self.ticksPerSecond = Config.TICKS_PER_BEAT * self.tempo / 60.0
        self.csnd.setTempo(self.tempo)
        self.sequencer.tempo = self.tempo
        self.drumFillin.setTempo(self.tempo)

    def handlePlayButton(self, val):
        if not self.playing:
            if not self.firstTime:
                self.regenerate()
                self.firstTime = True
            self.drumFillin.play()
            self.csnd.loopSetTick(0)
            self.csnd.loopStart()
            self.playing = True
            self._play_percussion_btn.props.icon_name = 'media-playback-stop'
        else:
            self.drumFillin.stop()
            self.sequencer.stopPlayback()
            self.csnd.loopPause()
            self.playing = False
            self._play_percussion_btn.props.icon_name = 'media-playback-start'

    def scale(self, input, input_min, input_max,
              output_min, output_max):
        range_input = input_max - input_min
        range_output = output_max - output_min
        result = (input - input_min) * range_output / range_input + output_min

        if (input_min > input_max and output_min > output_max) or \
           (output_min > output_max and input_min < input_max):
            if result > output_min:
                return output_min
            elif result < output_max:
                return output_max
            else:
                return result

        if (input_min < input_max and output_min < output_max) or \
           (output_min < output_max and input_min > input_max):
            if result > output_max:
                return output_max
            elif result < output_min:
                return output_min
            else:
                return result

    def handleComplexityChange(self, widget, event):
        self.regularity = self.complexity_button.get_value()
        img = int(self.complexity_button.get_value() * 7) + 1
        self.complexity_button.set_image(
            imagefile('complex' + str(img) + '.svg'))
        self.beatPickup = False
        self.regenerate()
        self.beatPickup = True

    """
    def handleBalanceSlider(self, adj):
        self.instVolume = int(adj.get_value())
        self.drumVolume = sqrt( (100-self.instVolume)*0.01 )
        self.adjustDrumVolume()
        self.drumFillin.setVolume(self.drumVolume)
        instrumentVolume = sqrt( self.instVolume*0.01 )
        self.loop.adjustLoopVolume(instrumentVolume)
        self.sequencer.adjustSequencerVolume(instrumentVolume)
        img = int(self.scale(self.instVolume,100,0,0,4.9))
        self._playToolbar.balanceSliderImgLeft.set_from_file(
                imagefile('dru' + str(img) + '.png'))
        img2 = int(self.scale(self.instVolume,0,100,0,4.9))
        self._playToolbar.balanceSliderImgRight.set_from_file(
                imagefile('instr' + str(img2) + '.png'))

    def handleReverbSlider(self, adj):
        self.reverb = adj.get_value()
        self.drumFillin.setReverb( self.reverb )
        img = int(self.scale(self.reverb,0,1,0,4))
        self._playToolbar.reverbSliderImgRight.set_from_file(
                imagefile('reverb' + str(img) + '.png'))
        self.keyboardStandAlone.setReverb(self.reverb)
    """
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

    def _play_recorded_keys(self, end_cb=None):
        GObject.source_remove(self.play_recording_thread)
        letter = self.recorded_keys[self.play_index]
        time_difference = 0
        if self.play_index == len(self.recorded_keys) - 1:
            time_difference = \
                self.recorded_keys[self.play_index][0] - \
                self.recorded_keys[self.play_index - 1][0]
        else:
            next_time = self.recorded_keys[self.play_index + 1][0]
            time_difference = next_time - letter[0]

        if not self.playing_recording:
            self.play_recording_button.props.icon_name = 'media-playback-start'
            return

        if letter[-1] == 1:
            self.keyboardStandAlone.do_key_release(
                LETTERS_TO_KEY_CODES[letter[3]])
            GObject.idle_add(self.piano.physical_key_changed,
                             LETTERS_TO_KEY_CODES[letter[3]], False)
        else:
            self.keyboardStandAlone.do_key_press(
                LETTERS_TO_KEY_CODES[letter[3]], None,
                math.sqrt(self.instVolume * 0.01))
            GObject.idle_add(self.piano.physical_key_changed,
                             LETTERS_TO_KEY_CODES[letter[3]], True)

        if self.play_index == len(self.recorded_keys) - 1:
            self.play_index = 0
            self.play_recording_button.props.icon_name = 'media-playback-start'
            self.playing_recording = False
            if end_cb is not None:
                end_cb()
        else:
            self.play_index += 1
            self.play_recording_thread = \
                GObject.timeout_add(int((time_difference) * 1000),
                                    self._play_recorded_keys, end_cb)

    def __key_pressed_cb(self, widget, octave_clicked, key_clicked, letter,
                         physicallKey):
        logging.debug(
            'Pressed Octave: %d Key: %d Letter: %s' %
            (octave_clicked, key_clicked, letter))
        if letter in LETTERS_TO_KEY_CODES.keys():
            if self.recording:
                self.recorded_keys.append(
                    [time.time(), octave_clicked, key_clicked, letter])
            if not physicallKey:
                self.keyboardStandAlone.do_key_press(
                    LETTERS_TO_KEY_CODES[letter], None,
                    math.sqrt(self.instVolume * 0.01))

    def __key_released_cb(self, widget, octave_clicked, key_clicked, letter,
                          physicallKey):
        if self.recording:
            self.recorded_keys.append(
                [time.time(), octave_clicked, key_clicked, letter, 1])
        if not physicallKey:
            if letter in LETTERS_TO_KEY_CODES.keys():
                self.keyboardStandAlone.do_key_release(
                    LETTERS_TO_KEY_CODES[letter])

    def onKeyPress(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return
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

    def write_file(self, file_path):
        f = open(file_path, 'w')
        # substract the initial time to all the saved values
        if len(self.recorded_keys) > 0:
            initial_time = self.recorded_keys[0][0]
            for key in self.recorded_keys:
                key[0] = key[0] - initial_time

        f.write(json.dumps(self.recorded_keys))
        f.close()

    def read_file(self, file_path):
        f = open(file_path, 'r')
        contents = f.read().strip()

        self.recorded_keys = json.loads(contents)
        if len(self.recorded_keys) != 0:
            self.play_recording_button.set_sensitive(True)
            self._save_as_audio_bt.set_sensitive(True)
        f.close()

    def close(self, skip_save=False):
        self.csnd.stop()  # without which Csound will segfault
        activity.Activity.close(self, skip_save=skip_save)
