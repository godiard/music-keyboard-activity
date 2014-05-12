<CsoundSynthesizer>
<CsOptions>
-n -odac -m0 -W -s -d
</CsOptions>
<CsInstruments>
sr=16000
ksmps=64
nchnls=2
giScale = 1/sr
giAliasSr = sr/2.1

gainrev init 0
gaoutL init 0
gaoutR init 0
gasynth init 0
gkTrackpadX init 0
gkTrackpadY init 0
gSpath strcpy " "

/*****************************
matrix for TamTam's SynthLab
*****************************/
zakinit 8, 32

/*****************************
opcodes needed by TamTam's SynthLab
*****************************/

opcode homeSine, a, kki
kpitch, kspread, iTable xin

kspread = kspread + 1

kr1 randomi 0.99, 1.01, 3.45
kr2 randomi 0.9901, 1.0101, 4.43
kr3 randomi 0.9899, 1.0091, 5.25
kr4 randomi 0.9889, 1.00921, 6.15

kpit1 = kpitch
kpit2 = kpit1*kspread
kpit3 = kpit2*kspread
kpit4 = kpit3*kspread
kpit5 = kpit4*kspread
kpit6 = kpit5*kspread
kpit7 = kpit6*kspread
kpit8 = kpit7*kspread

a1 oscil 1000, kpit1*kr1, iTable
a2 oscil 1000, kpit2*kr2, iTable
a3 oscil 1000, kpit3*kr3, iTable
a4 oscil 1000, kpit4*kr4, iTable
a5 oscil 1000, kpit5*kr1, iTable
a6 oscil 1000, kpit6*kr2, iTable
a7 oscil 1000, kpit7*kr3, iTable
a8 oscil 1000, kpit8*kr4, iTable

aout = a1+a2+a3+a4+a5+a6+a7+a8
xout aout
endop

opcode synthGrain, a, aaiiii
aindex, atrans, ifreq, iphase, itable, itabdur xin
apha phasor ifreq, iphase
aenv tab apha, 42, 1
atrig = int(1-aenv)
apos samphold aindex, atrig
adur samphold atrans, atrig

aline = apha * adur * sr + apos
aline limit aline, 0 , itabdur
ag tablei aline, itable, 0
aout = ag * aenv

xout aout
endop


opcode  ControlMatrice, i, iikkkk
iTable, iIndex, kc1, kc2, kc3, kc4  xin

iSomme table iIndex, iTable+3

if iSomme == 0 then
goto noparams
endif

iPar table iIndex, iTable

if iSomme == 1 then
kp = iPar
elseif iSomme == 3 then
kp = iPar * kc1
elseif iSomme == 5 then
kp = iPar * kc2
elseif iSomme == 7 then
kp = iPar * ((kc1 + kc2)*.5)
elseif iSomme == 9 then
kp = iPar * kc3
elseif iSomme == 11 then
kp = iPar * ((kc1 + kc3)*.5)
elseif iSomme == 13 then
kp = iPar * ((kc2 + kc3)*.5)
elseif iSomme == 15 then
kp = iPar * ((kc1 + kc2 + kc3)*.33)
elseif iSomme == 17 then
kp = iPar * kc4
elseif iSomme == 19 then
kp = iPar * ((kc1 + kc4)*.5)
elseif iSomme == 21 then
kp = iPar * ((kc2 + kc4)*.5)
elseif iSomme == 23 then
kp = iPar * ((kc1 + kc2 + kc4)*.33)
elseif iSomme == 25 then
kp = iPar * ((kc3 + kc4)*.5)
elseif iSomme == 27 then
kp = iPar * ((kc1 + kc3 + kc4)*.5)
elseif iSomme == 29 then
kp = iPar * ((kc2 + kc3 + kc4)*.33)
elseif iSomme == 31 then
kp = iPar * ((kc1 + kc2 + kc3 + kc4)*.25)
endif

if iTable == 5201 then
zkw     kp, iIndex+1
elseif iTable == 5202 then
zkw     kp, iIndex+17
endif

xout    iIndex

noparams:
endop

opcode  SourceMatrice, i, iaaaa
iIndex, as1, as2, as3, as4  xin

iSomme table iIndex-1, 5206

if iSomme == 0 then
goto noparams
endif

