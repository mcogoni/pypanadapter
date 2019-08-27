from rtlsdr import *
from time import sleep
import math
import numpy as np
from scipy.signal import welch, decimate
import pyqtgraph as pg
#import pyaudio
from PyQt4 import QtCore, QtGui

FS = 2.4e6 # Sampling Frequency of the RTL-SDR card (in Hz) # DON'T GO TOO LOW, QUALITY ISSUES ARISE
F_SDR = 8.8315e6 # center frequency in Hz # THIS IS FOR OLD KENWOOD RADIOS LIKE THE TS-180S (WIDE BAND IF OUTPUT)
#F_SDR = 45.0515e6 # center frequency in Hz # THIS IS FOR OLD KENWOOD RADIOS LIKE THE TS-180S (WIDE BAND IF OUTPUT)
N_AVG = 128 # averaging over how many spectra

class RTLSDR():
    def __init__(self, FS, F_SDR, signal):
        self.signal = signal
        self.sdr = RtlSdr()
        # configure device
        self.sdr.set_direct_sampling(2)
        self.sdr.sample_rate = FS
        self.sdr.center_freq = F_SDR

    def read(self):
        samples = self.sdr.read_samples(w.N_AVG*w.N_FFT)
        self.signal.emit(np.flip(samples)) # IQ inversion to correct low-high frequencies

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
        self.plotwidget1.addItem(self.waterfall)
        self.spectrum_plot = self.plotwidget2.plot()
        self.plotwidget2.setYRange(-250, -100, padding=0.)
        #self.plotwidget2.showGrid(x=True, y=True)

        pg.setConfigOptions(antialias=False)

        self.N_FFT = 2048 # FFT bins
        self.N_WIN = 1024  # How many pixels to show from the FFT (around the center)
        self.N_AVG = N_AVG
        self.fft_ratio = 2.

        self.mode = 0 # USB=0, LSB=1: defaults to USB
        self.scroll = -1
        
        self.minlev = 220
        self.maxlev = 140

        self.init_image()

        # RED-GREEN Colormap
        pos = np.array([0., 0.5, 1.])
        color = np.array([[0,0,0,255], [0,255,0,255], [255,0,0,255]], dtype=np.ubyte)

        # MATRIX Colormap
        pos = np.array([0., 1.])
        color = np.array([[0,0,0,255], [0,255,0,255]], dtype=np.ubyte)

        # BLUE-YELLOW-RED Colormap
        pos = np.array([0.,                 0.4,              1.])
        color = np.array([[0,0,90,255], [200,2020,0,255], [255,0,0,255]], dtype=np.ubyte)

        cmap = pg.ColorMap(pos, color)
        pg.colormap
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        # set colormap
        self.waterfall.setLookupTable(lut)
        self.waterfall.setLevels([self.minlev, self.maxlev])

        # setup the correct scaling for x-axis
        self.bw_hz = FS/float(self.N_FFT) * float(self.N_WIN)/1.e6/self.fft_ratio
        self.waterfall.scale(self.bw_hz,1)
        self.setLabel('bottom', 'Frequency', units='kHz')
        
        self.text_leftlim = pg.TextItem("-%.1f kHz"%(self.bw_hz*self.N_WIN/2.))
        self.text_leftlim.setParentItem(self.waterfall)
        self.plotwidget1.addItem(self.text_leftlim)
        self.text_leftlim.setPos(0, 0)

        self.text_rightlim = pg.TextItem("+%.1f kHz"%(self.bw_hz*self.N_WIN/2.))
        self.text_rightlim.setParentItem(self.waterfall)
        self.plotwidget1.addItem(self.text_rightlim)
        self.text_rightlim.setPos(self.bw_hz*(self.N_WIN-64), 0)

        self.plotwidget1.hideAxis("left")
        self.plotwidget1.hideAxis("bottom")
        self.plotwidget2.hideAxis("left")
        self.plotwidget2.hideAxis("bottom")

        self.hideAxis("top")
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.hideAxis("right")

        self.win.show()

    def init_image(self):
        self.img_array = 250*np.ones((self.N_WIN/4, self.N_WIN))
        # Plot the grid
        for x in [0, self.N_WIN/2, self.N_WIN-1]:
            if x==0 or x==self.N_WIN-1:
                #pass
                self.img_array[:,x] = 0
            else:
                #pass
                self.img_array[:,x] = 0


    def init_ui(self):
        self.win = QtGui.QWidget()
        self.win.setWindowTitle('PEPYSCOPE - IS0KYB')
        
        vbox = QtGui.QVBoxLayout()
        #self.setLayout(vbox)

        self.plotwidget1 = pg.PlotWidget()
        vbox.addWidget(self.plotwidget1)

        self.plotwidget2 = pg.PlotWidget()
        vbox.addWidget(self.plotwidget2)

        hbox = QtGui.QHBoxLayout()

        self.zoominbutton = QtGui.QPushButton("ZOOM IN")
        self.zoomoutbutton = QtGui.QPushButton("ZOOM OUT")
        self.avg_increase_button = QtGui.QPushButton("AVG +")
        self.avg_decrease_button = QtGui.QPushButton("AVG -")
        self.modechange = QtGui.QPushButton("USB")
        self.invertscroll = QtGui.QPushButton("Scroll")
        self.autolevel = QtGui.QPushButton("Auto Levels")

        hbox.addWidget(self.zoominbutton)
        hbox.addWidget(self.zoomoutbutton)
        hbox.addWidget(self.modechange)
        hbox.addWidget(self.invertscroll)
        hbox.addStretch()

        hbox.addWidget(self.autolevel)
        hbox.addWidget(self.avg_increase_button)
        hbox.addWidget(self.avg_decrease_button)

        #vbox.addStretch()
        vbox.addLayout(hbox)
        self.win.setLayout(vbox)

        self.win.setGeometry(10, 10, 1024, 512)
        self.win.show()

    def qt_connections(self):
        self.zoominbutton.clicked.connect(self.on_zoominbutton_clicked)
        self.zoomoutbutton.clicked.connect(self.on_zoomoutbutton_clicked)
        self.modechange.clicked.connect(self.on_modechange_clicked)
        self.invertscroll.clicked.connect(self.on_invertscroll_clicked)
        self.avg_increase_button.clicked.connect(self.on_avg_increase_clicked)
        self.avg_decrease_button.clicked.connect(self.on_avg_decrease_clicked)
        self.autolevel.clicked.connect(self.on_autolevel_clicked)

    def on_avg_increase_clicked(self):
        if self.N_AVG<512:
            self.N_AVG *= 2
        print self.N_AVG

    def on_avg_decrease_clicked(self):
        if self.N_AVG>1:
            self.N_AVG /= 2
        print self.N_AVG


    def on_modechange_clicked(self):
        if self.mode == 0:
            self.modechange.setText("LSB")
        elif self.mode == 1:
            self.modechange.setText("USB")
        self.mode += 1
        if self.mode>1:
            self.mode = 0


    def on_autolevel_clicked(self):
        tmp_array = np.copy(self.img_array[self.img_array>0])
        tmp_array = tmp_array[tmp_array<250]
        tmp_array = tmp_array[:]
        print tmp_array.shape

        self.minminlev = np.percentile(tmp_array, 99)
        self.minlev = np.percentile(tmp_array, 80)
        self.maxlev = np.percentile(tmp_array, 0.3)
        print self.minlev, self.maxlev
        self.waterfall.setLevels([self.minlev, self.maxlev])

        self.plotwidget2.setYRange(-self.minminlev, -self.maxlev, padding=0.3)



    def on_invertscroll_clicked(self):
        self.scroll *= -1
        self.init_image()

    def on_zoominbutton_clicked(self):
        if self.fft_ratio<512:
            self.fft_ratio *= 2
        #self.waterfall.scale(0.5,1)

    
    def on_zoomoutbutton_clicked(self):
        if self.fft_ratio>1:
            self.fft_ratio /= 2
        #self.waterfall.scale(2.0,1)
 

    def zoomfft(self, x, ratio = 1):
        f_demod = 1.
        t_total = (1/FS) * self.N_FFT * self.N_AVG
        t = np.arange(0, t_total, 1 / FS)
        lo = 2**.5 * np.exp(-2j*np.pi*f_demod * t) # local oscillator
        x_mix = x*lo
        
        power2 = int(np.log2(ratio))
        for mult in range(power2):
            x_mix = decimate(x_mix, 2) # mix and decimate

        return x_mix 
    

    def update(self, chunk):
        self.bw_hz = FS/float(self.N_FFT) * float(self.N_WIN)
        self.win.setWindowTitle('PEPYSCOPE - IS0KYB - N_FFT: %d, BW: %.1f kHz' % (self.N_FFT, self.bw_hz/1000./self.fft_ratio))

        if self.fft_ratio>1:
            chunk = self.zoomfft(chunk, self.fft_ratio)

        sample_freq, spec = welch(chunk, FS, window="hamming", nperseg=self.N_FFT,  nfft=self.N_FFT)
        spec = np.roll(spec, self.N_FFT/2, 0)[self.N_FFT/2-self.N_WIN/2:self.N_FFT/2+self.N_WIN/2]
        
        # get magnitude 
        psd = abs(spec)
        # convert to dB scale
        psd = -20 * np.log10(psd)

        # Plot the grid
        for x in [0, self.N_WIN/2, self.N_WIN-1]:
            #pass
            psd[x] = 0            

        # roll down one and replace leading edge with new data
        self.img_array[-1:] = psd
        self.img_array = np.roll(self.img_array, -1*self.scroll, 0)

        for i, x in enumerate(range(0, self.N_WIN-1, ((self.N_WIN)/10))):
            if i!=5 and i!=10:
                if self.scroll>0:
                    for y in range(5,15):
                        #pass
                        self.img_array[y,x] = 0
                elif self.scroll<0:
                    for y in range(-10,-2):
                        #pass
                        self.img_array[y,x] = 0

        #self.spectrum_plot.plot()

        self.waterfall.setImage(self.img_array.T, autoLevels=False, opacity = 1.0, autoDownsample=True)

        self.text_leftlim.setPos(0, 0)
        self.text_leftlim.setText(text="-%.1f kHz"%(self.bw_hz/2000./self.fft_ratio))
        #self.text_rightlim.setPos(self.bw_hz*1000, 0)
        self.text_rightlim.setText(text="+%.1f kHz"%(self.bw_hz/2000./self.fft_ratio))

        self.spectrum_plot.setData(np.arange(0,psd.shape[0]), -psd, pen="g")

        #self.plotwidget2.plot(x=[0,0], y=[-240,0], pen=pg.mkPen('r', width=1))
        #self.plotwidget2.plot(x=[self.N_WIN/2, self.N_WIN/2], y=[-240,0], pen=pg.mkPen('r', width=1))
        #self.plotwidget2.plot(x=[self.N_WIN-1, self.N_WIN-1], y=[-240,0], pen=pg.mkPen('r', width=1))



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

    t = QtCore.QTimer()
    t.timeout.connect(update_mode)
    t.timeout.connect(rtl.read)
    t.start(50) # max theoretical refresh rate 100 fps

    app.exec_()
    rtl.close()
