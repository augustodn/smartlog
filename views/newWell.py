from PyQt5 import uic
from PyQt5.QtWidgets import QSizePolicy, QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QDate
from datetime import datetime
import model.main as model

DB_PATH = './data/'

Ui_NewWell, QtBaseClass = uic.loadUiType("./resources/newWell.ui")

class NewWell(QDialog, Ui_NewWell):
    sessionChanged = pyqtSignal(model.Session)

    def __init__(self, parent=None):
        super(NewWell, self).__init__(parent)
        Ui_NewWell.__init__(self)
        self.setupUi(self)
        # controller handling
        today = QDate(datetime.today())
        self.dateEdit.setDate(today)
        self.session = model.Session()
        # connections
        self.okButton.clicked.connect(self.store_data)
        self.cancelButton.clicked.connect(self.close)

    def store_data(self):
        # Pass data from view to model
        self.model = model.Well()
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

        self.session.active['well'] = self.model.well['name']
        self.session.active['run'] = 1
        self.session.active['DBpath'] = "{}{}.db".format(
                                            DB_PATH,
                                            self.model.well['field'])
        passTable = model.Pass().\
                create_table(self.session.active['DBpath'])
        self.session.active['pass'] = passTable
        WellRunTable().create_table(self.session)
        print(self.model.well.values()) # DEBUG
        
        # Store well data
        error = self.model.write_toDB()
        if error:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("DB connection Failed")
            msg.setText(error)
            msg.exec_()
        else:
            self.sessionChanged.emit(self.session)
            self.close()
