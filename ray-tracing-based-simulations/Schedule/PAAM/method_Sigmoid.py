import casadi
import numpy as np
import matplotlib.pyplot as plt

import simulate
import general



def SigmoidSINR(sinr, snrMax, argDict={}):
    K = argDict['K'] if 'K' in argDict.keys() else 10.0
    B = argDict['B'] if 'B' in argDict.keys() else -0.0

    MAX = np.log(snrMax)
    input = sinr
    exp_x = np.exp(-K*B) * (input)**(-K/MAX)
    sig = 1/(1 + exp_x)
    return sig

def SigmoidSpeed(sinr, snrMax, argDict={}):
    K = argDict['K'] if 'K' in argDict.keys() else 10.0
    B = argDict['B'] if 'B' in argDict.keys() else -0.5

    MAX = np.log(1+snrMax)
    input = 1 + sinr
    exp_x = np.exp(-K*B) * (input)**(-K/MAX)
    sig = 1/(1 + exp_x)
    return sig
    
def OptimOptimal(signalList, interfList, noiseList, snrMaxList, method='Speed', argDict={}):
    radioNum = len(signalList)

    weightList = argDict['weight'] if 'weight' in argDict.keys() else np.ones(radioNum)
    optimal = 0
    for radioIdx in range(radioNum):
        signal = signalList[radioIdx]
        interf = interfList[radioIdx]
        noise = noiseList[radioIdx]
        snrMax = snrMaxList[radioIdx]

        if method == 'SINR':
            sig = SigmoidSINR(signal/(interf+noise), snrMax, argDict=argDict)
        else:
            sig = SigmoidSpeed(signal/(interf+noise), snrMax, argDict=argDict)
        optimal -= weightList[radioIdx] * sig
    
    return optimal

def OptimInit(elemNum):
    gainInit = np.zeros((elemNum))
    phaseInit = np.random.uniform(low=0, high=360, size=elemNum)
    return gainInit, phaseInit

def OptimRange(elemNum):
    gainRange = [-12*np.ones((elemNum)), np.zeros((elemNum))]
    phaseRange = [-np.inf*np.ones((elemNum)), np.inf*np.ones((elemNum))]
    return gainRange, phaseRange

def SigmoidCore(channelList, coorSetList, snrMaxList, maskSetList=None, method='Speed', argDict={}):
    elemNum = sum([len(coorSet) for coorSet in coorSetList])
    gainParam = casadi.MX.sym('A', elemNum)
    phaseParam = casadi.MX.sym('phase', elemNum)
    gainInit, phaseInit = OptimInit(elemNum)
    gainRange, phaseRange = OptimRange(elemNum)

    gainSetList = []
    phaseSetList = []
    startIdx = 0
    endIdx = 0
    for radioIdx in range(len(channelList)):
        coorSet = coorSetList[radioIdx]
        startIdx = endIdx
        endIdx += len(coorSet)
        gainSetList.append(gainParam[startIdx: endIdx])
        phaseSetList.append(phaseParam[startIdx: endIdx])
    signalList, interfList, noiseList = simulate.Simulate(channelList, coorSetList, gainSetList, phaseSetList, maskSetList=maskSetList)

    optimal = OptimOptimal(signalList, interfList, noiseList, snrMaxList, method=method, argDict=argDict)

    input = {
        'x': casadi.vcat((gainParam, phaseParam)), 
        'f': optimal}
    ipopt_opt = {
        'print_time': False,
        'ipopt.print_level': 0, 
        'ipopt.max_iter': 1000}
    solver = casadi.nlpsol('solver', 'ipopt', input, ipopt_opt)
    output = solver(
        x0=np.concatenate((gainInit, phaseInit)),
        lbx=np.concatenate((gainRange[0], phaseRange[0])),
        ubx=np.concatenate((gainRange[1], phaseRange[1])))

    gainOut = np.array(output['x'][: elemNum]).squeeze(1)
    phaseOut = np.array(output['x'][elemNum:]).squeeze(1) % 360
    return gainOut, phaseOut



# Sigmoid(x) = 1 / (1 + exp(-x))
# SINR:
# x = K * (10*log10(SINR)/10*log10(MAX)) + B
# => Sigmoid(SINR) = 1 / (1 + exp(-B) * SINR^(K/ln(MAX)))
# Speed:
# x = K * (log2(1+SINR)/log2(1+MAX)) + B
# => Sigmoid(SINR) = 1 / (1 + exp(-B) * (1+SINR)^K/ln(1+MAX))
# where MAX is the maximum SINR in Watt
def Sigmoid(channelList, coorSetList, maskSetList=None, method='Speed', argDict={}, fileName=None):
    snrMaxList = []
    for radioIdx in range(len(channelList)):
        channel = channelList[radioIdx]
        coorSet = coorSetList[radioIdx]
        maskSet = maskSetList[radioIdx]

        signal = simulate.SimSignalMax(channel, len(coorSet), maskSet=maskSet)
        noise = simulate.SimNoise(channel)
        snrMax = signal/noise
        snrMaxList.append(snrMax)
    
    if fileName is not None:
        fig, ax = plt.subplots()
        snrMax = general.Power2Gain(snrMaxList[0])
        sinrList = list(np.arange(-snrMax, +snrMax, 0.1))
        if method == 'SINR':
            xList = [snr/snrMax for snr in sinrList]
            yList = [SigmoidSINR(general.Gain2Power(sinr), snrMax, argDict=argDict) for sinr in sinrList]
        else:
            xList = [np.log2(1 + general.Gain2Power(sinr))/np.log2(1+general.Gain2Power(snrMax)) for sinr in sinrList]
            yList = [SigmoidSpeed(general.Gain2Power(sinr), snrMax, argDict=argDict) for sinr in sinrList]
        ax.plot(xList, yList)
        fig.savefig(fileName)
        plt.close(fig)

    gainOut, phaseOut = SigmoidCore(channelList, coorSetList, snrMaxList, maskSetList=maskSetList, 
        method=method, argDict=argDict)

    return gainOut, phaseOut