if iSomme == 1 then
as = as1
elseif iSomme == 2 then
as = as2
elseif iSomme == 3 then
as = as1 + as2
elseif iSomme == 4 then
as = as3
elseif iSomme == 5 then
as = as1 + as3
elseif iSomme == 6 then
as = as2 + as3
elseif iSomme == 7 then
as = as1 + as2 + as3
elseif iSomme == 8 then
as = as4
elseif iSomme == 9 then
as = as1 + as4
elseif iSomme == 10 then
as = as2 + as4
elseif iSomme == 11 then
as = as1 + as2 + as4
elseif iSomme == 12 then
as = as3 + as4
elseif iSomme == 13 then
as = as1 + as3 + as4
elseif iSomme == 14 then
as = as2 + as3 + as4
elseif iSomme == 15 then
as = as1 + as2 + as3 + as4
endif

zaw     as, iIndex
xout    iIndex

noparams:
endop

opcode  FxMatrice, i, iaaaa
iIndex, as1, as2, as3, as4  xin

iSomme table iIndex-1, 5206

if iSomme == 0 then
goto noparams
endif

if iSomme == 1 then
as = as1
elseif iSomme == 2 then
as = as2
elseif iSomme == 3 then
as = as1 + as2
elseif iSomme == 4 then
as = as3
elseif iSomme == 5 then
as = as1 + as3
elseif iSomme == 6 then
as = as2 + as3
elseif iSomme == 7 then
as = as1 + as2 + as3
elseif iSomme == 8 then
as = as4
elseif iSomme == 9 then
as = as1 + as4
elseif iSomme == 10 then
as = as2 + as4
elseif iSomme == 11 then
as = as1 + as2 + as4
elseif iSomme == 12 then
as = as3 + as4
elseif iSomme == 13 then
as = as1 + as3 + as4
elseif iSomme == 14 then
as = as2 + as3 + as4
endif

zaw     as, iIndex
xout    iIndex

noparams:
endop

opcode  controller, k, ii
iControlNum, idur   xin

iControlType table  iControlNum-1, 5203

if iControlType == 0 then
goto nocontrol
endif

ioffset = (iControlNum-1)*4
iPar1   table   ioffset, 5200
iPar2   table   ioffset+1, 5200
iPar3   table   ioffset+2, 5200
iPar4   table   ioffset+3, 5200

if iControlType == 1 then
    kControl    lfo     iPar1, iPar2, int(iPar3)
    kControl    =       kControl+iPar4
elseif iControlType == 2 then
    irange      =       (iPar2-iPar1)*.5
    kControl    randi   irange, iPar3, iPar4-.001, 0, irange+iPar1
elseif iControlType == 3 then
    kControl    adsr    iPar1*idur+.0001, iPar2*idur, iPar3, iPar4*idur
elseif iControlType == 4 then
    if iPar3 == 0 then
        kControl1 = ((gkTrackpadX+1)*.5)*(iPar2-iPar1)+iPar1
    elseif iPar3 == 1 then
        kval = (gkTrackpadX+1)*.5
        kControl1 pow kval, 2
        kControl1 = kControl1 * (iPar2-iPar1) + iPar1
    endif
    if iPar4 == 0 then
        kControl = kControl1
    else
        ktrig oscil 1, 1/iPar4, 45
        kControl samphold kControl1, ktrig, i(kControl1), 0
        endif
elseif iControlType == 5 then
    if iPar3 == 0 then
        kControl1 = ((gkTrackpadY+1)*.5)*(iPar2-iPar1)+iPar1
    elseif iPar3 == 1 then
        kval = (gkTrackpadY+1)*.5
        kControl1 pow kval, 2
        kControl1 = kControl1 * (iPar2-iPar1) + iPar1
    endif
    if iPar4 == 0 then
        kControl = kControl1
    else
        ktrig oscil 1, 1/iPar4, 45
        kControl samphold kControl1, ktrig, i(kControl1), 0
        endif
endif

xout    kControl

nocontrol:
endop

opcode  source, a, ii
iSourceNum, ipitch     xin

iSourceType table iSourceNum+3, 5203

if iSourceType == 0 then
goto nosource
endif

ioffset =   (iSourceNum-1)*4
kpara1  zkr ioffset+1
kpara2  zkr ioffset+2
kpara3  zkr ioffset+3
kpara4  zkr ioffset+4

iPar1   table   ioffset, 5201
iPar2   table   ioffset+1, 5201
iPar3   table   ioffset+2, 5201
iPar4   table   ioffset+3, 5201

if iSourceType == 1 then
    aSource	foscil	2000*kpara4, ipitch, kpara1, kpara2, kpara3, 1
elseif iSourceType == 2 then
    aSource	gbuzz	5000*kpara4, ipitch*kpara1, int(abs(kpara2))+5, 0, kpara3+0.01, 2
