from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.QtCore import QItemSelection, pyqtSlot, Qt
import sqlite3
import serial.tools.list_ports as serial


Ui_Settings, QtBaseClass = uic.loadUiType("./settings.ui")

class Settings(QDialog, Ui_Settings):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        Ui_Settings.__init__(self)
        self.setupUi(self)
        # View data filling
        portList = [port.name + " " + port.description
                    for port in serial.comports()]
        self.portDevices = [port.device for port in serial.comports()]
        bRateList = ['9600', '115200', '500000']
        self.portComboBox.insertItems(len(portList), portList)
        self.bRateComboBox.insertItems(len(bRateList), bRateList)


        # Connections
        self.buttonBox.accepted.connect(self.save_prefs)
        self.buttonBox.rejected.connect(self.close)

    def save_prefs(self):
        print(self.portDevices[self.portComboBox.currentIndex()])
        print(int(self.bRateComboBox.currentText()))
        print(self.minLeftSpinBox.value())
        print(self.maxLeftSpinBox.value())
        print(self.minRightSpinBox.value())
        print(self.maxRightSpinBox.value())

        # self.close()

if __name__ == "__main__":
    app = QApplication([])
    dialog = Settings()
    dialog.show()
    app.exec_()
