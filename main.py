import sys
from PyQt5 import QtWidgets
import views.mainMenu


app = QtWidgets.QApplication(sys.argv)
window = views.mainMenu.MainWindow()
window.show()
app.exec_()
