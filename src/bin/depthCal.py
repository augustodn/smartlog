from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QTimer
import src.lib.arducom as arducom
import numpy as np
import glob, os
from datetime import datetime
import time

qt_creator_file = "./src/resources/depthCal.ui"
Ui_DepthCal, QtBaseClass = uic.loadUiType(qt_creator_file)

class DepthCal(QDialog, Ui_DepthCal):
    def __init__(self, port, brate, parent=None):
        super(DepthCal, self).__init__(parent)
        Ui_DepthCal.__init__(self)
        self.setupUi(self)
        self.serial = arducom.Serial()
        self.serial.opened = False
        self.port = port
        self.brate = brate
        self.isCalibrating = False

        # Connections
        self.buttonBox.rejected.connect(self.close_cal)
        self.calibrate.clicked.connect(self.make_cal)


    def make_cal(self):
        if not self.isCalibrating:
            self.refreshValues = True
            self.isCalibrating = True
            self.calibrate.setText("Finish")
            self.open_serial()

        else:
            self.refreshValues = False
            self.isCalibrating = False
            self.calibrate.setText("Calibrate")
            rawCounts = int(self.le_RawCounts.text())
            self.check_cal(rawCounts)

    def check_cal(self, rawCounts):
        # Calibration is based in the amount of raw counts per 5m
        calFactor = rawCounts/5
        dlg = QMessageBox(self)
        dlg.setText("""Calibration factor has been determined """
                    """Do you want to create a new calibration file?""")
        dlg.setIcon(QMessageBox.Question)
        dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        ret = dlg.exec_()
        if ret == 1024:
            # 1024 is only the return value for QMessageBox.Ok
            fname = datetime.now().strftime("./cals/depth_%Y%m%d_%H%M.cal")
            calDate = datetime.now().strftime("%Y-%m-%d %H:%M")
            ff = open(fname, 'w+')
            ff.write("Calibration date: {}\n".format(calDate))
            ff.write("{}\n".format(calFactor))
            ff.close()
            print("[INFO] New cal file {} generated".format(fname))
        else:
            dlg.close()

    def close_cal(self):
        if self.serial.opened:
            self.serTimer.stop()
            self.serial.close()

        self.close()

    def open_serial(self):
        """
        Open microcontroller connection using the API
        """
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
        self.serTimer.start(300)

    def read_data(self):
        data, self.serSeq = self.serial.get_data(self.serSeq)
        col = 1 # Depth count values
        if data:
            # Get last depth element
            data = np.array(data)
            rawCounts = data.transpose()[col][-1]
            if self.refreshValues:
                self.le_RawCounts.setText(str(rawCounts))
                self.le_EstDepth.setText(str(rawCounts/401))
            else:
                self.serTimer.stop()
                self.serial.close()
                self.serial.opened = False

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
