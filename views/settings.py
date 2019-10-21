from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
import serial.tools.list_ports as serial


qt_creator_file = "./resources/settings.ui"
Ui_Settings, QtBaseClass = uic.loadUiType(qt_creator_file)

class Settings(QDialog, Ui_Settings):
    prefsChanged = pyqtSignal(dict)

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
        preferences = {}
        try:
            preferences['port'] = self.portDevices[\
                                    self.portComboBox.currentIndex()]
            preferences['brate'] = int(self.bRateComboBox.\
                                       currentText())
            preferences['axis_xmin'] = [self.minLeftSpinBox.value(),
                                        self.minRightSpinBox.value()]
            preferences['axis_xmax'] = [self.maxLeftSpinBox.value(),
                                        self.maxRightSpinBox.value()]
            self.prefsChanged.emit(preferences)
        except:
            self.dialog_critical("""Please check the settings """
                                 """selected and retry""")

        self.close()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
