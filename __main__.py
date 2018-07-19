import sys
import os
import warnings
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
        self.file_dates_unix = []
        self.file_dates = []
        self.file_frames = []
        self.frames_total = 200
        self.polyfit_frames = []
        self.polyfit_dates = {}
        self.polyfit_in = 0
        self.polyfit_out = 200
        self.DEGREES = {'Deg.: 1':1,
                'Deg.: 2':2,
                'Deg.: 3':3,
                'Deg.: 4':4,
                'Deg.: 5':5,
                'Deg.: 6':6}

        self.initUI()

    def initUI(self):
        """Initialize all UI elements

        For the main graph only the navigation toolbar, the figure and its
        canvas are initialized here.
        For Axes, Plots, Legends, etc. see update_plot()
        """

        # Window and grid layout
        self.setGeometry(600,300,1000,600)
        self.center_window()
        self.setWindowTitle('Date Modified Plotting')

        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)


        # 1.-2. Row: Plotting
        self.fig = plt.figure() #figsize=(15,5)
        self.canv = FigureCanvas(self.fig)
        plt.style.use('seaborn-whitegrid')
        self.toolbar = NavigationToolbar(self.canv, self)
        grid.addWidget(self.canv, 1,0,1,2)
        grid.addWidget(self.toolbar, 0,0,1,2)


        # 3. Row: Reading Files
        btn_loadFiles = QtWidgets.QPushButton('Load Files', self)
        btn_loadFiles.resize(btn_loadFiles.sizeHint())
        btn_loadFiles.clicked.connect(self.load_files)
        grid.addWidget(btn_loadFiles,2,0,1,1)

        self.lab_dispFilepath = QtWidgets.QLabel("No Files Selected", self)
        self.lab_dispFilepath.resize(self.lab_dispFilepath.sizeHint())
        grid.addWidget(self.lab_dispFilepath,2,1,1,1)


        # 4. Row left: Polyfit degree checkboxes
        degs_groupbox = QtWidgets.QGroupBox('Polyfit Degs')
        degs_subgrid = QtWidgets.QGridLayout()
        degs_groupbox.setLayout(degs_subgrid)
        self.deg_boxes = []
        i=0
        for label, content in self.DEGREES.items():
            checkBox = QtWidgets.QCheckBox(label, self)
            checkBox.resize(checkBox.sizeHint())
            checkBox.stateChanged.connect(self.update_degs)
            x = i%3
            y = (i-x)/3
            degs_subgrid.addWidget(checkBox,y,x)
            i+=1
            self.deg_boxes.append(checkBox)
        #grid.addLayout(degs_subgrid,3,0,1,1)
        grid.addWidget(degs_groupbox,3,0,1,1)


        # 5. Row left: In point, out point and number of frames for polyfit
        frames_groupbox = QtWidgets.QGroupBox('Polyfit Frames')
        frames_subgrid = QtWidgets.QGridLayout()
        frames_groupbox.setLayout(frames_subgrid)

        spi_numFrames = QtWidgets.QSpinBox(self, minimum=1,
                maximum=1000000,
                value=200)
        spi_numFrames.resize(spi_numFrames.sizeHint())
        spi_numFrames.valueChanged.connect(self.update_poly_total)
        frames_subgrid.addWidget(spi_numFrames,0,0,1,1)

        self.spi_in = QtWidgets.QSpinBox(self, minimum=0,
                maximum=1000000,
                value=0)
        self.spi_in.resize(self.spi_in.sizeHint())
        self.spi_in.valueChanged.connect(self.update_poly_in)
        frames_subgrid.addWidget(self.spi_in, 1,0,1,1)

        self.spi_out = QtWidgets.QSpinBox(self, minimum=0,
                maximum=1000000,
                value=200)
        self.spi_out.resize(self.spi_out.sizeHint())
        self.spi_out.valueChanged.connect(self.update_poly_out)
        frames_subgrid.addWidget(self.spi_out, 2,0,1,1)

        lab_numFrames = QtWidgets.QLabel("Total Number of Frames", self)
        lab_numFrames.resize(lab_numFrames.sizeHint())
        frames_subgrid.addWidget(lab_numFrames, 0,1,1,2)

        lab_in = QtWidgets.QLabel("First Frame", self)
        lab_in.resize(lab_in.sizeHint())
        frames_subgrid.addWidget(lab_in, 1,1,1,2)

        lab_out = QtWidgets.QLabel("Last Frame", self)
        lab_out.resize(lab_out.sizeHint())
        frames_subgrid.addWidget(lab_out, 2,1,1,2)

        #grid.addLayout(frames_subgrid,4,0,1,1)
        grid.addWidget(frames_groupbox,4,0,1,1)


        # 4.-5. Row right: Infobox
        info_groupbox = QtWidgets.QGroupBox('Info')
        info_layout = QtWidgets.QVBoxLayout()
        info_groupbox.setLayout(info_layout)
        self.lab_infobox = QtWidgets.QLabel("Info", self)
        info_layout.addWidget(self.lab_infobox)
        grid.addWidget(info_groupbox,3,1,2,1)

        grid.setRowStretch(1,100)
        grid.setColumnStretch(1,100)

        self.show()

    def load_files(self):
        """Load Files and create new graph

        Opens filebrowser, resets all polyfits and their checkboxes,
        draws new plot
        """

        filepaths = self.get_filepaths()
        if filepaths != None:
            self.lab_dispFilepath.setText(str(filepaths[0]))
            self.calc_modtimes(filepaths)
            self.polyfit_dates.clear()
            for chkbx in self.deg_boxes: chkbx.setChecked(False)
            self.update_polyfits()
            self.update_plot()
        else:
            pass

    def get_filepaths(self):
        """Open filebrowser and return selected filepaths as list os strings"""

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,
                "QFileDialog.getOpenFileNames()",
                "",
                "All Files (*);;Python Files (*.py)",
                options=options)
        if files:
            return(files)
        else:
            return(None)

    def calc_modtimes(self, filepaths):
        """Creates list of last modified dates from list of filepaths"""

        self.file_frames = range(len(filepaths))
        self.file_dates_unix = []
        self.file_dates = []

        for filepath in filepaths:
            filepath.replace('/', '\\')
            timeUnix = os.path.getmtime(filepath)
            time = datetime.fromtimestamp(timeUnix)
            self.file_dates_unix.append(timeUnix)
            self.file_dates.append(time)

        self.file_dates_unix.sort()
        self.file_dates.sort()

    def create_polyfit(self, deg):
        """Create polyfit dates for plotting"""

        #Set range of dates and frames to be analyzed
        frameNumsClamped = self.file_frames[self.polyfit_in:self.polyfit_out]
        modTimesUnixClamped = self.file_dates_unix[self.polyfit_in:self.polyfit_out]
        if len(frameNumsClamped) <= 0 or len(frameNumsClamped) != len(modTimesUnixClamped):
            print("Not computable")
            return None

        #Compute polyfit function
        x = np.array(frameNumsClamped)
        y = np.array(modTimesUnixClamped)
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                p1 = np.polyfit(x,y,deg)
            except np.RankWarning:
                print("Not enough data")
                return None

        #Compute dates from polyfit function
        polyfitTimesUnix = np.polyval(p1,self.polyfit_frames)
        polyfitTimes = []
        for timeU in polyfitTimesUnix:
            polyfitTimes.append(datetime.fromtimestamp(timeU))

        #Safe to global var
        self.polyfit_dates.update({deg: polyfitTimes})

    def update_plot(self):
        """Creates new axes containing selected info
        and sets ranges on polyfit in and out point
        based on axes limits
        """

        # Basic axes settings
        self.fig.clf()
        ax = self.fig.add_subplot(111, label='babo')
        ax.set(xlabel='Frame', ylabel='Creation Date', title='Render Progress')

        # Plots all available polyfit dates
        if len(self.polyfit_dates) > 0:
            for deg, timeList in self.polyfit_dates.items():
                if len(timeList) > 0 and len(timeList) == len(self.polyfit_frames):
                    ax.plot(self.polyfit_frames,timeList, label="Deg. "+str(deg))

        # Plots last modified dates of selected files
        if len(self.file_dates) > 0 and len(self.file_dates)==len(self.file_frames):
            ax.plot(self.file_frames, self.file_dates, '+', label='data')

        # Limit in and out point of polyfit and draw vlines for both
        lims = ax.get_xlim()
        x1 = np.clip(self.polyfit_in, lims[0], lims[1])
        x2 = np.clip(self.polyfit_out, lims[0], lims[1])
        self.spi_in.setRange(lims[0], self.polyfit_out)
        self.spi_out.setRange(self.polyfit_in, lims[1])
        ax.axvline(x1, label='In', linestyle='dashed')
        ax.axvline(x2, label='Out', linestyle='dotted')

        # Create legend
        ax.legend(frameon=True)

        self.canv.draw()

    def update_degs(self):
        """Update polyfit dictionary and plot if checkbox value changes"""

        chkbx = self.sender()
        if isinstance(chkbx, QtWidgets.QCheckBox):
            deg = self.DEGREES.get(chkbx.text())
            if chkbx.isChecked():
                self.create_polyfit(deg)
            else:
                self.polyfit_dates.pop(deg, None)
            self.update_plot()

    def update_poly_in(self, val):
        """Update polyfits for new in point"""

        self.polyfit_in = val
        self.update_polyfits()
        self.update_plot()

    def update_poly_out(self, val):
        """Update polyfits for new out point"""

        self.polyfit_out = val
        self.update_polyfits()
        self.update_plot()

    def update_poly_total(self, val):
        """Update polyfits for new total frame num"""

        self.frames_total = val
        self.update_polyfits()
        self.update_plot()

    def update_polyfits(self):
        """Update polyfits for new date range"""

        # Clear all previous polyfit data
        self.polyfit_dates.clear()

        # Update polyfit frame range
        frames = range(self.frames_total)
        self.polyfit_frames = frames[self.polyfit_in:self.frames_total]

        # Create polyfits for all checked checkboxes
        for chkbx in self.deg_boxes:
            deg = self.DEGREES.get(chkbx.text())
            if chkbx.isChecked(): self.create_polyfit(deg)

    def center_window(self):
        """Move window to screen center"""

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
