from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
import lib.arducom as arducom
import numpy as np
import glob, os
from datetime import datetime

qt_creator_file = "./resources/depthCal.ui"
Ui_DepthCal, QtBaseClass = uic.loadUiType(qt_creator_file)

class DepthCal(QDialog, Ui_DepthCal):
    def __init__(self, port, brate, parent=None):
        super(DepthCal, self).__init__(parent)
        Ui_DepthCal.__init__(self)
        self.setupUi(self)
        """
        self.serial = arducom.Serial()
        self.serial.opened = False
        self.port = port
        self.brate = brate
        self.open_con()
        """
        self.isCalibrating = False
        self.calibrate.clicked.connect(self.make_cal)


    def make_cal(self):
        if not self.isCalibrating:
            self.isCalibrating = True
            self.calibrate.setText("Finish")
        else:
            self.isCalibrating = False
            self.calibrate.setText("Calibrate")

    def open_con(self):
        """ Open microcontroller connection using the API """
        msg = ("""Failed to open serial port, check if """
               """winch panel is connected and retry""")

        try:
            if not self.serial.opened and self.port and self.brate:
                if not self.serial.open(self.port, self.brate, 1):
                    raise Exception

                self.serial.opened = True
        except:
            self.dialog_critical(msg)
            return -1

        if not self.serial.start():
            self.dialog_critical("""Communication not established, check if """
                                 """winch panel is connected and retry""")
            return -1

        self.serSeq = 0

        self.serTimer = QTimer(self)
        self.serTimer.timeout.connect(self.read_data)
        self.serTimer.start(1000)

    def read_data(self):
        data, self.serSeq = self.serial.get_data(self.serSeq)
        col = 2
        if data and self.coef:
            # Get last depth element
            rawCounts = data.transpose()[col][-1]
            if not self.isCalibrating:
                self.le_RawCounts.setText(rawCounts)
            else:
                # Serial connection is not closed mainly because this resets
                # depth display
                self.serTimer.stop()
                self.check_cal(rawCounts)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
