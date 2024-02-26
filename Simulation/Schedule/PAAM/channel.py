import numpy as np
import general



# Intrinsic Euler Angle X->Y->(Z)

class Channel():
    def __init__(self, snr, angleAxisX=np.arange(start=-180, stop=181), angleAxisY=np.arange(start=-90, stop=91)):
        super(Channel, self).__init__()

        self.snr = snr
        self.angleAxisX = angleAxisX
        self.angleAxisY = angleAxisY
        angleNumX = np.shape(self.angleAxisX)[0]
        angleNumY = np.shape(self.angleAxisY)[0]
        self.gainMap = -np.inf * np.ones((angleNumX, angleNumY))
        self.phaseMap = np.zeros((angleNumX, angleNumY))

    def addPath(self, angle, gain, phase=None, width=(0, 0)):
        angleAxisX = self.angleAxisX
        angleAxisY = self.angleAxisY
        gainMap = self.gainMap
        phaseMap = self.phaseMap

        angleX = angleAxisX[np.argmin(np.abs(angleAxisX-angle[0]))]
        angleY = angleAxisY[np.argmin(np.abs(angleAxisY-angle[1]))]
        if angleX-width[0]/2<angleAxisX[0] or angleX+width[0]/2>angleAxisX[-1]:
            print("Warning: Angle out of Range!")
            return
        else:
            angleIdxListX = np.where((angleAxisX>=angleX-width[0]/2)&(angleAxisX<=angleX+width[0]/2))[0]
            angleIdxNumX = len(angleIdxListX)
        if angleY-width[1]/2<angleAxisY[0] or angleY+width[1]>angleAxisY[-1]:
            print("Warning: Angle out of Range!")
            return
        else:
            angleIdxListY = np.where((angleAxisY>=angleY-width[1]/2)&(angleAxisY<=angleY+width[1]/2))[0]
            angleIdxNumY = len(angleIdxListY)

        for angleIdxX in angleIdxListX:
            for angleIdxY in angleIdxListY:
                gainOld = gainMap[angleIdxX, angleIdxY]
                phaseOld = phaseMap[angleIdxX, angleIdxY]
                ampOld_real, ampOld_imag = general.Gain2Amp(gain=gainOld, phase=phaseOld)
                gainNew = gain - general.Power2Gain(angleIdxNumX/angleIdxNumY)
                phaseNew = np.random.uniform(0, 360) if phase is None else phase
                ampNew_real, ampNew_imag = general.Gain2Amp(gain=gainNew, phase=phaseNew)
                amp_real = ampOld_real + ampNew_real
                amp_imag = ampOld_imag + ampNew_imag

                gainMap[angleIdxX, angleIdxY] = general.Amp2Gain(real=amp_real, imag=amp_imag)
                phaseMap[angleIdxX, angleIdxY] = general.Amp2Phase(real=amp_real, imag=amp_imag)

        self.gainMap = gainMap
        self.phaseMap = phaseMap