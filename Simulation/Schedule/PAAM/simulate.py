import numpy as np

import physics
import general



def SimSignal(channel, coorSet, gainSet, phaseSet, maskSet=None, gainBit=np.inf, phaseBit=np.inf):
    signal = physics.GetRxPower(channel, coorSet, gainSet, phaseSet, maskSet=maskSet,
        gainBit=gainBit, phaseBit=phaseBit)
    return signal

def SimSignalMax(channel, elemNum, maskSet=None):
    signal = physics.GetRxPowerMax(channel, elemNum, maskSet=maskSet)
    return signal

def SimInterf(channel, coorSetList, gainSetList, phaseSetList, maskSetList=None, gainBit=np.inf, phaseBit=np.inf):
    interf = 0
    for tokenIdx in range(len(coorSetList)):
        maskSet = maskSetList[tokenIdx] if maskSetList is not None else None
        interf += physics.GetRxPower(
            channel, coorSetList[tokenIdx], gainSetList[tokenIdx], phaseSetList[tokenIdx], maskSet=maskSet,
            gainBit=gainBit, phaseBit=phaseBit)
    return interf

def SimNoise(channel):
    snr = channel.snr
    noise = general.Gain2Power(-snr)
    return noise

def Simulate(channelList, coorSetList, gainSetList, phaseSetList, maskSetList=None, gainBit=np.inf, phaseBit=np.inf):
    signalList = []
    interfList = []
    noiseList = []
    for tokenIdx in range(len(channelList)):
        channel = channelList[tokenIdx]
        coorSet = coorSetList[tokenIdx]
        gainSet = gainSetList[tokenIdx]
        phaseSet = phaseSetList[tokenIdx]
        maskSet = maskSetList[tokenIdx] if maskSetList is not None else None

        signal = SimSignal(channel, coorSet, gainSet, phaseSet, maskSet=maskSet,
            gainBit=gainBit, phaseBit=phaseBit)
        signalList.append(signal)

        interf = SimInterf(channel, coorSetList, gainSetList, phaseSetList, maskSetList=maskSetList,
            gainBit=gainBit, phaseBit=phaseBit)
        interfList.append(interf-signal)

        noise = SimNoise(channel)
        noiseList.append(noise)
    return signalList, interfList, noiseList