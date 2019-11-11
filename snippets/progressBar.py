from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, qApp
from PyQt5.QtCore import pyqtSlot, QTimer, QThread, pyqtSignal
import time

Ui_ProgressBar, QtBaseClass = uic.loadUiType("./progressBar.ui")

class ProgressBar(QDialog, Ui_ProgressBar):
    def __init__(self, parent=None):
        super(ProgressBar, self).__init__(parent)
        Ui_ProgressBar.__init__(self)
        self.setupUi(self)
        self.progressBar.setRange(0, 100)
        self.count = 0

    def update_progress(self, value):
        self.progressBar.setValue(value)

class MyThread(QThread):
    change_value = pyqtSignal(int)

    def run(self):
        cnt = 0
        while cnt < 100:
            time.sleep(.3)
            cnt += 1
            self.change_value.emit(cnt)



if __name__ == "__main__":
    app = QApplication([])
    dialog = ProgressBar()
    thread = MyThread()
    thread.change_value.connect(dialog.update_progress)
    thread.start()
    dialog.show()

    app.exec_()
