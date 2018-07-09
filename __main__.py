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
        grid.addWidget(self.canv, 1,0,1,8)
        grid.addWidget(self.toolbar, 0,0,1,8)

        # 3. Row: Reading Files
        btn_loadFiles = QtWidgets.QPushButton('Load Files', self)
        btn_loadFiles.resize(btn_loadFiles.sizeHint())
        btn_loadFiles.clicked.connect(self.load_files)
        grid.addWidget(btn_loadFiles,2,0,1,4)

        self.lab_dispFilepath = QtWidgets.QLabel("No Files Selected", self)
        self.lab_dispFilepath.resize(self.lab_dispFilepath.sizeHint())
        grid.addWidget(self.lab_dispFilepath,2,4,1,4)

        # 4. Row: Polynomial Regression
        btn_polyFit = QtWidgets.QPushButton('Tell the Future', self)
        btn_polyFit.resize(btn_polyFit.sizeHint())
        btn_polyFit.clicked.connect(self.create_polyfit)
        grid.addWidget(btn_polyFit,3,0,1,4)

        lab_numFrames = QtWidgets.QLabel("Total Number of Frames:", self)
        lab_numFrames.resize(lab_numFrames.sizeHint())
        lab_numFrames.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        grid.addWidget(lab_numFrames,3,4,1,1)

        spi_numFrames = QtWidgets.QSpinBox(self, minimum = 1, maximum = 1000000, value = 200)
        spi_numFrames.resize(spi_numFrames.sizeHint())
        spi_numFrames.valueChanged.connect(self.update_framenumstotal)
        grid.addWidget(spi_numFrames,3,5,1,1)

        lab_polylevel = QtWidgets.QLabel("Polynomial Regression Level:", self)
        lab_polylevel.resize(lab_numFrames.sizeHint())
        lab_polylevel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        grid.addWidget(lab_polylevel,3,6,1,1)

        spi_polylevel = QtWidgets.QSpinBox(self, maximum = 10, value = 2)
        spi_polylevel.resize(spi_polylevel.sizeHint())
        spi_polylevel.valueChanged.connect(self.update_polylevel)
        grid.addWidget(spi_polylevel,3,7,1,1)

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

        #self.modTimesUnix.sort()
        #self.modTimes.sort()

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
