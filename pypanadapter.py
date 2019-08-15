from rtlsdr import *
from time import sleep
import numpy as np
from scipy.signal import welch
import pyqtgraph as pg
import pyaudio
from PyQt4 import QtCore, QtGui

FS = 1.0e6 # Sampling Frequency of the RTL-SDR card (in Hz) # DON'T GO TOO LOW, QUALITY ISSUES ARISE
F_SDR = 8.8315e6 # center frequency in Hz # THIS IS FOR OLD KENWOOD RADIOS LIKE THE TS-180S (WIDE BAND IF OUTPUT)
N_AVG = 1 # averaging over how many spectra

class RTLSDR():
    def __init__(self, signal):
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

        self.show()

    def init_ui(self):
        self.setWindowTitle('WATERFALL IS0KYB')
        hbox = QtGui.QVBoxLayout()
        self.setLayout(hbox)

        self.plotwidget1 = pg.PlotWidget()
        hbox.addWidget(self.plotwidget1)

        self.increasebutton = QtGui.QPushButton("ZOOM IN")
        self.decreasebutton = QtGui.QPushButton("ZOOM OUT")

        hbox.addWidget(self.increasebutton)
        hbox.addWidget(self.decreasebutton)

        self.setGeometry(10, 10, 1400, 900)
        self.show()

    def qt_connections(self):
        self.increasebutton.clicked.connect(self.on_increasebutton_clicked)
        self.decreasebutton.clicked.connect(self.on_decreasebutton_clicked)

    def on_increasebutton_clicked(self):
        self.N_FFT *= 2
        #self.waterfall.scale(0.5,1)

    
    def on_decreasebutton_clicked(self):
        self.N_FFT /= 2
        #self.waterfall.scale(2.0,1)
 

    def update(self, chunk):
        self.bw_hz = FS/float(self.N_FFT) * float(self.N_WIN)
        self.setWindowTitle('WATERFALL IS0KYB - N_FFT: %d, BW: %.1f kHz' % (self.N_FFT, self.bw_hz/1000.))

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

        self.waterfall.setImage(self.img_array.T, autoLevels=False, opacity = 1.0, autoDownsample=True)

        self.text_leftlim.setPos(0, 0)
        self.text_leftlim.setText(text="%.1f kHz"%(-self.bw_hz/2000.))
        #self.text_rightlim.setPos(self.bw_hz*1000, 0)
        self.text_rightlim.setText(text="%.1f kHz"%(self.bw_hz/2000.))


if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = SpectrogramWidget()
    w.read_collected.connect(w.update)

    mic = RTLSDR(w.read_collected)

    # time (seconds) between reads
    t = QtCore.QTimer()
    t.timeout.connect(mic.read)
    t.start(0.1) #QTimer takes ms

    app.exec_()
    mic.close()
