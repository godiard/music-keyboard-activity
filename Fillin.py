from gi.repository import GObject

from RythmGenerator import generator
from ttcommon.Util.CSoundClient import new_csound_client
from ttcommon.Util.NoteDB import Note
import ttcommon.Config as Config


class Fillin:
    def __init__(self, nbeats, tempo, instrument, reverb, volume):
        self.notesList = []
        self.barCount = 0
        self.gate = 0
        self.nbeats = nbeats
        self.tempo = tempo
        self.instrument = instrument
        self.reverb = reverb
        self.volume = volume
        self.onsets = []
        self.pitchs = []
        self.playBackTimeout = None
        self.csnd = new_csound_client()

    def reset(self):
        self.barCount = 0
        self.gate = 0

    def setInstrument(self, instrument):
        self.instrument = instrument

    def setBeats(self, nbeats):
        if self.playBackTimeout is not None:
            GObject.source_remove(self.playBackTimeout)

        self.nbeats = nbeats
        self.clear()
        self.reset()

    def setTempo(self, tempo):
        self.tempo = tempo
        if self.playBackTimeout is not None:
            GObject.source_remove(self.playBackTimeout)
            self.play()

    def setReverb(self, reverb):
        self.reverb = reverb

    def setVolume(self, volume):
        self.volume = volume

    def play(self):
        if self.playBackTimeout is None:
            self.playbackTimeout = GObject.timeout_add(
                int(60000 / self.tempo / 8), self.handleClock)
            self.handleClock()

    def stop(self):
        if self.playBackTimeout is not None:
            GObject.source_remove(self.playBackTimeout)
            self.clear()

    def clear(self):
        if self.notesList:
            for n in self.notesList:
                self.csnd.loopDelete(n)
                self.notesList = []

    def handleClock(self):
        tick = self.csnd.loopGetTick()
        if tick < (Config.TICKS_PER_BEAT / 2 + 1):
            if self.gate == 0:
                self.gate = 1
                self.barCount += 1
                self.barCount %= 4
                if self.barCount == 1:
                    self.clear()

        if tick > ((Config.TICKS_PER_BEAT * self.nbeats) - (
                   Config.TICKS_PER_BEAT / 2) - 1):
            if self.gate == 1:
                self.gate = 0
                if self.barCount == 3:
                    self.regenerate()
        return True

    def unavailable(self, onsets, pitchs):
        self.onsets = onsets
        self.pitchs = pitchs

    def regenerate(self):
        def flatten(ll):
            rval = []
            for l in ll:
                rval += l
            return rval
        i = 500
        self.notesList = []
        for x in flatten(generator(self.instrument, self.nbeats, 0.4, 0.1,
                                   self.reverb)):
            if x.onset not in self.onsets or x.pitch not in self.pitchs:
                x.amplitude = x.amplitude * self.volume
                n = Note(0, x.trackId, i, x)
                self.notesList.append(n)
                i += 1
                self.csnd.loopPlay(n, 1)                    # add as active
