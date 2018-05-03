import matplotlib.pyplot as plt
import matplotlib
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
            'port'          : '/dev/ttyACM1',
            'baudrate'      : 9600,
            'bufferLength'  : 5,
            'channelNbr'    : 2, 
            'XChan'         : False,
            'XStep'         : 1,
            'replaceNaNs'   : False,
        }
        
        # Use kwargs to setup problem, use defaults if not given
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

        return




class livePlot:

    def __init__(self, ax, **kwargs):

        defaults = {
            'updateData_cb' : None,
            'windowSize'    : 500,
            'nPlots'        : 2,
            'CustomLabels'  : ['label1', 'label2'],
            'autoResizeY'   : False,
            'minY'          : 0,
            'maxY'          : 500,
            'running'       : False,
        }
        
        # Use kwargsif available, defaults if not given
        for key in defaults:
            self.__setattr__(key, kwargs.pop(key, defaults[key]))

        # Warn if unexpected kwargs were given
        for key in kwargs:
            kwargWarn = 'kwarg "{} = {}" is unknown'.format(key, kwargs[key])
            warnings.warn(kwargWarn)

        # Init plotting
        self.ax     = ax
        self.maxX   = self.windowSize
        self.dataX  = [0]
        self.dataY  = [ [0] for _ in range(self.nPlots)]
        self.lines  = [ 
    
    def update_fig():
        #TODO
#             # update data
#             for i in range(0, nData):
#               if x.size > windowSize:
#                 lines[i].set_ydata(y[y[:,i].size-windowSize:y[:,i].size,i])
#                 lines[i].set_xdata(x[x.size-windowSize:x.size])
#               else:
#                 lines[i].set_ydata(y[:,i])
#                 lines[i].set_xdata(x)     
 
        return



# Test case
if __name__ == '__main__':
    print("Using python: " + platform.python_version())
    print("Using numpi: " + np.__version__)
    print("Using matplotlib: " + matplotlib.__version__)
    print("Serial: " + serial.__version__)

    
    #TODO: instantiate serial
    
    acquisition = serialAcq()
    time.sleep(1)
    acquisition.updateData()
    print(acquisition.buffers)
    #TODO: instantiate plotter and run


#ser = serial.Serial(serialPort, baud)
#
#x = np.array([0.0])
#y = np.zeros(shape=(1,nData))
#lines = []
#ax = []
#
#intX = int(firstInputAsX)
#
#
#
#if firstInputAsX:
#  dataNames = 'x'
#else:
#  dataNames = 'y0'
#    
#    
#dNames = [dataNames]
#for i in range(int(not firstInputAsX), nData):
#  dataNames = dataNames + ', y' + str(i) 
#  dNames = np.append(dNames, 'y' + str(i))
#
#
#
## dataTypes for parsing serial line
#dataTypes = []
#for i in range(0, intX+nData): # 1+ because of x input
#  dataTypes = np.append(dataTypes, np.dtype(np.float))
#
#
## make figure
#plt.ion()
#fig = plt.figure()
#
#ax = fig.add_subplot(111)
#ax.set_autoscale_on(True)
#ax.autoscale_view(True,True,True)
#
#
## add lines to plot
#for i in range(0, nData):
#  lines = np.append(lines, ax.plot(x, y[:,i]))
#
#
## add labels
#if useCustomLabels:
#  ax.legend(customLabels, bbox_to_anchor=(0,1.1), loc="upper left", ncol=nData)
#else:
#  ax.legend(dNames[intX:len(dNames)],bbox_to_anchor=(0,1.1), loc="upper left", ncol=nData)
#
#
#fig.canvas.draw()
#
#background = fig.canvas.copy_from_bbox(ax.bbox)
#lastDisplay = time.time()
#
#running = True
#while running:
#  
#  time.sleep(0.001)
#
#
#  
#  start = time.time()
#  
#  
#  # read line on serial

#  end = time.time()
#
#  
#  lastDisplay = time.time()
#  
#  
#  ax.autoscale_view(True,x.size < windowSize,autoResizeY)
#  if not autoResizeY:
#    ax.set_ylim(minY, maxY)
#    
#  if x.size < windowSize :
#    if firstInputAsX:
#      ax.set_xlim(0, dt*windowSize)
#    else:
#      ax.set_xlim(0, windowSize)
#      
#  else:
#    ax.set_xlim(x[x.size-windowSize], x[x.size-1], True, True)
#  
#  
#  ax.relim()
##DEBUG
#  relim = time.time()
#
#  
#  #fig.canvas.draw()
#  fig.canvas.restore_region(background)
#  for points in lines:
#    ax.draw_artist(points)
#  fig.canvas.blit(ax.bbox)
#  fig.canvas.flush_events()
#
##DEBUG
#  final = time.time()
#  print('serial: {}\t relim: {}\t draw: {}\t total: {}\t fps: {}'.format(end - start, relim - end, final - relim, final - start, 1/(final - start)))
#  
#  #print('fps: {}'.format(1/(final - start)))
#
#
#
#
#
#
#
#"""
#============
#Oscilloscope
#============
#
#Emulates an oscilloscope.
#"""
#import numpy as np
#from matplotlib.lines import Line2D
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation
#
#
#class Scope(object):
#    def __init__(self, ax, maxt=2, dt=0.02):
#        self.ax = ax
#        self.dt = dt
#        self.maxt = maxt
#        self.tdata = [0]
#        self.ydata = [0]
#        self.line = Line2D(self.tdata, self.ydata)
#        self.ax.add_line(self.line)
#        self.ax.set_ylim(-.1, 1.1)
#        self.ax.set_xlim(0, self.maxt)
#
#    def update(self, y):
#        lastt = self.tdata[-1]
#        if lastt > self.tdata[0] + self.maxt:  # reset the arrays
#            self.tdata = [self.tdata[-1]]
#            self.ydata = [self.ydata[-1]]
#            self.ax.set_xlim(self.tdata[0], self.tdata[0] + self.maxt)
#            self.ax.figure.canvas.draw()
#
#        t = self.tdata[-1] + self.dt
#        self.tdata.append(t)
#        self.ydata.append(y)
#        self.line.set_data(self.tdata, self.ydata)
#        return self.line,
#
#
#def emitter(p=0.03):
#    'return a random value with probability p, else 0'
#    while True:
#        v = np.random.rand(1)
#        if v > p:
#            yield 0.
#        else:
#            yield np.random.rand(1)
#
## Fixing random state for reproducibility
#np.random.seed(19680801)
#
#
#fig, ax = plt.subplots()
#scope = Scope(ax)
#
## pass a generator in "emitter" to produce data for the update func
#ani = animation.FuncAnimation(fig, scope.update, emitter, interval=10,
#                              blit=True)
#
#plt.show()
#
