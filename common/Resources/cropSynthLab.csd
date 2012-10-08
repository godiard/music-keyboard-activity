<CsoundSynthesizer>

<CsOptions>
-W -d -n
</CsOptions>

<CsInstruments>

sr=16000
ksmps=64
nchnls=1

/****************************************************************
Playing temp file
****************************************************************/
instr 1

Spath strget 999
Stempfile strcat Spath, "/tempMic.wav"
gilen filelen Stempfile
p3 = gilen
asig diskin Stempfile, 1
gasig dcblock asig

endin

/****************************************************************
Crop silence at the beginning
****************************************************************/
instr 2
ktimer timeinstk
ain = gasig
if ktimer > 40 then
    event "i", 3, 0, gilen - 0.2
    event "i", 4, gilen - 0.2, 0.01
    turnoff
endif
endin

/****************************************************************
recording
****************************************************************/
instr 3
kenv   adsr     0.01, 0.05, .9, 0.01

adel    delay   gasig, .005

Spath strget 999
Sfile strcat Spath, "/micTemp.wav"

ihandle fiopen Sfile, 2

fout Sfile, 2, adel*kenv

;out adel*kenv
adel = 0
endin

/****************************************************************
Audio input recording ( closing file )
****************************************************************/
instr 4
Spath strget 999
Sfile strcat Spath, "/micTemp.wav"
ficlose Sfile
endin


</CsInstruments>

<CsScore>
f1 0 8192 10 1
i1 0 4
i2 0 4
</CsScore>

</CsoundSynthesizer>
