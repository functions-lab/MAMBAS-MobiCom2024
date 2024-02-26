import numpy as np

import general
from method_MU_PC import SolvePC_A



def GetSteer(angle, coorSet, respSet=None):
    elemNum = len(coorSet)
    angleRad = general.Deg2Rad(np.array(angle))
    angleNorm = [ \
        np.sin(angleRad[1]), 
        -np.sin(angleRad[0]) * np.cos(angleRad[1]), 
        np.cos(angleRad[0]) * np.cos(angleRad[1])]

    steerSet = []
    for elemIdx in range(elemNum):
        coor = np.array(coorSet[elemIdx])
        delay = 360*np.dot(coor, angleNorm)
        resp = respSet[elemIdx] if respSet is not None else 0

        steer_real, steer_imag = general.Gain2Amp(resp, delay)
        steer = complex(steer_real, steer_imag)
        steerSet.append(steer)
    return steerSet

def ZF(H):
    ueNum = np.shape(H)[1]
    H_H = np.conjugate(H)
    H_T = np.transpose(H)
    W = np.matmul(H_H, np.linalg.inv(np.matmul(H_T, H_H)))
    c = 1/np.amax(np.abs(W))/ueNum
    return c * W

def PartialConnectCore(H, elemNumList):
    ueNum = np.shape(H)[1]
    W_ZF = ZF(H)

    W_D = np.identity(ueNum)
    W_A = np.exp(1j*np.random.uniform(0, 2*np.pi, (sum(elemNumList), ueNum)))
    W_A_mask = np.zeros((sum(elemNumList), ueNum))
    idx = 0
    for ueIdx in range(ueNum):
        elemNum = elemNumList[ueIdx]
        W_A_mask[idx: idx+elemNum, ueIdx] = np.ones((elemNum))
        idx += elemNum
    W_A = np.multiply(W_A_mask, W_A)

    W_A = SolvePC_A(W_ZF, W_D, W_A_init=W_A, W_A_mask=W_A_mask)

    return W_A

def PartialConnect(channelList, coorSetList):
    ueNum = len(channelList)
    coorList = []
    elemNumList = []
    for coorSet in coorSetList:
        coorList += coorSet
        elemNumList.append(len(coorSet))
    elemNum = len(coorList)

    H = np.zeros((elemNum, ueNum), dtype=np.complex_)
    for ueIdx in range(ueNum):
        channel = channelList[ueIdx]
        angleAxisX = channel.angleAxisX
        angleAxisY = channel.angleAxisY
        for angleIdxX in range(np.shape(angleAxisX)[0]):
            for angleIdxY in range(np.shape(angleAxisY)[0]):
                if channel.gainMap[angleIdxX, angleIdxY] == -np.inf:
                    continue
                angle = (angleAxisX[angleIdxX], angleAxisY[angleIdxY])
                steerSet = GetSteer(angle, coorList)

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                phaseChannel = channel.phaseMap[angleIdxX, angleIdxY]
                channel_real, channel_imag = general.Gain2Amp(gainChannel, phaseChannel)
                channel_comp = complex(channel_real, channel_imag)

                H[:, ueIdx] = H[:, ueIdx] + np.array([channel_comp*steer for steer in steerSet])

    W_A = PartialConnectCore(H, elemNumList)
    ampMax = np.max(np.abs(W_A))

    gainList = []
    phaseList = []
    idx = 0
    for ueIdx in range(len(channelList)):
        elemNum = elemNumList[ueIdx]
        ampList = list(W_A[idx: idx+elemNum, ueIdx])
        # ampMax = np.max(np.abs(W_A[idx: idx+elemNum, ueIdx]))
        
        gainList += [general.Amp2Gain(np.real(amp/ampMax)+1e-10, np.imag(amp/ampMax)) for amp in ampList]
        phaseList += [np.angle(amp, deg=True) for amp in ampList]

        idx += elemNum
    return gainList, phaseList
