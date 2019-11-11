from PyQt5 import uic
from PyQt5.QtWidgets import QLCDNumber, QVBoxLayout, QDialog

Ui_DigitalDisplay, QtBaseClass = uic.loadUiType("./src/resources/digitalDisplay.ui")

class DigitalDisplay(QDialog, Ui_DigitalDisplay):
    def __init__(self, parent=None, title='', decPnt=False):
        super(DigitalDisplay, self).__init__(parent)
        Ui_DigitalDisplay.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(title)
        self.label.setText(title)
        self.lcdNumber.setSmallDecimalPoint(decPnt)
        self.lcdNumber.display("1234.56")
