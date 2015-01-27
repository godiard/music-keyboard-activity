#!/usr/bin/env python
# Copyright (C) 2011, One Laptop Per Child
# Author, Gonzalo Odiard
# License: LGPLv2

import logging
from gi.repository import Gtk
from gi.repository import GObject

KEYB_NOTES = 25
# every cell represent 200 milliseconds
CELL_TIME = 200


class NotesView(Gtk.DrawingArea):

    def __init__(self):
        self._notes_matrix = None
        super(NotesView, self).__init__()
        self._select_color = (1, 1, 0)
        self._counter = 0
        self._page = 0
        self._keys_pressed = []
        self.connect('size-allocate', self.__allocate_cb)
        self.connect('draw', self.__draw_cb)
        self._keyboard_widget = None

    def _calculate_sizes(self, width, height):
        self._width = width
        self._height = height
        self._cell_size = self._height / KEYB_NOTES
        self._max_counter = self._width / self._cell_size

    def attach_keyboard(self, keyboard):
        self._keyboard_widget = keyboard
        if self._keyboard_widget is not None:
            GObject.timeout_add(CELL_TIME, self._update_pressed_keys)

    def set_select_color(self, r, g, b):
        """
        r, g, b : components of the color used to show pressed keys
                  (float) in the range 0.0 to 1.0
        """
        self._select_color = (r, g, b)

    def set_recorded_keys(self, recorded_keys):
        self._notes_matrix = []
        # create a array with one element for every CELL_TIME
        # every element is a array with the keys pressed at that time
        time_counter = 0
        pressed_keys = []
        for key_event in recorded_keys:
            time = key_event[0]
            cell = key_event[1] * 12 + key_event[2]
            pressed = len(key_event) == 4  # release events have a 5th element
            while time_counter < time:
                time_counter += (CELL_TIME / 1000.)
                self._notes_matrix.append(pressed_keys[:])
            if pressed:
                pressed_keys.append(cell)
            else:
                if cell in pressed_keys:
                    pressed_keys.remove(cell)
        logging.error('RECORDED_KEYS %s', recorded_keys)
        logging.error('NOTES_MATRIX %s', self._notes_matrix)
        self.reset_counter()

    def reset_counter(self):
        self._counter = 0
        self._page = 0
        self.queue_draw()

    def _update_pressed_keys(self):
        if self._keyboard_widget is None:
            return False

        self._keys_pressed = self._keyboard_widget.get_pressed_keys()

        x = self._counter * self._cell_size
        # we add 1 pixel at the left to hide the old cursor line
        if x < self._width:
            self.queue_draw_area(x - 1, 0, self._cell_size + 1, self._height)
        else:
            self.queue_draw()
        return True

    def _get_damaged_range(self, x, y):
        """
        Based on the x position, calculate what is the min & max X
        that need be redraw. Y is ignored due to most of the keys
        need redraw all the height
        """
        pass

    def __allocate_cb(self, widget, rect):
        self._calculate_sizes(rect.width, rect.height)

    def __draw_cb(self, widget, ctx):
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, self._width, self._height)
        ctx.fill()

        ctx.set_source_rgb(0.8, 0.8, 0.8)
        for n in range(0, KEYB_NOTES):
            y = (n + 1) * self._cell_size
            ctx.move_to(0, y)
            ctx.line_to(self._width, y)
            ctx.stroke()

        # draw cursor
        ctx.set_source_rgb(0.8, 0.8, 0.8)
        x = (self._counter + 1) * self._cell_size
        ctx.move_to(x, 0)
        ctx.line_to(x, self._height)
        ctx.stroke()

        r, g, b = self._select_color
        # draw recorded notes
        if self._notes_matrix is not None:
            ctx.set_source_rgba(r, g, b, 0.4)
            cell_counter = self._counter + self._page * self._max_counter

            while cell_counter < len(self._notes_matrix):
                x = cell_counter * self._cell_size
                pressed_keys = self._notes_matrix[cell_counter]
                for key in pressed_keys:
                    ctx.rectangle(cell_counter * self._cell_size,
                                  key * self._cell_size,
                                  self._cell_size, self._cell_size)
                    ctx.fill()
                cell_counter += 1

        # draw played notes
        ctx.set_source_rgb(r, g, b)
        for key in self._keys_pressed:
            octave_pressed = int(key[:key.find('_')])
            key_pressed = int(key[key.find('_') + 1:])
            # 12 keys by octave (counting black keys)
            cell_y = octave_pressed * 12 + key_pressed
            ctx.rectangle(self._counter * self._cell_size,
                          cell_y * self._cell_size,
                          self._cell_size, self._cell_size)
            ctx.fill()

        self._counter += 1
        if self._counter > self._max_counter:
            self._counter = 0
            self._page += 1
