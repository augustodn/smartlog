from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import (QItemSelection, pyqtSlot, Qt, pyqtSignal, QObject,
                         QModelIndex)
import sqlite3
import src.model.main as model

qt_creator_file = "./src/resources/loadPass.ui"
Ui_LoadPass, QtBaseClass = uic.loadUiType(qt_creator_file)


class LoadPass(QDialog, QObject, Ui_LoadPass):
    sessionChanged = pyqtSignal(model.Session)

    def __init__(self, parent=None):
        super(LoadPass, self).__init__(parent)
        Ui_LoadPass.__init__(self)
        self.setupUi(self)
        # self.selectedText = ""
        self.session = model.Session()

        self.standardModel = QStandardItemModel()
        self.rootNode = self.standardModel.invisibleRootItem()
        self.treeView.setModel(self.standardModel)
        self.treeView.expandAll()
        selectionModel= self.treeView.selectionModel()

        # controller handling
        selectionModel.selectionChanged.connect(self.selectionChangedSlot)
        self.openButton.clicked.connect(self.file_open)
        self.selectButton.clicked.connect(self.select_pass)

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
                    self, "Open file", "",
                    "Database Files (*.db);All files (*.*)")

        if path:
            self.path = path
            self.make_tree()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def select_pass(self):
        try:
            self.session.active['pass'] = self.selectedText
            self.session.active['DBpath'] = self.path
            self.session.active['run'] = int(self.itemParents[0][-1:])
            self.session.active['well'] = self.itemParents[1]
            self.session.active['mode'] = 'database'
        except Exception as e:
            self.dialog_critical(str(e))
            return -1

        # Pass object as emit argument.
        self.sessionChanged.emit(self.session)
        self.close()

    #decorator has same signature as the signal
    @pyqtSlot(QItemSelection, QItemSelection)
    def selectionChangedSlot(self,newSelection,oldSelection):
        # Get the text of the selected item
        index = self.treeView.selectionModel().currentIndex()
        self.selectedText = index.data(Qt.DisplayRole)

        # Trace hierarchy
        seekRoot = index
        invalid = QModelIndex()
        self.itemParents = []
        while seekRoot.parent() != invalid:
            seekRoot = seekRoot.parent()
            self.itemParents.append(seekRoot.data(Qt.DisplayRole))

    def make_tree(self):
        """ Algorithm to generate tree structure based on db structure.
        Data read from well_run_pass table which relates every object """

        rows = self.rootNode.rowCount()
        if rows > 0:
            self.rootNode.removeRows(0, rows)

        # TODO: Improve algorithm
        try:
            con = sqlite3.connect(self.path)
            result = con.execute("""select well.name, well_run_pass.run,"""
                          """ well_run_pass.id_pass"""
                          """ from well_run_pass inner join well"""
                          """ on well_run_pass.id_well = well.rowid""")

        except Exception as e:
            del self.path
            self.dialog_critical(str(e))
            return -1

        level = [[],[],[]]
        rows = []

        for row in result:
            level[0].append(row[0])
            level[1].append(row[1])
            level[2].append(row[2])
            rows.append(row)

        level[0] = list(set(level[0]))
        root_item = [QStandardItem(item) for item in level[0]]
        [self.rootNode.appendRow(item) for item in root_item]

        # Clean elements before appending
        level_1 = []
        level_1_item = []

        for i, rootNode in zip(range(len(level[0])), level[0]):
            level_1.append([])
            level_1_item.append([])
            for row in rows:
                if row[0] == rootNode:
                    if row[1] not in level_1[i]:
                        # print("append item")
                        level_1[i].append(row[1])
                        item = QStandardItem("Run {}".format(row[1]))
                        level_1_item[i].append(item)
                        root_item[i].appendRow(item)


        # print(level_1, level_1_item)
        for row in rows:
            for well, well_item in zip(level_1, level_1_item):
                for run, run_item in zip(well, well_item):
                    # print(run, run_item)
                    if row[1] == run:
                        pass_ = QStandardItem(row[2])
                        run_item.appendRow(pass_)
