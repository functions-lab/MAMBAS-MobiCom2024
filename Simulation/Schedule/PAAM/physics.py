import numpy as np

import general



def GetTxAmp(angle, coorSet, gainSet, phaseSet, respSet=None, gainBit=np.inf, phaseBit=np.inf):
    elemNum = len(coorSet)
    angleRad = general.Deg2Rad(np.array(angle))
    angleNorm = [ \
        np.sin(angleRad[1]), 
        -np.sin(angleRad[0]) * np.cos(angleRad[1]), 
        np.cos(angleRad[0]) * np.cos(angleRad[1])]
    ampOut_real = 0
    ampOut_imag = 0
    for elemIdx in range(elemNum):
        coor = np.array(coorSet[elemIdx])
        delay = 360*np.dot(coor, angleNorm)
        resp = respSet[elemIdx] if respSet is not None else 0

        if gainBit == np.inf:
            gainQuat = gainSet[elemIdx]
        else:
            amp, _ = general.Gain2Amp(gainSet[elemIdx])
            ampQuat = general.Quantize(amp, 0, 1, bit=gainBit)
            gainQuat = general.Amp2Gain(ampQuat)
        if phaseBit == np.inf:
            phaseQuat = phaseSet[elemIdx]
        else:
            phaseQuat = general.Quantize(phaseSet[elemIdx], -360, 360, bit=2*phaseBit)

        gain = gainQuat + resp
        phase = phaseQuat + delay
        ampTemp_real, ampTemp_imag = general.Gain2Amp(gain, phase)
        ampOut_real += ampTemp_real
        ampOut_imag += ampTemp_imag
    return ampOut_real, ampOut_imag

def GetTxPower(angle, coorSet, gainSet, phaseSet, respSet=None, gainBit=np.inf, phaseBit=np.inf):
    amp_real, amp_imag = GetTxAmp(angle, coorSet, gainSet, phaseSet, respSet,
        gainBit=gainBit, phaseBit=phaseBit)
    power = general.Amp2Power(amp_real, amp_imag)
    return power

def GetTxPowerMax(elemNum, respSet=None):
    if respSet is not None:
        ampTx = 0
        for resp in respSet:
            ampTx_real, _ = general.Gain2Amp(resp)
            ampTx += ampTx_real
        powerTx = ampTx ** 2
    else:
        powerTx = elemNum ** 2
    return powerTx

def GetChannelAmp(gain, phase):
    amp_real, amp_imag = general.Gain2Amp(gain, phase)
    return amp_real, amp_imag

def GetChannelPower(gain, phase):
    power = general.Gain2Power(gain)
    return power

def GetRxPower(channel, coorSet, gainSet, phaseSet, maskSet=None, mode='amp', gainBit=np.inf, phaseBit=np.inf):
    angleAxisX = channel.angleAxisX
    angleAxisY = channel.angleAxisY

    if mode == 'amp':
        ampRx_real = 0
        ampRx_imag = 0
        for angleIdxX in range(np.shape(angleAxisX)[0]):
            for angleIdxY in range(np.shape(angleAxisY)[0]):
                if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
                    continue
                angleTx = (angleAxisX[angleIdxX], angleAxisY[angleIdxY])
                respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet] if maskSet is not None else None
                ampTx_real, ampTx_imag = GetTxAmp(angleTx, coorSet, gainSet, phaseSet, respSet=respSet,
                    gainBit=gainBit, phaseBit=phaseBit)

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                phaseChannel = channel.phaseMap[angleIdxX, angleIdxY]
                ampChannel_real, ampChannel_imag = GetChannelAmp(gainChannel, phaseChannel)

                ampRx_real += ampTx_real*ampChannel_real - ampTx_imag*ampChannel_imag
                ampRx_imag += ampTx_real*ampChannel_imag + ampTx_imag*ampChannel_real
        powerRx = general.Amp2Power(ampRx_real, ampRx_imag)
    elif mode == 'power':
        powerRx = 0
        for angleIdxX in range(np.shape(angleAxisX)[0]):
            for angleIdxY in range(np.shape(angleAxisY)[0]):
                if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
                    continue
                angleTx = (angleAxisX[angleIdxX], angleAxisY[angleIdxY])
                respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet] if maskSet is not None else None
                powerTx = GetTxPower(angleTx, coorSet, gainSet, phaseSet, respSet=respSet)

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                phaseChannel = channel.phaseMap[angleIdxX, angleIdxY]
                powerChannel = GetChannelPower(gainChannel, phaseChannel)

                powerRx += powerTx * powerChannel
    else:
        print('Warning: Phase Coherence Mode NOT Found!')

    return powerRx

def GetRxPowerMax(channel, elemNum, maskSet=None, mode='amp'):
    angleAxisX = channel.angleAxisX
    angleAxisY = channel.angleAxisY

    if mode == 'amp':
        ampRx_real = 0
        for angleIdxX in range(np.shape(angleAxisX)[0]):
            for angleIdxY in range(np.shape(angleAxisY)[0]):
                if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
                    continue
                
                if maskSet is not None:
                    respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet]
                    ampTx = 0
                    for resp in respSet:
                        ampTx_real, _ = general.Gain2Amp(resp)
                        ampTx += ampTx_real
                else:
                    powerTx = elemNum

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                ampChannel, _ = GetChannelAmp(gainChannel, 0)

                ampRx_real += ampTx*ampChannel
        powerRx = general.Amp2Power(ampRx_real)
    elif mode == 'power':
        powerRx = 0
        for angleIdxX in range(np.shape(angleAxisX)[0]):
            for angleIdxY in range(np.shape(angleAxisY)[0]):
                if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
                    continue
                if maskSet is not None:
                    respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet]
                    ampTx = 0
                    for resp in respSet:
                        ampTx_real, _ = general.Gain2Amp(resp)
                        ampTx += ampTx_real
                    powerTx = ampTx ** 2
                else:
                    powerTx = elemNum ** 2

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                phaseChannel = channel.phaseMap[angleIdxX, angleIdxY]
                powerChannel = GetChannelPower(gainChannel, phaseChannel)

                powerRx += powerTx * powerChannel
    else:
        print('Warning: Phase Coherence Mode NOT Found!')

    return powerRx



# def GetRxAmp(channel, coorSet, gainSet, phaseSet):
#     angleAxisX = channel.angleAxisX
#     angleAxisY = channel.angleAxisY

#     ampRx_real = 0
#     ampRx_imag = 0
#     for angleIdxX in range(np.shape(angleAxisX)[0]):
#         for angleIdxY in range(np.shape(angleAxisY)[0]):
#             if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
#                 continue
#             angle = (angleAxisX[angleIdxX], angleAxisY[angleIdxY])
#             ampTx_real, ampTx_imag = GetTxAmp(angle, coorSet, gainSet, phaseSet)
#             ampChannel_real, ampChannel_imag = GetAmp(gain=channel.gainMap[angleIdxX, angleIdxY], phase=channel.phaseMap[angleIdxX, angleIdxY])
#             ampRx_real += ampTx_real*ampChannel_real - ampTx_imag*ampChannel_imag
#             ampRx_imag += ampTx_real*ampChannel_imag + ampTx_imag*ampChannel_real

#     return ampRx_real, ampRx_imag

# def GetRxPower(channel, coorSet, gainSet, phaseSet):
#     amp_real, amp_imag = GetRxAmp(channel, coorSet, gainSet, phaseSet)
#     power = general.Amp2Power(amp_real, amp_imag)
#     return power