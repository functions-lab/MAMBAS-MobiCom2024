import importlib
import math
import numpy as np
import casadi



def Gain2Power(gain):
    power = 10**(gain/10)
    return power

def Power2Gain(power):
    if power == 0:
        gain = -np.inf
    elif power < 0:
        print('Warning: Power is Negative!')
        gain = -np.inf
    else:
        gain = 10*math.log10(power)
    return gain

def Gain2Amp(gain, phase=0):
    amp = 10**(gain/20)
    phaseRad = Deg2Rad(phase)
    amp_real = amp * casadi.cos(phaseRad)
    amp_imag = amp * casadi.sin(phaseRad)
    return amp_real, amp_imag

def Amp2Gain(real, imag=0):
    gain = 10*math.log10(real**2+imag**2+1e-10)
    return gain

def Amp2Phase(real, imag=0):
    phaseRad = np.arctan2(imag, real)
    phase = Rad2Deg(phaseRad)
    return phase

def Amp2Power(real, imag=0):
    power = real**2 + imag**2
    return power

def Deg2Rad(deg):
    rad = deg/360*2*math.pi
    return rad

def Rad2Deg(rad):
    deg = rad/2/math.pi*360
    return deg

def Quantize(valueIn, valueMin, valueMax, bit):
    if bit == np.inf:
        valueOut = valueIn
    else:
        valueAxis = np.linspace(valueMin, valueMax, num=bit+1)
        valueIdx = np.argmin(np.abs(valueIn - valueAxis))
        valueOut = valueAxis[valueIdx]
    return valueOut