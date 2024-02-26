import numpy as np
from tqdm import tqdm
from scipy.io import loadmat, savemat
import argparse
import os

from Schedule.scheduling import Scheduling



parser = argparse.ArgumentParser(description='PAAM Board Simulation')
parser.add_argument('--scheduler', default='DP', type=str, choices=['DP', 'TDMA', 'All', 'Spacing'],
    help='DP, TDMA, All, Spacing')
parser.add_argument('--optimizer', default='Individual', type=str, choices=['Individual', 'Conjugate', 'MU-ZF', 'Nullify'],
    help='Individual, Conjugate, MU-ZF, Nullify')
parser.add_argument('--bound', default=30, type=int,
    help='Angle of Bound')
parser.add_argument('--ueNum', default=8, type=int,
    help='Number of UEs')
parser.add_argument('--elem', default=16, type=int,
    help='Subarray Size')
parser.add_argument('--array', default=8, type=int,
    help='Subarray Number')

if __name__ == "__main__":
    opt = parser.parse_args()

    ueNum = opt.ueNum
    bound = opt.bound
    scheduler = opt.scheduler
    optimizer = opt.optimizer
    elem = opt.elem
    array = opt.array

    snr = 30
    dpCache = 'dp_cache/DP_' + str(elem) + '.mat'

    scenario = './Dataset/'
    fileName = \
        'Result/Result_UE'+str(ueNum)+'_elem'+str(elem)+'_array'+str(array)+\
        '_'+scheduler+'_'+optimizer

    MCStable = {
        'mcsNum': 28,
        'speedList': np.array([
            0.2344, 0.3770, 0.6016, 0.8770, 1.1758,
            1.4766, 1.6953, 1.9141, 2.1602, 2.4063,
            2.5703, 2.7305, 3.0293, 3.3223, 3.6094,
            3.9023, 4.2129, 4.5223, 4.8164, 5.1152,
            5.3320, 5.5547, 5.8906, 6.2266, 6.5703,
            6.9141, 7.1602, 7.4063]) * 92.16,
        'sinrList': np.array([
            -6, -4, -2,  0,  2,  7, 10, 11, 12, 12,
            13, 15, 16, 19, 19, 21, 21, 23, 24, 24,
            28, 31, 35,
            +np.inf, +np.inf, +np.inf, +np.inf, +np.inf]),
        'blerList': np.array([
            0.000, 0.055, 0.025, 0.065, 0.000,
            0.100, 0.025, 0.095, 0.045, 0.090,
            0.085, 0.085, 0.070, 0.060, 0.055, 
            0.005, 0.055, 0.010, 0.055, 0.090,
            0.070, 0.070, 0.010, 1, 1, 1, 1, 1])}

    sinrMatList = []
    speedMatList = []
    dataIdx = 0
    while os.path.exists(scenario+'Scenario_'+str(dataIdx+1)+'/'):
        dataIdx += 1

        direcSetList = []
        gainSetList = []
        phaseSetList = []
        snrList = []
        ueIdx = 0
        index = 0
        while os.path.exists(scenario+'Scenario_'+str(dataIdx)+'/UE_'+str(index+1)+'.mat'):
            index += 1
            ueIdx += 1

            ueInfo = loadmat(scenario+'Scenario_'+str(dataIdx)+'/UE_'+str(index)+'.mat')
            if np.shape(ueInfo['AoD']) == (0, 0):
                ueIdx -= 1
                continue
            AoDSet = np.squeeze(ueInfo['AoD'], axis=0)
            pathLossSet = np.squeeze(ueInfo['pathLoss'], axis=0)
            phaseShiftSet = np.squeeze(ueInfo['phaseShift'], axis=0)

            pathMax = np.argmin(pathLossSet)
            direcMax = AoDSet[pathMax]
            if(direcMax<-bound)or(direcMax>+bound):
                ueIdx -= 1
                continue
            direcSetTemp = list(AoDSet)
            gainSetTemp = list(-pathLossSet+np.min(pathLossSet))
            snrList.append(snr+90-np.min(pathLossSet))
            phaseSetTemp = list(phaseShiftSet)
            
            direcSet = []
            gainSet = []
            phaseSet = []
            for idx in range(len(direcSetTemp)):
                if(direcSetTemp[idx]>-bound)and(direcSetTemp[idx]<+bound):
                    direcSet.append(direcSetTemp[idx])
                    gainSet.append(gainSetTemp[idx])
                    phaseSet.append(phaseSetTemp[idx])

            direcSetList.append(direcSet)
            gainSetList.append(gainSet)
            phaseSetList.append(phaseSet)

            if ueIdx == ueNum:
                break
        if ueIdx < ueNum:
            continue
        
        scheduling = Scheduling(
            direcSetList=direcSetList, gainSetList=gainSetList, phaseSetList=phaseSetList, snrList=snrList,
            elemNum=elem, arrayNum=array, MCStable=MCStable)
        sinrMat, speedMat = scheduling.Proceed(
            slotNum=20, scheduler=scheduler, optimizer=optimizer, dpCache=dpCache, fileName=None, isPlot=True)
        sinrMatList.append(sinrMat)
        speedMatList.append(speedMat)

        savemat(fileName+'.mat',
            {'sinrMatList':sinrMatList, 'speedMatList': speedMatList})