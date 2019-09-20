from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QSizePolicy, QDialog, QMessageBox
from datetime import datetime
from model.main import WellModel

Ui_NewWell, QtBaseClass = uic.loadUiType("./resources/newWell.ui")

class NewWell(QDialog, Ui_NewWell):
    def __init__(self, parent=None):
        super(NewWell, self).__init__(parent)
        Ui_NewWell.__init__(self)
        self.setupUi(self)
        # controller handling
        today = QtCore.QDate(datetime.today())
        self.dateEdit.setDate(today)
        # connections
        self.okButton.clicked.connect(self.store_data)
        self.cancelButton.clicked.connect(self.close)

        self.show()

    def store_data(self):
        # Pass data from view to model
        self.model = WellModel()
        self.model.well['name'] = self.nameEdit.text()
        self.model.well['field'] = self.fieldEdit.text()
        self.model.well['area'] =  self.areaEdit.text()
        self.model.well['province'] = self.provinceEdit.text()
        self.model.well['country'] = self.countryEdit.text()
        self.model.well['company'] = self.companyEdit.text()
        self.model.well['driller'] = self.drillerEdit.text()
        self.model.well['operator'] = self.operatorEdit.text()
        self.model.well['witness'] = self.witnessEdit.text()
        self.model.well['date'] = self.dateEdit.date().toString("yyyy-MM-dd")
        self.model.well['service'] = self.serviceEdit.text()
        self.model.well['comments'] = self.commentsEdit.toPlainText()
        self.model.well['footNote'] = self.footNoteEdit.toPlainText()
        self.model.well['inDate'] = datetime.today().\
                                        strftime("%Y-%m-%d %H:%M:%S")

        print(self.model.well.values()) # DEBUG

        # Store well data
        error = self.model.insert_inDB()
        if error:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("DB connection Failed")
            msg.setText(error)
            msg.exec_()
        else:
            self.close()
