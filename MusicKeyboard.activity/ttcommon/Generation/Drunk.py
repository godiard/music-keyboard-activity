# Random:
# Randomly choose, within a certain range, a new next value
# arg 1: maxStepSize (negative value not allowed stepSize == 0)
# arg 2: maximum value allowed

import random

class Drunk:
    def __init__( self, minValue, maxValue, trackLength=None ):
        self.minValue = min(minValue, maxValue)
        self.maxValue = max(minValue, maxValue)
        self.lastValue = random.randint( self.minValue, self.maxValue )


    def getNextValue( self, maxStepSize, maxValue ):
        if self.lastValue < 0 or self.lastValue > maxValue:
            return random.randint( self.minValue, maxValue )

        direction = self.getDirection( maxValue )
        stepSize = self.getStepSize( direction, abs(maxStepSize), maxValue )
        
        if maxStepSize < 0:
            minStepSize = 1
        else:
            minStepSize = 0
  
        self.lastValue += direction * random.randint( minStepSize, stepSize )

        if self.lastValue < self.minValue:
            self.lastValue = self.minValue
        elif self.lastValue > maxValue:  #instead of 14...
            self.lastValue = maxValue
        else:
            self.lastValue = self.lastValue

        return self.lastValue

    def getDirection( self, maxValue ):
        if self.lastValue == 0:
            return 1
        elif self.lastValue == maxValue:
            return -1
        else:
            return random.choice( [ 1, -1 ] )

    def getStepSize( self, direction, maxStepSize, maxValue, ):
        if direction == -1:
            return min( maxStepSize, self.lastValue )
        else:
            return min( maxStepSize, maxValue - self.lastValue )

class DroneAndJump( Drunk ):
    def __init__( self, minValue, maxValue, trackLength=None ):
        Drunk.__init__( self, minValue, maxValue, trackLength=None )
        self.minValue = min(minValue, maxValue)
        self.maxValue = max(minValue, maxValue)        
        self.beforeLastValue = random.randint( self.minValue, self.maxValue ) #self.minValue
        self.lastValue = self.beforeLastValue + 1

    def getNextValue( self, maxStepSize, maxValue ):
        if self.beforeLastValue != self.lastValue:
            self.lastValue = self.beforeLastValue
            return self.beforeLastValue

        self.beforeLastValue = self.lastValue
        self.lastValue = Drunk.getNextValue( self, abs(maxStepSize), maxValue )
        return self.lastValue

    def getStepSize( self, direction, maxStepSize, maxValue ):
        if random.randint( 0, 100 ) < 42:
            return Drunk.getStepSize( self, direction, maxStepSize, maxValue )
        else:
            return Drunk.getStepSize( self, direction, 0, maxValue )

class Repeter( Drunk ):
    def __init__( self, minValue, maxValue, trackLength=None ):
        Drunk.__init__( self, minValue, maxValue, trackLength=None)
        self.minValue = min(minValue, maxValue)
        self.maxValue = max(minValue, maxValue)
        self.lastValue = random.randint( self.minValue, self.maxValue)

    def getNextValue( self, maxStepSize, maxValue ):
        self.lastValue = Drunk.getNextValue( self, abs(maxStepSize), maxValue )
        return self.lastValue

    def getStepSize( self, direction, maxStepSize, maxValue ):
        if random.randint( 0, 100 ) < 35:
            return Drunk.getStepSize( self, direction, maxStepSize, maxValue )
        else:
            return Drunk.getStepSize( self, direction, 0, maxValue )    

class Loopseg( Drunk ):
    def __init__( self, minValue, maxValue, trackLength=None ):
        Drunk.__init__( self, minValue, maxValue, trackLength=None )
        self.recordedValues = []
        self.recordState = 2
        self.recordPlayback = 0
        self.loopPlayback = 1
        self.recordLength = random.randint( 3, 6 ) 
        self.recordLoopTime = random.randint( 1, 4 )

    def getNextValue( self, maxStepSize, maxValue ):
        if self.recordState == 2:
            self.lastValue = Drunk.getNextValue( self, maxStepSize, maxValue )
            self.recordState = random.choice([2, 2, 2, 1])

        if len(self.recordedValues) != self.recordLength and self.recordState == 1:
            self.lastValue = Drunk.getNextValue( self, maxStepSize, maxValue )
            self.recordedValues.append( self.lastValue )
        elif self.recordState == 1 or self.recordState == 0:
            self.recordState = 0
            if self.recordPlayback < self.recordLength:
                self.loopAround()
            else:
                if self.loopPlayback < self.recordLoopTime:
                    self.recordPlayback = 0
                    self.loopPlayback += 1
                    self.loopAround()
                else:
                    self.recordedValues = []
                    self.recordState = 2
                    self.recordPlayback = 0
                    self.loopPlayback = 1
                    self.recordLength = random.randint( 3, 6 ) 
                    self.recordLoopTime = random.randint( 1, 4 )
                    self.lastValue = Drunk.getNextValue( self, maxStepSize, maxValue )
                    self.recordedValues = [self.lastValue]
        return self.lastValue  

    def loopAround( self ):
        self.lastValue = self.recordedValues[self.recordPlayback]
        self.recordPlayback += 1
        
class Line:
    def __init__(self, minValue, maxValue, trackLength=20):
        maxVal = max(minValue, maxValue)
        if maxVal == minValue:
            self.reverse = True
            minVal = maxValue
            self.lastValue = maxVal
        else:
            self.reverse = False
            minVal = minValue
            self.lastValue = minVal
            
        scale = float(maxVal - minVal)
        if self.reverse:
            self.inc = -scale/trackLength
        else:
            self.inc = scale/trackLength  
                
    def getNextValue(self, rand, maxValue):
        self.val = self.lastValue + int(random.randint(0, rand)*random.choice([-0.5,0.5]))
        if self.val < 0:
            self.val = 0
        elif self.val > maxValue:
            self.val = maxValue
        else:
            self.val = self.val
        self.lastValue = self.val+self.inc    
        return self.val
   
