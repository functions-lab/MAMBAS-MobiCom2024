import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy.io import loadmat, savemat
import copy

import sys
sys.path.append('./Schedule')
sys.path.append('./Schedule/PAAM')
from PAAM.beamforming import Beamforming
from PAAM.method_MU import MultiUser
from PAAM.channel import Channel
import scheduler_DP
import scheduler_spacing



# Please normalize the max(gainSet)=0 for all users
class Scheduling():
    def __init__(self, direcSetList, gainSetList=None, phaseSetList=None, snrList=30,
        elemNum=8, arrayNum=8, MCStable=None):
        super(Scheduling, self).__init__()

        ueNum = len(direcSetList)
        beamforming = Beamforming(layout='Custom', 
            icSizeX=arrayNum, elemSizeY=elemNum, 
            icSizeY=1, elemSizeX=1, elemDist=0.5506666666666666666, rotate=0,
            angleRangeX=[-30, +30], angleRangeY=[-0, +0], resol=0.1)
        
        direcList = []
        for ueIdx in range(ueNum):
            idx = np.argmax(np.array(gainSetList[ueIdx]))
            direcList.append(direcSetList[ueIdx][idx])

        self.ueNum = ueNum
        self.direcList = direcList
        self.beamforming = beamforming

        self.direcSetList = direcSetList
        self.gainSetList = gainSetList
        self.phaseSetList = phaseSetList
        self.snrList = snrList
        self.elemNum = elemNum
        self.arrayNum = arrayNum
        self.MCStable = MCStable

    def _OptimizeCore_(self, 
        direcSetList, gainSetList, phaseSetList, snrList, icSetList, optimizer):

        elemNum = self.elemNum
        beamforming = self.beamforming
        ueNum = len(direcSetList)

        beamformingTemp = copy.deepcopy(beamforming)
        for ueIdx in range(ueNum):
            if len(icSetList[ueIdx]) == 0:
                continue
            direcSet = direcSetList[ueIdx]
            if isinstance(direcSet, list):
                gainSet = gainSetList[ueIdx] if gainSetList is not None else [0 for _ in direcSet]
                phaseSet = phaseSetList[ueIdx] if phaseSetList is not None else [0 for _ in direcSet]
            else:
                direcSet = [direcSet]
                gainSet = gainSetList[ueIdx] if gainSetList is not None else [0]
                phaseSet = phaseSetList[ueIdx] if phaseSetList is not None else [0]
            snr = snrList[ueIdx] - 20*np.log10(elemNum)
            icSet = icSetList[ueIdx]
            beamformingTemp.CreateRadio(
                direcSet=direcSet, gainSet=gainSet, phaseSet=phaseSet, snr=snr,
                icList=icSet, elemSetList=[list(range(elemNum)) for _ in range(len(icSet))])
        
            beamformingTemp.Optimize(method=optimizer)
            beamformingTemp.Plot(fileName=None)
            sinrList, _ = beamformingTemp.Simulate()

        return sinrList

    def _OptimizeASA_(self, ueOnList, weightList, optimizer):
        ueNum = self.ueNum
        arrayNum = self.arrayNum
        snrList = self.snrList
        direcSetList = self.direcSetList
        gainSetList = self.gainSetList
        phaseSetList = self.phaseSetList

        if(len(ueOnList)==1)and(optimizer=='Conjugate'):
            sinrList = [-np.inf for _ in range(ueNum)]
            ueIdx = ueOnList[0]
            sinrList[ueIdx] = 10*np.log10(arrayNum**2)+snrList[ueIdx]
            return sinrList
        
        weightOnList = [weightList[ueOn] for ueOn in ueOnList]
        ueOnSortList = [ueOn for _, ueOn in sorted(zip(weightOnList, ueOnList), reverse=True)]
        icSetList = [[] for _ in range(ueNum)]
        for arrayIdx in range(arrayNum):
            idx = arrayIdx%len(ueOnSortList)
            ueOn = ueOnSortList[idx]
            icSetList[ueOn].append(arrayIdx)
        ueOnList = [ueIdx for ueIdx in range(ueNum) if len(icSetList[ueIdx])>0]

        sinrOnList = self._OptimizeCore_(
            direcSetList=[direcSetList[ueOn] for ueOn in ueOnList],
            gainSetList=[gainSetList[ueOn] for ueOn in ueOnList],
            phaseSetList=[phaseSetList[ueOn] for ueOn in ueOnList],
            snrList=[snrList[ueOn] for ueOn in ueOnList],
            icSetList=[icSetList[ueOn] for ueOn in ueOnList], 
            optimizer=optimizer)
        
        sinrList = [-np.inf for _ in range(ueNum)]
        for ueOnIdx in range(len(ueOnList)):
            sinrList[ueOnList[ueOnIdx]] = sinrOnList[ueOnIdx]

        return sinrList

    def _OptimizeMU_(self, ueOnList, optimizer):
        ueNum = self.ueNum
        elemNum = self.elemNum
        arrayNum = self.arrayNum
        snrList = self.snrList
        direcSetList = self.direcSetList
        gainSetList = self.gainSetList
        phaseSetList = self.phaseSetList
        
        if elemNum*arrayNum < len(ueOnList):
            return [0 for _ in range(ueNum)]
        
        channelList = []
        for ueIdx in ueOnList:
            snr = snrList[ueIdx] - 20*np.log10(elemNum)
            direcSet = direcSetList[ueIdx]
            gainSet = gainSetList[ueIdx]
            phaseSet = phaseSetList[ueIdx]

            channel = Channel(snr=snr)
            for direcIdx in range(len(direcSet)):
                gain = gainSet[direcIdx]
                phase = phaseSet[direcIdx]
                direc = (direcSet[direcIdx], 0)
                channel.addPath(angle=direc, gain=gain, phase=phase)
            channelList.append(channel)

        coorSet = []
        for elemIdx in range(elemNum):
            for arrayIdx in range(arrayNum):
                coorX = arrayIdx * 0.5506666666666666666
                coorY = elemIdx * 0.5506666666666666666
                coor = (coorX, coorY, 0)
                coorSet.append(coor)
        
        sinrOnList, _, _ = MultiUser(channelList, coorSet, method=optimizer)

        sinrList = [-np.inf for _ in range(ueNum)]
        for ueOnIdx in range(len(ueOnList)):
            sinrList[ueOnList[ueOnIdx]] = sinrOnList[ueOnIdx]

        return sinrList

    def _Sinr2Speed_(self, sinr, isMCS=True):
        MCStable = self.MCStable
        if(isMCS)and(MCStable is not None):
            mcsNum = MCStable['mcsNum']
            speedList = MCStable['speedList']
            sinrList = MCStable['sinrList']
            blerList = MCStable['blerList']

            for mcs in range(mcsNum):
                if sinr < sinrList[mcs]:
                    break
            mcs -= 1
            if mcs < 0:
                speed = 0
            else:
                speed = 0 if np.random.uniform(low=0, high=1)<blerList[mcs] else speedList[mcs]
        else:
            speed = np.log2(1 + 10 ** (sinr/10))
        return speed

    def Proceed(self, slotNum=20, scheduler='DP', optimizer='Individual', dpCache='DP_sine.mat', 
        fileName=None, alpha=0.5, pastInit=1, isProgress=True, isPlot=True):

        ueNum = self.ueNum
        direcList = self.direcList
        elemNum = self.elemNum
        snrList = self.snrList
        beamforming = self.beamforming

        speedMaxList = [self._Sinr2Speed_(snr, isMCS=False) for snr in snrList]

        sinrMat = np.zeros((slotNum, ueNum))
        speedMat = np.zeros((slotNum, ueNum))
        pastList = pastInit * np.ones((ueNum))
        loop = tqdm(range(slotNum)) if isProgress else range(slotNum)
        for slotIdx in loop:
            weightList = np.array(speedMaxList) / pastList

            beamformingTemp = copy.deepcopy(beamforming)
            if scheduler=='TDMA':
                ueOnList = [np.argmax(weightList)]
            elif scheduler=='All':
                ueOnList = list(np.arange(ueNum))
            elif scheduler=='Spacing':
                ueOnList = scheduler_spacing.Scheduler(
                    direcSet=direcList, spacing=1.0/elemNum/0.5506666666666666666/2, weightList=weightList)
            elif scheduler=='DP':
                ueOnList = scheduler_DP.Scheduler(
                    direcSet=direcList, dpCache=dpCache, weightList=weightList)
            else:
                print('Warning: Scheduler NOT Found!')

            if 'MU-' in optimizer:
                sinrList = self._OptimizeMU_(
                    ueOnList=ueOnList, optimizer=optimizer[3:])
            else:
                sinrList = self._OptimizeASA_(
                    ueOnList=ueOnList, weightList=list(weightList), optimizer=optimizer)

            speedList = [self._Sinr2Speed_(sinr) for sinr in sinrList]
            sinrList = np.array(sinrList)
            speedList = np.array(speedList)

            sinrMat[slotIdx, :] = sinrList
            speedMat[slotIdx, :] = speedList
            pastList = alpha * pastList + (1-alpha) * speedList

            if fileName is not None:
                if isPlot:
                    fig, ax = plt.subplots()
                    ax.imshow(sinrMat)
                    fig.savefig(fileName+'_SINR.png')
                    plt.close(fig)

                    fig, ax = plt.subplots()
                    ax.imshow(speedMat)
                    fig.savefig(fileName+'_Speed.png')
                    plt.close(fig)

                savemat(fileName+'.mat', {
                    'sinrMat': sinrMat, 'speedMat': speedMat})

        return sinrMat, speedMat