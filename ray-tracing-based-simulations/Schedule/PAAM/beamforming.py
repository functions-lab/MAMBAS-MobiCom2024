import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat, savemat
from tqdm import tqdm
import copy

from channel import Channel
import method_MU
import method_conjugate
import method_PC
import method_ZF
import method_nullify
import method_individual
import method_optimizer
import simulate
import physics
import general
import phasedarray



class Beamforming():
    def __init__(self, layout='PAAM', 
        icSizeX=4, icSizeY=1, elemSizeX=1, elemSizeY=16, elemDist=0.5506666666666666666, rotate=0, 
        angleRangeX=[-180, +180], angleRangeY=[-90, +90], resol=1):
        super(Beamforming, self).__init__()

        self.angleAxisX = np.arange(start=angleRangeX[0], stop=angleRangeX[1]+resol, step=resol)
        self.angleAxisY = np.arange(start=angleRangeY[0], stop=angleRangeY[1]+resol, step=resol)

        self.channelList = []
        self.pathList = []
        # self.icemSetList = []
        self.posSetList = []

        PA = phasedarray.PhasedArray(layout=layout, 
            icSizeX=icSizeX, icSizeY=icSizeY, elemSizeX=elemSizeX, elemSizeY=elemSizeY, elemDist=elemDist)
        self.PA = PA
        self.icemUsed = np.full((PA.icNum, PA.elemNum), np.nan)
        self.gainMap = np.full((PA.sizeX, PA.sizeY), np.nan)
        self.phaseMap = np.full((PA.sizeX, PA.sizeY), np.nan)
        self.maskMap = np.zeros((PA.sizeX, PA.sizeY, np.shape(self.angleAxisX)[0], np.shape(self.angleAxisY)[0]))

        self.rotate=rotate



    def _Show_(self):
        posSetList = self.posSetList
        gainMap = self.gainMap
        phaseMap = self.phaseMap

        radioMap = np.nan * np.ones(np.shape(gainMap))
        for radioIdx in range(len(posSetList)):
            for pos in posSetList[radioIdx]:
                posX, posY = pos
                radioMap[posX, posY] = radioIdx
        print(radioMap)
        print(np.array2string(gainMap, formatter={'float_kind': '{0:6.2f}'.format}))
        print(np.array2string(phaseMap, formatter={'float_kind': '{0:6.1f}'.format}))

    def _Icem2Pos_(self, icem):
        PA = self.PA

        ic, elem = icem
        pos = None
        for posX in range(PA.sizeX):
            for posY in range(PA.sizeY):
                if ic==PA.icMap[posX, posY] and elem==PA.elemMap[posX, posY]:
                    pos = (posX, posY)
        if pos is None:
            print("Warning: IC/ELEM NOT found!")
        return pos

    def _Pos2Info_(self, posSet):
        PA = self.PA
        gainMap = self.gainMap
        phaseMap = self.phaseMap
        maskMap = self.maskMap
        rotate = self.rotate

        rotateRad = general.Deg2Rad(rotate+180)
        coorSet = []
        gainSet = []
        phaseSet = []
        maskSet = []
        for posIdx in range(len(posSet)):
            coorX = PA.elemDist*posSet[posIdx][0] * np.cos(rotateRad) + \
                PA.elemDist*posSet[posIdx][1] * np.sin(rotateRad)
            coorY = -PA.elemDist*posSet[posIdx][0] * np.sin(rotateRad) + \
                PA.elemDist*posSet[posIdx][1] * np.cos(rotateRad)
            coor = (coorX, coorY, 0)
            coorSet.append(coor)
            gainSet.append(gainMap[posSet[posIdx][0], posSet[posIdx][1]])
            phaseSet.append(phaseMap[posSet[posIdx][0], posSet[posIdx][1]])
            maskSet.append(maskMap[posSet[posIdx][0], posSet[posIdx][1], :, :])
        return coorSet, gainSet, phaseSet, maskSet

    def _Map2List_(self, gainMap, phaseMap, icList):
        PA = self.PA

        gainList = []
        phaseList = []
        for icIdx in range(len(icList)):
            ic = icList[icIdx]
            gain = np.zeros((PA.elemSizeX, PA.elemSizeY))
            phase = np.zeros((PA.elemSizeX, PA.elemSizeY))
            for elem in range(PA.elemNum):
                icem = (ic, elem)
                pos = self._Icem2Pos_(icem)
                gain[pos[0]%PA.elemSizeX, pos[1]%PA.elemSizeY] = gainMap[pos[0], pos[1]]
                phase[pos[0]%PA.elemSizeX, pos[1]%PA.elemSizeY] = phaseMap[pos[0], pos[1]]
            gainList.append(gain)
            phaseList.append(phase)
        
        return gainList, phaseList



    def _StrategyTDMA_(self, ueMin):
        PA = self.PA
        channel = self.channelList[ueMin]
        path = self.pathList[ueMin]

        beamforming = copy.deepcopy(self)
        beamforming.channelList = [channel]
        beamforming.pathList = [path]
        posSet = []
        for posX in range(PA.sizeX):
            for posY in range(PA.sizeY):
                posSet.append((posX, posY))
        beamforming.posSetList = [posSet]

        beamforming.Optimize(method='Conjugate')
        sinrList, speedList = beamforming.Simulate()
        return sinrList[0], speedList[0]

    def _StrategyOurs_(self, weightList, method_1='Sigmoid-Speed', method_2='Speed', speedThres=1):
        beamforming = copy.deepcopy(self)

        beamforming.Optimize(method=method_1, argDict={'weight': weightList})
        _, speedList_1 = beamforming.Simulate()
        
        radioOffList = []
        radioOnList = []
        for radioIdx in range(len(speedList_1)):
            thres = speedThres[radioIdx] if isinstance(speedThres, list) else speedThres
            if speedList_1[radioIdx] < thres:
                radioOffList.append(radioIdx)
            else:
                radioOnList.append(radioIdx)
        
        weightOnList = [weightList[radioOn] for radioOn in radioOnList]
        radioOnList = [radioOn for _, radioOn in sorted(zip(weightOnList, radioOnList))]
        radioOnList.reverse()

        for radioOffIdx in range(len(radioOffList)):
            radioOff = radioOffList[radioOffIdx]
            radioOnIdx = radioOffIdx % len(radioOnList)
            radioOn = radioOnList[radioOnIdx]
            
            beamforming.posSetList[radioOn] += beamforming.posSetList[radioOff]
            beamforming.posSetList[radioOff] = []
        beamforming.Optimize(method=method_2)
        sinrList_2, speedList_2 = beamforming.Simulate()

        return sinrList_2, speedList_2



    def LoadMask(self, ic, fileName, inputPower=0):
        PA = self.PA
        angleAxisX = self.angleAxisX
        angleAxisY = self.angleAxisY
        maskMap = self.maskMap

        angleNumX = np.shape(angleAxisX)[0]
        angleNumY = np.shape(angleAxisY)[0]

        dict = loadmat(fileName)
        pattern = dict['pattern']
        elemList = dict['elemList'][0]

        for elemIdx in range(len(elemList)):
            elem = elemList[elemIdx]
            icem = (ic, elem)
            pos = self._Icem2Pos_(icem)

            if('angleList' in dict):
                angleList = dict['angleList'][0]
                patternX = np.interp(angleAxisX, angleList, pattern[elemIdx, :])
                patternXY = np.repeat(patternX[:, np.newaxis], angleNumY, axis=-1)
            elif('angleListX' in dict)and('angleListY' in dict): ### NOT debugged yet
                angleListX = dict['angleListX'][0]
                angleListY = dict['angleListY'][0]

                patternX = np.zeros((angleNumX, len(angleListY)))
                for angleIdxY in range(len(angleListY)):
                    patternX[:, angleIdxY] = np.interp(angleAxisX, angleListX, pattern[elemIdx, :, angleIdxY])
                patternXY = np.zeros((angleNumX, angleNumY))
                for angleIdxX in range(angleNumX):
                    patternXY[angleIdxX, :] = np.interp(angleAxisY, angleListY, patternX[angleIdxX, :])
            else:
                print('Warning: File Format NOT Matched!')

            maskMap[pos[0], pos[1], :, :] = patternXY + inputPower

        self.maskMap = maskMap

    def CreateRadio(self, direcSet, gainSet, snr, icList, elemSetList, phaseSet=None, widthSet=None):
        angleAxisX = self.angleAxisX
        angleAxisY = self.angleAxisY
        channelList = self.channelList
        pathList = self.pathList
        # icemSetList = self.icemSetList
        posSetList = self.posSetList
        icemUsed = self.icemUsed

        channel = Channel(snr=snr, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
        for direcIdx in range(len(direcSet)):
            gain = gainSet[direcIdx]
            phase = None if phaseSet is None else phaseSet[direcIdx]
            if isinstance(direcSet[direcIdx], tuple):
                direc = direcSet[direcIdx]
            else:
                direc = (direcSet[direcIdx], 0)
            if widthSet is None:
                width = (0, 0)
            elif isinstance(widthSet[direcIdx], tuple):
                width = widthSet[direcIdx]
            else:
                width = (widthSet[direcIdx], widthSet[direcIdx])
            channel.addPath(angle=direc, gain=gain, phase=phase, width=width)

            if direcIdx == np.argmax(gainSet):
                path = {'direc': direc, 'width': width}
        channelList.append(channel)
        pathList.append(path)

        icemSet = []
        posSet= []
        for icIdx in range(len(icList)):
            ic = icList[icIdx]
            elemSet = elemSetList[icIdx]
            for elem in elemSet:
                if icemUsed[ic, elem] >= 0:
                    print('Warning: IC/ELEM has been occupied!')
                    continue
                icemUsed[ic, elem] = len(channelList) - 1
                icem = (ic, elem)
                icemSet.append(icem)
                pos = self._Icem2Pos_(icem)
                posSet.append(pos)
        # icemSetList.append(icemSet)
        posSetList.append(posSet)

        self.channelList = channelList
        self.pathList = pathList
        # self.icemSetList = icemSetList
        self.posSetList = posSetList
        self.icemUsed = icemUsed
    
    def Clean(self):
        PA = self.PA

        self.channelList = []
        self.pathList = []
        # self.icemSetList = []
        self.posSetList = []
        self.icemUsed = np.full((PA.icNum, PA.elemNum), np.nan)

    # mode 'individual': no re-allocation is applied
    # mode 'all': re-allocate all the used icem to UEs
    def MaxRadio(self, mode='individual'):
        channelList = self.channelList
        posSetList = self.posSetList

        snrList = []
        speedList = []
        if mode == 'individual':
            for radioIdx in range(len(channelList)):
                channel = channelList[radioIdx]
                posSet = posSetList[radioIdx]

                coorSet, _, _, maskSet = self._Pos2Info_(posSet)
                
                signal = simulate.SimSignalMax(channel, len(coorSet), maskSet=maskSet)
                noise = simulate.SimNoise(channel)
                snr = general.Power2Gain(signal/noise)
                speed = np.log2(1 + signal/noise)

                snrList.append(snr)
                speedList.append(speed)
        elif mode == 'all':
            maskSet = []
            elemNum = 0
            for radioIdx in range(len(channelList)):
                posSet = posSetList[radioIdx]

                coorSet, _, _, maskSetTemp = self._Pos2Info_(posSet)
                maskSet += maskSetTemp
                elemNum += len(coorSet)

            for radioIdx in range(len(channelList)):
                channel = channelList[radioIdx]

                signal = simulate.SimSignalMax(channel, elemNum, maskSet=maskSet)
                noise = simulate.SimNoise(channel)
                snr = general.Power2Gain(signal/noise)
                speed = np.log2(1 + signal/noise)

                snrList.append(snr)
                speedList.append(speed)
        else:
            print('Warning: Mode NOT Supported!')
        return snrList, speedList



    def MultiUser(self, method='Conjugate'):
        channelList = self.channelList
        posSetList = self.posSetList
        PA = self.PA

        coorSet = []
        maskSet = []
        elemNumList = []
        radioEffList = []
        for radioIdx in range(len(posSetList)):
            posSet = posSetList[radioIdx]
            if len(posSet) > 0:
                radioEffList.append(radioIdx)
                
            coorSetTemp, _, _, maskSetTemp = self._Pos2Info_(posSet)
            coorSet += coorSetTemp
            maskSet += maskSetTemp
            elemNumList.append(len(coorSetTemp))

        sinrEffList, capacity, W = method_MU.MultiUser(
            channelList=[channelList[radioIdx] for radioIdx in radioEffList],
            coorSet=coorSet, maskSet=maskSet, 
            elemNumList=[elemNumList[radioIdx] for radioIdx in radioEffList],
            method=method)
        
        sinrList = [-np.inf for _ in range(len(posSetList))]
        for radioIdx in range(len(radioEffList)):
            sinrList[radioEffList[radioIdx]] = sinrEffList[radioIdx]
        speedList = [np.log2(1+general.Gain2Power(sinr)) for sinr in sinrList]

        gainListList = [[] for _ in range(len(posSetList))]
        phaseListList = [[] for _ in range(len(posSetList))]
        for radioIdx in range(len(radioEffList)):
            W_col = W[:, radioIdx]

            gainMap = np.full((PA.sizeX, PA.sizeY), np.nan)
            phaseMap = np.full((PA.sizeX, PA.sizeY), np.nan)
            index = -1
            for posSet in posSetList:
                for elemIdx in range(len(posSet)):
                    (posX, posY) = posSet[elemIdx]
                    index = index + 1
                    gainMap[posX, posY] = \
                        general.Amp2Gain(np.real(W_col[index]), np.imag(W_col[index]))
                    phaseMap[posX, posY] = \
                        general.Amp2Phase(np.real(W_col[index]), np.imag(W_col[index]))

            gainList, phaseList = self._Map2List_(gainMap, phaseMap, icList=list(range(PA.icNum)))
            gainListList[radioEffList[radioIdx]] = gainList
            phaseListList[radioEffList[radioIdx]] = phaseList
        return sinrList, speedList, capacity, gainListList, phaseListList

    def Optimize(self, method='Individual', argDict={}):
        PA = self.PA
        angleAxisX = self.angleAxisX
        angleAxisY = self.angleAxisY
        channelList = self.channelList
        pathList = self.pathList
        posSetList = self.posSetList

        coorSetList = []
        gainList = []
        phaseList = []
        maskSetList = []
        for radioIdx in range(len(posSetList)):
            posSet = posSetList[radioIdx]
            coorSet, gainSet, phaseSet, maskSet = self._Pos2Info_(posSet)
            coorSetList.append(coorSet)
            gainList += gainSet
            phaseList += phaseSet
            maskSetList.append(maskSet)

        if method == 'Conjugate':
            gainList, phaseList = method_conjugate.Conjugate(pathList, coorSetList)
        elif method == 'PC':
            gainList, phaseList = method_PC.PartialConnect(channelList, coorSetList)
        elif method == 'ZF':
            gainList, phaseList = method_ZF.ZeroForce(channelList, coorSetList)
        elif method == 'Nullify':
            gainList = [0 for _ in range(len(phaseList))]
            phaseList = method_nullify.Nullify(pathList, coorSetList, delta=15)
        elif method == 'Individual':
            gainList, phaseList = method_individual.Individual(
                pathList, coorSetList, delta=100,
                maskSetList=maskSetList, angleAxisX=angleAxisX, angleAxisY=angleAxisY)
        else:
            gainList, phaseList = method_optimizer.Optimizer(
                channelList, coorSetList, maskSetList=maskSetList, gainIn=gainList, phaseIn=phaseList,
                method=method, argDict=argDict)

        gainMap = np.full((PA.sizeX, PA.sizeY), np.nan)
        phaseMap = np.full((PA.sizeX, PA.sizeY), np.nan)
        index = -1
        for radioIdx in range(len(posSetList)):
            posSet = posSetList[radioIdx]
            for elemIdx in range(len(posSet)):
                (posX, posY) = posSet[elemIdx]
                index = index + 1
                gainMap[posX, posY] = gainList[index]
                phaseMap[posX, posY] = phaseList[index]

        self.gainMap = gainMap
        self.phaseMap = phaseMap



    def Simulate(self, gainBit=33, phaseBit=75):
        channelList = self.channelList
        posSetList = self.posSetList

        coorSetList = []
        gainSetList = []
        phaseSetList = []
        maskSetList = []
        for radioIdx in range(len(channelList)):
            posSet = posSetList[radioIdx]
            coorSet, gainSet, phaseSet, maskSet = self._Pos2Info_(posSet)
            coorSetList.append(coorSet)
            gainSetList.append(gainSet)
            phaseSetList.append(phaseSet)
            maskSetList.append(maskSet)

        signalList, interfList, noiseList = simulate.Simulate(
            channelList, coorSetList, gainSetList, phaseSetList, maskSetList=maskSetList, 
            gainBit=gainBit, phaseBit=phaseBit)

        sinrList = []
        speedList = []
        for radioIdx in range(len(channelList)):
            signal = signalList[radioIdx]
            interf = interfList[radioIdx]
            noise = noiseList[radioIdx]

            sinr = general.Power2Gain(signal/(interf+noise))
            sinrList.append(sinr)
            speed = np.log2(1+signal/(interf+noise))
            speedList.append(speed)
        return sinrList, speedList

    def Plot(self, fileName=None, angleRange=None, resol=1, gainBit=33, phaseBit=75):
        channelList = self.channelList
        posSetList = self.posSetList

        if angleRange is None:
            angleAxis = self.angleAxisX
        else:
            angleAxis = np.arange(start=angleRange[0], stop=angleRange[1]+resol, step=resol)
        angleNum = np.shape(angleAxis)[0]

        coorSetList = []
        gainSetList = []
        phaseSetList = []
        maskSetList = []
        for radioIdx in range(len(channelList)):
            posSet = posSetList[radioIdx]
            coorSet, gainSet, phaseSet, maskSet = self._Pos2Info_(posSet)
            coorSetList.append(coorSet)
            gainSetList.append(gainSet)
            phaseSetList.append(phaseSet)
            maskSetList.append(maskSet)

        fig, ax = plt.subplots()
        colorSet = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        gainMatList = []
        for radioIdx in range(len(channelList)):
            channel = channelList[radioIdx]
            coorSet = coorSetList[radioIdx]
            gainSet = gainSetList[radioIdx]
            phaseSet = phaseSetList[radioIdx]
            maskSet = maskSetList[radioIdx]
            color = colorSet[radioIdx % len(colorSet)]

            angleIdxY = np.argmin(np.abs(channel.angleAxisY-0))
            ax.plot(channel.angleAxisX, np.clip(channel.gainMap[:, angleIdxY], a_min=-10, a_max=np.inf), \
                '--', color=color)

            noise = simulate.SimNoise(channel)
            powerMat = np.zeros((angleNum))
            for angleIdx in range(angleNum):
                angle = (angleAxis[angleIdx], 0)
                respSet = [mask[angleIdx, angleIdxY] for mask in maskSet]
                powerMat[angleIdx] = physics.GetTxPower(angle, coorSet, gainSet, phaseSet, respSet=respSet,
                    gainBit=gainBit, phaseBit=phaseBit)
            gainMat = 10*np.log10(powerMat+noise)
            ax.plot(angleAxis, gainMat, '-', color=color)
            gainMatList.append(gainMat)

        if fileName is not None:
            fig.savefig(fileName+'_2D.png')
        plt.close(fig)

        return gainMatList

    def Plot3D(self, fileName=None, angleRangeX=None, angleRangeY=None, resol=1, gainBit=33, phaseBit=75):
        channelList = self.channelList
        posSetList = self.posSetList

        if angleRangeX is None:
            angleAxisX = self.angleAxisX
        else:
            angleAxisX = np.arange(start=angleRangeX[0], stop=angleRangeX[1]+resol, step=resol)
        if angleRangeY is None:
            angleAxisY = self.angleAxisY
        else:
            angleAxisY = np.arange(start=angleRangeY[0], stop=angleRangeY[1]+resol, step=resol)
        angleNumX = np.shape(angleAxisX)[0]
        angleNumY = np.shape(angleAxisY)[0]

        coorSetList = []
        gainSetList = []
        phaseSetList = []
        maskSetList = []
        for radioIdx in range(len(channelList)):
            posSet = posSetList[radioIdx]
            coorSet, gainSet, phaseSet, maskSet = self._Pos2Info_(posSet)
            coorSetList.append(coorSet)
            gainSetList.append(gainSet)
            phaseSetList.append(phaseSet)
            maskSetList.append(maskSet)

        gainMatList = []
        for radioIdx in range(len(channelList)):
            channel = channelList[radioIdx]
            coorSet = coorSetList[radioIdx]
            gainSet = gainSetList[radioIdx]
            phaseSet = phaseSetList[radioIdx]

            powerMat = np.zeros((angleNumX, angleNumY))
            for angleIdxX in range(angleNumX):
                for angleIdxY in range(angleNumY):
                    angle = (angleAxisX[angleIdxX], angleAxisY[angleIdxY])
                    respSet = [mask[angleIdxX, angleIdxY] for mask in maskSet]
                    powerMat[angleIdxX, angleIdxY] = physics.GetTxPower(angle, coorSet, gainSet, phaseSet, respSet=respSet,
                        gainBit=gainBit, phaseBit=phaseBit)
            noise = simulate.SimNoise(channel)
            gainMat = 10*np.log10(powerMat+noise)
            fig, ax = plt.subplots()
            ax.imshow(np.transpose(gainMat))
            if fileName is not None:
                fig.savefig(fileName+'_'+str(radioIdx)+'.png')
            plt.close(fig)
            gainMatList.append(gainMat)
        
        return gainMatList



    def Load(self, gainList, phaseList, icList=[0, 1, 2, 3], isShow=False):
        PA = self.PA
        gainMap = self.gainMap
        phaseMap = self.phaseMap
        icemUsed = self.icemUsed

        if len(icList) != len(set(icList)):
            print('Warning: Repeated Input IC List!')
        
        for icIdx in range(len(icList)):
            ic = icList[icIdx]
            gain = gainList[icIdx]
            phase = phaseList[icIdx]
            for elem in range(PA.elemNum):
                if not icemUsed[ic][elem] >= 0:
                    print('Warning: The IC/Element is not used!')
                    continue
                icem = (ic, elem)
                pos = self._Icem2Pos_(icem)
                gainMap[pos[0], pos[1]] = gain[pos[0]%PA.elemSizeX, pos[1]%PA.elemSizeY]
                phaseMap[pos[0], pos[1]] = phase[pos[0]%PA.elemSizeX, pos[1]%PA.elemSizeY]

        if isShow:
            self._Show_()

        self.gainMap = gainMap
        self.phaseMap = phaseMap

    def Save(self, icList=[0, 1, 2, 3], isShow=True):
        gainMap = self.gainMap
        phaseMap = self.phaseMap

        if len(icList) != len(set(icList)):
            print('Warning: Repeated Input IC List!')

        if isShow:
            self._Show_()

        gainList, phaseList = self._Map2List_(gainMap, phaseMap, icList=icList)

        return gainList, phaseList



    def Schedule(self, slotNum, method_1='Sigmoid-Speed', method_2='Speed', fileName=None, alpha=0.5, pastInit=1, isProgress=True):
        channelList = self.channelList

        _, speedList = self.MaxRadio(mode='individual')
        speedThresList = [0.3*speed for speed in speedList]

        sinrMat = np.zeros((slotNum, len(channelList)))
        speedMat = np.zeros((slotNum, len(channelList)))
        pastList = pastInit * np.ones((len(channelList)))
        loop = tqdm(range(slotNum)) if isProgress else range(slotNum)
        for slotIdx in loop:
            if (method_1=='TDMA')or(method_2=='TDMA'):
                ueMin = np.argmin(pastList)
                sinr, speed = self._StrategyTDMA_(ueMin)
                sinrList = [0 for _ in range(len(channelList))]
                sinrList[ueMin] = sinr
                speedList = [0 for _ in range(len(channelList))]
                speedList[ueMin] = speed
            else:
                weightList = np.array(speedThresList) / pastList
                sinrList, speedList = self._StrategyOurs_(
                    list(weightList), method_1=method_1, method_2=method_2, speedThres=speedThresList)
            sinrList = np.array(sinrList)
            speedList = np.array(speedList)
            
            sinrMat[slotIdx, :] = sinrList
            speedMat[slotIdx, :] = speedList
            pastList = alpha * pastList + (1-alpha) * speedList

            if fileName is not None:
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