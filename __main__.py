import sys
import os
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
        self.polylevel = 2
        self.polyfitTimes = []
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

        chk_lvl1 = QtWidgets.QCheckBox("1", self)
        chk_lvl1.resize(chk_lvl1.sizeHint())
        subgrid_lvls.addWidget(chk_lvl1,0,0)

        chk_lvl2 = QtWidgets.QCheckBox("2", self)
        chk_lvl2.resize(chk_lvl2.sizeHint())
        subgrid_lvls.addWidget(chk_lvl2,0,1)

        chk_lvl3 = QtWidgets.QCheckBox("3", self)
        chk_lvl3.resize(chk_lvl3.sizeHint())
        subgrid_lvls.addWidget(chk_lvl3,0,2)

        chk_lvl4 = QtWidgets.QCheckBox("4", self)
        chk_lvl4.resize(chk_lvl4.sizeHint())
        subgrid_lvls.addWidget(chk_lvl4,1,0)

        chk_lvl5 = QtWidgets.QCheckBox("5", self)
        chk_lvl5.resize(chk_lvl5.sizeHint())
        subgrid_lvls.addWidget(chk_lvl5,1,1)

        chk_lvl6 = QtWidgets.QCheckBox("6", self)
        chk_lvl6.resize(chk_lvl6.sizeHint())
        subgrid_lvls.addWidget(chk_lvl6,1,2)

        grid.addLayout(subgrid_lvls,3,0,1,1)

        subgrid_frames = QtWidgets.QGridLayout()

        spi_numFrames = QtWidgets.QSpinBox(self, minimum = 1, maximum = 1000000, value = 200)
        spi_numFrames.resize(spi_numFrames.sizeHint())
        # spi_numFrames.valueChanged.connect(self.update_framenumstotal)
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
            self.polyfitTimes = []
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

    def create_polyfit(self):
        if len(self.frameNums) <= 0 or len(self.frameNums) != len(self.modTimesUnix):
            print("Not computable")
            return None

        x = np.array(self.frameNums)
        y = np.array(self.modTimesUnix)
        p1 = np.polyfit(x,y,self.polylevel)

        polyfitTimesUnix = np.polyval(p1,range(self.frameNumsTotal))
        self.polyfitTimes = []
        for timeU in polyfitTimesUnix:
            self.polyfitTimes.append(datetime.fromtimestamp(timeU))
        self.timeFinished = datetime.fromtimestamp(int(polyfitTimesUnix[self.frameNumsTotal-1]))

        self.update_plot()

    def update_plot(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111, label='babo')
        ax.set(xlabel='Frame', ylabel='Creation Date', title='Render Progress')

        if len(self.polyfitTimes) > 0:
            ax.plot(range(len(self.polyfitTimes)),self.polyfitTimes, label="approximation")
            ax.text(self.frameNumsTotal-1, self.timeFinished, "Finished approx.: " + str(self.timeFinished), fontsize=10, horizontalalignment="right")

        if len(self.modTimes) > 0 and len(self.modTimes)==len(self.frameNums):
            ax.plot(self.frameNums, self.modTimes, '+', label='data')

        ax.legend(frameon=True)

        self.canv.draw()

    def update_framenumstotal(self, val):
        self.frameNumsTotal = val

    def update_polylevel(self, val):
        self.polylevel = val

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