elseif iSourceType == 3 then
    iPar2 = int(iPar2)
    if iPar2 == 0 then
        imode = 0
    elseif iPar2 == 1 then
        imode = 10
    elseif iPar2 == 2 then
        imode = 12
    endif
    aSource vco2    2000*kpara4, ipitch*kpara1, imode, 0.1, 0, iPar3
elseif iSourceType == 4 then
    if iPar3 == 0 then
        kvib = 0
        goto novib
    else
        kvibenv    linseg  0, .3, 1, p3-.3, 1
        kvib    oscil	ipitch*.015, kpara3, 1
    endif
    novib:
    aSource pluck   5000*kpara4, ipitch*(abs(kpara1))+.001+kvib, 40, 0, 6
    aSource butterlp    aSource, kpara2
elseif iSourceType == 5 then
    if int(iPar1) == 0 then
        ar rand   5000*kpara4
    elseif int(iPar1) == 1 then
        ar pinkish 5000*kpara4
    elseif int(iPar1) == 2 then
        ar gauss   5000*kpara4
    endif
    knoisebandwith limit abs(kpara3), 1, sr/2
    aSource butterbp ar, kpara2, knoisebandwith
    aSource balance aSource, ar
elseif iSourceType == 6 then
    iSndpitch = p4/261.626
    iLoopIndex = iPar2 * 3
    ils table iLoopIndex, 5755
    ile table iLoopIndex+1, 5755
    icd table iLoopIndex+2, 5755
    if ile == 0 then
        ile = nsamp(5000+iPar2) * giScale - .01
    endif
    if icd == 0 then
        icd = .01
    endif
    aSource	     flooper2	kpara4*.4, iSndpitch*abs(kpara1), ils, ile, icd, 5000+iPar2
    aSource butterlp aSource, abs(kpara3)
elseif iSourceType == 7 then
    kvoy    =  int(kpara2*3)
    kform1  table   kvoy, 4
    kform2  table   kvoy+1, 4
    kform3  table   kvoy+2, 4
    kform1  port    kform1, .1, 500
    kform2  port    kform2, .1, 1500
    kform3  port    kform3, .1, 2500
    kvibadev	randomi	-.0852, .0152, .5
    kvibfdev	randomi	-.032, .032, .5
    kvibfreqrand	randomi	kpara3-.75, kpara3+.75, .2
    kvibfatt    linseg  0, .3, 1, p3-.3, 1
    kvib		oscili	(1+kvibadev)*kvibfatt, (kvibfreqrand+kvibfdev), 1
    kharm		randomi	40, 50, 1.34
    kmul		randomi	.80, .84, 1.45
    kbam		randomi	480., 510., 2.07
    kfunddev	randomi	-.0053, .0052, 1.05
    ar  		gbuzz  	kbam, (p4*kpara1*(1+kfunddev)+kvib), int(kharm), 0, kmul, 2
    a1 			resonx 	ar, kform1, 140, 2, 1
    a2 			resonx 	ar, kform2, 180, 2, 1
    a3 			resonx 	ar, kform3, 220, 2 , 1
    aSource     = ((a1*80)+(a2*55)+(a3*40))*kpara4
elseif iSourceType == 8 then
    iSndPitch = p4/261.626
    igrdur = .1
    itable = 5000+iPar2
    irealTable = 5500 + iSourceNum
    itabdur = nsamp(itable)
    ifreq = 1 / igrdur
    kamp = kpara4 * .2
    aindex upsamp abs(kpara3) * itabdur
    atrans upsamp kpara1 * igrdur * iSndPitch

    as1 synthGrain aindex, atrans, ifreq, 0.82, irealTable, itabdur
    as2 synthGrain aindex, atrans, ifreq, .58, irealTable, itabdur
    as3 synthGrain aindex, atrans, ifreq, .41, irealTable, itabdur
    as4 synthGrain aindex, atrans, ifreq, 0.19, irealTable, itabdur
    as5 synthGrain aindex, atrans, ifreq, 0, irealTable, itabdur
    aSource = (as1+as2+as3+as4+as5)*kamp
    aSource butterlp aSource, 7500
elseif iSourceType == 9 then
    aSource	homeSine p4*kpara1, kpara2*0.1, iPar3+30
    aSource = aSource*kpara4
elseif iSourceType == 10 then
    Sname       sprintf "/labmic%d", iPar2
    Sfullname   strcat gSpath, Sname
    iSndpitch   = p4/261.626
    aSource	    diskin	Sfullname, iSndpitch*abs(kpara3), 0, 1
    aSource     = aSource * kpara4
