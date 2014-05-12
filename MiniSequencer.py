from gi.repository import GObject
import time
import ttcommon.Config as Config
from ttcommon.Util.CSoundNote import CSoundNote
from ttcommon.Util.CSoundClient import new_csound_client
from ttcommon.Util.NoteDB import Note
from ttcommon.Util.NoteDB import PARAMETER

class MiniSequencer:
    def __init__( self, recordButtonState, recordOverSensitivity ):
        self.notesList = []
        self.sequencer = []
        self.pitchs = []
        self.beat = 4
        self.volume = 0.5
        self.tempo = Config.PLAYER_TEMPO
        self.checkOk = 0
        self.tick = 0
        self.id = 1000
        self.csnd = new_csound_client()
        self.startLooking = 0
        self.recordState = 0
        self.startPoint = 0
        self.recordButtonState = recordButtonState
        self.recordOverSensitivity = recordOverSensitivity
        self.playbackTimeout = None
        self.playState = 0

    def setTempo( self, tempo ):
        self.tempo = tempo
        GObject.source_remove( self.playBackTimeout )
        self.playState = 0

    def handleRecordButton( self, widget, data=None ):
        if not self.startLooking:
            if widget.get_active() == True and not self.recordState:
                self.button = 1
                self.recordOverSensitivity( True )
                self.beats = [i*4 for i in range(self.beat)]
                self.upBeats = [i+2 for i in self.beats]
                self.realTick = [i for i in range(self.beat*4)]
                self.clearSequencer()
                self.startLooking = 1
                self.startPlayback()

    def handleOverButton( self, widget, data=None ):
        if not self.startLooking:
            if widget.get_active() == True and not self.recordState:
                self.button = 2
                self.startLooking = 1
                self.startPlayback()

    def clearSequencer( self, widget=None ):
        for n in self.notesList:
            self.csnd.loopDelete(n)
            self.notesList = []

    def getPlayState( self ):
        return self.playState

    def startPlayback( self ):
        if not self.playState:
            self.playbackTimeout = GObject.timeout_add(int(60000/self.tempo/12),
                    self.handleClock)
            self.handleClock()
            self.playState = 1

    def stopPlayback( self ):
        if self.playbackTimeout != None:
            GObject.source_remove( self.playbackTimeout )
            self.playbackTimeout = None
            self.playState = 0

    def recording( self, note ):
        if self.startLooking:
            self.sequencer = []
            self.pitchs = []
            self.recordState = 1
            self.startLooking = 0
            self.recordButtonState(self.button, True)
            self.startPoint = int(self.csnd.loopGetTick())
            if self.startPoint == 0:
                self.startPoint = self.beat * Config.TICKS_PER_BEAT - 1
        if self.recordState:
            self.pitchs.append( note.pitch )
            self.sequencer.append( note )

    def quantize( self, onset ):
        if ( onset % 3 ) == 0:
            return onset
        elif ( onset % 3 ) == 1:
            return ( onset // 3 ) * 3
        elif ( onset % 3 ) == 2:
            return ( ( onset // 3 ) + 1 ) * 3

    def adjustDuration( self, pitch, onset ):
        if pitch in self.pitchs:
            offset = int(self.csnd.loopGetTick())
            for note in self.sequencer:
                if note.pitch == pitch and note.onset == onset:
                    if offset > note.onset:
                        note.duration = ( offset - note.onset ) + 4
                    else:
                        note.duration = ( (offset+(self.beat*Config.TICKS_PER_BEAT)) - note.onset ) + 4
                    note.onset = self.quantize( note.onset )
                    n = Note(0, note.trackId, self.id, note)
                    self.notesList.append(n)
                    self.id = self.id + 1
                    self.csnd.loopPlay(n,1)                    #add as active

            self.pitchs.remove( pitch )

    def adjustSequencerVolume(self, volume):
        self.volume = volume
        for n in self.notesList:
            self.csnd.loopUpdate(n, PARAMETER.AMPLITUDE, n.cs.amplitude*self.volume, 1)

    def handleClock( self ):
        currentTick = int(self.csnd.loopGetTick())
        t = currentTick / 3
        if self.tick != t:
            self.tick = t
            if self.startLooking:
                if self.tick in self.beats:
                    self.recordButtonState(self.button, True)
                if self.tick in self.upBeats:
                    self.recordButtonState(self.button, False)

        if self.recordState:
            if currentTick < self.startPoint:
                self.checkOk = 1
            if currentTick >= self.startPoint and self.checkOk:
                self.checkOk = 0
                self.recordState = 0
                self.recordButtonState(self.button, False)

        return True
