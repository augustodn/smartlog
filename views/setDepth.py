from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
import glob, os
import serial.tools.list_ports as serial
import lib.arducom as arducom

qt_creator_file = "./resources/setDepth.ui"
Ui_SetDepth, QtBaseClass = uic.loadUiType(qt_creator_file)

class SetDepth(QDialog, Ui_SetDepth):
    sendDepth2panel = pyqtSignal(dict)

    def __init__(self, depthCal, parent=None):
        super(SetDepth, self).__init__(parent)
        Ui_SetDepth.__init__(self)
        self.setupUi(self)
        self.depthCal = depthCal

        # Connections
        self.buttonBox.accepted.connect(self.send_cal)
        self.buttonBox.rejected.connect(self.close)

    def send_cal(self):
        depth = self.depthSBox.value()
        self.sendDepth2panel.emit({'val': depth, 'cal': self.depthCal})
        self.close()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
