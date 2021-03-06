import os
from math import sqrt
import logging

import ctcsound
import ttcommon.Config as Config

from ttcommon.Generation.GenerationConstants import GenerationConstants
from ttcommon.Util import NoteDB
import ttcommon.Util.InstrumentDB as InstrumentDB

loadedInstruments = []


def _new_note_array():
    return [0] * 19


def _noteid(dbnote):
    return (dbnote.page << 16) + dbnote.id

_loop_default = 0


class _CSoundClientPlugin:

    # array index constants for csound
    (INSTR_TRACK,
     ONSET,
     DURATION,
     PITCH,
     REVERBSEND,
     AMPLITUDE,
     PAN,
     INST_ID,
     ATTACK,
     DECAY,
     FILTERTYPE,
     FILTERCUTOFF,
     INSTRUMENT2) = list(range(13))

    def __init__(self):
        ctcsound.csoundInitialize(ctcsound.CSOUNDINIT_NO_SIGNAL_HANDLER)
        self._csnd = ctcsound.Csound()
        self._csnd.compileCsd(Config.PLUGIN_UNIVORC)
        self._csnd.setDebug(False)
        self._csnd.start()
        self._perfThread = ctcsound.CsoundPerformanceThread(self._csnd.csound())
        self._perfThread.play()

        # TODO
        # sc_initialize(Config.PLUGIN_UNIVORC, Config.PLUGIN_DEBUG,
        #        Config.PLUGIN_VERBOSE, Config.PLUGIN_RATE)
        self.on = False
        self.setMasterVolume(100.0)
        self.periods_per_buffer = 2
        global _loop_default
        # TODO
        # _loop_default = self.loopCreate()
        self.instrumentDB = InstrumentDB.getRef()

        # temporyary dictionary of loopId: loopNumTicks,
        # while I wait for james to implement it properly
        self.jamesSux = {}

    def stop(self):
        self._perfThread.stop()
        self._csnd.stop()

    def setChannel(self, name, val):
        self._csnd.setControlChannel(name, val)

    def setMasterVolume(self, volume):
        self._csnd.setControlChannel('masterVolume', volume)

    def setTrackVolume(self, volume, trackId):
        self._csnd.setControlChannel('trackVolume' + str(trackId + 1), volume)

    def setTrackpadX(self, value):
        self._csnd.setControlChannel('trackpadX', value)

    def setTrackpadY(self, value):
        self._csnd.setControlChannel('trackpadY', value)

    def micRecording(self, table):
        self._csnd.inputMessage(Config.CSOUND_MIC_RECORD % table)

    def load_mic_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        instrumentId = Config.INSTRUMENT_TABLE_OFFSET + \
            self.instrumentDB.instNamed[inst].instrumentId
        self._csnd.inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (
            instrumentId, fileName))

    def load_synth_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        instrumentId = Config.INSTRUMENT_TABLE_OFFSET + \
            self.instrumentDB.instNamed[inst].instrumentId
        self._csnd.inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (
            instrumentId, fileName))

    def load_ls_instrument(self, inst):
        fileName = Config.DATA_DIR + '/' + inst
        self._csnd.inputMessage(Config.CSOUND_LOAD_LS_INSTRUMENT % fileName)

    def load_instruments(self):
        for instrumentSoundFile in list(self.instrumentDB.instNamed.keys()):
            if instrumentSoundFile[0:3] == 'mic' or \
                    instrumentSoundFile[0:3] == 'lab' or \
                    self.instrumentDB.instNamed[instrumentSoundFile
                                                ].category == 'mysounds':
                fileName = Config.DATA_DIR + '/' + instrumentSoundFile
            else:
                fileName = Config.SOUNDS_DIR + "/" + instrumentSoundFile
            instrumentId = Config.INSTRUMENT_TABLE_OFFSET + \
                self.instrumentDB.instNamed[instrumentSoundFile].instrumentId
            self._csnd.inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (
                instrumentId, fileName))

    def load_instrument(self, inst):
        if inst not in loadedInstruments:
            if inst[0:3] == 'mic' or inst[0:3] == 'lab' or \
                    self.instrumentDB.instNamed[inst].category == 'mysounds':
                if os.path.isfile(os.path.join(Config.DATA_DIR, inst)):
                    fileName = os.path.join(Config.DATA_DIR, inst)
                else:
                    fileName = os.path.join(Config.SOUNDS_DIR, 'armbone')
            else:
                fileName = os.path.join(Config.SOUNDS_DIR, inst)
            instrumentId = Config.INSTRUMENT_TABLE_OFFSET + \
                self.instrumentDB.instNamed[inst].instrumentId
            message = Config.CSOUND_LOAD_INSTRUMENT % (instrumentId, fileName)
            logging.error('CSoundClient load_instrument msg %s', message)
            self._csnd.inputMessage(message)
            loadedInstruments.append(inst)

    def load_drumkit(self, kit):
        if kit not in loadedInstruments:
            for i in list(self.instrumentDB.instNamed[kit].kit.values()):
                fileName = Config.SOUNDS_DIR + "/" + i
                instrumentId = Config.INSTRUMENT_TABLE_OFFSET + \
                    self.instrumentDB.instNamed[i].instrumentId
                self._csnd.inputMessage(Config.CSOUND_LOAD_INSTRUMENT % (
                    instrumentId, fileName))
                loadedInstruments.append(i)
            loadedInstruments.append(kit)

    def inputMessage(self, msg):
        self._csnd.inputMessage(msg)

    def getTick(self):
        return sc_getTickf()

    def adjustTick(self, amt):
        sc_adjustTick(amt)

    def setTempo(self, t):
        tempo = 60.0 / (Config.TICKS_PER_BEAT * t)
        if (Config.DEBUG > 3):
            print('INFO: loop tempo: %f -> %f' % (t, tempo))
        # TODO
        # sc_setTickDuration(tempo)

    def loopCreate(self):
        return sc_loop_new()

    def loopDestroy(self, loopId):
        sc_loop_delete(loopId)
        try:
            del self.jamesSux[loopId]
        except:
            pass

    def loopClear(self):
        global _loop_default
        # TODO
        """
        sc_loop_delete(_loop_default)
        _loop_default = sc_loop_new()
        try:
            del self.jamesSux[ loopId ]
        except:
            pass
        """

    # this is function deletes an Event from a loop
    # TODO: rename this function
    def loopDelete(self, dbnote, loopId=_loop_default):
        sc_loop_delScoreEvent(loopId, _noteid(dbnote))

    def loopDelete1(self, page, id, loopId=_loop_default):
        sc_loop_delScoreEvent(loopId, (page << 16) + id)

    def loopStart(self, loopId=_loop_default):
        sc_loop_playing(loopId, 1)

    def loopPause(self, loopId=_loop_default):
        sc_loop_playing(loopId, 0)

    def loopSetTick(self, t, loopId=_loop_default):
        sc_loop_setTickf(loopId, t)

    def loopGetTick(self, loopId=_loop_default):
        return sc_loop_getTickf(loopId)

    def loopSetNumTicks(self, n, loopId=_loop_default):
        # TODO
        """
        sc_loop_setNumTicks(loopId, n)
        self.jamesSux[loopId] = n
        """
        pass

    def loopGetNumTicks(self, loopId=_loop_default):
        return self.jamesSux[loopId]

    def loopSetTickDuration(self, d, loopId=_loop_default):
        # TODO
        """
        sc_loop_setTickDuration(loopId, d)
        james
        """
        pass

    def loopDeactivate(self, note='all', loopId=_loop_default):
        if note == 'all':
            sc_loop_deactivate_all(loopId)
        else:
            if (Config.DEBUG > 0):
                print('ERROR: deactivating a single note is not implemented')

    def loopUpdate(self, note, parameter, value, cmd, loopId=_loop_default):
        page = note.page
        track = note.track
        id = note.id
        if note.cs.mode == 'mini':
            instrument_id_offset = 0
        elif note.cs.mode == 'edit':
            if self.instrumentDB.instId[note.cs.instrumentId].kit is not None:
                instrument_id_offset = 0
            else:
                instrument_id_offset = 100
        if (parameter == NoteDB.PARAMETER.ONSET):
            if (Config.DEBUG > 2):
                print('INFO: updating onset', (page << 16) + id, value)
            sc_loop_updateEvent(loopId, (page << 16) + id, 1, value, cmd)
        elif (parameter == NoteDB.PARAMETER.PITCH):
            if (Config.DEBUG > 2):
                print('INFO: updating pitch', (page << 16) + id, value)
            pitch = value
            if self.instrumentDB.instId[note.cs.instrumentId].kit is not None:
                instrument = self.instrumentDB.instNamed[
                    self.instrumentDB.instId[note.cs.instrumentId].kit[pitch]]
                csoundInstId = instrument.csoundInstrumentId
                csoundTable = Config.INSTRUMENT_TABLE_OFFSET + \
                    instrument.instrumentId
                if (Config.DEBUG > 2):
                    print('INFO: updating drum instrument (pitch)', \
                        (page << 16)+id, instrument.name, csoundInstId)
                sc_loop_updateEvent(
                    loopId, (page << 16) + id, 0,
                    (csoundInstId + instrument_id_offset) + note.track * 0.01,
                    -1)
                sc_loop_updateEvent(loopId, (page << 16) + id, 7, csoundTable,
                                    -1)
                pitch = 1
            else:
                pitch = GenerationConstants.TRANSPOSE[pitch - 24]
            sc_loop_updateEvent(loopId, (page << 16)+id, 3, pitch, cmd)
        elif (parameter == NoteDB.PARAMETER.AMPLITUDE):
            if (Config.DEBUG > 2):
                print('INFO: updating amp', (page << 16) + id, value)
            sc_loop_updateEvent(loopId, (page << 16) + id, 5, value, cmd)
        elif (parameter == NoteDB.PARAMETER.DURATION):
            if (Config.DEBUG > 2):
                print('INFO: updating duration', (page << 16) + id, value)
            sc_loop_updateEvent(loopId, (page << 16) + id, self.DURATION,
                                value, cmd)
        elif (parameter == NoteDB.PARAMETER.INSTRUMENT):
            pitch = note.cs.pitch
            instrument = self.instrumentDB.instId[value]
            if instrument.kit is not None:
                instrument = self.instrumentDB.instNamed[instrument.kit[pitch]]
            csoundInstId = instrument.csoundInstrumentId
            csoundTable = Config.INSTRUMENT_TABLE_OFFSET + \
                instrument.instrumentId
            loopStart = instrument.loopStart
            loopEnd = instrument.loopEnd
            crossDur = instrument.crossDur
            if (Config.DEBUG > 2):
                print('INFO: updating instrument', (page << 16) + id, \
                    instrument.name, csoundInstId)
            sc_loop_updateEvent(loopId, (page << 16) + id, 0, (csoundInstId +
                                (track+1) + instrument_id_offset) +
                                note.track * 0.01, cmd)
            sc_loop_updateEvent(loopId, (page << 16) + id, 7, csoundTable, -1)
            sc_loop_updateEvent(loopId, (page << 16) + id, 12, loopStart, -1)
            sc_loop_updateEvent(loopId, (page << 16) + id, 13, loopEnd, -1)
            sc_loop_updateEvent(loopId, (page << 16) + id, 14, crossDur, -1)
        elif (parameter == NoteDB.PARAMETER.PAN):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.PAN, value,
                                cmd)
        elif (parameter == NoteDB.PARAMETER.REVERB):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.REVERBSEND,
                                value, cmd)
        elif (parameter == NoteDB.PARAMETER.ATTACK):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.ATTACK, value,
                                cmd)
        elif (parameter == NoteDB.PARAMETER.DECAY):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.DECAY, value,
                                cmd)
        elif (parameter == NoteDB.PARAMETER.FILTERTYPE):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.FILTERTYPE,
                                value, cmd)
        elif (parameter == NoteDB.PARAMETER.FILTERCUTOFF):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.FILTERCUTOFF,
                                value, cmd)
        elif (parameter == NoteDB.PARAMETER.INSTRUMENT2):
            sc_loop_updateEvent(loopId, (page << 16) + id, self.INSTRUMENT2,
                                value, cmd)
        else:
            if (Config.DEBUG > 0):
                print('ERROR: loopUpdate(): unsupported parameter change')

    def loopPlay(self, dbnote, active, storage=_new_note_array(),
                 loopId=_loop_default):
        # TODO
        """
        qid = (dbnote.page << 16) + dbnote.id
        sc_loop_addScoreEvent(loopId, qid, 1, active, 'i',
                self.csnote_to_array(dbnote.cs, storage))
        """

    def play(self, csnote, secs_per_tick, storage=_new_note_array()):
        a = self.csnote_to_array(csnote, storage)
        a[self.DURATION] = a[self.DURATION] * secs_per_tick
        a[self.ATTACK] = max(a[self.ATTACK]*a[self.DURATION], 0.002)
        a[self.DECAY] = max(a[self.DECAY]*a[self.DURATION], 0.002)

        message = 'i ' + " ".join(map(str, a))
        self._perfThread.inputMessage(message)

    def csnote_to_array(self, csnote, storage):
        return self._csnote_to_array1(
            storage,
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
            csnote.instrumentId2)

    def _csnote_to_array1(
            self, storage, onset, pitch, amplitude, pan, duration,
            trackId, attack, decay, reverbSend, filterType, filterCutoff,
            tied, instrumentId, mode, instrumentId2=-1):

        rval = storage
        instrument = self.instrumentDB.instId[instrumentId]

        if instrument.volatile is not None:
            sound = os.path.join(Config.DATA_DIR, instrument.name)
            if os.path.isfile(sound):
                st_mtime = os.stat(sound).st_mtime
                if st_mtime != instrument.volatile:
                    instrument.volatile = st_mtime
                    loadedInstruments.remove(instrument.name)
                    self.load_instrument(instrument.name)

        if instrument.kit is not None:
            instrument = self.instrumentDB.instNamed[instrument.kit[pitch]]
            pitch = 1
            time_in_ticks = 0
        else:
            pitch = GenerationConstants.TRANSPOSE[pitch - 24]
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

        elif instrument.csoundInstrumentId == Config.INST_SIMP:
            if mode == 'mini':
                instrument_id_offset = 0
            elif mode == 'edit':
                if instrument.name[0:4] == 'drum':
                    instrument_id_offset = 0
                else:
                    instrument_id_offset = 100

        amplitude = amplitude / sqrt(pitch) * instrument.ampScale
        rval[0] = (instrument.csoundInstrumentId +
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
        rval[10] = filterType
        rval[11] = filterCutoff
        rval[12] = float(instrument.loopStart)
        rval[13] = float(instrument.loopEnd)
        rval[14] = float(instrument.crossDur)

        if instrumentId2 != -1:
            instrument2 = self.instrumentDB.instId[instrumentId2]
            csInstrumentId2 = (instrument2.csoundInstrumentId + 100) * 0.0001
            rval[15] = Config.INSTRUMENT_TABLE_OFFSET + instrumentId2 + \
                csInstrumentId2
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
    if _Client is None:
        _Client = _CSoundClientPlugin()
        # _Client.load_instruments()
    return _Client
