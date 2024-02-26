from scipy.io import loadmat
import numpy as np
import os



def FindAngleIdx(angle, angleAxis):
    angleIdx = np.argmin(np.abs(angle-angleAxis))
    if angleAxis[angleIdx]>angle and angleIdx>0:
        angleIdx -= 1
    return angleIdx

def Scheduler(direcSet, dpCache='DP_sine.mat', weightList=None):
    ueNum = len(direcSet)
    direcSetSort = np.sort(direcSet)
    indexSet = np.argsort(direcSet)

    dpDict = loadmat(os.path.dirname(__file__)+'/'+dpCache)
    # dp_h2 = dpDict['dp_2'].squeeze()
    dp_h3 = dpDict['dp_3'].squeeze()
    direcAxis = dpDict['sineList'].squeeze()

    dp_w = np.ones((ueNum))
    if weightList is not None:
        for ueIdx in range(ueNum):
            dp_w[ueIdx] = weightList[indexSet[ueIdx]]

    dp_f = -np.inf * np.ones((ueNum, ueNum))
    dp_last = -np.ones((ueNum, ueNum), dtype=int)
    for i in range(ueNum):
        for j in range(i+1):
            if i == j:
                dp_f[i, j] = dp_w[i]
                dp_last[i, j] = i
                continue
            for k in range(j+1):
                direcIdx_1 = FindAngleIdx(
                    np.abs(np.sin(direcSetSort[i]/360*2*np.pi)-np.sin(direcSetSort[j]/360*2*np.pi)), direcAxis)
                if j!=k:
                    direcIdx_2 = FindAngleIdx(
                    np.abs(np.sin(direcSetSort[j]/360*2*np.pi)-np.sin(direcSetSort[k]/360*2*np.pi)), direcAxis)
                else:
                    direcIdx_2 = np.shape(direcAxis)[0]-1
                # direcIdx_1 = np.argmin(np.abs(direcSetSort[i]-direcSetSort[j]-direcAxis))
                # direcIdx_2 = np.argmin(np.abs(direcSetSort[j]-direcSetSort[k]-direcAxis)) if j!=k else np.shape(direcAxis)[0]-1
                if(dp_h3[direcIdx_1, direcIdx_2]>0.95)and(dp_f[i, j]<dp_w[i]+dp_f[j, k]):
                    dp_f[i, j] = dp_w[i] + dp_f[j, k]
                    dp_last[i, j] = k

    i, j = np.unravel_index(np.nanargmax(dp_f, axis=None), dp_f.shape)
    if i !=j:
        ueList = [i, j]
        while j != dp_last[i, j]:
            temp = dp_last[i, j]
            i = j
            j = temp
            ueList.append(j)
    else:
        ueList = [i]

    ueList.reverse()
    ueList = [indexSet[ue] for ue in ueList]
    return ueList