endif

aSource dcblock aSource
xout    aSource

nosource:
endop

opcode  effects, a, ii
iFxNum, ipitch     xin

iFxType table iFxNum+7, 5203

if iFxType == 0 then
goto nofx
endif

as1  zar iFxNum
as2  zar iFxNum+4
as  =   as1+as2

ioffset =   (iFxNum+3)*4
kpara1  zkr ioffset+1
kpara2  zkr ioffset+2
kpara3  zkr ioffset+3
kpara4  zkr ioffset+4

ioffset2 =   (iFxNum-1)*4
iPar1   table   ioffset2, 5202
iPar2   table   ioffset2+1, 5202
iPar3   table   ioffset2+2, 5202
iPar4   table   ioffset2+3, 5202

if iFxType == 1 then
    kwgfeed limit kpara3, 0, 1
    aFx	wguide1	as, abs(kpara1)+1, kpara2, kwgfeed
    aFx	=		aFx*kpara4
elseif iFxType == 2 then
    aFx	lpf18	as*.0005, abs(kpara1)+20, kpara2, kpara3
    aFx	=		aFx*5000*kpara4
elseif iFxType == 3 then
    aFx bqrez   as*kpara4, abs(kpara1)+20, abs(kpara2)+1, int(iPar3)
    aFx balance aFx, as*kpara4
elseif iFxType == 4 then
    amod lfo 1, kpara1, int(iPar3)
    aFx = ((as*amod*kpara2)+(as*(1-kpara2)))*kpara4
elseif iFxType == 5 then
    ain =   as*kpara4
    krevLength limit kpara1, 0.01, 10
    arev reverb ain, krevLength
    arev butterlp arev, kpara2
    aFx =   (arev*kpara3)+(as*(1-kpara3))
elseif iFxType == 6 then
    fsig  pvsanal   as, 1024, 256, 1024, 1
    ftps1  pvscale   fsig, kpara1
    aFx  pvsynth  ftps1
    adry delay as, iPar2
    aFx = ((aFx*kpara3)+(adry*(1-kpara3)))*kpara4
elseif iFxType == 7 then
    aeq1 butterbp as, 700, 400
    aeq2 butterbp as, 1500, 600
    aeq3 butterbp as, 3000, 1000
    aeq4 butterbp as, 5000, 2000
    aFx = (aeq1*kpara1)+(aeq2*kpara2)+(aeq3*kpara3)+(aeq4*kpara4)
elseif iFxType == 8 then
    afeed init 0
    adel oscil  kpara1, kpara2, 1
    adel = adel + kpara1 + kpara3
    adel limit adel, 0, 50
    aFx vdelay as+afeed, adel, 50
    afeed = aFx * kpara4
endif

xout    aFx

nofx:
endop


/****************************************************************
Reverb + master out
*****************************************************************/
instr 200

gktime timek

kTrackpadX chnget "trackpadX"
gkTrackpadX = kTrackpadX / 600.
gkTrackpadX limit gkTrackpadX, -1, 1

kTrackpadY chnget "trackpadY"
gkTrackpadY = kTrackpadY / 450.
gkTrackpadY limit -gkTrackpadY, -1, 1

koutGain chnget "masterVolume"
koutGain = koutGain * 0.02
gkduck  init    1
gkduck port gkduck, .03, 1.

ain		dcblock		gainrev*0.05
arev	reverb		ain, 2.5
arev	butterlp	arev, 5000

aLeft   butterlp        gaoutL, 7500
aRight  butterlp        gaoutR, 7500

aLeft   eqfil       aLeft, 4000, 1000, 0.125
aRight  eqfil       aRight, 4000, 1000, 0.125

;aLeft   butterhp    aLeft, 150
;aRight  butterhp    aRight, 150

aOutLeft dcblock (arev + aLeft) * koutGain * gkduck
aOutRight dcblock (arev + aRight) * koutGain * gkduck
gaRecL  =   aOutLeft
gaRecR  =   aOutRight
		outs		aOutLeft, aOutRight

        gaoutL = 0
        gaoutR = 0
		gainrev	=	0

endin

/****************************************************************
ducking
****************************************************************/
instr 5600
gkduck linseg 1., 0.005, 0.05, 3.9, 0.05, 0.095, 1
endin

/****************************************************************
Performance recording start
*****************************************************************/
instr 5400
Sname strget p4
ihandle fiopen Sname, 2
fout Sname, 2, gaRecL, gaRecR
clear gaRecL, gaRecR
endin

