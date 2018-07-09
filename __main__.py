import sys, os, warnings
from datetime import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt
import numpy as np

class GraphWindow(QtWidgets.QWidget):

    def __init__(self):
        super(GraphWindow, self).__init__()

        #Setup Globals
        self.modTimesUnix = []
        self.modTimes = []
        self.frameNums = []
        self.frameNumsTotal = 200
        self.polyfits = {}
        self.timeFinished = None

        self.initUI()

    def initUI(self):
        self.setGeometry(600,300,1000,600)
        self.center()
        self.setWindowTitle('Date Modified Plotting')

        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        # 1.-2. Row: Plotting
        self.fig = plt.figure(figsize=(15,5))
        self.canv = FigureCanvas(self.fig)
        plt.style.use('seaborn-whitegrid')
        self.toolbar = NavigationToolbar(self.canv, self)
        grid.addWidget(self.canv, 1,0,1,4)
        grid.addWidget(self.toolbar, 0,0,1,4)

        # 3. Row: Reading Files
        btn_loadFiles = QtWidgets.QPushButton('Load Files', self)
        btn_loadFiles.resize(btn_loadFiles.sizeHint())
        btn_loadFiles.clicked.connect(self.load_files)
        grid.addWidget(btn_loadFiles,2,0,1,1)

        self.lab_dispFilepath = QtWidgets.QLabel("No Files Selected", self)
        self.lab_dispFilepath.resize(self.lab_dispFilepath.sizeHint())
        grid.addWidget(self.lab_dispFilepath,2,1,1,3)

        subgrid_lvls = QtWidgets.QGridLayout()

        self.chk_lvl1 = QtWidgets.QCheckBox("1", self)
        self.chk_lvl1.resize(self.chk_lvl1.sizeHint())
        self.chk_lvl1.stateChanged.connect(self.update_deg1)
        subgrid_lvls.addWidget(self.chk_lvl1,0,0)

        self.chk_lvl2 = QtWidgets.QCheckBox("2", self)
        self.chk_lvl2.resize(self.chk_lvl2.sizeHint())
        self.chk_lvl2.stateChanged.connect(self.update_deg2)
        subgrid_lvls.addWidget(self.chk_lvl2,0,1)

        self.chk_lvl3 = QtWidgets.QCheckBox("3", self)
        self.chk_lvl3.resize(self.chk_lvl3.sizeHint())
        self.chk_lvl3.stateChanged.connect(self.update_deg3)
        subgrid_lvls.addWidget(self.chk_lvl3,0,2)

        self.chk_lvl4 = QtWidgets.QCheckBox("4", self)
        self.chk_lvl4.resize(self.chk_lvl4.sizeHint())
        self.chk_lvl4.stateChanged.connect(self.update_deg4)
        subgrid_lvls.addWidget(self.chk_lvl4,1,0)

        self.chk_lvl5 = QtWidgets.QCheckBox("5", self)
        self.chk_lvl5.resize(self.chk_lvl5.sizeHint())
        self.chk_lvl5.stateChanged.connect(self.update_deg5)
        subgrid_lvls.addWidget(self.chk_lvl5,1,1)

        self.chk_lvl6 = QtWidgets.QCheckBox("6", self)
        self.chk_lvl6.resize(self.chk_lvl6.sizeHint())
        self.chk_lvl6.stateChanged.connect(self.update_deg6)
        subgrid_lvls.addWidget(self.chk_lvl6,1,2)

        grid.addLayout(subgrid_lvls,3,0,1,1)

        subgrid_frames = QtWidgets.QGridLayout()

        spi_numFrames = QtWidgets.QSpinBox(self, minimum = 1, maximum = 1000000, value = 200)
        spi_numFrames.resize(spi_numFrames.sizeHint())
        spi_numFrames.valueChanged.connect(self.update_framenumstotal)
        subgrid_frames.addWidget(spi_numFrames,0,0,1,1)

        spi_in = QtWidgets.QSpinBox(self, minimum = 0, maximum = 1000000, value = 0)
        spi_in.resize(spi_in.sizeHint())
        subgrid_frames.addWidget(spi_in, 1,0,1,1)

        spi_out = QtWidgets.QSpinBox(self, minimum = 0, maximum = 1000000, value = 200)
        spi_out.resize(spi_out.sizeHint())
        subgrid_frames.addWidget(spi_out, 2,0,1,1)

        lab_numFrames = QtWidgets.QLabel("Total Number of Frames", self)
        lab_numFrames.resize(lab_numFrames.sizeHint())
        subgrid_frames.addWidget(lab_numFrames, 0,1,1,2)

        lab_in = QtWidgets.QLabel("First Frame", self)
        lab_in.resize(lab_in.sizeHint())
        subgrid_frames.addWidget(lab_in, 1,1,1,2)

        lab_out = QtWidgets.QLabel("Last Frame", self)
        lab_out.resize(lab_out.sizeHint())
        subgrid_frames.addWidget(lab_out, 2,1,1,2)

        grid.addLayout(subgrid_frames,4,0,1,1)

        lab_infobox = QtWidgets.QLabel("Info", self)
        grid.addWidget(lab_infobox,2,1,2,2)

        self.show()

    def load_files(self):
        filepaths = self.get_filepaths()
        if filepaths != None:
            self.lab_dispFilepath.setText(str(filepaths[0]))
            self.calc_modtimes(filepaths)
            self.polyfits.clear()
            self.chk_lvl1.setChecked(False)
            self.chk_lvl2.setChecked(False)
            self.chk_lvl3.setChecked(False)
            self.chk_lvl4.setChecked(False)
            self.chk_lvl5.setChecked(False)
            self.chk_lvl6.setChecked(False)
            self.update_plot()
        else:
            pass

    def get_filepaths(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;Python Files (*.py)", options=options)
        if files:
            return(files)
        else:
            return(None)

    def calc_modtimes(self, filepaths):
        self.frameNums = range(len(filepaths))
        self.modTimesUnix = []
        self.modTimes = []

        for filepath in filepaths:
            filepath.replace('/', '\\')
            timeUnix = os.path.getmtime(filepath)
            time = datetime.fromtimestamp(timeUnix)
            self.modTimesUnix.append(timeUnix)
            self.modTimes.append(time)

        self.modTimesUnix.sort()
        self.modTimes.sort()

    def create_polyfit(self, deg):
        if len(self.frameNums) <= 0 or len(self.frameNums) != len(self.modTimesUnix):
            print("Not computable")
            return None

        x = np.array(self.frameNums)
        y = np.array(self.modTimesUnix)
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                p1 = np.polyfit(x,y,deg)
            except np.RankWarning:
                print("Not enough data")
                return None

        polyfitTimesUnix = np.polyval(p1,range(self.frameNumsTotal))
        polyfitTimes = []
        for timeU in polyfitTimesUnix:
            polyfitTimes.append(datetime.fromtimestamp(timeU))
        self.polyfits.update({deg: polyfitTimes})
        #self.timeFinished = datetime.fromtimestamp(int(polyfitTimesUnix[self.frameNumsTotal-1]))

    def update_plot(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111, label='babo')
        ax.set(xlabel='Frame', ylabel='Creation Date', title='Render Progress')

        if len(self.polyfits) > 0:
            for deg, timeList in self.polyfits.items():
                if len(timeList) > 0:
                    ax.plot(range(len(timeList)),timeList, label="Deg.:"+str(deg))
                    #ax.text(self.frameNumsTotal-1, self.timeFinished, "Finished approx.: " + str(self.timeFinished), fontsize=10, horizontalalignment="right")

        if len(self.modTimes) > 0 and len(self.modTimes)==len(self.frameNums):
            ax.plot(self.frameNums, self.modTimes, '+', label='data')

        ax.legend(frameon=True)

        self.canv.draw()

    def update_deg1(self):
        if self.chk_lvl1.isChecked():
            self.create_polyfit(1)
        else:
            self.polyfits.pop(1, None)
        self.update_plot()

    def update_deg2(self):
        if self.chk_lvl2.isChecked():
            self.create_polyfit(2)
        else:
            self.polyfits.pop(2, None)
        self.update_plot()

    def update_deg3(self):
        if self.chk_lvl3.isChecked():
            self.create_polyfit(3)
        else:
            self.polyfits.pop(3, None)
        self.update_plot()

    def update_deg4(self):
        if self.chk_lvl4.isChecked():
            self.create_polyfit(4)
        else:
            self.polyfits.pop(4, None)
        self.update_plot()

    def update_deg5(self):
        if self.chk_lvl5.isChecked():
            self.create_polyfit(5)
        else:
            self.polyfits.pop(5, None)
        self.update_plot()

    def update_deg6(self):
        if self.chk_lvl6.isChecked():
            self.create_polyfit(6)
        else:
            self.polyfits.pop(6, None)
        self.update_plot()

    def update_framenumstotal(self, val):
        self.frameNumsTotal = val
        self.polyfits.clear()
        degs = []
        if self.chk_lvl1.isChecked(): degs.append(1)
        if self.chk_lvl2.isChecked(): degs.append(2)
        if self.chk_lvl3.isChecked(): degs.append(3)
        if self.chk_lvl4.isChecked(): degs.append(4)
        if self.chk_lvl5.isChecked(): degs.append(5)
        if self.chk_lvl6.isChecked(): degs.append(6)
        for deg in degs:
            self.create_polyfit(deg)
        self.update_plot()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())



def main():
    app = QtWidgets.QApplication(sys.argv)
    w = GraphWindow()
    app.exec_()

if __name__ == '__main__' :
    main()
