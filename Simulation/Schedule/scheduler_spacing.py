import numpy as np



def Scheduler(direcSet, spacing, weightList=None):
    ueNum = len(direcSet)
    sineList = np.array([np.sin(direc/360*2*np.pi) for direc in direcSet])
    rankList = np.argsort(-weightList) if weightList is not None else np.arange(ueNum)

    ueList = []
    for ueIdx in range(ueNum):
        ueNow = rankList[ueIdx]
        sineNow = sineList[ueNow]
        if all([np.abs(sineList[ue]-sineNow)>spacing for ue in ueList]):
            ueList.append(ueNow)
            
    return ueList