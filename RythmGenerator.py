import random

import ttcommon.Util.InstrumentDB as InstrumentDB
import ttcommon.Config as Config
from ttcommon.Util.CSoundNote import CSoundNote
from ttcommon.Generation.GenerationConstants import GenerationConstants
from GenRythm import GenRythm

instrumentDB = InstrumentDB.getRef()

def generator( instrument, nbeats, density, regularity, reverbSend ):

    makeRythm = GenRythm()

    noteDuration = GenerationConstants.DOUBLE_TICK_DUR / 2
    trackId = 0
    pan = 0.5
    attack = 0.005
    decay = 0.095
    filterType = 0
    filterCutoff = 1000
    tied = False
    mode = 'mini'

    def makePitchSequence(length, drumPitch):
        pitchSequence = []
        append = pitchSequence.append
        list = range(length)
        max = len(drumPitch) - 1
        for i in list:
            append(drumPitch[ random.randint( 0, max ) ] )
        return pitchSequence

    def makeGainSequence( onsetList ):
        gainSequence = []
        append = gainSequence.append
        for onset in onsetList:
            if onset == 0:
                gain = random.uniform(GenerationConstants.GAIN_MID_MAX_BOUNDARY, GenerationConstants.GAIN_MAX_BOUNDARY)
            elif ( onset % Config.TICKS_PER_BEAT) == 0:
                gain = random.uniform(GenerationConstants.GAIN_MID_MIN_BOUNDARY, GenerationConstants.GAIN_MID_MAX_BOUNDARY)
            else:
                gain = random.uniform(GenerationConstants.GAIN_MIN_BOUNDARY, GenerationConstants.GAIN_MID_MIN_BOUNDARY)
            append(gain)
        return gainSequence

    def pageGenerate( regularity, drumPitch ):
        barLength = Config.TICKS_PER_BEAT * nbeats

        #print 'pageGenerate drumPitch[0] ', drumPitch[0]
        currentInstrument = instrumentDB.instNamed[ instrument ].kit[ drumPitch[0] ]

        rythmSequence = makeRythm.drumRythmSequence(currentInstrument, nbeats, density, regularity)
        pitchSequence = makePitchSequence(len(rythmSequence), drumPitch )
        gainSequence = makeGainSequence(rythmSequence)

        trackNotes = []
        list = range(len(rythmSequence))
        for i in list:
            trackNotes.append( CSoundNote( rythmSequence[i], pitchSequence[i], gainSequence[i],
                                           pan, noteDuration, trackId,
                                           instrumentDB.instNamed[instrument].instrumentId, attack,
                                           decay, reverbSend, filterType, filterCutoff, tied, mode))
        return trackNotes

##################################################################################
    #  begin generate()
    if regularity > 0.75:
        streamOfPitch = GenerationConstants.DRUM_COMPLEXITY1
    elif regularity > 0.5:
        streamOfPitch = GenerationConstants.DRUM_COMPLEXITY2
    elif regularity > 0.25:
        streamOfPitch = GenerationConstants.DRUM_COMPLEXITY3
    else:
        streamOfPitch = GenerationConstants.DRUM_COMPLEXITY4

    trackNotes = []
    for drumPitch in streamOfPitch:
        trackNotes.append(pageGenerate( regularity, drumPitch ))
    return trackNotes
