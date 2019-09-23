# -*- coding: utf-8 -*-
"""
@author: Taar
"""

#conversion of https://github.com/openwebos/qt/tree/master/examples/tutorials/modelview/6_treeview

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt as qt
import sqlite3

ROWS = 2
COLS = 3

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        treeView = QtWidgets.QTreeView(self)
        self.setCentralWidget(treeView)
        standardModel = QtGui.QStandardItemModel()
        rootNode = standardModel.invisibleRootItem()
        
        #defining a couple of items
        
        con = sqlite3.connect('../data/LLan-123.db')
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
       
        root_item = [QtGui.QStandardItem(item) for item in level[0]]

        [rootNode.appendRow(item) for item in root_item]
        
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
                        item = QtGui.QStandardItem("Run {}".format(row[1]))
                        level_1_item[i].append(item)
                        root_item[i].appendRow(item)


        print(level_1, level_1_item)
        for row in rows:
            for well, well_item in zip(level_1, level_1_item):
                for run, run_item in zip(well, well_item):
                    print(run, run_item)
                    if row[1] == run:
                        pass_ = QtGui.QStandardItem(row[2])
                        run_item.appendRow(pass_)

        
        
        """
        americaItem = QtGui.QStandardItem("America")
        mexicoItem =  QtGui.QStandardItem("Canada")
        usaItem =     QtGui.QStandardItem("USA")
        bostonItem =  QtGui.QStandardItem("Boston")
        europeItem =  QtGui.QStandardItem("Europe")
        italyItem =   QtGui.QStandardItem("Italy")
        romeItem =    QtGui.QStandardItem("Rome")
        veronaItem =  QtGui.QStandardItem("Verona")
        
        #building up the hierarchy
        rootNode.appendRow(americaItem)
        rootNode.appendRow(europeItem)
        americaItem.appendRow(mexicoItem)
        americaItem.appendRow(usaItem)
        usaItem.appendRow(bostonItem)
        europeItem.appendRow(italyItem)
        italyItem.appendRow(romeItem)
        italyItem.appendRow(veronaItem)
        """
        #register the model
        treeView.setModel(standardModel)
        treeView.expandAll()
        
        #selection changes shall trigger a slot
        selectionModel= treeView.selectionModel()
        selectionModel.selectionChanged.connect(self.selectionChangedSlot)
        
        self.treeView = treeView
        
    @QtCore.pyqtSlot(QtCore.QItemSelection,QtCore.QItemSelection) #decorator has same signature as the signal
    def selectionChangedSlot(self,newSelection,oldSelection):
        #get the text of the selected item
        index = self.treeView.selectionModel().currentIndex()
        selectedText = index.data(qt.DisplayRole)
        
        #find out the hierarchy level of the selected item
        hierarchyLevel=1
        seekRoot = index
        invalid = QtCore.QModelIndex()
        while seekRoot.parent() != invalid:
            seekRoot = seekRoot.parent()
            hierarchyLevel += 1
        showString = '{}, Level {}'.format(selectedText,hierarchyLevel)
        self.setWindowTitle(showString)
        
if __name__ == '__main__':
    app = QtWidgets.QApplication.instance()
    if app is None:
        app= QtWidgets.QApplication(sys.argv)
    w = MainWindow(None)
    w.show()
    app.exec_()
    
