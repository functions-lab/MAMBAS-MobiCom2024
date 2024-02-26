import casadi
import numpy as np

import method_conjugate
import physics



def NullifyCore(coorSet, phaseSetIn, direcList=[], widthList=[], delta=15, rel=1):
    if len(direcList)==0 or len(widthList)==0:
        return phaseSetIn
    gainSet = np.zeros(np.shape(phaseSetIn))

    phaseParam = casadi.MX.sym('phase', len(coorSet))
    phaseInit = np.random.uniform(low=0, high=360, size=len(coorSet))
    phaseRange = [phaseSetIn-delta, phaseSetIn+delta]

    optimal = -np.inf
    for nullIdx in range(len(direcList)):
        null = direcList[nullIdx][0]
        width = widthList[nullIdx][0]
        for angle in np.arange(null-width/2, null+width/2+rel, rel):
            interf = physics.GetTxPower((angle, 0), coorSet=coorSet, gainSet=gainSet, phaseSet=phaseParam)
            optimal = casadi.fmax(optimal, interf)
    input = {
        "x": phaseParam, 
        "f": optimal}
    ipopt_opt = {
        "print_time": False,
        "ipopt.print_level": 0, 
        "ipopt.max_iter": 1000}
    solver = casadi.nlpsol("solver", "ipopt", input, ipopt_opt)
    output = solver(
        x0=phaseInit,
        lbx=phaseRange[0], ubx=phaseRange[1])
    phaseOut = np.array(output['x']).squeeze() % 360

    return phaseOut



def Nullify(pathList, coorSetList, delta=15):
    phaseList = []
    for radioIdx in range(len(pathList)):
        coorSet = coorSetList[radioIdx]

        _, phaseTemp = method_conjugate.Conjugate(pathList=[pathList[radioIdx]], coorSetList=[coorSet])
        phaseInit = np.array(phaseTemp)
        
        phaseSet = NullifyCore(
            coorSet=coorSet, phaseSetIn=phaseInit, 
            direcList=[pathList[idx]['direc'] for idx in range(len(pathList)) if idx!=radioIdx],
            widthList=[pathList[idx]['width'] for idx in range(len(pathList)) if idx!=radioIdx], 
            delta=delta)

        phaseList += list(phaseSet)

    return phaseList