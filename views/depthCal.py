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
        self.serial = arducom.Serial()
        self.serial.opened = False
        self.port = port
        self.brate = brate
        self.open_con()
        self.isCalibrating = False

        # Connections
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.rejected.connect(self.close)
        self.calibrate.clicked.connect(self.make_cal)


    def make_cal(self):
        if not self.isCalibrating:
            self.isCalibrating = True
            self.calibrate.setText("Finish")
            self.rawCountsInit = int(self.le_RawCounts.text())

        else:
            self.isCalibrating = False
            self.refreshValues = False
            self.calibrate.setText("Calibrate")
            rawCountsEnd = int(self.le_RawCounts.text())
            rawCounts = rawCountsEnd - self.rawCountsInit
            self.check_cal(rawCounts)

    def check_cal(self, rawCounts):
        calFactor = rawCounts/1000
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
        self.refreshValues = True

        self.serTimer = QTimer(self)
        self.serTimer.timeout.connect(self.read_data)
        self.serTimer.start(1000)

    def read_data(self):
        data, self.serSeq = self.serial.get_data(self.serSeq)
        col = 1 # Depth count values
        if data:
            # Get last depth element
            data = np.array(data)
            rawCounts = data.transpose()[col][-1]
            if self.refreshValues:
                self.le_RawCounts.setText(str(rawCounts))
                self.le_EstDepth.setText(str(rawCounts/100))
            else:
                # Serial connection is not closed mainly because this resets
                # depth display
                self.serTimer.stop()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()