from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
import serial
#import lib.arducom as arducom
import importlib.util
import numpy as np
import glob, os
from datetime import datetime

#TODO: Fix this when integrated to the SLS SW
spec = importlib.util.spec_from_file_location("arducom", "../lib/arducom.py")
arducom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arducom)

Ui_TensionCal, QtBaseClass = uic.loadUiType("./tensionCal.ui")

class TensionCal(QDialog, Ui_TensionCal):
    def __init__(self, parent=None):
        super(TensionCal, self).__init__(parent)
        Ui_TensionCal.__init__(self)
        self.setupUi(self)
        self.serial = arducom.Serial()
        self.serial.opened = False
        #TODO: Fix port & brate with arguments from mainMenu
        self.port = '/dev/ttyUSB0'
        self.brate = 500000
        self.open_con()
        self.noToolsCal = False
        self.toolStrCal = False
        # Read coefficients verify path
        # TODO: Change path to ./cal/
        fileList = glob.glob('*.cal')
        self.coef = None
        self.rawCounts = [0, 0, 0, 1023]
        self.avgTension = [0, 0, 0, 20000]
        self.comboBox.insertItems(len(fileList), fileList)

        self.buttonBox.accepted.connect(self.save_cal)
        self.buttonBox.rejected.connect(self.close)
        self.calibrate.clicked.connect(self.make_cal)
        self.comboBox.activated.connect(self.read_cal_file)

    def read_cal_file(self):
        path = self.comboBox.currentText()
        ff = open(path, "r")
        ff.readline() # skip date line
        coef = ff.readline().split(',')
        self.coef = [float(c) for c in coef]

    def make_cal(self):
        # self.calibrate.setEnabled(False)
        if not self.noToolsCal:
            self.le_NoToolsRead.setEnabled(False)
            self.le_NoToolsCalc.setEnabled(False)
            self.noToolsCal = True

        elif not self.toolStrCal:
            self.le_ToolStrRead.setEnabled(False)
            self.le_ToolStrCalc.setEnabled(False)
            self.toolStrCal = True
        else:
            self.dialog_critical("Calibration Done")

        # self.calibrate.setEnabled(True)

    def check_cal(self):
        # Read values from labels
        nToolsCalc = float(self.le_NoToolsCalc.text())
        tStrCalc = float(self.le_ToolStrCalc.text())
        nToolsRead = float(self.le_NoToolsRead.text())
        tStrRead = float(self.le_ToolStrRead.text())
        nToolsRatio = (nToolsRead - nToolsCalc) / (nToolsCalc * 1.0)
        tStrRatio = (tStrRead - tStrCalc) / (tStrCalc * 1.0)

        if abs(nToolsRatio) < 0.05 and abs(tStrRatio) < 0.05:
            self.labelCalStatus.setText("Passed")
        else:
            self.labelCalStatus.setText("Failed")
            self.correct_cal()

    def correct_cal(self):
        dlg = QMessageBox(self)
        dlg.setText("""Do you want to correct the calibration and """
                    """create a new file?""")
        dlg.setIcon(QMessageBox.Question)
        dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        ret = dlg.exec_()
        if ret == 1024:
            # 1024 is only the return value for QMessageBox.Ok
            # Apply poly fit and send the values to new_cal
            fit = np.polyfit(self.rawCounts,self.avgTension,1)
            fit_fn = np.poly1d(fit)
            self.new_cal(fit_fn)
        elif ret > 1024:
            dlg.close()

    def new_cal(self, fit_fn):
        """ Save coefficients to new file """
        fname = datetime.now().strftime("tension_%Y%m%d_%H%M.cal")
        calDate = datetime.now().strftime("%Y-%m-%d %H:%M")
        ff = open(fname, 'w+')
        ff.writelines("Calibration date: {}\n".format(calDate))
        for i, _ in enumerate(range(1024)):
            if i == 1023:
                ff.write("{}".format(fit_fn(i)))
            else:
                ff.write("{}, ".format(fit_fn(i)))

        ff.close()
        print("[INFO] New cal file {} generated".format(fname))


    def save_cal(self):
        self.close()

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
        col = 3
        if data and self.coef:
            if not self.noToolsCal:
                avg, raw = self.calc_average(data, col)
                self.rawCounts[1] = raw
                self.avgTension[1] = avg
                self.le_NoToolsRead.setText(str(round(avg, 2)))
            elif not self.toolStrCal:
                avg, raw = self.calc_average(data, col)
                self.rawCounts[2] = raw
                self.avgTension[2] = avg
                self.le_ToolStrRead.setText(str(round(avg, 2)))
            else:
                # Serial connection is not closed mainly because this resets
                # depth display
                # self.serial.close()
                self.serTimer.stop()
                self.check_cal()
        return 0

    def calc_average(self, data, col):
        data = np.array(data)
        tension_raw = data.transpose()[col]
        tension = [self.coef[t] for t in tension_raw]
        return np.average(tension), int(np.average(tension_raw))


    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

if __name__ == "__main__":
    app = QApplication([])
    dialog = TensionCal()
    dialog.show()
    app.exec_()
