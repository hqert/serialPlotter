
###################################################################################
###################################################################################
#
# Serial plotter module, actually comprises of a few different modules that should 
# probably be separated into different files.
#
# Developped for the 2018 LiT competition, but with flexibility in mind
#
#
# TODO: Better X axis implementation, as of now it is always passed around
# TODO: implement numerical value output
# 2018.05.05 - Loïs Bosson
#
###################################################################################
###################################################################################

import PySide
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from io import BytesIO
import serial
import time
import platform
from collections import deque
from itertools import chain
import warnings




###################################################################################
# Serial acquisition
#
# TODO: test XY mode
# TODO: make the serial reading more robust
###################################################################################

class serialAcq:

    def __init__(self, **kwargs):
        defaults = {
            'port'          : '/dev/ttyACM2',
            'baudrate'      : 9600,
            'bufferLength'  : 500,
            'channelNbr'    : 2, 
            'XChan'         : False,
            'XStep'         : 1,
            'replaceNaNs'   : False,
        }
        
        # Use kwargs if available, use defaults if not given
        for key in defaults:
            self.__setattr__(key, kwargs.pop(key, defaults[key]))

        # Warn if unexpected kwargs were given
        for key in kwargs:
            kwargWarn = 'kwarg "{} = {}" is unknown'.format(key, kwargs[key])
            warnings.warn(kwargWarn)

        # Define buffers and X channel (buffer[0])
        self.buffers = [ deque([0] *self.bufferLength, maxlen=self.bufferLength) 
                            for _ in range(self.channelNbr+int(not self.XChan))]
        self.currentX = 0

        # Open the serial port
        self.SPort = serial.Serial(self.port, self.baudrate)


    def updateData(self):
        #TODO: check readline timeout possible issue
        while self.SPort.inWaiting():
            line = self.SPort.readline() 
            #TODO maybe add option for input format?
            data = np.genfromtxt(BytesIO(line), dtype = float)
            
            #check we have a complete line, else replace entries with NaNs
            #TODO: wait for a line to be complete instead
            if data.size != self.channelNbr:
                data = [np.NaN] * self.channelNbr

            if self.replaceNaNs:
                data = [0 if np.isnan(i) else i for i in data]
            
            # Update buffers
            for new,buf in zip(data, self.buffers[int(not self.XChan):]):
                buf.append(new)

            # Update x axis
            self.buffers[0].append(self.currentX)
            self.currentX += self.XStep
        return self.buffers





###################################################################################
# mainWindow
# 
#
# TODO: Parametrize the plotters instantiated (via kwargs?)
# TODO: Allow horizontal subplots/2D tiling
# TODO: Allow shared x axis
# TODO: Allow scrolling to be controlled
###################################################################################

class mainWindow:

    def __init__(self, plotterDictList, title='Serial plotter',  **kwargs):
        #QtGui.QApplication.setGraphicsSystem('raster')
        app = QtGui.QApplication([])
        mw = QtGui.QMainWindow()
        mw.setWindowTitle(title)
        cw = QtGui.QWidget()
        mw.setCentralWidget(cw)
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        cw.setLayout(grid)
        mw.show()
        
        # create an array of plotters
        self.plotters = [ livePlot(plotterDict.pop('dataUpdate_cb'), grid, yPos, **plotterDict ) 
                for plotterDict, yPos in zip(plotterDictList, range(len(plotterDictList)))]





        # define a timer that will signal all plots to update
        t = QtCore.QTimer()
        for plotter in self.plotters:
            t.timeout.connect(plotter.update)
        
        #start timer
        t.start(50)
        ## Start Qt event loop
        if __name__ == '__main__':
            import sys
            if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
                QtGui.QApplication.instance().exec_()



#    def stopAnimation(self):
#        if not self.running:
#            print('stop!')




