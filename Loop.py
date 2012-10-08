import common.Config as Config
import random
import lps
from  common.Generation.Drunk import *
from common.Util.CSoundNote import CSoundNote
from common.Util.CSoundClient import new_csound_client
from common.Util.NoteDB import Note
from common.Util.NoteDB import PARAMETER
from common.Generation.GenerationConstants import GenerationConstants
from common.Util import InstrumentDB

class Loop:
    def __init__( self, beat, volume ):
        self.instrumentDB = InstrumentDB.getRef()
        self.notesDict = {}
        self.notesList = []
        self.beat = beat
        self.volume = volume
        self.id = 4000
        self.csnd = new_csound_client()

    def stop( self, key ):
        if (Config.DEBUG > 3): print 'stop loop at key: ' + str(key)
        for n in self.notesDict[key]:
            self.csnd.loopDelete(n)
        del self.notesDict[key]
        if (Config.DEBUG > 3): print self.notesDict

    def start(self, key, instrument, reverb):
        if self.notesDict.has_key(key):
            return
        self.notesList = []
        for i in lps.LOOPS[key][self.beat-2]:
            note = self.createCsNote(i, instrument, reverb)
            n = Note(0, note.trackId, self.id, note)
            self.notesList.append(n)
            self.id = self.id + 1
            self.csnd.loopPlay(n,1)                    #add as active
        if (Config.DEBUG > 3): print 'play loop at key: ' + str(key)
        self.notesDict[key] = self.notesList
        if (Config.DEBUG > 3): print self.notesDict

    def adjustLoopVolume(self, volume):
        self.volume = volume
        for k in self.notesDict.keys():
            for n in self.notesDict[k]:
                self.csnd.loopUpdate(n, PARAMETER.AMPLITUDE, n.cs.amplitude*self.volume, 1)

    def createCsNote(self, i, instrument, reverb):
        onset = i[0]
        pitch = i[1]
        gain = i[2]*self.volume
        duration = i[3]
        if self.instrumentDB.instNamed[instrument].kit != None:
            if GenerationConstants.DRUMPITCH.has_key(pitch):
                pitch = GenerationConstants.DRUMPITCH[pitch]
            instrument = self.instrumentDB.instNamed[ instrument ].kit[pitch].name
            pitch = 36
        return CSoundNote( onset = onset,
                    pitch = pitch,
                    amplitude = gain,
                    pan = 0.5,
                    duration = duration,
                    trackId = 0,
                    instrumentId = self.instrumentDB.instNamed[instrument].instrumentId,
                    reverbSend = reverb,
                    tied = False,
                    mode = 'mini')


################ precompose all loops and write a dictionary #################

    def precompose(self, maxbeat):
        def makeGainSequence(onsetList):
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

        def makeDurationSequence(onsetList, barLength):
            durationSequence = []
            append = durationSequence.append
            if len( onsetList ) > 1:
                for i in range(len(onsetList) - 1):
                    append((onsetList[i+1] - onsetList[i]))
                append(( barLength - onsetList[-1]))
            elif len( onsetList ) == 1:
                append( ( barLength - onsetList[0] ))
            return durationSequence

        def makePitchSequence(length, pitchRegularity, step, table_pitch, pitchMethod):
            pitchSequence = []
            append = pitchSequence.append
            numberOfPitch = int( ( 1 - (regularity*.8) )  * 10 + 1 )
            step = -(8 - (int(step * 8)))
            max = len(table_pitch)-1
            nextValue = pitchMethod.getNextValue
            tonique = GenerationConstants.DEFAULT_TONIQUE
            for i in range(numberOfPitch):
                append((table_pitch[nextValue(step, max)]) + tonique)
            restOfNotes = range( length - numberOfPitch )
            for i in restOfNotes:
                position = i % numberOfPitch
                append( pitchSequence[ position ] )
            return pitchSequence


        def makeRythmSequence(barLength, density, regularity ):
            rythmSequence = [0, ]
            self.count = 0
            lastOnsetTime = 0
            onsetLen = len(GenerationConstants.LOOP_TABLE_ONSET_VALUES)

            onsetValue  = int( ( 1 -  density ) * onsetLen )
            onsetDeviation = int( ( 1 - regularity ) * 20 )
            currentOnsetValue = onsetValue + ( random.randint( 0, onsetDeviation ) - ( onsetDeviation / 2 ) )
            if currentOnsetValue < 0:
                currentOnsetValue = 0
            elif currentOnsetValue > onsetLen:
                currentOnsetValue = onsetLen
            else:
                currentOnsetValue = currentOnsetValue

            onsetDelta = GenerationConstants.LOOP_TABLE_ONSET_VALUES[ currentOnsetValue ]
            listLen = range( int( barLength / Config.TICKS_PER_BEAT * 8 ) )
            randInt = random.randint
            for i in listLen:
                if self.count == 0:
                    currentOnsetValue = onsetValue + ( randInt( 0, onsetDeviation ) - ( onsetDeviation / 2 ) )
                    if currentOnsetValue < 0:
                        currentOnsetValue = 0
                    elif currentOnsetValue > onsetLen:
                        currentOnsetValue = onsetLen
                    else:
                        currentOnsetValue = currentOnsetValue
                    onsetDelta = GenerationConstants.LOOP_TABLE_ONSET_VALUES[ currentOnsetValue ]

                if onsetDelta == GenerationConstants.DOUBLE_TICK_DUR:
                    if self.count < (GenerationConstants.DOUBLE_HOW_MANY - 1):
                        self.count += 1
                    else:
                        self.count = 0
                    onsetTime = onsetDelta + lastOnsetTime
                    lastOnsetTime = onsetTime
                    if onsetTime < barLength:
                        rythmSequence.append(onsetTime)
                        continue
                    else:
                        break

                onsetTime = onsetDelta + lastOnsetTime
                lastOnsetTime = onsetTime
                if onsetTime < barLength:
                    rythmSequence.append(onsetTime)
                else:
                    break
            return rythmSequence

