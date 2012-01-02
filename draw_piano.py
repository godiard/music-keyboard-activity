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

import gobject
import gtk
import cairo


class PianoKeyboard(gtk.DrawingArea):

    __gsignals__ = {'key_pressed': (gobject.SIGNAL_RUN_FIRST,
                          gobject.TYPE_NONE,
                          ([gobject.TYPE_INT, gobject.TYPE_INT,
                            gobject.TYPE_STRING])),
                    'key_released': (gobject.SIGNAL_RUN_FIRST,
                          gobject.TYPE_NONE,
                          ([gobject.TYPE_INT, gobject.TYPE_INT,
                            gobject.TYPE_STRING]))}

    def __init__(self, octaves=1, add_c=False, labels=None):
        self._octaves = octaves
        self._add_c = add_c
        self._labels = labels
        self._pressed_key = None
        self.font_size = 20
        super(PianoKeyboard, self).__init__()
        # info needed to check keys positions
        self._white_keys = [0, 2, 4, 5, 7, 9, 11]
        self._l_keys_areas = [0, 3]
        self._t_keys_areas = [1, 4, 5]
        self._j_keys_areas = [2, 6]
        self.connect('expose_event', self.expose)
        self.connect('button_press_event', self.__button_press_cb)
        self.connect('button_release_event', self.__button_release_cb)
        self.connect('motion_notify_event', self.__motion_notify_cb)
        self.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_PRESS_MASK | \
                gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK | \
                gtk.gdk.POINTER_MOTION_HINT_MASK)

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
        self._black_keys_height = self._height * 2 / 3
        self._octave_width = self._key_width * 7

    def __button_press_cb(self, widget, event):
        if event.button == 1:
            x, y = event.x, event.y
            key_found = self.__get_key_at_position(x, y)
            if key_found is None:
                return True
            else:
                self._pressed_key = key_found
                octave_clicked = key_found[0]
                key_clicked = key_found[1]
                self.emit('key_pressed', octave_clicked, key_clicked,
                        self.get_label(octave_clicked, key_clicked))
                self.queue_draw()
                return True

    def __motion_notify_cb(self, widget, event):
        # only continue if the button is pressed
        if self._pressed_key is None:
            return True

        # if this is a hint, then let's get all the necessary
        # information, if not it's all we need.
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        key_found = self.__get_key_at_position(x, y)
        if key_found != self._pressed_key:
            self.emit('key_released', self._pressed_key[0],
                self._pressed_key[1], self.get_label(*self._pressed_key))

            self._pressed_key = key_found
            if key_found is not None:
                octave_clicked = key_found[0]
                key_clicked = key_found[1]
                self.emit('key_pressed', octave_clicked, key_clicked,
                        self.get_label(octave_clicked, key_clicked))
            self.queue_draw()

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
                if click_x > self._key_width * 2 / 3:
                    key_found = self._white_keys[key_area] + 1
            # check black key at the left
            if key_found == -1 and \
                key_area in self._j_keys_areas or \
                key_area in self._t_keys_areas:
                if click_x < self._key_width * 1 / 3:
                    key_found = self._white_keys[key_area] - 1
            if key_found == -1:
                key_found = self._white_keys[key_area]
        return (octave_found, key_found)

    def __button_release_cb(self, widget, event):
        if self._pressed_key is not None:
            self.emit('key_released', self._pressed_key[0],
                    self._pressed_key[1], self.get_label(*self._pressed_key))
            self._pressed_key = None
            self.queue_draw()

    def get_label(self, octave, key):
        if self._labels is None:
            return ""
        try:
            return self._labels[octave][key]
        except:
            return ""

    def expose(self, widget, event):
        rect = self.get_allocation()
        self.calculate_sizes(rect.width)

        ctx = widget.window.cairo_create()

        # set a clip region for the expose event
        ctx.rectangle(event.area.x, event.area.y, event.area.width,
                event.area.height)
        ctx.clip()

        # calculate text height
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(self.font_size)
        x_bearing, y_bearing, width, height, x_advance, y_advance = \
                ctx.text_extents('M')
        self._text_height = height

        self.draw(ctx)
        return False

    def draw(self, ctx):
        for n in range(0, self._octaves):
            self.draw_octave(ctx, n)
        if self._add_c:
            self.draw_last_C(ctx, n + 1)
        if self._pressed_key is not None:
            octave, key = self._pressed_key
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
        x = self._key_width * (octave_number * 7) + self._key_width * 2 / 3
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 1, True, highlighted)

    def draw_D(self, ctx, octave_number, highlighted=False):
        x = self._key_width + self._key_width * (octave_number * 7)
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 2, False, highlighted)

    def draw_DB(self, ctx, octave_number, highlighted=False):
        x = self._key_width + self._key_width * 2 / 3 + \
                self._key_width * (octave_number * 7)
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 3, True, highlighted)

    def draw_E(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 2 + self._key_width * (octave_number * 7)
        self.draw_key_J(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 4, False, highlighted)

    def draw_F(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 3 + self._key_width * (octave_number * 7)
        self.draw_key_L(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 5, False, highlighted)

    def draw_FB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 3 + self._key_width * 2 / 3 + \
                self._key_width * (octave_number * 7)
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 6, True, highlighted)

    def draw_G(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 4 + self._key_width * (octave_number * 7)
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 7, False, highlighted)

    def draw_GB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 4 + self._key_width * 2 / 3 + \
                self._key_width * (octave_number * 7)
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 8, True, highlighted)

    def draw_A(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 5 + self._key_width * (octave_number * 7)
        self.draw_key_T(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 9, False, highlighted)

    def draw_AB(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 5 + self._key_width * 2 / 3 + \
                self._key_width * (octave_number * 7)
        self.draw_black(ctx, x, highlighted)
        self._draw_label(ctx, x, octave_number, 10, True, highlighted)

    def draw_B(self, ctx, octave_number, highlighted=False):
        x = self._key_width * 6 + self._key_width * (octave_number * 7)
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

        ctx.line_to(x + self._key_width * 2 / 3, 0)
        ctx.line_to(x + self._key_width * 2 / 3, self._black_keys_height)
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
        ctx.move_to(x + self._key_width * 1 / 3, 0)
        ctx.line_to(x + self._key_width * 2 / 3, 0)
        ctx.line_to(x + self._key_width * 2 / 3, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._black_keys_height)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.line_to(x, self._black_keys_height)
        ctx.line_to(x + self._key_width * 1 / 3, self._black_keys_height)
        ctx.close_path()
        self._fill_and_stroke(ctx, fill, stroke)
        ctx.restore()

    def draw_key_J(self, ctx, x, highlighted):
        ctx.save()
        stroke = (0, 0, 0)
        fill = (1, 1, 1)
        if highlighted:
            fill = (1, 1, 0)
        ctx.move_to(x + self._key_width * 1 / 3, 0)
        ctx.line_to(x + self._key_width, 0)
        ctx.line_to(x + self._key_width, self._height)
        ctx.line_to(x, self._height)
        ctx.line_to(x, self._black_keys_height)
        ctx.line_to(x + self._key_width * 1 / 3, self._black_keys_height)
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

        ctx.line_to(x + self._key_width * 2 / 3, 0)
        ctx.line_to(x + self._key_width * 2 / 3, self._black_keys_height)
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
                x_text = x + self._key_width * 1 / 3 - (width / 2 + x_bearing)
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
    window = gtk.Window()
    labels_tamtam = ['Q2W3ER5T6Y7UI', 'ZSXDCVGBHNJM', ',']
    piano = PianoKeyboard(octaves=2, add_c=True, labels=labels_tamtam)
    piano.connect('key_pressed', print_key_pressed)
    piano.connect('key_released', print_key_released)

    window.add(piano)
    window.connect("destroy", gtk.main_quit)
    window.show_all()
    gtk.main()

if __name__ == "__main__":
    main()
