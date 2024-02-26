import numpy as np

import general
from method_MU_PC import SolvePC_D, SolvePC_A



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

# Probably not correct
def Capacity(H, snrList):
    _, S, _ = np.linalg.svd(H)
    capacity = 0
    for ueIdx in range(len(snrList)):
        signal = S[ueIdx]
        noise = general.Gain2Power(-snrList[ueIdx])
        capacityTemp = np.log2(1+signal/noise)
        capacity += capacityTemp
    return capacity

def Conjugate(H):
    ueNum = np.shape(H)[1]
    H_H = np.conjugate(H)
    W = H_H
    c = 1/np.amax(np.abs(W))/ueNum
    return c * W

def ZF(H):
    ueNum = np.shape(H)[1]
    H_H = np.conjugate(H)
    H_T = np.transpose(H)
    W = np.matmul(H_H, np.linalg.inv(np.matmul(H_T, H_H)))
    c = 1/np.amax(np.abs(W))/ueNum
    return c * W

def PC(H, elemNumList, iterNum=10, initNum=10):
    ueNum = np.shape(H)[1]
    W_ZF = ZF(H)

    deltaMin = +np.inf
    W_min = np.zeros((sum(elemNumList), ueNum))
    for _ in range(initNum):
        W_A_mask = np.zeros((sum(elemNumList), ueNum))
        idx = 0
        for ueIdx in range(ueNum):
            elemNum = elemNumList[ueIdx]
            W_A_mask[idx: idx+elemNum, ueIdx] = np.ones((elemNum))
            idx += elemNum

        W_D = np.eye(ueNum)
        W_A = np.exp(1j*np.random.uniform(0, 2*np.pi, (sum(elemNumList), ueNum)))
        W_A = np.multiply(W_A_mask, W_A)
        for iterIdx in range(iterNum):
            if iterIdx % 2 == 0:
                W_A = SolvePC_A(W_ZF, W_D, W_A_init=W_A, W_A_mask=W_A_mask, hard=False)
            else:
                W_D = SolvePC_D(W_ZF, W_A, W_D_init=W_D)
        W = np.matmul(W_A, W_D)
        delta = np.sum(np.abs(W_ZF-W)**2)
        if delta < deltaMin:
            deltaMin = delta
            c_A = 1/np.max(np.abs(W_A), axis=0)
            c_D = ueNum/np.sum(np.abs(W_D)**2)
            W_min = c_D * W
            for ueIdx in range(ueNum):
                W_min[:, ueIdx] *= c_A[ueIdx]
    return W_min

def Brute(H, elemNumList, iterNum=10, initNum=10):
    ueNum = np.shape(H)[1]
    W_ZF = ZF(H)

    deltaMin = +np.inf
    W_min = np.zeros((sum(elemNumList), ueNum))
    for _ in range(initNum):
        W_A_mask = np.zeros((sum(elemNumList), ueNum))
        idx = 0
        for ueIdx in range(ueNum):
            elemNum = elemNumList[ueIdx]
            W_A_mask[idx: idx+elemNum, ueIdx] = np.ones((elemNum))
            idx += elemNum

        W_D = np.eye(ueNum)
        W_A = np.exp(1j*np.random.uniform(0, 2*np.pi, (sum(elemNumList), ueNum)))
        W_A = np.multiply(W_A_mask, W_A)
        for iterIdx in range(iterNum):
            if iterIdx % 2 == 0:
                W_A = SolvePC_A(W_ZF, W_D, W_A_init=W_A, W_A_mask=W_A_mask, hard=False)
            else:
                W_D = SolvePC_D(W_ZF, W_A, W_D_init=W_D)
        W = np.matmul(W_A, W_D)
        delta = np.sum(np.abs(W_ZF-W)**2)
        if delta < deltaMin:
            deltaMin = delta
            c_A = 1/np.max(np.abs(W_A), axis=0)
            c_D = ueNum/np.sum(np.abs(W_D)**2)
            W_min = c_D * W
            for ueIdx in range(ueNum):
                W_min[:, ueIdx] *= c_A[ueIdx]
    return W_min

def MultiUser(channelList, coorSet, maskSet=None, elemNumList=None, method='Conjugate'):
    ueNum = len(channelList)
    elemNum = len(coorSet)

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
                respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet] if maskSet is not None else None
                steerSet = GetSteer(angle, coorSet, respSet=respSet)

                gainChannel = channel.gainMap[angleIdxX, angleIdxY]
                phaseChannel = channel.phaseMap[angleIdxX, angleIdxY]
                channel_real, channel_imag = general.Gain2Amp(gainChannel, phaseChannel)
                channel_comp = complex(channel_real, channel_imag)

                H[:, ueIdx] = H[:, ueIdx] + np.array([channel_comp*steer for steer in steerSet])

    capacity = Capacity(H, snrList=[channel.snr for channel in channelList])

    if method == 'Conjugate':
        W = Conjugate(H)
    elif method == 'ZF':
        W = ZF(H)
    elif(method == 'PC')and(elemNumList is not None):
        W = PC(H, elemNumList)
    else:
        print('Warning: Method NOT Found!')
    Y = np.matmul(np.transpose(H), W)

    sinrList = []
    for ueIdx in range(ueNum):
        snr = channelList[ueIdx].snr

        signal = np.abs(Y[ueIdx, ueIdx]) ** 2
        interf = np.sum(np.abs(Y[ueIdx, :]) ** 2) - signal
        noise = general.Gain2Power(-snr)
        sinr = general.Power2Gain(signal / (interf + noise))
        sinrList.append(sinr)

    return sinrList, capacity, W