############ begin generate #####################
        #file = open(Config.TAM_TAM_ROOT + '/miniTamTam/lps.py', 'w')
        #file.write('LOOPS = {\n')

        counter = 0
        table_pitch = [-12, -10, -12, -7, -5, -4, -2, 0, 2, 0, 5, 7, 8, 10, 12]
        table_density = [1., .92, .84, .76, .68, .6, .52, .46, .4, .46, .52, .6, .68, .76, .84, .95]
        table_regularity = [1., .96, .9, .84, .78, .72, .66, .6, .54, .48, .42, .36, .3, .24, .18, .1]
        table_pitchRegularity = [1., .96, .9, .84, .78, .72, .66, .6, .54, .48, .42, .36, .3, .24, .18, .1]
        table_step = [2, 4, 3, 2, 4, 6, 5, 4, 6, 8, 7, 6, 8, 9, 8, 10]
        table_pitchMethod = [0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3]

        names = ['', '', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        numKeys = 5 #len(Config.LOOP_KEYS)
        for key in range(numKeys):
            #file.write(str(Config.LOOP_KEYS[key]) + ': [')
            for beat in range(2, maxbeat+1):
                density = table_density[key*3]
                regularity = table_regularity[key*3]
                pitchRegularity = table_pitchRegularity[key*3]
                step = table_step[key*3]
                pattern = table_pitchMethod[key*3]
                if pattern == 0:
                    pitchMethod = Drunk( 5, 10 )
                elif pattern == 1:
                    pitchMethod = DroneAndJump( 5, 10 )
                elif pattern == 2:
                    pitchMethod = Repeter( 5, 10 )
                elif pattern == 3:
                    pitchMethod = Loopseg( 5, 10 )

                barLength = Config.TICKS_PER_BEAT * beat
                loopList = []

                rythmSequence = makeRythmSequence(barLength, density, regularity)
                pitchSequence = makePitchSequence(len(rythmSequence), pitchRegularity, step, table_pitch, pitchMethod )
                gainSequence = makeGainSequence(rythmSequence)
                durationSequence = makeDurationSequence(rythmSequence, barLength)

                for k in range(len(rythmSequence)):
                    loopList.append([rythmSequence[k], pitchSequence[k], gainSequence[k], durationSequence[k]])


                f = open(Config.INSTANCE_DIR + '/loops/loop' + names[beat] + '_' + str(counter) + '.ttl', 'w')
                print "open file"
                f.write('page_add 1 ' + str(beat) + ' 0 [1, 1, 1, 1, 1]\n')
                print "write page_add"
                noteIdCount = 0
                for l in loopList:
                    f.write('note_add %s 1 0 %s %s %s 0.5 %s 0 1 0.005 0.098 0.1 0 1000 0 edit\n' % (str(counter + noteIdCount + 1000), str(l[0]), str(l[1]), str(l[2]), str(l[3])))
                noteIdCount += 1
                f.close()
            counter += 1

                #if beat == maxbeat and key == (numKeys-1):
                    #file.write(str(loopList) + ']\n')
                #elif beat != maxbeat:
                    #file.write(str(loopList) + ',\n')
                #else:
                    #file.write(str(loopList) + '],\n')
        #file.write('}')
        #file.close()
