import matplotlib.pyplot as plt
import matplotlib
#import matplotlib.animation as animation
import numpy as np
from io import BytesIO
import serial
import time
import platform
from collections import deque

class serialAcq:

    def __init__(self, **kwargs):
        
        #TODO: Implement X axis input functionnality

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




class livePlot:

    def __init__(self, updateData_cb, ax, **kwargs):

        defaults = {
            'windowSize'    : 500,
            'nPlots'        : 2,
            'showLegend'    : True,
            'customLabels'  : ['label1', 'label2'],
            'autoResizeY'   : False,
            'minY'          : -20,
            'maxY'          : 500,
            'running'       : False,
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
        self.lines  = [ matplotlib.lines.Line2D (self.dataX, Y) for Y in self.dataY ]
        
        for line in self.lines:
            self.ax.add_line(line)
        
        self.ax.set_xlim(0, self.windowSize)
        self.ax.set_ylim(self.minY, self.maxY) # Will be resized later if needed

        # ax.xaxis.set_animated(True)
        if self.showLegend:
            self.ax.legend(self.customLabels)
    
    def updateFig(self, frame = 0): #frame number given by matplotlib's animation, useless
        data = np.array(self.updateData_cb())
        print(data)
        self.dataX = data[0]
        self.dataY = data[1:]
        for line, Y in zip(self.lines, self.dataY):
            line.set_data(self.dataX, Y)
        
        #TODO y rescaling
        self.maxX = np.max([self.windowSize, self.dataX[-1]])
        self.ax.set_xlim(self.maxX - self.windowSize, self.maxX)
        self.ax.relim()
        return self.lines#, self.ax.xaxis



# Test 
if __name__ == '__main__':
    print("Using python: " + platform.python_version())
    print("Using numpy: " + np.__version__)
    print("Using matplotlib: " + matplotlib.__version__)
    print("Serial: " + serial.__version__)

    
    #TODO: instantiate serial
    acquisition = serialAcq(XChan=False)
    acquisition.updateData()
    # print(acquisition.buffers)
    
    
    #TODO: instantiate plotter and run
    fig, ax = plt.subplots()
    plotter = livePlot(acquisition.updateData, ax)
    plotter.updateFig()    

    ani = matplotlib.animation.FuncAnimation(fig, plotter.updateFig, interval=10, blit=True) 
    

