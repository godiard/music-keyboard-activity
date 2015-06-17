#!/usr/bin/env python
# Copyright (C) 2011, One Laptop Per Child
# Author, Gonzalo Odiard
# License: LGPLv2

import logging
from gi.repository import Gtk

KEYB_NOTES = 25

class NotesView(Gtk.DrawingArea):

    def __init__(self, notes=None):
        self._notes = notes 
        super(NotesView, self).__init__()

        self.connect('size-allocate', self.__allocate_cb)
        self.connect('draw', self.__draw_cb)

    def _calculate_sizes(self, width, height):
        self._width = width
        self._height = height
        self._cell_size = self._height / KEYB_NOTES
        self.set_size_request(self._width, self._height)

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
        logging.error('NOTESVIEW draw')
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, self._width, self._height)
        ctx.fill()

        ctx.set_source_rgb(0, 0, 0)
        for n in range(0, KEYB_NOTES):
            y = (n + 1) * self._cell_size
            ctx.move_to(0, y)
            ctx.line_to(self._width, y)
            ctx.stroke()

