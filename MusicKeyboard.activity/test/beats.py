# python version of http://www.csounds.com/manualOLPC/GEN01.html

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
c.SetDebug(True)
c.SetOption("-odac")
c.SetOption("-m7")
c.CompileOrc(orc)
c.Start()
c.InputMessage('f 1 0 131072 1 "beats.wav" 0 4 0')
c.InputMessage('i 1 0 2')
c.Perform()