/****************************************************************
Performance recording stop ( closing file )
*****************************************************************/
instr 5401
Sname strget p4
turnoff2 5400, 8, 0
ficlose Sname
endin

/****************************************************************
Handler audio input recording
****************************************************************/
instr 5201

ktim timeinsts

gkduck = .05
itab = p4
ain inch 1
krms    rms     ain
ktrig   trigger     krms, 1500, 0

if ktrig == 1 then
event "i", 5202, 0 , 1, itab
turnoff
endif

ithresh = p3 - 1

if ktim > ithresh then
gkduck linseg .05, .8, .05, .2, 1
endif

endin

/****************************************************************
Audio input recording
****************************************************************/
instr 5202
kenv   adsr     0.005, 0.05, .9, 0.01
gkduck  linseg .05, .8, .05, .2, 1
ain inch 1

adel    delay   ain, .01

Sname sprintf "/home/olpc/.sugar/default/tamtam/snds/mic%d", int(p4)-6
ihandle fiopen Sname, 2
event "i", 5212, 1 , .01, p4

fout Sname, 2, adel*kenv
adel = 0
endin

/****************************************************************
Audio input recording ( closing file )
****************************************************************/
instr 5212
Sname sprintf "/home/olpc/.sugar/default/tamtam/snds/mic%d", int(p4)-6
ficlose Sname
endin

/****************************************************************
SynthLab mic recording
****************************************************************/
instr 6000
ain inch 1
aindex  phasor  1/p3
tablew  ain, aindex, 6000+p4, 1
endin

/****************************************************************
SynthLab input recording
****************************************************************/
instr 5204

Sname sprintf "/lab%d", int(p4)-85
Sfile strcat gSpath, Sname
fout Sfile, 2, gasynth
clear gasynth
endin

/************************
TamTam's SynthLab instrument
************************/
instr 5203

gSpath strget p10

if p5 != 0 then
event_i "i", 5204, 0, p3, p5
endif

aSource1	init	0
aSource2	init	0
aSource3	init	0
aSource4	init	0
aFx1		init	0
aFx2		init	0
aFx3		init	0
aFx4		init	0
aout		init	0

ipitch  =   p4

kc1     controller     1,p3
kc2     controller     2,p3
kc3     controller     3,p3
kc4     controller     4,p3

is1p1   ControlMatrice     5201, 0, kc1, kc2, kc3, kc4
is1p2   ControlMatrice     5201, 1, kc1, kc2, kc3, kc4
is1p3   ControlMatrice     5201, 2, kc1, kc2, kc3, kc4
is1p4   ControlMatrice     5201, 3, kc1, kc2, kc3, kc4
is2p1   ControlMatrice     5201, 4, kc1, kc2, kc3, kc4
is2p2   ControlMatrice     5201, 5, kc1, kc2, kc3, kc4
is2p3   ControlMatrice     5201, 6, kc1, kc2, kc3, kc4
is2p4   ControlMatrice     5201, 7, kc1, kc2, kc3, kc4
is3p1   ControlMatrice     5201, 8, kc1, kc2, kc3, kc4
is3p2   ControlMatrice     5201, 9, kc1, kc2, kc3, kc4
is3p3   ControlMatrice     5201, 10, kc1, kc2, kc3, kc4
is3p4   ControlMatrice     5201, 11, kc1, kc2, kc3, kc4
is4p1   ControlMatrice     5201, 12, kc1, kc2, kc3, kc4
is4p2   ControlMatrice     5201, 13, kc1, kc2, kc3, kc4
is4p3   ControlMatrice     5201, 14, kc1, kc2, kc3, kc4
is4p4   ControlMatrice     5201, 15, kc1, kc2, kc3, kc4

aSource1    source  1, ipitch*2
aSource2    source  2, ipitch*2
aSource3    source  3, ipitch*2
aSource4    source  4, ipitch*2

