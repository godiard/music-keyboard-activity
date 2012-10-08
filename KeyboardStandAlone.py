from gi.repository import Gdk

import common.Config as Config
from common.Generation.GenerationConstants import GenerationConstants
from common.Util.NoteDB  import Note
from common.Util.CSoundNote import CSoundNote
from common.Util.CSoundClient import new_csound_client
from common.Util import InstrumentDB

KEY_MAP_PIANO = Config.KEY_MAP_PIANO

#log = file('/home/olpc/log.tamtam','w')

class KeyboardStandAlone:
    def __init__( self, recordingFunction, adjustDurationFunction, getCurrentTick, getPlayState, loop ):
        self.instrumentDB = InstrumentDB.getRef()
        self.csnd = new_csound_client()
        self.recording = recordingFunction
        self.adjustDuration = adjustDurationFunction
        self.getPlayState = getPlayState
        self.key_dict = dict()
        self.onset_dict = dict()
        self.trackCount = 0
        self.instrument = 'flute'
        self.reverb = 0
        self.loop = loop
        self.loopSustain = False
        self.sustainedLoop = []

    def setInstrument( self , instrument ):
        self.instrument = instrument

    def setReverb(self , reverb):
        self.reverb = reverb

    def onKeyPress(self,widget,event, volume):
        key = event.hardware_keycode
        if key == 50 or key == 62: #Left Shift
            self.loopSustain = True

        # If the key is already in the dictionnary, exit function (to avoir key repeats)
        if self.key_dict.has_key(key):
            return

        if key in Config.LOOP_KEYS:
            if key in self.sustainedLoop:
                self.loop.stop(key)
                self.sustainedLoop.remove(key)
            elif self.loopSustain:
                self.loop.start(key, self.instrument, self.reverb)
                self.sustainedLoop.append(key)
            else:
                self.loop.start(key, self.instrument, self.reverb)
            return

        # Assign on which track the note will be created according to the number of keys pressed
        if self.trackCount >= 9:
            self.trackCount = 1
        track = self.trackCount
        self.trackCount += 1
        # If the pressed key is in the keymap
        if KEY_MAP_PIANO.has_key(key):
            def playkey(pitch,duration,instrument):
                # Create and play the note
                self.key_dict[key] = CSoundNote(onset = 0,
                                                pitch = pitch,
                                                amplitude = volume,
                                                pan = 0.5,
                                                duration = duration,
                                                trackId = track,
                                                instrumentId = instrument.instrumentId,
                                                reverbSend = self.reverb,
                                                tied = True,
                                                mode = 'mini')
                self.csnd.play(self.key_dict[key], 0.3)
                if self.getPlayState():
                    recOnset = int(self.csnd.loopGetTick())
                    self.onset_dict[key] = recOnset
                    self.recording( CSoundNote(
                                         onset = recOnset,
                                         pitch = pitch,
                                         amplitude = volume,
                                         pan = 0.5,
                                         duration = 100,
                                         trackId = 0,
                                         decay = .1,
                                         instrumentId = instrument.instrumentId,
                                         reverbSend = self.reverb,
                                         tied = False,
                                         mode = 'mini'))

            instrumentName = self.instrument
            #print >>log, 'instrumentName:', instrumentName
            pitch = KEY_MAP_PIANO[key]

            if self.instrumentDB.instNamed[instrumentName].kit != None:
                if pitch in GenerationConstants.DRUMPITCH:
                    pitch = GenerationConstants.DRUMPITCH[pitch]
                #print >>log, 'kit_element: ', Config.KIT_ELEMENT[pitch]
                playkey(36,100, self.instrumentDB.instNamed[instrumentName].kit[pitch])

            else:
                if event.state == Gdk.ModifierType.MOD1_MASK:
                    pitch += 5

                instrument = self.instrumentDB.instNamed[ instrumentName ]
                if instrument.csoundInstrumentId == Config.INST_PERC:    #Percussions resonance
                    playkey( pitch, 60, instrument)
                else:
                    playkey( pitch, -1, instrument)


    def onKeyRelease(self,widget,event):
        key = event.hardware_keycode
        if key == 50 or key == 62:
            self.loopSustain = False

        if key in Config.LOOP_KEYS:
            if key in self.sustainedLoop:
                return
            else:
                self.loop.stop(key)
            return

        if KEY_MAP_PIANO.has_key(key):
            csnote = self.key_dict[key]
            if self.instrumentDB.instId[ csnote.instrumentId ].csoundInstrumentId == Config.INST_TIED:
                csnote.duration = .5
                csnote.decay = 0.7
                #csnote.amplitude = 1
                csnote.tied = False
                csnote.mode = 'mini'
                self.csnd.play(csnote, 0.3)
            if self.getPlayState():
                self.adjustDuration(csnote.pitch, self.onset_dict[key])
            del self.key_dict[key]
        if self.getPlayState():
            if self.onset_dict.has_key(key):
                del self.onset_dict[key]

    def onButtonPress( self, widget, event ):
        pass
