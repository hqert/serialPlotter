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



###################################################################################
# Serial acquisition
#
# TODO: implement X axis input functionnality (XY plots?)
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
# an associated plotter object to update various parts of it
#
# TODO: Allow multiple subplots
# TODO: Allow scrolling to be controlled
###################################################################################

class animator:

    def __init__(self, updateData_cb, **kwargs):

        self.fig, self.ax = plt.subplots(1, 1)
        
        self.ax.grid(which='both')
       
        # Plot and run
        self.plotter = livePlot(updateData_cb, self.ax,
                            windowSize  = 500,
    #                        maxY        = 100, 
    #                        minY        = 50,
    #                        autoResizeY = True,
                            XScroll     = True,
    #                        running     = False,
                            nPlots      = 4,
                            labels      = ['1', '2', 'f1', 'f2']
                        )

    
        self.anim = matplotlib.animation.FuncAnimation(self.fig, self.plotter.updateFig, interval = 1/24, blit=True) 
        #Hack the drawing method to allow blitting of objects outside the axes bbox
        matplotlib.animation.Animation._blit_draw = self._blit_draw

#        self.anim.event_source.stop()
#        if not self.running:
#            print('stop!')
#            self.anim.event_source.stop()

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
# TODO: get animation outside of plotter, which should only update 
#       data in the artists of its ax
# TODO: Allow scrolling to be controlled (to be moved to animator class)
###################################################################################

class livePlot:

    def __init__(self, updateData_cb, ax, **kwargs):

        defaults = {
            'windowSize'    : 500 ,
            'nPlots'        : 2,
            'showLegend'    : True,
            'labels'        : ['poney 1', 'poney 2'],
            'autoResizeY'   : False,
            'XScroll'       : True,
            'minY'          : -20,
            'maxY'          : 500,
#            'running'       : False,
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
        self.maxX   = self.windowSize
        self.dataX  = [0]
        self.dataY  = [ [0] for _ in range(self.nPlots) ]
        
        #TODO make label length not matter
        self.lines = []
        for Y, legend in zip(self.dataY, self.labels):
            line = ax.plot(self.dataX, Y, label=legend)  # Returns a list of only one Line2D
            self.lines.append(line[0])

        self.ax.set_xlim(0, self.windowSize)
        self.ax.set_ylim(self.minY, self.maxY) # Will be resized later if needed

        self.ax.legend().set_visible(self.showLegend)
        
    
    def updateFig(self, frame = 0): #frame number given by matplotlib's animation, useless
        data = np.array(self.updateData_cb())
#        print(data)
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

    def __init__(self, updateData_cb, processFuncs, **kwargs):
        self.updateData_cb  = updateData_cb
        self.processFuncs    = processFuncs

    def process(self):
        dataIn = np.array(self.updateData_cb())
        
        output = [processor(dataIn) for processor in selfprocessFuncs] 

        return output






# Test 
if __name__ == '__main__':
    print("Using python: " + platform.python_version())
    print("Using numpy: " + np.__version__)
    print("Using matplotlib: " + matplotlib.__version__)
    print("Serial: " + serial.__version__)


    # Serial
    acquisition = serialAcq(
                            port            = '/dev/ttyACM5',
                            XChan           = False,
                            replaceNaNs     = True,
                            bufferLength    = 500,
                        )
    acquisition.updateData()
    
    
    # Processing

#    processor = dataProcessor(acquisition.updateData, )

    # Animator
    live = animator(acquisition.updateData)
