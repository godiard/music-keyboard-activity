import random
import ttcommon.Config as Config
import ttcommon.Util.InstrumentDB as InstrumentDB

from ttcommon.Generation.GenerationConstants import GenerationConstants
from ttcommon.Generation.Utils import *


class GenRythm:
    def __init__(self):
        self.instrumentDB = InstrumentDB.getRef()

    def drumRythmSequence(self, instrumentName, nbeats, density, regularity):
        rythmSequence = []
        binSelection = []
        downBeats = []
        upBeats = []
        beats = []
        countDown = 0
        onsetTime = None

        instrument = self.instrumentDB.instNamed[instrumentName]
        if instrument.instrumentRegister == Config.PUNCH:
            registerDensity = 0.5
            downBeatRecurence = 4
            downBeats = [x for x in GenerationConstants.DRUM_PUNCH_ACCENTS[
                nbeats]]
            for downBeat in downBeats:
                upBeats.append(downBeat + Config.TICKS_PER_BEAT / 2)

        if instrument.instrumentRegister == Config.LOW:
            registerDensity = 1
            downBeatRecurence = 4
            downBeats = [x for x in GenerationConstants.DRUM_LOW_ACCENTS[
                nbeats]]
            for downBeat in downBeats:
                upBeats.append(downBeat + Config.TICKS_PER_BEAT / 2)

        if instrument.instrumentRegister == Config.MID:
            registerDensity = .75
            downBeatRecurence = 1
            downBeats = [x for x in GenerationConstants.DRUM_MID_ACCENTS[
                nbeats]]
            for downBeat in downBeats:
                upBeats.append(downBeat + Config.TICKS_PER_BEAT / 4)

        if instrument.instrumentRegister == Config.HIGH:
            registerDensity = 1.5
            downBeatRecurence = 1
            downBeats = [x for x in GenerationConstants.DRUM_HIGH_ACCENTS[
                nbeats]]
            for downBeat in downBeats:
                upBeats.append(downBeat + Config.TICKS_PER_BEAT / 4)

        realDensity = density * registerDensity
        if realDensity > 1.:
            realDensity = 1.

        list = range(int(realDensity * len(downBeats)))
        for i in list:
            if random.random() < (regularity * downBeatRecurence) and \
                    binSelection.count(1) < len(downBeats):
                binSelection.append(1)
            else:
                if binSelection.count(0) < len(downBeats):
                    binSelection.append(0)
                else:
                    binSelection.append(1)

        countDown = binSelection.count(1)

        length = len(downBeats) - 1
        for i in range(countDown):
            ran1 = random.randint(0, length)
            ran2 = random.randint(0, length)
            randMin = min(ran1, ran2)
            onsetTime = downBeats.pop(randMin)
            rythmSequence.append(onsetTime)
            length -= 1

        length = len(upBeats) - 1
        for i in range(len(binSelection) - countDown):
            ran1 = random.randint(0, length)
            ran2 = random.randint(0, length)
            randMin = min(ran1, ran2)
            onsetTime = upBeats.pop(randMin)
            rythmSequence.append(onsetTime)
            length -= 1

        rythmSequence.sort()
        return rythmSequence
