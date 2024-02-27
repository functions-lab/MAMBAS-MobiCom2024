import casadi
import numpy as np

import simulate
import general



# We adapt the zero forcing (ZF) in our scenario by minimizing the overall interference.
def ZeroForce(channelList, coorSetList):
    elemNum = sum([len(coorSet) for coorSet in coorSetList])
    gainParam = casadi.MX.sym('A', elemNum)
    phaseParam = casadi.MX.sym('phase', elemNum)
    gainInit = np.zeros((elemNum))
    phaseInit = np.random.uniform(low=0, high=360, size=elemNum)
    gainRange = [0*np.ones((elemNum)), np.zeros((elemNum))]
    phaseRange = [-np.inf*np.ones((elemNum)), np.inf*np.ones((elemNum))]

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
    _, interfList, _ = simulate.Simulate(channelList, coorSetList, gainSetList, phaseSetList)

    optimal = 0
    for interf in interfList:
        optimal += general.Gain2Power(interf)

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