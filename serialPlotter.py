
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


import matplotlib.pyplot as plt
import matplotlib
#import matplotlib.animation as animation
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
# Animator
# 
# Manages the figure and animation state. Holds the axes for each subplot and 
# an associated plotter object to update various parts of it. TODO: Formulation/check
# callback list is 
# given at init, each corresponding to a new subplot.
#
# TODO: Parametrize the plotters instantiated (via kwargs?)
# TODO: Allow horizontal subplots/2D tiling
# TODO: Allow shared x axis
# TODO: Allow scrolling to be controlled
###################################################################################

class animator:

    def __init__(self, plotterDictList, **kwargs):
        self.fig, self.ax = plt.subplots(len(plotterDictList), 1)
        
        # Make it iterable no matter what, there must be a better way... TODO
        if len(plotterDictList) == 1:
            self.ax = [self.ax]
        self.plotters = [ livePlot(plotterDict.pop('dataUpdate_cb'), ax, **plotterDict ) 
                for plotterDict, ax in zip(plotterDictList, self.ax)]
 
        
        self.updaters = [plotter.updateFig for plotter in self.plotters]
        self.anim = matplotlib.animation.FuncAnimation(self.fig, self.updateAxes, interval = 1/24, blit=True) 
        #Hack the drawing method to allow blitting of objects outside the axes bbox
        matplotlib.animation.Animation._blit_draw = self._blit_draw


#    def stopAnimation(self):
#        if not self.running:
#            print('stop!')
#            self.anim.event_source.stop()


    def updateAxes(self, frame = 0): 
        artists = []
        for updater in self.updaters:
            for plotArtist in updater(frame):
                artists.append(plotArtist)
        return artists


    # Redefinition of the drawing routine from Stack Overflow question "Animated Title in Matplotlib"
    def _blit_draw(self, artists, bg_cache):
        # Handles blitted drawing, which renders only the artists given instead
        # of the entire figure.
        updated_ax = []
        for a in artists:
            # If we haven't cached the background for this axes object, do
            # so now. This might not always be reliable, but it's an attempt
            # to automate the process.
            if a.axes not in bg_cache:
                bg_cache[a.axes] = a.figure.canvas.copy_from_bbox(a.axes.figure.bbox)
            a.axes.draw_artist(a)
            updated_ax.append(a.axes)

        # After rendering all the needed artists, blit each axes individually.
        for ax in set(updated_ax):
            ax.figure.canvas.blit(ax.figure.bbox)



###################################################################################
# Live plotter
#
# For a line to be visible, it MUST have a legend entry, even if empty!
# The updateData_cb callback must provide the X axis as first array in list
# There may be more legend entries than arrays returned by the updater callback
#
# TODO: implement automatic number of lines
# TODO: switch to something else than matplotlib, the thing is terribly slow
#       and glitchy with scrolling axes hack
# 
###################################################################################

class livePlot:


    def __init__(self, updateData_cb, ax, **kwargs):

        defaults = {
            'windowSize'    : 500 ,
            'showLegend'    : True,
            'labels'        : ['poney 1', 'poney 2'],
            'autoResizeY'   : False,
            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
            'title'         : '',
        }
        
        # Use kwargs if available, defaults if not given
        for key in defaults:
            self.__setattr__(key, kwargs.pop(key, defaults[key]))

        # Warn if unexpected kwargs were given
        for key in kwargs:
            kwargWarn = 'kwarg "{} = {}" is unknown'.format(key, kwargs[key])
            warnings.warn(kwargWarn)
        
        self.updateData_cb = updateData_cb

        # Init plotting
        self.ax     = ax
        self.ax.set_title(self.title)
        self.maxX   = self.windowSize
        self.dataX  = [0]
        self.dataY  = [ [0] for _ in range(len(self.labels)) ]
        
        self.lines  = []
        for Y, legend in zip(self.dataY, self.labels):
            line = ax.plot(self.dataX, Y, label=legend)  # Returns a list of only one Line2D
            self.lines.append(line[0])

        self.ax.set_xlim(0, self.windowSize)
        self.ax.set_ylim(self.minY, self.maxY) # Will be resized later if needed

        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1)).set_visible(self.showLegend)
        
    
    def updateFig(self, frame = 0): #frame number given by matplotlib's animation, useless here
        data = np.array(self.updateData_cb())
        self.dataX = data[0]
        self.dataY = data[1:]
        for line, Y in zip(self.lines, self.dataY):
            line.set_data(self.dataX, Y)
         
        # Default artists to be updated
        artists = []
        for a in self.lines:
            artists.append(a)
        
        # Y axis
        if self.autoResizeY:
            rangeY = (np.nanmin(self.dataY), np.nanmax(self.dataY))
            #resize only if needed
            if rangeY != self.ax.get_ylim():
                self.ax.set_ylim(rangeY)
            artists.append(self.ax.yaxis)

        #X axis
        if self.XScroll:
            self.maxX = np.max([self.windowSize, self.dataX[-1]])
            self.ax.set_xlim(self.maxX - self.windowSize, self.maxX)
            artists.append(self.ax.xaxis)

        return artists
        
   



###################################################################################
# Data Processor
# 
###################################################################################


class dataProcessor:

    def __init__(self, updateData_cb, processFuncs, outputRaw=False):
        self.updateData_cb  = updateData_cb
        self.processFuncs   = processFuncs
        self.outputRaw      = outputRaw

    def process(self):
        dataIn = np.array(self.updateData_cb())

#        print('dataIn.shape: {}'.format(dataIn.shape))
#        print('processFuncs len: {}'.format(len(self.processFuncs)))
        
        output = np.array([processor(data) for processor,data in zip(self.processFuncs, dataIn[1:])])
        
       
#        print('currentValue: {}'.format((output[:, -400-1])))

       
#         print('output.shape: {}'.format(output.shape))
        if self.outputRaw:
            a = dataIn
        else:
            a = dataIn[0]

        return np.vstack([a, output])




###################################################################################
# Test case
# 
###################################################################################




# Simple running average for now
def dataFilter(dataIn):
#    dataOut = np.convolve(dataIn, [1/5]*5, mode='same')
    dataOut = [np.NaN for _ in range(len(dataIn))] # Init the array
    averageLen = 100
    for i in range(len(dataOut) - averageLen):
        dataOut[i] = dataIn[i: i+averageLen].sum() / averageLen
    
    return dataOut





if __name__ == '__main__':
    print("Using python: " + platform.python_version())
    print("Using numpy: " + np.__version__)
    print("Using matplotlib: " + matplotlib.__version__)
    print("Serial: " + serial.__version__)


    # Serial
    acquisition = serialAcq(
                            port            = '/dev/ttyACM4',
                            XChan           = False,
                            replaceNaNs     = True,
                            bufferLength    = 500,
                        )
    acquisition.updateData()
    
    
    # Processing

    filtering = dataProcessor(
            acquisition.updateData,
            [dataFilter]*2,
            outputRaw = True)

    # Animator
    live = animator([
       {
            'dataUpdate_cb' : acquisition.updateData,
            'windowSize'    : 500,
            'showLegend'    : False,
            'labels'        : ['Poney 1', 'Poney 2'],
            'autoResizeY'   : True,
            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
            'title'         :'Raw data',
            },
        {
            'dataUpdate_cb' : filtering.process,
            'windowSize'    : 500,
            'showLegend'    : True,
            'labels'        : ['Poney 1', 'Poney 2', 'Cheval 1', 'Cheval 2'],
            'autoResizeY'   : False,
            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
            'title'         : 'Filtered data',
            }
        ])
