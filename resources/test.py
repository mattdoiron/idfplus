# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 21:40:49 2014

@author: matt
"""

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Model(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.m_data = [["1","2","3"],["4","5","6"],["7","8","9"]]

    def rowCount(self, parent=QModelIndex()):
        return len(self.m_data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.m_data[0])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.m_data[index.row()][index.column()]

if __name__ == "__main__":
    app = QApplication(sys.argv);
    model = Model()
    proxy = QSortFilterProxyModel()
    proxy.setSourceModel(model)
    tv = QTableView()
    tv.setModel(proxy);
    tv.setSortingEnabled(True)
    tv.show();
    sys.exit(app.exec_())