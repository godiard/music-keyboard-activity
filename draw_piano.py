#!/usr/bin/env python
# Copyright (C) 2011, One Laptop Per Child
# Author, Gonzalo Odiard
# License: LGPLv2
#
# The class PianoKeyboard draw a keybord and interact with the mouse
# References
# http://www.josef-k.net/mim/MusicSystem.html
# http://wiki.laptop.org/images/4/4e/Tamtamhelp2.png
#

import logging
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
import cairo

# constants used to calculate the draw of black keys
# right now is 4/5 of the white key
# then is 2/5 and 3/5 (before was 1/3 and 2/3)
K1 = 3.
K2 = 4.
D = 7.
BLACK_KEY_WIDTH = 1 - K2 / D + K1 / D


class PianoKeyboard(Gtk.DrawingArea):

    __gsignals__ = {'key_pressed': (GObject.SignalFlags.RUN_FIRST,
                          None,
                          ([GObject.TYPE_INT, GObject.TYPE_INT,
                            GObject.TYPE_STRING])),
                    'key_released': (GObject.SignalFlags.RUN_FIRST,
                          None,
                          ([GObject.TYPE_INT, GObject.TYPE_INT,
                            GObject.TYPE_STRING]))}

    def __init__(self, octaves=1, add_c=False, labels=None, values=None):
        self._octaves = octaves
        self._add_c = add_c
        self._labels = labels
        self._values = ['ZSXDCVGBHNJM', 'Q2W3ER5T6Y7U', 'I']
        if values is not None:
            self._values = values
        self._pressed_keys = []
        self.font_size = 25
        self._touches = {}
        self._mouse_button_pressed = False
        super(PianoKeyboard, self).__init__()
        # info needed to check keys positions
        self._white_keys = [0, 2, 4, 5, 7, 9, 11]
        self._l_keys_areas = [0, 3]
        self._t_keys_areas = [1, 4, 5]
        self._j_keys_areas = [2, 6]

        self.connect('size-allocate', self.__allocate_cb)
        self.connect('draw', self.__draw_cb)
        self.connect('event', self.__event_cb)

        self.set_events(Gdk.EventMask.EXPOSURE_MASK |
                Gdk.EventMask.BUTTON_PRESS_MASK | \
                Gdk.EventMask.BUTTON_RELEASE_MASK | \
                Gdk.EventMask.BUTTON_MOTION_MASK | \
                Gdk.EventMask.POINTER_MOTION_MASK | \
                Gdk.EventMask.POINTER_MOTION_HINT_MASK | \
                Gdk.EventMask.TOUCH_MASK)

    def set_labels(self, labels):
        self._labels = labels
        self.queue_draw()

    def calculate_sizes(self, width):
        self._width = width
        self._height = self._width / 2
        cant_keys = 7 * self._octaves
        if self._add_c:
            cant_keys += 1
        self._key_width = self._width / cant_keys
        logging.error('key_width %s', self._key_width)
        self._black_keys_height = self._height * 2 / 3
        self._octave_width = self._key_width * 7

        self._x_start = {'C': 0,
                'CB': self._key_width * K2 / D,
                'D': self._key_width,
                'DB': self._key_width + self._key_width * K2 / D,
                'E': self._key_width * 2,
                'F': self._key_width * 3,
                'FB': self._key_width * 3 + self._key_width * K2 / D,
                'G': self._key_width * 4,
                'GB': self._key_width * 4 + self._key_width * K2 / D,
                'A': self._key_width * 5,
                'AB': self._key_width * 5 + self._key_width * K2 / D,
                'B': self._key_width * 6}

        self.set_size_request(-1, self._height)

    def __event_cb(self, widget, event):
        if event.type in (Gdk.EventType.TOUCH_BEGIN,
                Gdk.EventType.TOUCH_CANCEL, Gdk.EventType.TOUCH_END,
                Gdk.EventType.TOUCH_UPDATE, Gdk.EventType.BUTTON_PRESS,
                Gdk.EventType.BUTTON_RELEASE, Gdk.EventType.MOTION_NOTIFY):
            x = event.touch.x
            y = event.touch.y
            seq = str(event.touch.sequence)
            updated_positions = False
            # save a copy of the old touches
            old_touches = []
            old_touches.extend(self._touches.values())
            if event.type in (Gdk.EventType.TOUCH_BEGIN,
                    Gdk.EventType.TOUCH_UPDATE, Gdk.EventType.BUTTON_PRESS):
                if event.type == Gdk.EventType.TOUCH_BEGIN:
                    # verify if there are another touch pointed to the same key
                    # we receive a MOTION_NOTIFY event before TOUCH_BEGIN
                    for touch in self._touches.keys():
                        if self._touches[touch] == (x, y):
                            del self._touches[touch]
                self._touches[seq] = (x, y)
                updated_positions = True
            elif event.type == Gdk.EventType.MOTION_NOTIFY and \
                    event.get_state()[1] & Gdk.ModifierType.BUTTON1_MASK:
                self._touches[seq] = (x, y)
                updated_positions = True
            elif event.type in (Gdk.EventType.TOUCH_END,
                                Gdk.EventType.BUTTON_RELEASE):
                del self._touches[seq]
                # execute the update pressed keys with a delay,
                # because motion events can came after the button release
                # and all the state is confused
                GObject.timeout_add(10, self._update_pressed_keys, old_touches)
            if updated_positions:
                self._update_pressed_keys(old_touches)

    def _update_pressed_keys(self, old_touches):
        new_pressed_keys = []
        for touch in self._touches.values():
            key_found = self.__get_key_at_position(touch[0], touch[1])  # x, y
            if key_found is not None and key_found not in new_pressed_keys:
                new_pressed_keys.append(key_found)

        # compare with the registered pressed keys, and emit events
        for pressed_key in new_pressed_keys:

            if pressed_key not in self._pressed_keys:
                octave_pressed = int(pressed_key[:pressed_key.find('_')])
                key_pressed = int(pressed_key[pressed_key.find('_') + 1:])
                self.emit('key_pressed', octave_pressed, key_pressed,
                        self.get_value(octave_pressed, key_pressed))
            else:
                del self._pressed_keys[self._pressed_keys.index(pressed_key)]

        # the remaining keys were released
        for key in self._pressed_keys:
            octave_released = int(key[:key.find('_')])
            key_released = int(key[key.find('_') + 1:])
            self.emit('key_released', octave_released, key_released,
                    self.get_value(octave_released, key_released))

        self._pressed_keys = new_pressed_keys

        # calculate the damaged area
        # create a list with the old and new touches uniqified
        uniq_touches = []
        uniq_touches.extend(self._touches.values())
        for old_touch in old_touches:
            if old_touch not in uniq_touches:
                uniq_touches.append(old_touch)
        min_x = self._width
        max_x = 0
        for touch in uniq_touches:
            min_x_touch, max_x_touch = \
                    self.get_damaged_range(int(touch[0]), int(touch[1]))
            if min_x_touch < min_x:
                min_x = min_x_touch
            if max_x_touch > max_x:
                max_x = max_x_touch

        self.queue_draw_area(min_x, 0, max_x - min_x, self._height)

    def __get_key_at_position(self, x, y):
        if y > self._height:
            return None
        octave_found = int(x / self._octave_width)
        key_area = int((x % self._octave_width) / self._key_width)
        click_x = int(x % self._key_width)
        if y > self._black_keys_height or \
            (self._add_c and x > self._width - self._key_width):
            key_found = self._white_keys[key_area]
        else:
            # check black key at the right
            key_found = -1
            if key_area in self._l_keys_areas or \
                key_area in self._t_keys_areas:
                if click_x > self._key_width * K2 / D:
                    key_found = self._white_keys[key_area] + 1
            # check black key at the left
            if key_found == -1 and \
                key_area in self._j_keys_areas or \
                key_area in self._t_keys_areas:
                if click_x < self._key_width * K1 / D:
                    key_found = self._white_keys[key_area] - 1
            if key_found == -1:
                key_found = self._white_keys[key_area]
        return '%d_%d' % (octave_found, key_found)

    def get_damaged_range(self, x, y):
        """
        Based on the x position, calculate what is the min & max X
        that need be redraw. Y is ignored due to most of the keys
        need redraw all the height
        """
        octave_found = int(x / self._octave_width)
        key_area = int((x % self._octave_width) / self._key_width)
        click_x = int(x % self._key_width)
        if y > self._black_keys_height or \
                (self._add_c and x > self._width - self._key_width):
            x_min = x - click_x
            x_max = x_min + self._key_width
        else:
            # check black key at the right
            key_found = -1
            if key_area in self._l_keys_areas or \
                    key_area in self._t_keys_areas:
                if click_x > self._key_width * K2 / D:
                    x_min = x - click_x + self._key_width * K2 / D
                    x_max = x_min + self._key_width * BLACK_KEY_WIDTH
                    key_found = 1
            # check black key at the left
            if key_found == -1 and \
                    key_area in self._j_keys_areas or \
                    key_area in self._t_keys_areas:
                if click_x < self._key_width * K1 / D:
                    x_max = x - click_x + self._key_width * K1 / D
                    x_min = x_max - self._key_width * BLACK_KEY_WIDTH
                    key_found = 1
            if key_found == -1:
                x_min = x - click_x
                x_max = x_min + self._key_width
        return x_min, x_max

    def get_label(self, octave, key):
        if self._labels is None:
            return ""
        try:
            return self._labels[octave][key]
        except:
            return ""

    def get_value(self, octave, key):
        try:
            return self._values[octave][key]
        except:
            return ""

    def __allocate_cb(self, widget, rect):
        self.calculate_sizes(rect.width)

    def __draw_cb(self, widget, ctx):

        # calculate text height
        # TODO:
        ctx.select_font_face('sans-serif', cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(self.font_size)
        x_bearing, y_bearing, width, height, x_advance, y_advance = \
                ctx.text_extents('M')
        self._text_height = height

        for n in range(0, self._octaves):
            self.draw_octave(ctx, n)
        if self._add_c:
            self.draw_last_C(ctx, n + 1)
        for pressed_key in self._pressed_keys:
            octave = int(pressed_key[:pressed_key.find('_')])
            key = int(pressed_key[pressed_key.find('_') + 1:])

            if octave == -1 or (octave == self._octaves and key > 0):
                return
            if key == 0:
                if octave < self._octaves:
                    self.draw_C(ctx, octave, True)
                else:
                    self.draw_last_C(ctx, octave, True)
            elif key == 1:
                self.draw_CB(ctx, octave, True)
            elif key == 2:
                self.draw_D(ctx, octave, True)
            elif key == 3:
                self.draw_DB(ctx, octave, True)
            elif key == 4:
                self.draw_E(ctx, octave, True)
            elif key == 5:
                self.draw_F(ctx, octave, True)
            elif key == 6:
                self.draw_FB(ctx, octave, True)
            elif key == 7:
                self.draw_G(ctx, octave, True)
            elif key == 8:
                self.draw_GB(ctx, octave, True)
            elif key == 9:
                self.draw_A(ctx, octave, True)
            elif key == 10:
                self.draw_AB(ctx, octave, True)
            elif key == 11:
                self.draw_B(ctx, octave, True)

    def draw_octave(self, ctx, octave_number):
        self.draw_C(ctx, octave_number)
        self.draw_CB(ctx, octave_number)
        self.draw_D(ctx, octave_number)
        self.draw_DB(ctx, octave_number)
        self.draw_E(ctx, octave_number)
        self.draw_F(ctx, octave_number)
        self.draw_FB(ctx, octave_number)
        self.draw_G(ctx, octave_number)
        self.draw_GB(ctx, octave_number)
        self.draw_A(ctx, octave_number)
        self.draw_AB(ctx, octave_number)
        self.draw_B(ctx, octave_number)

        """
        Draw 5 types of keys: L keys, T keys, J keys and black keys,
        and if we add a c key is a simple key
        +--+---+--+---+--+---+
        |  |Bl |  |Bl |  | S |
        |  | ak|  | ak|  | i |
        |  +---+  +---+  | m |
        |    |      |    | p |
        |  L |  T   | J  | l |
        +----+------+----+---+
        """

    def draw_C(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7)
        self.draw_key_L(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 0, False, highlighted)

    def draw_CB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['CB']
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 1, True, highlighted)

    def draw_D(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['D']
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 2, False, highlighted)

    def draw_DB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['DB']
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 3, True, highlighted)

    def draw_E(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['E']
        self.draw_key_J(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 4, False, highlighted)

    def draw_F(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['F']
        self.draw_key_L(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 5, False, highlighted)

    def draw_FB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['FB']
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 6, True, highlighted)

    def draw_G(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['G']
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 7, False, highlighted)

    def draw_GB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['GB']
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 8, True, highlighted)

    def draw_A(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['A']
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 9, False, highlighted)

    def draw_AB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['AB']
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 10, True, highlighted)

    def draw_B(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7) + self._x_start['B']
        self.draw_key_J(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 11, False, highlighted)

    def draw_last_C(self, ctx, octave_number, highlighted=False):
        x = self._key_width * (octave_number * 7)
        self.draw_key_simple(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 0, False, highlighted)

    def draw_key_L(self, ctx, x, highlighted):
        ctx.save()
        ctx.move_to(x, 0)
        stroke = (0, 0, 0)
        fill = (1, 1, 1)
        if highlighted:
            fill = (1, 1, 0)

        ctx.line_to(x + self._key_width * K2 / D, 0)
        ctx.line_to(x + self._key_width * K2 / D, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.line_to(x, 0)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def draw_key_T(self, ctx, x, highlighted):
        ctx.save()
        stroke = (0, 0, 0)
        fill = (1, 1, 1)
        if highlighted:
            fill = (1, 1, 0)
        ctx.move_to(x + self._key_width * K1 / D, 0)
        ctx.line_to(x + self._key_width * K2 / D, 0)
        ctx.line_to(x + self._key_width * K2 / D, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.line_to(x, self._black_keys_height)
        ctx.line_to(x + self._key_width * K1 / D, self._black_keys_height)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def draw_key_J(self, ctx, x, highlighted):
        ctx.save()
        stroke = (0, 0, 0)
        fill = (1, 1, 1)
        if highlighted:
            fill = (1, 1, 0)
        ctx.move_to(x + self._key_width * K1 / D, 0)
        ctx.line_to(x + self._key_width, 0)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.line_to(x, self._black_keys_height)
        ctx.line_to(x + self._key_width * K1 / D, self._black_keys_height)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def draw_key_simple(self, ctx, x, highlighted):
        ctx.save()
        stroke = (0, 0, 0)
        fill = (1, 1, 1)
        if highlighted:
            fill = (1, 1, 0)
        ctx.move_to(x, 0)
        ctx.line_to(x + self._key_width, 0)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def draw_black(self, ctx, x, highlighted):
        ctx.save()
        ctx.move_to(x, 0)
        stroke = (0, 0, 0)
        fill = (0, 0, 0)
        if highlighted:
            fill = (1, 1, 0)

        ctx.line_to(x + self._key_width * K1 * 2 / D, 0)
        ctx.line_to(x + self._key_width * K1 * 2 / D, self._black_keys_height)
        ctx.line_to(x, self._black_keys_height)
        ctx.line_to(x, 0)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def _fill_and_stroke(self, ctx, fill, stroke):
        ctx.set_source_rgb(*fill)
        ctx.fill_preserve()
        ctx.set_source_rgb(*stroke)
        ctx.stroke()

    def _draw_label(self, ctx, x, octave_number, position, black_key,
                highlighted):
        #print "Dibujando ",text
        if self._labels is not None:
            text = self._labels[octave_number][position]
            x_bearing, y_bearing, width, height, x_advance, y_advance = \
                    ctx.text_extents(text)
            if black_key:
                x_text = x + self._key_width * K1 / D - (width / 2 + x_bearing)
                y_text = self._black_keys_height - (self._text_height * 2)
                if highlighted:
                    stroke = (0, 0, 0)
                else:
                    stroke = (1, 1, 1)
            else:
                x_text = x + self._key_width / 2 - (width / 2 + x_bearing)
                y_text = self._height - (self._text_height * 2)
                stroke = (0, 0, 0)
            ctx.set_source_rgb(*stroke)
            ctx.move_to(x_text, y_text)
            ctx.show_text(text)


def print_key_pressed(widget, octave_clicked, key_clicked, letter):
    print 'Pressed Octave: %d Key: %d Letter: %s' % (octave_clicked,
        key_clicked, letter)


def print_key_released(widget, octave_clicked, key_clicked, letter):
    print 'Released Octave: %d Key: %d Letter: %s' % (octave_clicked,
        key_clicked, letter)


def main():
    window = Gtk.Window()
    labels_tamtam = ['Q2W3ER5T6Y7UI', 'ZSXDCVGBHNJM', ',']
    piano = PianoKeyboard(octaves=2, add_c=True, labels=labels_tamtam)
    piano.connect('key_pressed', print_key_pressed)
    piano.connect('key_released', print_key_released)

    window.add(piano)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
