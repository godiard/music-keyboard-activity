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

import gtk
import logging

from gettext import gettext as _

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton

from draw_piano import PianoKeyboard
import gst
import math


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

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

        self.tone_generator = GstToneGenerator()

        self.keyboard_letters = ['Q2W3ER5T6Y7UI', 'ZSXDCVGBHNJM', ',']

        notes = ['DO', 'DO#', 'RE', 'RE#', 'MI', 'FA', 'FA#', 'SOL',
                        'SOL#', 'LA', 'LA#', 'SI']
        labels_tamtam = [notes, notes, ['DO']]

        piano = PianoKeyboard(octaves=2, add_c=True,
                labels=self.keyboard_letters)
        piano.connect('key_pressed', self.__key_pressed_cb)
        piano.connect('key_released', self.__key_released_cb)
        piano.show()
        self.set_canvas(piano)

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
        self.tone_generator.set_values(freq, 100)
        self.tone_generator.start()

    def __key_released_cb(self, widget, octave_clicked, key_clicked, letter):
        self.tone_generator.stop()


class GstToneGenerator(object):
    """Gstreamer based tone generator.
        from https://github.com/iamFIREcracker/py-tone-generator/
    """

    def __init__(self):
        str_pipe = '''audiotestsrc name=source !autoaudiosink'''
        self.pipeline = gst.parse_launch(str_pipe)
        self.source = self.pipeline.get_by_name('source')

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop(self):
        self.pipeline.set_state(gst.STATE_NULL)

    def set_values(self, freq, volume):
        """Change the frequency and volume values of the sound source.
        Keywords:
        freq frequency value between 0 and 20k.
        volume volume value between 0 and 1.
        """
        self.source.set_property('freq', max(0, min(freq, 20000)))
        self.source.set_property('volume', max(0, min(volume, 1)))