###################################################################################
# Live plotter
#
# For a line to be visible, it MUST have a legend entry, even if empty!
# The updateData_cb callback must provide the X axis as first array in list
# There may be more legend entries than arrays returned by the updater callback
#
# TODO: implement automatic number of lines
# TODO: implement autoresizing of Y
# TODO: implement X scrolling instead of sowing negative time
# TODO: implement sample to second conversion
# 
###################################################################################

class livePlot:


    def __init__(self, updateData_cb, grid, yPos, **kwargs):

        defaults = {
            'windowSize'    : 500,
            'showLegend'    : True,
            'labels'        : ['poney 1', 'poney 2'],
#            'autoResizeY'   : False,
#            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
            'XLabel'        : 'Time',
            'XUnits'        : 'samples',
            'YLabel'        : '',
            'YUnits'        : '',
            'title'         : '',
            'textOffset'    : 0,
        }

        # Use kwargs if available, defaults if not given
        for key in defaults:
            self.__setattr__(key, kwargs.pop(key, defaults[key]))

        # Warn if unexpected kwargs were given
        for key in kwargs:
            kwargWarn = 'kwarg "{} = {}" is unknown'.format(key, kwargs[key])
            warnings.warn(kwargWarn)
        
        self.updateData_cb = updateData_cb

        pw1 = pg.PlotWidget()
        grid.addWidget(pw1, yPos, 0)
        self.label = QtGui.QLabel('test {}'.format(yPos))
        self.label.setMinimumWidth(200)
        grid.addWidget(self.label, yPos, 1)
        pw1.setTitle(self.title)
        pw1.setLabel('left', self.YLabel, units=self.YUnits)
        pw1.setLabel('bottom', self.XLabel, units=self.XUnits)
        pw1.setXRange(-self.windowSize, 0)
        pw1.setYRange(self.minY, self.maxY)
        pw1.showGrid(x=True, y=True, alpha=1)
        samplingPos = pg.InfiniteLine(angle=90, pos = -self.textOffset)
        pw1.addItem(samplingPos)

        if self.showLegend:
            pw1.addLegend()

        #create empty plots with the right parameters
        nplots = len(self.labels)
        self.plots = [pw1.plot(pen=(i, nplots*1.3), name = label) 
                for i, label in zip(range(nplots), self.labels)]
    def update(self):
        data = np.array(self.updateData_cb())
        labelText = ''
        for (plot, yData, label) in zip(self.plots, data[1:], self.labels):
            plot.setData( x= np.array(range(-len(yData), 0)), y = yData)
            labelText +=('{}: {: 4.2f}'.format(label, yData[-self.textOffset-1]))
            labelText += '\n'
        self.label.setText(labelText)



###################################################################################
# Data Processor
# 
###################################################################################


class dataProcessor:

    def __init__(self, updateData_cb, processFunc, outputRaw=False):
        self.updateData_cb  = updateData_cb
        self.processFunc    = processFunc
        self.outputRaw      = outputRaw

    def process(self):
        dataIn = np.array(self.updateData_cb())

#        print('dataIn.shape: {}'.format(dataIn.shape))
#        print('processFuncs len: {}'.format(len(self.processFuncs)))
        
        output = np.array(self.processFunc(dataIn[1:]))
       
#        print('currentValue: {}'.format((output[:, -400-1])))

       
#         print('output.shape: {}'.format(output.shape))
        if self.outputRaw:
            a = dataIn
        else:
            a = dataIn[0]

        return np.vstack([a, output])



#class dataProcessor:
#
#    def __init__(self, updateData_cb, processFuncs, outputRaw=False):
#        self.updateData_cb  = updateData_cb
#        self.processFuncs   = processFuncs
#        self.outputRaw      = outputRaw
#
#    def process(self):
#        dataIn = np.array(self.updateData_cb())
#
##        print('dataIn.shape: {}'.format(dataIn.shape))
##        print('processFuncs len: {}'.format(len(self.processFuncs)))
#        
#        output = np.array([processor(data) for processor,data in zip(self.processFuncs, dataIn[1:])])
#        
#       
##        print('currentValue: {}'.format((output[:, -400-1])))
#
#       
##         print('output.shape: {}'.format(output.shape))
#        if self.outputRaw:
#            a = dataIn
#        else:
#            a = dataIn[0]
#
#        return np.vstack([a, output])
#



