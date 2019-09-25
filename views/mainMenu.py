from PyQt5 import QtCore, QtGui, QtWidgets, uic
from . import (digitalDisplay as dsp, curvePlot as cplt, newWell as nw,
               loadPass as lp)
import model.main as model

qt_creator_file = "./resources/mainMenu.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.session = model.Session()
        self.newWell = nw.NewWell()
        self.loadPass = lp.LoadPass()
        self.curvePlot = cplt.CurvePlot()
        # Connections
        self.actionNew.triggered.connect(self.new_well)
        self.actionLoad.triggered.connect(self.load_pass)

        self.actionPlot.triggered.connect(self.curve_plot)
        self.actionDepth.triggered.connect(self.depth_window)
        self.actionSpeed.triggered.connect(self.speed_window)
        self.actionExit.triggered.connect(QtWidgets.qApp.quit)
        # Signals

        self.loadPass.sessionChanged.connect(self.update_session)
        self.newWell.sessionChanged.connect(self.update_session)
        # Misc
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
        self.curvePlot.update_depth()
        self.curvePlot.show()

    def new_well(self):
        self.newWell.show()

    def load_pass(self):
        self.loadPass.show()
        # self.loadPass.exec_()

    def update_session(self, session):
        # read session object as argument coming from emit signal. Update
        # session on Main Window
        self.session = session
        self.curvePlot.session = session
        print(self.session.active)
        self.actionPlot.setEnabled(True)
