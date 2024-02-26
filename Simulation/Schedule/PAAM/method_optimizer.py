import casadi
import numpy as np

import simulate



def OptimOptimal(signalList, interfList, noiseList, method, argDict):
    radioNum = len(signalList)
    if method == 'SINR':
        sinrList = []
        for radioIdx in range(radioNum):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            noise = noiseList[radioIdx]
            sinrList.append(casadi.log(signal/(interf+noise)))
        optimal = -sum(sinrList)
    elif method == 'SIR':
        sirList = []
        for radioIdx in range(radioNum):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            sirList.append(casadi.log(signal/(interf+1e-10)))
        optimal = -sum(sirList)
    elif method in ['Speed', 'Speed-Limit']:
        if 'weight' in argDict.keys():
            weightList = argDict['weight']
        else:
            weightList = [1 for _ in range(radioNum)]
        optimal = 0
        for radioIdx in range(radioNum):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            noise = noiseList[radioIdx]
            optimal += - weightList[radioIdx] * casadi.log(1+signal/(interf+noise))/casadi.log(2)
    elif method == 'Speed-LASSO':
        decay = argDict['arg'] if 'arg' in argDict else 1
        speedList = []
        for radioIdx in range(len(signalList)):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            noise = noiseList[radioIdx]
            speedList.append(casadi.log(1+signal/(interf+noise))/casadi.log(2))
        optimal_1 = -sum(speedList)

        optimal_2 = 0
        if len(signalList)>1:
            for speed_1 in speedList:
                for speed_2 in speedList:
                    optimal_2 += decay * casadi.fabs(speed_1 - speed_2)/radioNum/(radioNum-1)
        
        optimal = optimal_1 + optimal_2
    elif method in ['Gain', 'Single']:
        optimal = 0
        for signal in signalList:
            optimal += -casadi.log(signal)
    else:
        print('Warning: Method NOT Found!')
    
    return optimal

def OptimLimit(signalList, interfList, noiseList, method, argDict):
    if method in ['SINR', 'SIR', 'Speed', 'Speed-LASSO', 'Single']:
        limit = []
        limitRange = [[], []]
    elif method == 'Speed-Limit':
        ratio = argDict['arg'] if 'arg' in argDict else 0.5
        
        speedList = []
        for radioIdx in range(len(signalList)):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            noise = noiseList[radioIdx]
            speedList.append(casadi.log(1+signal/(interf+noise))/casadi.log(2))

        limit = []
        limitRange = [[], []]
        if len(signalList)>1:
            for speed_1 in speedList:
                for speed_2 in speedList:
                    limit = casadi.vcat((limit, speed_1/speed_2))
                    limitRange[0].append(ratio)
                    limitRange[1].append(1/ratio)
        limitRange[0] = np.array(limitRange[0])
        limitRange[1] = np.array(limitRange[1])
    elif method == 'Gain':
        suppress = argDict['arg'] if 'arg' in argDict else -30
        limit = []
        limitRange = [[], []]
        for interf in interfList:
            limit = casadi.vcat((limit, 10*casadi.log(interf+1e-20)/casadi.log(10)))
            limitRange[0].append(-np.inf)
            limitRange[1].append(suppress)
        limitRange[0] = np.array(limitRange[0])
        limitRange[1] = np.array(limitRange[1])
    else:
        print('Warning: Method NOT Found!')

    return limit, limitRange

def OptimInit(elemNum, gainList, phaseList, argDict):
    scratch = argDict['scratch'] if 'scratch' in argDict.keys() else False

    gainInit = np.zeros((elemNum))
    phaseInit = np.random.uniform(low=0, high=360, size=elemNum)
    if not scratch:
        for elemIdx in range(elemNum):
            if(gainList is not None)and(not np.isnan(gainList[elemIdx])):
                gainInit[elemIdx] = gainList[elemIdx]
            if(phaseList is not None)and(not np.isnan(phaseList[elemIdx])):
                phaseInit[elemIdx] = phaseList[elemIdx]
    return gainInit, phaseInit

def OptimRange(elemNum):
    gainRange = [-12*np.ones((elemNum)), np.zeros((elemNum))]
    phaseRange = [-np.inf*np.ones((elemNum)), np.inf*np.ones((elemNum))]
    return gainRange, phaseRange

def Optimizer(channelList, coorSetList, maskSetList=None, gainIn=None, phaseIn=None, method='SINR', argDict={}):
    elemNum = sum([len(coorSet) for coorSet in coorSetList])
    gainParam = casadi.MX.sym('A', elemNum)
    phaseParam = casadi.MX.sym('phase', elemNum)
    gainInit, phaseInit = OptimInit(elemNum, gainIn, phaseIn, argDict)
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

    optimal = OptimOptimal(signalList, interfList, noiseList, method, argDict)
    limit, limitRange = OptimLimit(signalList, interfList, noiseList, method, argDict)

    input = {
        'x': casadi.vcat((gainParam, phaseParam)), 
        'f': optimal,
        'g': limit}
    ipopt_opt = {
        'print_time': False,
        'ipopt.print_level': 0, 
        'ipopt.max_iter': 1000}
    solver = casadi.nlpsol('solver', 'ipopt', input, ipopt_opt)
    output = solver(
        x0=np.concatenate((gainInit, phaseInit)),
        lbx=np.concatenate((gainRange[0], phaseRange[0])),
        ubx=np.concatenate((gainRange[1], phaseRange[1])),
        lbg=limitRange[0],
        ubg=limitRange[1])

    gainOut = np.array(output['x'][: elemNum]).squeeze(1)
    phaseOut = np.array(output['x'][elemNum:]).squeeze(1) % 360
    return gainOut, phaseOut