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
        self.frameNumsPolyfit = []
        self.polyfits = {}
        self.polyfitIn = 0
        self.polyfitOut = 200
        self.timeFinished = None
        self.degrees = {'Deg.: 1':1, 'Deg.: 2':2, 'Deg.: 3':3, 'Deg.: 4':4, 'Deg.: 5':5, 'Deg.: 6':6}

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
        self.lvlBoxes = []
        i=0
        for label, content in self.degrees.items():
            checkBox = QtWidgets.QCheckBox(label, self)
            checkBox.resize(checkBox.sizeHint())
            checkBox.stateChanged.connect(self.update_degs)
            x = i%3
            y = (i-x)/3
            subgrid_lvls.addWidget(checkBox,y,x)
            i+=1
            self.lvlBoxes.append(checkBox)
        grid.addLayout(subgrid_lvls,3,0,1,1)

        subgrid_frames = QtWidgets.QGridLayout()

        spi_numFrames = QtWidgets.QSpinBox(self, minimum = 1, maximum = 1000000, value = 200)
        spi_numFrames.resize(spi_numFrames.sizeHint())
        spi_numFrames.valueChanged.connect(self.update_framenumstotal)
        subgrid_frames.addWidget(spi_numFrames,0,0,1,1)

        self.spi_in = QtWidgets.QSpinBox(self, minimum = 0, maximum = 1000000, value = 0)
        self.spi_in.resize(self.spi_in.sizeHint())
        self.spi_in.valueChanged.connect(self.update_polyIn)
        subgrid_frames.addWidget(self.spi_in, 1,0,1,1)

        self.spi_out = QtWidgets.QSpinBox(self, minimum = 0, maximum = 1000000, value = 200)
        self.spi_out.resize(self.spi_out.sizeHint())
        self.spi_out.valueChanged.connect(self.update_polyOut)
        subgrid_frames.addWidget(self.spi_out, 2,0,1,1)

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
            for chkbx in self.lvlBoxes: chkbx.setChecked(False)
            self.update_polyFits()
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
        frameNumsClamped = self.frameNums[self.polyfitIn:self.polyfitOut]
        modTimesUnixClamped = self.modTimesUnix[self.polyfitIn:self.polyfitOut]
        if len(frameNumsClamped) <= 0 or len(frameNumsClamped) != len(modTimesUnixClamped):
            print("Not computable")
            return None

        x = np.array(frameNumsClamped)
        y = np.array(modTimesUnixClamped)
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                p1 = np.polyfit(x,y,deg)
            except np.RankWarning:
                print("Not enough data")
                return None

        polyfitTimesUnix = np.polyval(p1,self.frameNumsPolyfit)
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
                if len(timeList) > 0 and len(timeList) == len(self.frameNumsPolyfit):
                    ax.plot(self.frameNumsPolyfit,timeList, label="Deg. "+str(deg))
                    #ax.text(self.frameNumsTotal-1, self.timeFinished, "Finished approx.: " + str(self.timeFinished), fontsize=10, horizontalalignment="right")

        if len(self.modTimes) > 0 and len(self.modTimes)==len(self.frameNums):
            ax.plot(self.frameNums, self.modTimes, '+', label='data')

        lims = ax.get_xlim()
        x1 = np.clip(self.polyfitIn, lims[0], lims[1])
        x2 = np.clip(self.polyfitOut, lims[0], lims[1])
        self.spi_in.setRange(lims[0], self.polyfitOut)
        self.spi_out.setRange(self.polyfitIn, lims[1])
        ax.axvline(x1, label = 'In', linestyle = 'dashed')
        ax.axvline(x2, label = 'Out', linestyle = 'dotted')

        ax.legend(frameon=True)

        self.canv.draw()

    def update_degs(self):
        chkbx = self.sender()
        if isinstance(chkbx, QtWidgets.QCheckBox):
            deg = self.degrees.get(chkbx.text())
            if chkbx.isChecked():
                self.create_polyfit(deg)
            else:
                self.polyfits.pop(deg, None)
            self.update_plot()

    def update_polyIn(self, val):
        self.polyfitIn = val
        self.update_polyFits()
        self.update_plot()

    def update_polyOut(self, val):
        self.polyfitOut = val
        self.update_polyFits()
        self.update_plot()

    def update_framenumstotal(self, val):
        self.frameNumsTotal = val
        self.update_polyFits()
        self.update_plot()

    def update_polyFits(self):
        self.polyfits.clear()

        frames = range(self.frameNumsTotal)
        self.frameNumsPolyfit = frames[self.polyfitIn:self.frameNumsTotal]

        for chkbx in self.lvlBoxes:
            deg = self.degrees.get(chkbx.text())
            if chkbx.isChecked(): self.create_polyfit(deg)

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
