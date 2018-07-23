import sys
import os
import warnings
from datetime import datetime, timedelta

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
        self.got_files = False
        self.frames_total = 200
        self.polyfit_frames = []
        self.polyfit_dates_unix = {}
        self.polyfit_in = 0
        self.polyfit_out = 200
        self.polyfit_mean = []
        self.info_dic = {}
        self.info_poly = {}
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

        self.lab_dispFilepath = QtWidgets.QLineEdit(self)
        self.lab_dispFilepath.setText("No Files Selected")
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
        self.lab_infobox = QtWidgets.QPlainTextEdit()
        self.lab_infobox.resize(self.lab_infobox.sizeHint())
        self.lab_infobox.insertPlainText("No Info available\n")
        self.lab_infobox.clear()
        self.lab_infobox.insertPlainText("Absolutely No Info available\n")
        grid.addWidget(self.lab_infobox,3,1,2,1)

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
            self.calc_modtimes(filepaths)

            self.polyfit_dates_unix.clear()
            for chkbx in self.deg_boxes: chkbx.setChecked(False)
            self.update_polyfits()
            self.polyfit_in = 0
            self.polyfit_out = len(filepaths)

            self.lab_dispFilepath.setText(str(filepaths[0]))
            self.info_dic.clear()
            self.info_add_filebased()

            self.update_info()
            self.update_plot()
            self.got_files = True
        else:
            pass

    def get_filepaths(self):
        """Open filebrowser and return selected filepaths as list of strings"""

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

        #Safe to global var
        self.polyfit_dates_unix.update({deg: polyfitTimesUnix})

    def create_mean(self):
        """Creates mean graph from all generated polyfits"""

        self.polyfit_mean = []

        if len(self.polyfit_dates_unix) == 0:
            return

        if len(self.polyfit_dates_unix) == 1:
            return

        datelistlist = []
        for label, datelist in self.polyfit_dates_unix.items():
            datelistlist.append(datelist)

        xy = np.array(datelistlist)
        means = np.mean(xy, axis=0)
        self.polyfit_mean = means

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
        if len(self.polyfit_dates_unix) > 0:
            for deg, timeList in self.polyfit_dates_unix.items():
                if len(timeList) > 0 and len(timeList) == len(self.polyfit_frames):
                    polyfitTimes = []
                    for timeU in timeList:
                        polyfitTimes.append(datetime.fromtimestamp(timeU))
                    ax.plot(self.polyfit_frames,polyfitTimes, label="Deg. "+str(deg))

        #Plots mean polyfit curve
        if len(self.polyfit_mean)>0 and len(self.polyfit_mean) == len(self.polyfit_frames):
            meanTimes = []
            for timeU in self.polyfit_mean:
                meanTimes.append(datetime.fromtimestamp(timeU))
            ax.plot(self.polyfit_frames, meanTimes, label="Mean")

        # Plots last modified dates of selected files
        if len(self.file_dates) > 0 and len(self.file_dates)==len(self.file_frames):
            ax.plot(self.file_frames, self.file_dates, '+', label='data')

        # Limit in and out point of polyfit and draw vlines for both
        lims = ax.get_xlim()
        x1 = np.clip(self.polyfit_in, lims[0], lims[1])
        x2 = np.clip(self.polyfit_out, lims[0], lims[1])
        self.spi_in.setRange(0, self.polyfit_out)
        self.spi_out.setRange(self.polyfit_in, lims[1])
        ax.axvline(x1, label='In', linestyle='dashed')
        ax.axvline(x2, label='Out', linestyle='dotted')

        # Create legend
        ax.legend(frameon=True)

        self.canv.draw()

    def update_info(self):
        """Update contents of Infobox"""

        self.lab_infobox.clear()

        self.lab_infobox.insertPlainText("File bases info:\n")
        for label, val in self.info_dic.items():
            self.lab_infobox.insertPlainText(label+": "+str(val)+"\n")

        if len(self.info_poly) > 0:
            self.lab_infobox.insertPlainText("\nPolyfit bases info:\n")
            for label, val in self.info_poly.items():
                self.lab_infobox.insertPlainText(label+": "+str(val)+"\n")

    def info_add_filebased(self):
        """Add info based on selected files"""

        file_dates_clamped = self.file_dates_unix[self.polyfit_in:self.polyfit_out]
        self.info_dic.clear()

        frameFirst = datetime.fromtimestamp(int(file_dates_clamped[0]))
        frameLast = datetime.fromtimestamp(int(file_dates_clamped[len(file_dates_clamped)-1]))
        delta = frameLast - frameFirst
        self.info_dic.update({"Time already spent rendering":delta})

        dates = np.array(file_dates_clamped)
        diffs = np.diff(dates)
        mean = timedelta(seconds=int(np.mean(diffs)))
        self.info_dic.update({"Mean rendertime":mean})

        slowest = timedelta(seconds=int(np.amax(diffs)))
        self.info_dic.update({"Slowest frame":slowest})

        fastest = timedelta(seconds=int(np.amin(diffs)))
        self.info_dic.update({"Fastest frame":fastest})

    def info_add_polybased(self):
        """Add info based on mean or single polyfit"""
        if len(self.polyfit_dates_unix) == 0:
            return

        dates = []
        if len(self.polyfit_mean) == 0:
            dates = next(iter(self.polyfit_dates_unix.values()))
        else:
            dates = self.polyfit_mean

        self.info_poly.clear()

        date_finished = datetime.fromtimestamp(dates[len(dates)-1])
        self.info_poly.update({"Date finished":date_finished})

        date_started = datetime.fromtimestamp(dates[0])
        time_total = date_finished - date_started
        self.info_poly.update({"Rendertime total":time_total})

        time_spent = self.info_dic.get("Time already spent rendering", None)
        if time_spent != None:
            time_remaining = time_total - time_spent
            self.info_poly.update({"Time remaining":time_remaining})

    def update_degs(self):
        """Update polyfit dictionary and plot if checkbox value changes"""

        chkbx = self.sender()
        if isinstance(chkbx, QtWidgets.QCheckBox) and self.got_files:
            deg = self.DEGREES.get(chkbx.text())
            if chkbx.isChecked():
                self.create_polyfit(deg)
            else:
                self.polyfit_dates_unix.pop(deg, None)
            self.create_mean()
            self.info_add_polybased()
            self.update_plot()
            self.update_info()

    def update_poly_in(self, val):
        """Update polyfits for new in point"""

        self.polyfit_in = val
        if self.got_files:
            self.update_polyfits()
            self.update_plot()
            self.info_add_filebased()
            self.info_add_polybased()
            self.update_info()

    def update_poly_out(self, val):
        """Update polyfits for new out point"""

        self.polyfit_out = val
        if self.got_files:
            self.update_polyfits()
            self.update_plot()
            self.info_add_filebased()
            self.info_add_polybased()
            self.update_info()

    def update_poly_total(self, val):
        """Update polyfits for new total frame num"""

        self.frames_total = val
        if self.got_files:
            self.update_polyfits()
            self.info_add_polybased()
            self.update_plot()
            self.update_info()

    def update_polyfits(self):
        """Update polyfits for new date range"""

        # Clear all previous polyfit data
        self.polyfit_dates_unix.clear()

        # Update polyfit frame range
        frames = range(self.frames_total)
        self.polyfit_frames = frames[self.polyfit_in:self.frames_total]

        # Create polyfits for all checked checkboxes
        for chkbx in self.deg_boxes:
            deg = self.DEGREES.get(chkbx.text())
            if chkbx.isChecked(): self.create_polyfit(deg)

        self.create_mean()

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

#        import pdb;pdb.set_trace()
