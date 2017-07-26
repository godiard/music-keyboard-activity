# Gtk version of https://github.com/csound/csoundAPI_examples/blob/master/python/example11.py
# but using a loaded istrument

from gi.repository import Gtk
import csnd6

orc = """
sr = 44100
kr = 4410
ksmps = 10
nchnls = 1

; Instrument #1.
instr 1
   kamp = 30000
   kcps = 1
   ifn = 1
   ibas = 1

   ; Play the audio sample stored in Table #1.
   a1 loscil kamp, kcps, ifn, ibas
   out a1
endin"""

c = csnd6.Csound()
c.SetOption("-odac")
c.CompileOrc(orc)
c.Start()
c.InputMessage('f 1 0 131072 1 "beats.wav" 0 4 0')

perfThread = csnd6.CsoundPerformanceThread(c)
perfThread.Play()

def clicked_cb(button, perf):
    perf.InputMessage("i 1 0 2")

win = Gtk.Window()
btn = Gtk.Button('Play')
btn.connect('clicked', clicked_cb, perfThread)
win.add(btn)
win.show_all()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
