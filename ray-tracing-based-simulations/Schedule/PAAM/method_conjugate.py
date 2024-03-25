import casadi
import numpy as np

from channel import Channel
import method_optimizer



def ConjugateCore(direc, coorSet):
    channel = Channel(snr=0)
    channel.addPath(angle=direc, gain=0, phase=0, width=(0, 0))
    gainSet, phaseSet = method_optimizer.Optimizer([channel], [coorSet])
    return gainSet, phaseSet

def Conjugate(pathList, coorSetList):
    gainList = []
    phaseList = []
    for ueIdx in range(len(pathList)):
        coorSet = coorSetList[ueIdx]
        if len(coorSet) == 0:
            continue
        gainSet, phaseSet = ConjugateCore(direc=pathList[ueIdx]['direc'], coorSet=coorSet)
        gainList += list(gainSet)
        phaseList += list(phaseSet)

    return gainList, phaseList