from PyQt5 import QtCore, uic
from PyQt5.QWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtCore import QTimer
from . import (digitalDisplay as dsp, curvePlot as cplt, newWell as nw,
               loadPass as lp)
import model.main as model
import lib.arducom as arducom
import time

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 500000
SERIAL_TIMEOUT = 1

qt_creator_file = "./resources/mainMenu.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.session = model.Session()
        self.newWell = nw.NewWell()
        self.loadPass = lp.LoadPass()
        self.curvePlot = cplt.CurvePlot()
        self.serial = arducom.Serial()
        self.ardu2DB = arducom.DB()
        self.serSeq = 0
        # Connections
        self.actionWell.triggered.connect(self.new_well)
        self.actionLoad.triggered.connect(self.load_pass)

        self.actionStart.triggered.connect(self.read_data)
        self.actionStop.triggered.connect(self.close_con)

        self.actionPlot.triggered.connect(self.curve_plot)
        self.actionDepth.triggered.connect(self.depth_window)
        self.actionSpeed.triggered.connect(self.speed_window)
        self.actionExit.triggered.connect(qApp.quit)
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
        """ Read session object as argument coming from emit signal. 
        Update session on Main Window """

        self.session = session
        self.curvePlot.session = session
        print(self.session.active)
        self.actionPlot.setEnabled(True)

    def open_con(self):
        """ Open microcontroller connection using the API """

        if (not self.serial.start_acq(SERIAL_PORT, BAUD_RATE, 1)):
            self.dialog_critical("""Serial connection failed, check if """
                                 """winch panel is connected and retry""")
            return -1

        self.ardu2DB.open_db(self.session.active['DBpath'])
        serTimer = QTimer(self)
        serTimer.timeout.connect(self.read_data)
        serTimer.start(1000)

    def close_con(self):
        """ Close connection with microncontroller """
        try:
            self.ardu2DB.close()
        except Exception as e:
            self.dialog_critical(str(e))
            return -1

    def read_data (self):
        data, self.serSeq = self.serial.get_data(self.serSeq, SERIAL_TIMEOUT)
        table = self.session.active['pass']
        if data and self.session.active['mode'] == 'realtime':
            while(not self.ardu2DB.write_toDB(data, table)):
                time.sleep(.1)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
