import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from . import digitalDisplay as dsp
from . import curvePlot as cplt
from . import newWell as nw


qt_creator_file = "./resources/mainMenu.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.actionPlot.setEnabled(True)
        self.actionPlot.triggered.connect(self.curve_plot)
        self.actionNew.triggered.connect(self.new_well)

        self.actionDepth.triggered.connect(self.depth_window)
        self.actionSpeed.triggered.connect(self.speed_window)
        self.actionExit.triggered.connect(QtWidgets.qApp.quit)

        self.actionExit.setStatusTip('Exit the application')
        self.actionDepth.setStatusTip('Open depth window')
        self.statusBar()

    def depth_window(self):
        widget = dsp.DigitalDisplay(title='Depth')
        widget.exec_()

    def speed_window(self):
        widget = dsp.DigitalDisplay(title='Speed')
        widget.exec_()

    def curve_plot(self):
        widget = cplt.CurvePlot()
        widget.exec_()

    def new_well(self):
        widget = nw.NewWell()
        widget.exec_()