ifx1p1   ControlMatrice     5202, 0, kc1, kc2, kc3, kc4
ifx1p2   ControlMatrice     5202, 1, kc1, kc2, kc3, kc4
ifx1p3   ControlMatrice     5202, 2, kc1, kc2, kc3, kc4
ifx1p4   ControlMatrice     5202, 3, kc1, kc2, kc3, kc4
ifx2p1   ControlMatrice     5202, 4, kc1, kc2, kc3, kc4
ifx2p2   ControlMatrice     5202, 5, kc1, kc2, kc3, kc4
ifx2p3   ControlMatrice     5202, 6, kc1, kc2, kc3, kc4
ifx2p4   ControlMatrice     5202, 7, kc1, kc2, kc3, kc4
ifx3p1   ControlMatrice     5202, 8, kc1, kc2, kc3, kc4
ifx3p2   ControlMatrice     5202, 9, kc1, kc2, kc3, kc4
ifx3p3   ControlMatrice     5202, 10, kc1, kc2, kc3, kc4
ifx3p4   ControlMatrice     5202, 11, kc1, kc2, kc3, kc4
ifx4p1   ControlMatrice     5202, 12, kc1, kc2, kc3, kc4
ifx4p2   ControlMatrice     5202, 13, kc1, kc2, kc3, kc4
ifx4p3   ControlMatrice     5202, 14, kc1, kc2, kc3, kc4
ifx4p4   ControlMatrice     5202, 15, kc1, kc2, kc3, kc4

ifx1in   SourceMatrice	    1, aSource1, aSource2, aSource3, aSource4
ifx2in   SourceMatrice	    2, aSource1, aSource2, aSource3, aSource4
ifx3in   SourceMatrice	    3, aSource1, aSource2, aSource3, aSource4
ifx4in   SourceMatrice	    4, aSource1, aSource2, aSource3, aSource4

ifx1in1  FxMatrice          5, aFx1, aFx2, aFx3, aFx4
ifx2in1  FxMatrice          6, aFx1, aFx2, aFx3, aFx4
ifx3in1  FxMatrice          7, aFx1, aFx2, aFx3, aFx4
ifx4in1  FxMatrice          8, aFx1, aFx2, aFx3, aFx4

aFx1	   effects		    1, ipitch
aFx2	   effects		    2, ipitch
aFx3	   effects		    3, ipitch
aFx4	   effects		    4, ipitch

iSourceOut1 table 8, 5206
iSourceOut2 table 9, 5206
iSourceOut3 table 10, 5206
iSourceOut4 table 11, 5206
iFxOut1 table 12, 5206
iFxOut2 table 13, 5206
iFxOut3 table 14, 5206
iFxOut4 table 15, 5206

aout    =   (aSource1*iSourceOut1)+(aSource2*iSourceOut2)+(aSource3*iSourceOut3)+(aSource4*iSourceOut4)+(aFx1*iFxOut1)+(aFx2*iFxOut2)+(aFx3*iFxOut3)+(aFx4*iFxOut4)

kenv adsr p3*p6+0.001, p3*p7, p8, p3*p9
aout = aout*kenv

vincr gasynth, aout

        outs    aout*.707, aout*.707

zacl	0, 8

endin

/***********************
DELETE RESOURCES
************************/

instr 5000

icount init 0

again:
ftfree 5000+icount, 0
icount = icount+1

if icount < p4 goto again

turnoff

endin

/*************************
Loop points editor
*************************/
instr 5022

kstart chnget "lstart"
kend chnget "lend"
kdur chnget "ldur"
kvol chnget "lvol"

idurfadein     init    0.005
idurfadeout     init    0.095
iampe0    	init    1
iampe1    	init  	1
iampe2    	init    1

itie     	tival
if itie  ==  1     	igoto nofadein

iampe0    	init     0
iskip   =   1

nofadein:
iskip   =   0
igliss  =   0.005

if p3   < 	0       igoto nofadeout

iampe2      init    0

nofadeout:

idelta  =   idurfadein+idurfadeout
if idelta > abs(p3) then
idelta = abs(p3)
endif

iampe0      =       iampe0
iampe2      =       iampe2
kenv     	linseg  iampe0, idurfadein, iampe1, abs(p3)-idelta, iampe1, idurfadeout,  iampe2


ivibRand    random  4.1, 5.7

kvibrato    oscil   .006, ivibRand, 1

           	tigoto  tieskip

a1	     flooper2	0.5, 1+kvibrato, kstart, kend, kdur, 4999, 0, 0, 0, iskip

a1      =   a1*kenv*kvol

gaoutL = a1*0.5+gaoutL
gaoutR =  a1*0.5+gaoutR

gainrev	=	        a1*0.05+gainrev

  tieskip:
endin

/*************************
Loop points editor, simple player
*************************/
instr 5023

kvol chnget "lvol"

p3      =   nsamp(4999) * giScale

a1      loscil  0.5, 1, 4999, 1

kenv   adsr     0.005, 0.05, .8, 0.1

a1  =   a1*kenv*kvol

gaoutL = a1*0.5+gaoutL
gaoutR = a1*0.5+gaoutR

gainrev =	    a1*0.05+gainrev

endin

