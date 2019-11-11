from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
import glob, os
import serial.tools.list_ports as serial
import src.lib.arducom as arducom


qt_creator_file = "./src/resources/settings.ui"
Ui_Settings, QtBaseClass = uic.loadUiType(qt_creator_file)


class Settings(QDialog, Ui_Settings):
    prefsChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        Ui_Settings.__init__(self)
        self.setupUi(self)
        # View data filling
        self.tabWidget.setCurrentIndex(0)
        self.refresh_comboBoxes()
        bRateList = ['500000']
        self.bRateComboBox.insertItems(len(bRateList), bRateList)
        # Connections
        self.sendDepthCal.clicked.connect(self.send_depthCal)
        self.buttonBox.accepted.connect(self.save_prefs)
        self.buttonBox.rejected.connect(self.close)

    def refresh_comboBoxes(self):
        # Clear the lists first, before refreshing
        self.portComboBox.clear()
        self.tensionComboBox.clear()
        self.depthComboBox.clear()

        portList = [port.device + " " + port.description
                    for port in serial.comports()]
        self.portDevices = [port.device for port in serial.comports()]
        self.portComboBox.insertItems(len(portList), portList)

        tensionCalList = glob.glob('./src/cals/tension*.cal')
        depthCalList = glob.glob('./src/cals/depth*.cal')
        self.tensionComboBox.insertItems(len(tensionCalList), tensionCalList)
        self.depthComboBox.insertItems(len(depthCalList), depthCalList)

    def send_depthCal(self):
        calPath = self.depthComboBox.currentText()
        if not calPath:
            self.dialog_critical("Please select a calibration file first")
            return -1
        calFile = open(calPath, 'r')
        calFile.readline()
        calValue = float(calFile.readline())
        calFile.close()
        try:
            port = self.portDevices[\
                   self.portComboBox.currentIndex()]
            brate = int(self.bRateComboBox.currentText())
        except:
            # self.dialog_critical("""Please select the correspondent """
            #                     """ port and bitrate """)
            port = ''
            brate = ''
            # return -1
        serial = arducom.Serial()
        # TODO: Check if port is already opened
        serial.open(port, brate, 1)
        serial.start()
        answer = serial.set_depthCal(calValue)
        if answer < 0:
            self.dialog_critical("New calibration not verified")
            return -1
        serial.close()
        self.dialog_critical("New calibration set")
        return 0


    def save_prefs(self):
        preferences = {}
        try:
            preferences['port'] = self.portDevices[\
                                    self.portComboBox.currentIndex()]
        except:
            preferences['port'] = ''
        try:
            preferences['brate'] = int(self.bRateComboBox.\
                                       currentText())
            preferences['axis_xmin'] = [self.minLeftSpinBox.value(),
                                        self.minRightSpinBox.value()]
            preferences['axis_xmax'] = [self.maxLeftSpinBox.value(),
                                        self.maxRightSpinBox.value()]
            tension_cal_path = self.tensionComboBox.currentText()
            depth_cal_path = self.depthComboBox.currentText()
            preferences['tension_cal'] = self.get_tension_cal(tension_cal_path)
            preferences['depth_cal'] = self.get_depth_cal(depth_cal_path)
            self.prefsChanged.emit(preferences)
        except:
            self.dialog_critical("""Please check the settings """
                                 """selected and retry""")

        self.close()

    def get_depth_cal(self, path):
        calFile = open(path, 'r')
        calFile.readline()
        value = float(calFile.readline())
        calFile.close()
        return value

    def get_tension_cal(self, path):
        calFile = open(path, 'r')
        calFile.readline()
        coefs = calFile.readline().split(',')
        coefs = [float(c) for c in coefs]
        return coefs

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
