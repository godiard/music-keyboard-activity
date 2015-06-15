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

def clicked_cb(button, c):
    python_array = [1.0, 0.0, 2.0]
    csnd_array = csnd6.doubleArray(len(python_array))
    for n in range(len(python_array)):
        csnd_array[n] = python_array[n]
    c.ScoreEvent('i', csnd_array, len(python_array))
    # TODO: these are to try avoid seg fault at activity close (not enough)
    # del csnd_array
    # del python_array

def quit(widget, c):
    # TODO: these are to try avoid seg fault at activity close (not enough)
    # c.Stop()
    # c.Cleanup()
    Gtk.main_quit()

win = Gtk.Window()
btn = Gtk.Button('Play')
btn.connect('clicked', clicked_cb, c)
win.add(btn)
win.show_all()
win.connect("destroy", quit, c)
Gtk.main()