/****************************************************************
Soundfile player with miniTamTam's tied notes
****************************************************************/
/*************************
pitch, reverbGain, amp, pan, table, att, dec, filtType, cutoff, loopstart, loopend, crossdur
*************************/
instr 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010

idump = p16
idump2 = p17
idump3 = p18
idump4 = p19

iTrackId = int(p1-5001)
SvolTrackName sprintf "trackVolume%0d", iTrackId
kvol chnget SvolTrackName
kvol = kvol * 0.01
kvol port kvol, .01, i(kvol)

idurfadein     init    0.005
idurfadeout     init    0.095
iampe0    	init    1
iampe1    	=  	p6
iampe2    	init    1

itie     	tival
if itie  ==  1     	igoto nofadein

idurfadein  init p9
iampe0    	init     0
iskip   =   1
kpitch     	init  	p4
kamp   init    p6
kpan        init    p7
krg         init    p5

nofadein:
iskip   =   0
igliss  =   0.005

if p3   < 	0       igoto nofadeout

idurfadeout     init    p10
iampe2      init    0

nofadeout:

idelta  =   idurfadein+idurfadeout
if idelta > abs(p3) then
idelta = abs(p3)
endif

iampe0      =       iampe0 * p6
iampe2      =       iampe2 * p6
kenv     	linseg  iampe0, idurfadein, iampe1, abs(p3)-idelta, iampe1, idurfadeout,  iampe2

kpitchBend port gkTrackpadX, .03, i(gkTrackpadX)
kpitchBend pow kpitchBend + 1, 5
kampBend port gkTrackpadY, .03, i(gkTrackpadY)
kampBend pow kampBend + 1, 5

ivibRand    random  4.1, 5.7

kvibrato    oscil   .006*kampBend, ivibRand*kpitchBend, 1

           	tigoto  tieskip

kpitch     	portk  	p4, igliss, p4
kpan        portk   p7, igliss, p7
krg         portk   p5, igliss, p5
kcutoff     portk   p12, igliss, p12
kls	    portk   p13, igliss, p13
kle	    portk   p14, igliss, p14
kcd         portk   p15, igliss, p15

a1	     flooper2	1, kpitch+kvibrato, kls, kle, kcd, p8, 0, 0, 0, iskip

if (p11-1) != -1 then
acomp   =  a1
a1      bqrez   a1, kcutoff, 6, p11-1
a1      balance     a1, acomp
endif

if kpitch < 1 then
kalias = giAliasSr*kpitch
else
kalias = giAliasSr
endif

a1      tone   a1, kalias

a1      =   a1*kenv*kvol

gaoutL = a1*(1-kpan)+gaoutL
gaoutR =  a1*kpan+gaoutR

gainrev	=	        a1*krg+gainrev

  tieskip:
endin


/*************************
Soundfile player with edit's looped notes
*************************/
instr 5101, 5102, 5103, 5104, 5105, 5106, 5107, 5108, 5109, 5110

if p16 != -1 then
    inum    =   frac(p16) * 10000
    itable2 =   int(p16)
    event_i "i", inum, 0, p3, p4, p5, p6, p7, itable2, p9, p10, p11, p12, p17, p18, p19, -1
endif

ipitch random p4*.995, p4*1.005

iTrackId = int(p1-5101)
SvolTrackName2 sprintf "trackVolume%0d", iTrackId
kvol chnget SvolTrackName2
kvol = kvol * 0.01
kvol port kvol, .01, 0 ;i(kvol)

ivibRand    random  4.1, 5.7

kvibrato    oscil   .006, ivibRand, 1

a1	     flooper2	1, ipitch+kvibrato, p13, p14, p15, p8, 0, 0, 0

if (p11-1) != -1 then
acomp   =  a1
a1      bqrez   a1, p12, 6, p11-1
a1      balance     a1, acomp
endif

;if p4 < 1 then
;ialias = giAliasSr*p4
;else
;ialias = giAliasSr
;endif

;a1      tone   a1, ialias

aenv   adsr     p9, 0.005, p6, p10
a1      =   a1*aenv*kvol

gaoutL = a1*(1-p7)+gaoutL
gaoutR =  a1*p7+gaoutR

gainrev	= a1*p5+gainrev

endin

/**************************************************************
Simple soundfile player (miniTamTam)
**************************************************************/

instr 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018, 5019, 5020

idump = p16
idump2 = p17
idump3 = p18
idump4 = p19

iTrackId = int(p1-5011)
SvolTrackName3 sprintf "trackVolume%0d", iTrackId
kvol chnget SvolTrackName3
kvol = kvol * 0.01
kvol port kvol, .01

