from rtlsdr import *
from time import sleep
import math
import numpy as np
from scipy.signal import welch
import pyqtgraph as pg
import pyaudio
from PyQt4 import QtCore, QtGui

FS = 1.0e6 # Sampling Frequency of the RTL-SDR card (in Hz) # DON'T GO TOO LOW, QUALITY ISSUES ARISE
F_SDR = 8.8315e6 # center frequency in Hz # THIS IS FOR OLD KENWOOD RADIOS LIKE THE TS-180S (WIDE BAND IF OUTPUT)
N_AVG = 1 # averaging over how many spectra

class RTLSDR():
    def __init__(self, FS, F_SDR, signal):
        self.signal = signal
        self.sdr = RtlSdr()
        # configure device
        self.sdr.set_direct_sampling(2)
        self.sdr.sample_rate = FS
        self.sdr.center_freq = F_SDR

    def read(self):
        samples = self.sdr.read_samples(N_AVG*w.N_FFT)
        self.signal.emit(np.flip(samples))

    def close(self):
        self.sdr.close()
    
    def changef(self, F_SDR):
        self.sdr.center_freq = F_SDR


class SpectrogramWidget(pg.PlotWidget):
    read_collected = QtCore.pyqtSignal(np.ndarray)
    def __init__(self):
        super(SpectrogramWidget, self).__init__()

        self.init_ui()
        self.qt_connections()
        self.waterfall = pg.ImageItem()
        self.spectrum = pg.PlotItem()
        self.plotwidget1.addItem(self.waterfall)
    
        self.N_FFT = 16384 # FFT bins
        self.N_WIN = 1024  # How many pixels to show from the FFT (around the center)
        
        self.mode = 0 # USB=0, LSB=1: defaults to USB

        self.img_array = 250*np.ones((self.N_WIN, self.N_WIN))
        # Plot the grid
        for x in [0, self.N_WIN/2, self.N_WIN-1]:
            if x==0 or x==self.N_WIN-1:
                self.img_array[:,x] = 0
            else:
                self.img_array[:,x] = 0


        # MATRIX Colormap
        pos = np.array([0., 0.5, 1.])
        color = np.array([[0,0,0,255], [0,255,0,255], [255,0,0,255]], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        pg.colormap
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        # set colormap
        self.waterfall.setLookupTable(lut)
        self.waterfall.setLevels([220,140]) # this should be user settable!

        # setup the correct scaling for x-axis
        self.bw_hz = FS/float(self.N_FFT) * float(self.N_WIN)/1.e6
        self.waterfall.scale(self.bw_hz,1)
        self.setLabel('bottom', 'Frequency', units='kHz')
        
        self.text_leftlim = pg.TextItem("%.1f kHz"%(-self.bw_hz*self.N_WIN/2.))
        self.text_leftlim.setParentItem(self.waterfall)
        self.plotwidget1.addItem(self.text_leftlim)
        self.text_leftlim.setPos(0, 0)

        self.text_rightlim = pg.TextItem("%.1f kHz"%(self.bw_hz*self.N_WIN/2.))
        self.text_rightlim.setParentItem(self.waterfall)
        self.plotwidget1.addItem(self.text_rightlim)
        self.text_rightlim.setPos(self.bw_hz*(self.N_WIN-1), 0)

        self.plotwidget1.hideAxis("left")
        self.plotwidget1.hideAxis("bottom")

        self.hideAxis("top")
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.hideAxis("right")

        self.win.show()

    def init_ui(self):
        self.win = QtGui.QWidget()
        self.win.setWindowTitle('WATERFALL IS0KYB')
        
        vbox = QtGui.QVBoxLayout()
        #self.setLayout(vbox)

        self.plotwidget1 = pg.PlotWidget()
        vbox.addWidget(self.plotwidget1)

        hbox = QtGui.QHBoxLayout()

        self.zoominbutton = QtGui.QPushButton("ZOOM IN")
        self.zoomoutbutton = QtGui.QPushButton("ZOOM OUT")
        self.modechange = QtGui.QPushButton("USB")
        self.button4 = QtGui.QPushButton("")

        hbox.addWidget(self.zoominbutton)
        hbox.addWidget(self.zoomoutbutton)
        hbox.addWidget(self.modechange)
        hbox.addWidget(self.button4)
        #vbox.addStretch()
        vbox.addLayout(hbox)
        self.win.setLayout(vbox)

        self.win.setGeometry(10, 10, 1400, 900)
        self.win.show()

    def qt_connections(self):
        self.zoominbutton.clicked.connect(self.on_zoominbutton_clicked)
        self.zoomoutbutton.clicked.connect(self.on_zoomoutbutton_clicked)
        self.modechange.clicked.connect(self.on_modechange_clicked)

    def on_modechange_clicked(self):
        if self.mode == 0:
            self.modechange.setText("LSB")
        elif self.mode == 1:
            self.modechange.setText("USB")
        self.mode += 1
        if self.mode>1:
            self.mode = 0



    def on_zoominbutton_clicked(self):
        if self.N_FFT<400000:
            self.N_FFT *= 2
        #self.waterfall.scale(0.5,1)

    
    def on_zoomoutbutton_clicked(self):
        if self.N_FFT>1024:
            self.N_FFT /= 2
        #self.waterfall.scale(2.0,1)
 

    def update(self, chunk):
        self.bw_hz = FS/float(self.N_FFT) * float(self.N_WIN)
        self.win.setWindowTitle('WATERFALL IS0KYB - N_FFT: %d, BW: %.1f kHz' % (self.N_FFT, self.bw_hz/1000.))

        sample_freq, spec = welch(chunk, FS, window="hamming", nperseg=self.N_FFT,  nfft=self.N_FFT)
        spec = np.roll(spec, self.N_FFT/2, 0)[self.N_FFT/2-self.N_WIN/2:self.N_FFT/2+self.N_WIN/2]
        
        # get magnitude 
        psd = abs(spec)
        # convert to dB scale
        psd = -20 * np.log10(psd)

        # Plot the grid
        for x in [0, self.N_WIN/2, self.N_WIN-1]:
            if x==0 or x==self.N_WIN-1:
                psd[x] = 0
            else:
                psd[x] = 0            

        # roll down one and replace leading edge with new data
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = psd

        for i, x in enumerate(range(0, self.N_WIN-1, ((self.N_WIN)/10))):
            if i!=5 and i!=10:
                for y in range(0,10):
                    self.img_array[y,x] = 0


        self.waterfall.setImage(self.img_array.T, autoLevels=False, opacity = 1.0, autoDownsample=True)

        self.text_leftlim.setPos(0, 0)
        self.text_leftlim.setText(text="%.1f kHz"%(-self.bw_hz/2000.))
        #self.text_rightlim.setPos(self.bw_hz*1000, 0)
        self.text_rightlim.setText(text="%.1f kHz"%(self.bw_hz/2000.))



def update_mode():
    global old_mode
    global rtl
    if w.mode!=old_mode:
        sign = (w.mode-old_mode)
        sign /= math.fabs(sign)
        if sign<0:
            sign = 0
        rtl.changef(F_SDR-sign*3000)
        old_mode = w.mode
        return rtl

if __name__ == '__main__':
    old_mode = 0
    app = QtGui.QApplication([])
    w = SpectrogramWidget()
    w.read_collected.connect(w.update)

    rtl = RTLSDR(FS, F_SDR, w.read_collected)

    # time (seconds) between reads
    t = QtCore.QTimer()
    t.timeout.connect(update_mode)
    t.timeout.connect(rtl.read)
    t.start(0.1) #QTimer takes ms

    app.exec_()
    rtl.close()
