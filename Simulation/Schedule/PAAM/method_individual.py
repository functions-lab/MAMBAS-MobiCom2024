import casadi
import numpy as np

import physics
import general



def GetTxPower(direc, coorSet, gainSet, phaseSet, maskSet=None, maskMax=0, angleAxisX=None, angleAxisY=None):
    if maskSet is None or angleAxisX is None or angleAxisY is None:
        respSet = None
    else:
        angleIdxX = np.argmin(np.abs(angleAxisX-direc[0]))
        angleIdxY = np.argmin(np.abs(angleAxisY-direc[1]))
        respSet = [mask[angleIdxX, angleIdxY]-maskMax for mask in maskSet]

    power = physics.GetTxPower(direc, coorSet, gainSet=gainSet, phaseSet=phaseSet, respSet=respSet)
    return power

def GetTxPowerMax(direc, coorSet, maskSet=None, maskMax=0, angleAxisX=None, angleAxisY=None):
    if maskSet is None or angleAxisX is None or angleAxisY is None:
        respSet = None
    else:
        angleIdxX = np.argmin(np.abs(angleAxisX-direc[0]))
        angleIdxY = np.argmin(np.abs(angleAxisY-direc[1]))
        respSet = [mask[angleIdxX, angleIdxY]-maskMax for mask in maskSet]

    power = physics.GetTxPowerMax(len(coorSet), respSet=respSet)
    return power

def IndividualCore(coorSet, direc, delta=100, nullList=[],
    maskSet=None, angleAxisX=None, angleAxisY=None):

    elemNum = len(coorSet)
    # The usage of maskMax is for the precision issue in Casadi
    maskMax = max([np.max(mask) for mask in maskSet]) if elemNum>0 else 0

    gainParam = casadi.MX.sym('A', elemNum)
    phaseParam = casadi.MX.sym('phase', elemNum)
    gainInit = np.zeros((elemNum))
    phaseInit = np.random.uniform(low=0, high=360, size=elemNum)
    gainRange = [-12*np.ones((elemNum)), np.zeros((elemNum))]
    phaseRange = [-np.inf*np.ones((elemNum)), np.inf*np.ones((elemNum))]

    signal = GetTxPower(direc=direc, coorSet=coorSet, gainSet=gainParam, phaseSet=phaseParam, 
        maskSet=maskSet, maskMax=maskMax, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
    optimal = -signal

    signalMax = GetTxPowerMax(direc=direc, coorSet=coorSet,
        maskSet=maskSet, maskMax=maskMax, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
    limit = []
    limitRange = [[], []]
    for radioIdx in range(len(nullList)):
        interf = GetTxPower(nullList[radioIdx], coorSet=coorSet, gainSet=gainParam, phaseSet=phaseParam, 
            maskSet=maskSet, maskMax=maskMax, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
        limit = casadi.vcat((limit, interf))
        limitRange[0].append(-np.inf)
        limitRange[1].append(general.Gain2Power(-delta)*signalMax)
        
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



# We cannot adopt the multi-path gain because
# a) Too little SINR gain from the multi-path
# b) Large extra interference to other UEs
def Individual(pathList, coorSetList, delta=100, maskSetList=None, angleAxisX=None, angleAxisY=None):
    gainList = []
    phaseList = []
    for radioIdx in range(len(pathList)):
        coorSet = coorSetList[radioIdx]
        maskSet = maskSetList[radioIdx]
        
        nullList = []
        for idx in range(len(pathList)):
            if(idx!=radioIdx)and(len(coorSetList[idx])>0):
                nullList.append(pathList[idx]['direc'])

        gainSet, phaseSet = IndividualCore(coorSet=coorSet, direc=pathList[radioIdx]['direc'], 
            delta=delta, nullList=nullList,
            maskSet=maskSet, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
        
        gainList += list(gainSet)
        phaseList += list(phaseSet)

    return gainList, phaseList