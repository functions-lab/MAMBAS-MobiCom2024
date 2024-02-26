import numpy as np



class PhasedArray():
    def __init__(self, layout='PAAM', 
        icSizeX=4, icSizeY=1, 
        elemSizeX=1, elemSizeY=16, elemDist=0.5506666666666666666):

        if layout=='PAAM':
            self.PAAM()
        elif layout in ['PAAM_Virtual', 'PAAM_Virtual_2']:
            self.PAAM_Virtual_2(icSizeX)
        elif layout == 'PAAM_Virtual_1':
            self.PAAM_Virtual_1(icSizeX)
        elif layout=='Linear':
            self.Linear()
        elif layout=='Custom':
            self.Custom(icSizeX, icSizeY, elemSizeX, elemSizeY, elemDist)
        else:
            print('Warning: Phased array name not found!')
    
    def PAAM(self):
        self.icNum = 4
        self.icSizeX = 2
        self.icSizeY = 2
        self.icMap = np.array([ \
            [0, 0, 0, 0, 1, 1, 1, 1], 
            [0, 0, 0, 0, 1, 1, 1, 1], 
            [0, 0, 0, 0, 1, 1, 1, 1], 
            [0, 0, 0, 0, 1, 1, 1, 1], 
            [3, 3, 3, 3, 2, 2, 2, 2],
            [3, 3, 3, 3, 2, 2, 2, 2],
            [3, 3, 3, 3, 2, 2, 2, 2],
            [3, 3, 3, 3, 2, 2, 2, 2]])

        self.elemNum = 16
        self.elemSizeX = 4
        self.elemSizeY = 4
        self.elemMap = np.array([ \
            [15, 14,  6,  7, 15, 14,  6,  7],
            [13, 12,  4,  5, 13, 12,  4,  5],
            [10, 11,  3,  2, 10, 11,  3,  2],
            [ 8,  9,  1,  0,  8,  9,  1,  0],
            [ 0,  1,  9,  8,  0,  1,  9,  8],
            [ 2,  3, 11, 10,  2,  3, 11, 10],
            [ 5,  4, 12, 13,  5,  4, 12, 13],
            [ 7,  6, 14, 15,  7,  6, 14, 15]])
        self.elemDist = 0.5506666666666666666 # (in wavelength)

        self.sizeX = self.icSizeX * self.elemSizeX
        self.sizeY = self.icSizeY * self.elemSizeY
    
    def PAAM_Virtual_1(self, icSizeX):
        self.icNum = icSizeX * 2
        self.icSizeX = icSizeX
        self.icSizeY = 2
        icMapTemp = np.reshape(np.arange(icSizeX*2), [icSizeX, 2])
        self.icMap = np.kron(icMapTemp, np.ones((4, 4)))

        self.elemNum = 16
        self.elemSizeX = 4
        self.elemSizeY = 4
        elemMapTemp = np.array([ \
            [15, 14,  6,  7, 15, 14,  6,  7],
            [13, 12,  4,  5, 13, 12,  4,  5],
            [10, 11,  3,  2, 10, 11,  3,  2],
            [ 8,  9,  1,  0,  8,  9,  1,  0]])
        self.elemMap = np.zeros((0, 8))
        for _ in range(icSizeX):
            self.elemMap = np.vstack((self.elemMap, elemMapTemp))
        self.elemDist = 0.5506666666666666666 # (in wavelength)

        self.sizeX = self.icSizeX * self.elemSizeX
        self.sizeY = self.icSizeY * self.elemSizeY
    
    def PAAM_Virtual_2(self, icSizeX):
        self.icNum = icSizeX * 2
        self.icSizeX = icSizeX
        self.icSizeY = 2
        icMapTemp = np.reshape(np.arange(icSizeX*2), [icSizeX, 2])
        for idx in range(icSizeX//2):
            icMapTemp[idx*2+1, :] = icMapTemp[idx*2+1, ::-1]
        self.icMap = np.kron(icMapTemp, np.ones((4, 4)))

        self.elemNum = 16
        self.elemSizeX = 4
        self.elemSizeY = 4
        elemMapTemp_even = np.array([ \
            [15, 14,  6,  7, 15, 14,  6,  7],
            [13, 12,  4,  5, 13, 12,  4,  5],
            [10, 11,  3,  2, 10, 11,  3,  2],
            [ 8,  9,  1,  0,  8,  9,  1,  0]])
        elemMapTemp_odd = np.array([ \
            [ 0,  1,  9,  8,  0,  1,  9,  8],
            [ 2,  3, 11, 10,  2,  3, 11, 10],
            [ 5,  4, 12, 13,  5,  4, 12, 13],
            [ 7,  6, 14, 15,  7,  6, 14, 15]])
        self.elemMap = np.zeros((0, 8))
        for idx in range(icSizeX):
            if idx % 2 == 0:
                self.elemMap = np.vstack((self.elemMap, elemMapTemp_even))
            else:
                self.elemMap = np.vstack((self.elemMap, elemMapTemp_odd))
        self.elemDist = 0.5506666666666666666 # (in wavelength)

        self.sizeX = self.icSizeX * self.elemSizeX
        self.sizeY = self.icSizeY * self.elemSizeY
    
    def Linear(self):
        self.icNum = 4
        self.icSizeX = 4
        self.icSizeY = 1
        self.icMap = np.array([ \
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], 
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]])
        
        self.elemNum = 16
        self.elemSizeX = 1
        self.elemSizeY = 16
        self.elemMap = np.array([ \
            [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15],
            [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15],
            [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15],
            [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15]])
        self.elemDist = 0.5506666666666666666 # (in wavelength)

        self.sizeX = self.icSizeX * self.elemSizeX
        self.sizeY = self.icSizeY * self.elemSizeY

    def Custom(self, icSizeX, icSizeY, elemSizeX, elemSizeY, elemDist):
        self.icNum = icSizeX * icSizeY
        self.icSizeX = icSizeX
        self.icSizeY = icSizeY
        icMapTemp = np.reshape(np.arange(icSizeX*icSizeY), (icSizeX, icSizeY))
        self.icMap = np.kron(icMapTemp, np.ones((elemSizeX, elemSizeY)))

        self.elemNum = elemSizeX * elemSizeY
        self.elemSizeX = elemSizeX
        self.elemSizeY = elemSizeY
        elemMapTemp = np.reshape(np.arange(elemSizeX*elemSizeY), (elemSizeX, elemSizeY))
        self.elemMap = np.kron(np.ones((icSizeX, icSizeY)), elemMapTemp)
        self.elemDist = elemDist # (in wavelength)

        self.sizeX = self.icSizeX * self.elemSizeX
        self.sizeY = self.icSizeY * self.elemSizeY