###################################################################################
# Test case
# 
###################################################################################




# Simple running average for now
def runningAvg(dataIn):
#    dataOut = np.convolve(dataIn, [1/5]*5, mode='same')
    dataIn = np.array(dataIn)
    dataOut = [np.NaN for _ in range(len(dataIn))] # Init the array
    averageLen = 300
    for i in range(averageLen, len(dataOut)):
        dataOut[i] = dataIn[i-averageLen: i].sum() / averageLen
    
    return dataOut


def sample2T(sample, gain):
    #sample in ADC range
    #output in degree Celsius
    #constants for conversion to degrees
    T0      = 25
    R0      = 500 # RTD value à T0, approximated
    V_ref   = 5
    maxBit  = 1023
    V_in    = 0.0061
    alpha   = 0.0023

    return T0 - 4*sample*V_ref/maxBit/(alpha*(sample*V_ref/maxBit - gain*V_in))


def filterTemps(dataIn):
            
    gains    = [50e3, 50e3]
    dataOut = np.array([[sample2T(sample, gain) for sample in channel] for channel, gain in zip(dataIn[0:2], gains)])
    # Filter the two channels
    dataOut = np.array([runningAvg(channel) for channel in dataOut])
    mean    = dataOut.mean(0) #average the two channels)
    dataOut = np.vstack([dataOut, mean])
    
    return dataOut


def filterFlow(dataIn):
    deltaT = runningAvg([sample2T(sample, 50000)-25 for sample in dataIn[2]])
    dataOut = [np.exp((dT + 1.5)/(-0.205))*1e6 for dT in deltaT] 
    return dataOut 

if __name__ == '__main__':
    print("Using python: " + platform.python_version())
    print("Using numpy: " + np.__version__)
#    print("Using matplotlib: " + matplotlib.__version__)
    print("Serial: " + serial.__version__)


    # Serial
    acquisition = serialAcq(
                            port            = '/dev/ttyACM0',
                            XChan           = False,
                            replaceNaNs     = True,
                            bufferLength    = 900,
                            channelNbr      = 3,
                        )
    acquisition.updateData()
     
     
    # Processing

    getTemps = dataProcessor(
            acquisition.updateData,
            filterTemps,
            outputRaw = False)

    getFlow  = dataProcessor(
            acquisition.updateData,
            filterFlow,
            outputRaw = False)
 

    # mainWindow
    live = mainWindow([
       {
            'dataUpdate_cb' : acquisition.updateData,
            'windowSize'    : 500,
            'showLegend'    : False,
            'labels'        : ['Upstream', 'Downstream', 'Difference'],
#            'autoResizeY'   : True,
#            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
            'YLabel'        : '',
            'title'         :'Raw data',
            },
        {
            'dataUpdate_cb' : getTemps.process,
            'windowSize'    : 500,
            'showLegend'    : True,
            'labels'        : ['Upstream', 'Downstream', 'Average'],
#            'autoResizeY'   : False,
#            'XScroll'       : True,
            'minY'          : 20,
            'maxY'          : 50,
            'YLabel'        : 'Temperature',
            'YUnits'        : '°C',
            'title'         : 'Temperature',
            'textOffset'    : 000,
            },
        {
            'dataUpdate_cb' : getFlow.process,
            'windowSize'    : 500,
            'showLegend'    : True,
            'labels'        : ['Flow'],
#            'autoResizeY'   : False,
#            'XScroll'       : True,
            'minY'          : 0,
            'maxY'          : 100,
            'YLabel'        : 'Water flow',
            'YUnits'        : 'mL/s',
            'title'         : 'Flow',
            'textOffset'    : 000,
            }
        ], title='Lit 2018 - Team 1')
