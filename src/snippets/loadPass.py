from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.QtCore import QItemSelection, pyqtSlot, Qt
import sqlite3

Ui_LoadPass, QtBaseClass = uic.loadUiType("./loadPass.ui")

class LoadPass(QDialog, Ui_LoadPass):
    def __init__(self, parent=None):
        super(LoadPass, self).__init__(parent)
        Ui_LoadPass.__init__(self)
        self.setupUi(self)
        self.selectedText = ""
        self.standardModel = QStandardItemModel()
        self.rootNode = self.standardModel.invisibleRootItem()
        #rootNode.appendRow(QStandardItem("A First Element"))

        self.treeView.setModel(self.standardModel)
        self.treeView.expandAll()
        selectionModel= self.treeView.selectionModel()


        # controller handling
        """
        today = QtCore.QDate(datetime.today())
        self.dateEdit.setDate(today)
        # connections
        self.okButton.clicked.connect(self.store_data)
        self.cancelButton.clicked.connect(self.close)
        """
        selectionModel.selectionChanged.connect(self.selectionChangedSlot)
        self.openButton.clicked.connect(self.file_open)
        self.selectButton.clicked.connect(self.select_pass)
        #self.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
                    self, "Open file", "",
                    "Database Files (*.db);All files (*.*)")

        if path:
            try:
                self.path = path
                # Eecute model method to create tree based on DB 
            except Exception as e:
                self.dialog_critical(str(e))

            else:
                self.path = path
        self.make_tree()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def select_pass(self):
        print(self.selectedText)

    #decorator has same signature as the signal
    @pyqtSlot(QItemSelection, QItemSelection)     
    
    def selectionChangedSlot(self,newSelection,oldSelection):
        #get the text of the selected item
        index = self.treeView.selectionModel().currentIndex()
        self.selectedText = index.data(Qt.DisplayRole)
       
        """
        #find out the hierarchy level of the selected item
        hierarchyLevel=1
        seekRoot = index
        invalid = QtCore.QModelIndex()
        while seekRoot.parent() != invalid:
            seekRoot = seekRoot.parent()
            hierarchyLevel += 1
        showString = '{}, Level {}'.format(selectedText,hierarchyLevel)
        self.setWindowTitle(showString)
        """
    def make_tree(self):

            
        con = sqlite3.connect(self.path)
        result = con.execute("""select well.name, well_run_pass.run,"""
                          """ well_run_pass.id_pass"""
                          """ from well_run_pass inner join well"""
                          """ on well_run_pass.id_well = well.rowid""")
        
        level = [[],[],[]]
        rows = []
        for row in result:
            level[0].append(row[0])
            level[1].append(row[1])
            level[2].append(row[2])
            rows.append(row)

        level[0] = list(set(level[0]))
        # print(level)
        # print(rows)
       
        root_item = [QStandardItem(item) for item in level[0]]

        [self.rootNode.appendRow(item) for item in root_item]
        
        level_1 = []
        level_1_item = []

        for i, rootNode in zip(range(len(level[0])), level[0]):
            level_1.append([])
            level_1_item.append([])
            for row in rows:
                if row[0] == rootNode:
                    if row[1] not in level_1[i]:
                        print("append item")
                        level_1[i].append(row[1])
                        item = QStandardItem("Run {}".format(row[1]))
                        level_1_item[i].append(item)
                        root_item[i].appendRow(item)


        print(level_1, level_1_item)
        for row in rows:
            for well, well_item in zip(level_1, level_1_item):
                for run, run_item in zip(well, well_item):
                    print(run, run_item)
                    if row[1] == run:
                        pass_ = QStandardItem(row[2])
                        run_item.appendRow(pass_)



if __name__ == "__main__":
    app = QApplication([])
    dialog = LoadPass()
    dialog.show()
    app.exec_()
