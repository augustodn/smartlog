from PyQt5 import uic
from PyQt5.QtWidgets import QLCDNumber, QVBoxLayout, QDialog

Ui_DigitalDisplay, QtBaseClass = uic.loadUiType("./resources/digitalDisplay.ui")

class DigitalDisplay(QDialog, Ui_DigitalDisplay):
    def __init__(self, parent=None, title=''):
        super(DigitalDisplay, self).__init__(parent)
        self.title = title
        Ui_DigitalDisplay.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(self.title)
        self.label.setText(self.title)
        self.lcdNumber.display(1234)
        self.show()