p3      =   nsamp(p8) * giScale / p4

a1      loscil  p6, p4, p8, 1

if (p11-1) != -1 then
acomp = a1
a1      bqrez   a1, p12, 6, p11-1
a1      balance     a1, acomp
endif

if p4 < 1 then
ialias = giAliasSr*p4
else
ialias = giAliasSr
endif

a1      tone   a1, ialias

kenv   adsr     p9, 0.05, .8, p10
a1  =  a1*kenv*kvol

gaoutL = a1*(1-p7)+gaoutL
gaoutR = a1*p7+gaoutR

gainrev =	    a1*p5+gainrev

endin

/**************************************************************
Simple soundfile player (Edit)
**************************************************************/

instr 5111, 5112, 5113, 5114, 5115, 5116, 5117, 5118, 5119, 5120

if p16 != -1 then
    inum    =   frac(p16) * 10000
    itable2 =   int(p16)
    event_i "i", inum, 0, p3, p4, p5, p6, p7, itable2, p9, p10, p11, p12, p17, p18, p19, -1
endif

iTrackId = int(p1-5111)
SvolTrackName4 sprintf "trackVolume%0d", iTrackId
kvol chnget SvolTrackName4
kvol = kvol * 0.01
kvol port kvol, .01

a1      loscil  p6, p4, p8, 1

if (p11-1) != -1 then
acomp = a1
a1      bqrez   a1, p12, 6, p11-1
a1      balance     a1, acomp
endif

;if p4 < 1 then
;ialias = giAliasSr*p4
;else
;ialias = giAliasSr
;endif

;a1      tone   a1, ialias

kenv   adsr     p9, 0.05, .8, p10

a1  =   a1*kenv*kvol

gaoutL = a1*(1-p7)+gaoutL
gaoutR = a1*p7+gaoutR

gainrev =	    a1*p5+gainrev

endin



/********************************************************************
soundfile player for percussion - resonance notes
********************************************************************/
instr 5021

a1	 flooper2	1, p4, .25, .750, .2, p8

if (p11-1) != -1 then
acomp   =   a1
a1      bqrez   a1, p12, 6, p11-1
a1      balance     a1, acomp
endif

kenv    expseg  0.001, .003, .6, p3 - .003, 0.001
klocalenv   adsr     p8, 0.05, .8, p10

a1      =   a1*kenv*klocalenv

gaoutL = a1*(1-p7)+gaoutL
gaoutR = a1*p7+gaoutR

gainrev	=	    a1*p5+gainrev

endin

</CsInstruments>
<CsScore>
f1 0 8192 10 1
f2 0 8192 11 1 1

f4 0 32 -2 	250 2250 2980 	420 2050 2630 	590 1770 2580
		750 1450 2590	290 750 2300	360 770 2530			     520 900 2510    710 1230 2700   570 1560 2560			  0 0 0 0 0
f30 0 1024 10 1 0 .3 0 .1
f31 0 1024 10 1 .5 .3 .25 .1
f32 0 1024 10 1 0 .1 0 .3 .2 0 0 .1
f33 0 1024 10 1 0 0 0 .1 0 0 .2 .1 0 0 .1
f34 0 1024 10 1 .6 0 0 .4 .2 .1 0 0 .1
f35 0 1024 10 1 .5 .3 0 .1 0 0 0 .1 .1
f36 0 1024 10 1 0 .6 .4 .1 0 0 .2 .1 0 0 .1
f37 0 1024 10 1 0 0 0 .1 .2 .1 0 0 0 .1 0 0 .1
f38 0 1024 10 1 .4 .3 0 .1 .2 .1 .1 .1 0 0 0 0 .1 .05
f39 0 1024 10 1 0  .5 0 0 .3  0 0 .2 0 .1 0 0 0 0 .2 0 0 0 .05 0 0 0 0 .03 ; ADDITIVE SYNTHESIS WAVE
f41 0 8193 19 .5 .5 270 .5 ; SIGMOID FUNCTION
f42 0 8192 -20 2 1
f44 0 8192 5 1 8192 0.001 ; EXPONENTIAL FUNCTION
f45 0 512 7 0 500 0 2 1 10 1
f5150 0 32768 7 0 32768 0
f6001 0 131072 7 0 131072 0
f6002 0 131072 7 0 131072 0
f6003 0 131072 7 0 131072 0
f6004 0 131072 7 0 131072 0
i200 0 600000
</CsScore>
</CsoundSynthesizer>
