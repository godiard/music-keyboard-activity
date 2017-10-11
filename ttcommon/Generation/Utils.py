import random
import time
import math

#----------------------------------------------------------------------
# TODO: replace magic numbers with constants
# http://en.wikipedia.org/wiki/Magic_number_(programming)
#----------------------------------------------------------------------

def prob(x):
    sum1 = 0
    sum2 = 0
    
    for i in x:
        sum1 = sum1 + i

    val = sum1 * random.randint(0, 32767) / 32768

    for i in range(len(x)):
        sum2 = sum2 + x[i]
        if x[i]:
            if sum2 >= val:
                return i
                break	

def prob2(x):
    sum1 = 0
    sum2 = 0

    for i in x:
        sum1 = sum1 + i[1]

    val = sum1 * random.randint(0, 32767) / 32768
    
    for i in x:
        sum2 = sum2 + i[1]
        if i[1]:
            if sum2 >= val:
                return i[0]
                break

def scale(val, mini=0., maxi=1., length=100):
    slope = []

    up = 1.-val 
    if up <= 0.5:
        low_val = (pow(1.-(up*2.),4.)*(-50.5)+0.5)
    else:
        low_val = up

    if val <= 0.5:
        high_val = (pow(1.-(val * 2.),4.)*(-50.5)+0.5)
    else:
        high_val = val

    step = (maxi - mini) * (1. / length)

    calc = (1. / length) * (high_val - low_val)
    append = slope.append
    for i in range(length + 1):
        temp = i * calc + low_val
        if temp < 0:
            temp = 0
        elif temp > 1:
            temp = 1
        else:
            temp = temp	

        append(((step * i) + mini, int(temp * 100)))

    return slope	

def midtotrans(x):
    return pow(1.059463, x - 36)
