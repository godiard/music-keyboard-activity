import os
import socket
import select
import sys
import threading
import time
import array
from math import sqrt

from common.Util.Clooper import *
import common.Config as Config

from common.Generation.GenerationConstants import GenerationConstants
from common.Util import NoteDB
import common.Util.InstrumentDB as InstrumentDB

loadedInstruments = []

_note_template = array.array('f', [0] * 19)


def _new_note_array():
    return _note_template.__copy__()

def _noteid(dbnote):
    return (dbnote.page << 16) + dbnote.id

_loop_default=0


class _CSoundClientPlugin:

    #array index constants for csound
    (INSTR_TRACK, \
    ONSET, \
    DURATION, \
    PITCH,
    REVERBSEND, \
    AMPLITUDE, \
    PAN, \
    INST_ID, \
    ATTACK, \
    DECAY, \
    FILTERTYPE, \
    FILTERCUTOFF, \
    INSTRUMENT2 ) = range(13)

    def __init__(self):
        sc_initialize( Config.PLUGIN_UNIVORC, Config.PLUGIN_DEBUG,
                Config.PLUGIN_VERBOSE, Config.PLUGIN_RATE)
        self.on = False
        #self.masterVolume = 100.0
        self.periods_per_buffer = 2
        global _loop_default
        _loop_default = self.loopCreate()
        self.instrumentDB = InstrumentDB.getRef()

        self.jamesSux = {} # temporyary dictionary of loopId: loopNumTicks, while I wait for james to implement it properly

    def __del__(self):
        self.connect(False)
        sc_destroy()

    def setChannel(self, name, val):
        sc_setChannel(name, val)

    def setMasterVolume(self, volume):
        sc_setChannel('masterVolume', volume)

    def setTrackVolume(self, volume, trackId):
        sc_setChannel('trackVolume' + str(trackId + 1), volume)

    def setTrackpadX(self, value):
        sc_setChannel('trackpadX', value)

    def setTrackpadY(self, value):
        sc_setChannel('trackpadY', value)

    def micRecording(self, table):
        sc_inputMessage(Config.CSOUND_MIC_RECORD % table)

    def load_mic_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        instrumentId = Config.INSTRUMENT_TABLE_OFFSET + self.instrumentDB.instNamed[inst].instrumentId
        sc_inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName))

    def load_synth_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        instrumentId = Config.INSTRUMENT_TABLE_OFFSET + self.instrumentDB.instNamed[inst].instrumentId
        sc_inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName))

    def load_ls_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        sc_inputMessage(Config.CSOUND_LOAD_LS_INSTRUMENT % fileName)

    def load_instruments(self):
        for instrumentSoundFile in self.instrumentDB.instNamed.keys():
            if instrumentSoundFile[0:3] == 'mic' or instrumentSoundFile[0:3] == 'lab' or self.instrumentDB.instNamed[instrumentSoundFile].category == 'mysounds':
                fileName = Config.DATA_DIR + '/' + instrumentSoundFile
            else:
                fileName = Config.SOUNDS_DIR + "/" + instrumentSoundFile
            instrumentId = Config.INSTRUMENT_TABLE_OFFSET + self.instrumentDB.instNamed[ instrumentSoundFile ].instrumentId
            sc_inputMessage( Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName) )

    def load_instrument(self, inst):
        if not inst in loadedInstruments:
            if inst[0:3] == 'mic' or inst[0:3] == 'lab' or self.instrumentDB.instNamed[inst].category == 'mysounds':
                if os.path.isfile(os.path.join(Config.DATA_DIR, inst)):
                    fileName = os.path.join(Config.DATA_DIR, inst)
                else:
                    fileName = os.path.join(Config.SOUNDS_DIR, 'armbone')
            else:
                fileName = os.path.join(Config.SOUNDS_DIR, inst)
            instrumentId = Config.INSTRUMENT_TABLE_OFFSET + self.instrumentDB.instNamed[ inst ].instrumentId
            sc_inputMessage( Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName) )
            loadedInstruments.append(inst)

    def load_drumkit(self, kit):
        if not kit in loadedInstruments:
            for i in self.instrumentDB.instNamed[kit].kit.values():
                fileName = Config.SOUNDS_DIR + "/" + i
                instrumentId = Config.INSTRUMENT_TABLE_OFFSET + self.instrumentDB.instNamed[ i ].instrumentId
                sc_inputMessage( Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName) )
                loadedInstruments.append(i)
            loadedInstruments.append(kit)

    def connect(self, init=True):
        def reconnect():
            if sc_start(self.periods_per_buffer) :
                if (Config.DEBUG > 0) : print 'ERROR connecting'
            else:
                self.on = True
        def disconnect():
            if sc_stop() :
                if (Config.DEBUG > 0) : print 'ERROR connecting'
            else:
                self.on = False

        if init and not self.on :
            reconnect()
        if not init and self.on :
            disconnect()

    def destroy(self):
        self.connect(False)
        sc_destroy()

    def inputMessage(self,msg):
        sc_inputMessage(msg)

    def getTick(self):
        return sc_getTickf()

    def adjustTick(self, amt):
        sc_adjustTick(amt)

    def setTempo(self,t):
        if (Config.DEBUG > 3) : print 'INFO: loop tempo: %f -> %f' % (t, 60.0 / (Config.TICKS_PER_BEAT * t))
        sc_setTickDuration(60.0 / (Config.TICKS_PER_BEAT * t))


    def loopCreate(self):
        return sc_loop_new()

    def loopDestroy(self, loopId):
        sc_loop_delete(loopId)
        try:
            del self.jamesSux[ loopId ]
        except:
            pass

    def loopClear(self):
        global _loop_default
        sc_loop_delete(_loop_default)
        _loop_default = sc_loop_new()
        try:
            del self.jamesSux[ loopId ]
        except:
            pass


    # this is function deletes an Event from a loop
    # TODO: rename this function
    def loopDelete(self, dbnote, loopId=_loop_default):
        sc_loop_delScoreEvent( loopId, _noteid(dbnote))

    def loopDelete1(self, page, id, loopId=_loop_default):
        sc_loop_delScoreEvent( loopId, (page << 16) + id)

    def loopStart(self, loopId=_loop_default):
        sc_loop_playing(loopId, 1)

    def loopPause(self, loopId=_loop_default):
        sc_loop_playing(loopId, 0)

    def loopSetTick(self,t, loopId=_loop_default):
        sc_loop_setTickf(loopId, t)

    def loopGetTick(self, loopId=_loop_default):
        return sc_loop_getTickf(loopId)

    def loopSetNumTicks(self,n, loopId=_loop_default):
        sc_loop_setNumTicks(loopId, n)
        self.jamesSux[loopId] = n

    def loopGetNumTicks( self, loopId = _loop_default ):
        return self.jamesSux[loopId]

    def loopSetTickDuration(self,d, loopId=_loop_default):
        sc_loop_setTickDuration(loopId, d)
        james

    def loopDeactivate(self, note = 'all', loopId=_loop_default):
        if note == 'all':
            sc_loop_deactivate_all(loopId)
        else:
            if (Config.DEBUG > 0) : print 'ERROR: deactivating a single note is not implemented'

    def loopUpdate(self, note, parameter, value,cmd, loopId=_loop_default):
        page = note.page
        track = note.track
        id = note.id
        if note.cs.mode == 'mini':
            instrument_id_offset = 0
        elif note.cs.mode == 'edit':
            if self.instrumentDB.instId[note.cs.instrumentId].kit != None:
                instrument_id_offset = 0
            else:
                instrument_id_offset = 100
        if (parameter == NoteDB.PARAMETER.ONSET):
            if (Config.DEBUG > 2): print 'INFO: updating onset', (page<<16)+id, value
            sc_loop_updateEvent( loopId, (page<<16)+id, 1, value, cmd)
        elif (parameter == NoteDB.PARAMETER.PITCH):
            if (Config.DEBUG > 2): print 'INFO: updating pitch', (page<<16)+id, value
            pitch = value
            if self.instrumentDB.instId[note.cs.instrumentId].kit != None:
                instrument = self.instrumentDB.instNamed[
                        self.instrumentDB.instId[note.cs.instrumentId].kit[pitch]]
                csoundInstId = instrument.csoundInstrumentId
                csoundTable  = Config.INSTRUMENT_TABLE_OFFSET + instrument.instrumentId
                if (Config.DEBUG > 2): print 'INFO: updating drum instrument (pitch)', (page<<16)+id, instrument.name, csoundInstId
                sc_loop_updateEvent( loopId, (page<<16)+id, 0, (csoundInstId + instrument_id_offset) + note.track * 0.01, -1 )
                sc_loop_updateEvent( loopId, (page<<16)+id, 7, csoundTable  , -1 )
                pitch = 1
            else:
                pitch = GenerationConstants.TRANSPOSE[ pitch - 24 ]
            sc_loop_updateEvent( loopId, (page<<16)+id, 3, pitch, cmd)
        elif (parameter == NoteDB.PARAMETER.AMPLITUDE):
            if (Config.DEBUG > 2): print 'INFO: updating amp', (page<<16)+id, value
            sc_loop_updateEvent( loopId, (page<<16)+id, 5, value, cmd)
        elif (parameter == NoteDB.PARAMETER.DURATION):
            if (Config.DEBUG > 2): print 'INFO: updating duration', (page<<16)+id, value
            sc_loop_updateEvent( loopId, (page<<16)+id, self.DURATION, value, cmd)
        elif (parameter == NoteDB.PARAMETER.INSTRUMENT):
            pitch = note.cs.pitch
            instrument = self.instrumentDB.instId[value]
            if instrument.kit != None:
                instrument = self.instrumentDB.instNamed[instrument.kit[pitch]]
            csoundInstId = instrument.csoundInstrumentId
            csoundTable  = Config.INSTRUMENT_TABLE_OFFSET + instrument.instrumentId
            loopStart = instrument.loopStart
            loopEnd = instrument.loopEnd
            crossDur = instrument.crossDur
            if (Config.DEBUG > 2): print 'INFO: updating instrument', (page<<16)+id, instrument.name, csoundInstId
            sc_loop_updateEvent( loopId, (page<<16)+id, 0, (csoundInstId + (track+1) + instrument_id_offset) + note.track * 0.01, cmd )
            sc_loop_updateEvent( loopId, (page<<16)+id, 7, csoundTable, -1 )
            sc_loop_updateEvent( loopId, (page<<16)+id, 12, loopStart, -1 )
            sc_loop_updateEvent( loopId, (page<<16)+id, 13, loopEnd, -1 )
            sc_loop_updateEvent( loopId, (page<<16)+id, 14, crossDur , -1 )
        elif (parameter == NoteDB.PARAMETER.PAN):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.PAN, value, cmd)
        elif (parameter == NoteDB.PARAMETER.REVERB):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.REVERBSEND, value, cmd)
        elif (parameter == NoteDB.PARAMETER.ATTACK):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.ATTACK, value, cmd)
        elif (parameter == NoteDB.PARAMETER.DECAY):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.DECAY, value, cmd)
        elif (parameter == NoteDB.PARAMETER.FILTERTYPE):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.FILTERTYPE, value, cmd)
        elif (parameter == NoteDB.PARAMETER.FILTERCUTOFF):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.FILTERCUTOFF, value, cmd)
        elif (parameter == NoteDB.PARAMETER.INSTRUMENT2):
            sc_loop_updateEvent( loopId, (page<<16)+id, self.INSTRUMENT2, value, cmd)
        else:
            if (Config.DEBUG > 0): print 'ERROR: loopUpdate(): unsupported parameter change'

    def loopPlay(self, dbnote, active, storage=_new_note_array(),
            loopId=_loop_default ):
        qid = (dbnote.page << 16) + dbnote.id
        sc_loop_addScoreEvent( loopId, qid, 1, active, 'i',
                self.csnote_to_array(dbnote.cs, storage))

    def play(self, csnote, secs_per_tick, storage=_new_note_array()):
        a = self.csnote_to_array(csnote, storage)
        a[self.DURATION] = a[self.DURATION] * secs_per_tick
        a[self.ATTACK] = max(a[self.ATTACK]*a[self.DURATION], 0.002)
        a[self.DECAY] = max(a[self.DECAY]*a[self.DURATION], 0.002)
        sc_scoreEvent('i', a)

    def csnote_to_array(self, csnote, storage):
        return self._csnote_to_array1(storage,
                csnote.onset,
                csnote.pitch,
                csnote.amplitude,
                csnote.pan,
                csnote.duration,
                csnote.trackId,
                csnote.attack,
                csnote.decay,
                csnote.reverbSend,
                csnote.filterType,
                csnote.filterCutoff,
                csnote.tied,
                csnote.instrumentId,
                csnote.mode,
                csnote.instrumentId2 )

    def _csnote_to_array1(self, storage, onset, pitch, amplitude, pan, duration,
            trackId, attack, decay, reverbSend, filterType, filterCutoff,
            tied, instrumentId, mode, instrumentId2 = -1):

        rval=storage
        instrument = self.instrumentDB.instId[instrumentId]

        if instrument.volatile != None:
            sound = os.path.join(Config.DATA_DIR, instrument.name)
            if os.path.isfile(sound):
                st_mtime = os.stat(sound).st_mtime
                if st_mtime != instrument.volatile:
                    instrument.volatile = st_mtime
                    loadedInstruments.remove(instrument.name)
                    self.load_instrument(instrument.name)
                    time.sleep(0.2)

        if instrument.kit != None:
            instrument = self.instrumentDB.instNamed[instrument.kit[pitch]]
            pitch = 1
            time_in_ticks = 0
        else:
            pitch = GenerationConstants.TRANSPOSE[ pitch - 24 ]
            time_in_ticks = 1

        instrument_id_offset = 0
        # condition for tied notes
        if instrument.csoundInstrumentId == Config.INST_TIED:
            if tied:
                if mode == 'mini':
                    duration = -1
                    instrument_id_offset = 0
                elif mode == 'edit':
                    instrument_id_offset = 0
                    if duration < 0:
                        duration = -1
            else:
                if mode == 'mini':
                    instrument_id_offset = 0
                elif mode == 'edit':
                    instrument_id_offset = 100

        if instrument.csoundInstrumentId == Config.INST_SIMP:
            if mode == 'mini':
                instrument_id_offset = 0
            elif mode == 'edit':
                if instrument.name[0:4] == 'drum':
                    instrument_id_offset = 0
                else:
                    instrument_id_offset = 100

        amplitude = amplitude / sqrt(pitch) * instrument.ampScale
        rval[0] = (instrument.csoundInstrumentId + \
                (trackId+1) + instrument_id_offset) + trackId * 0.01
        rval[1] = onset
        rval[2] = duration
        rval[3] = pitch
        rval[4] = reverbSend
        rval[5] = amplitude
        rval[6] = pan
        rval[7] = Config.INSTRUMENT_TABLE_OFFSET + instrument.instrumentId
        rval[8] = attack
        rval[9] = decay
        rval[10]= filterType
        rval[11]= filterCutoff
        rval[12]= float(instrument.loopStart)
        rval[13]= float(instrument.loopEnd)
        rval[14]= float(instrument.crossDur)

        if instrumentId2 != -1:
            instrument2 = self.instrumentDB.instId[instrumentId2]
            csInstrumentId2 = (instrument2.csoundInstrumentId + 100) * 0.0001
            rval[15] = Config.INSTRUMENT_TABLE_OFFSET + instrumentId2 + csInstrumentId2
            rval[16] = instrument2.loopStart
            rval[17] = instrument2.loopEnd
            rval[18] = instrument2.crossDur
        else:
            rval[15] = -1
            rval[16] = 0
            rval[17] = 0
            rval[18] = 0

        return rval

_Client = None

def new_csound_client():
    global _Client
    if _Client == None:
        _Client = _CSoundClientPlugin()
        _Client.connect(True)
        _Client.setMasterVolume(100.0)
        #_Client.load_instruments()
        time.sleep(0.2)
    return _Client
