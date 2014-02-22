#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PySide tutorial

This example shows
how to use QtGui.QSplitter widget.

author: Jan Bodnar
website: zetcode.com
last edited: August 2011
"""

import sys
from PySide import QtGui, QtCore
import simpletreemodel_rc

class Communicate(QtCore.QObject):

    msgToSB = QtCore.Signal(str)


class IDFPlus(QtGui.QMainWindow):

    def __init__(self):
        super(IDFPlus, self).__init__()

        self.setGeometry(100, 100, 800, 680)
        self.setWindowTitle('idfPlus Testing')
        self.mainView = IDFPanes(self)

        self.setCentralWidget(self.mainView)

        self.statusBar().showMessage('Status: Ready')

        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

        self.center()

        # Menu Bar and Toolbar Actions
        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        openFile = QtGui.QAction('Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.openFile)

        # Toolbar Itself
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)

        # Menu Bar Itself
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(openFile)

        import shelve
        self.idd = shelve.open('myIDD.dat')
#        self.idd = db['idd']

    def center(self):

        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def closeEvent(self, event):

        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def openFile(self):

        fname, _ = QtGui.QFileDialog.getOpenFileName(self,
                                                     'Open file',
                                                     '/home',
                                                     "EnergyPlus Files (*.idf *.imf)")

        from parseIDF import parseIDD

        object_count, eol_char, options, groups, objects = parseIDD(fname)
#        with open(fname, 'r') as f:
#            data = f.read()
#            self.mainView.topright.setText(data)

#        left = QtGui.QTreeView()
#        model = SimpleTreeModel(objects, self.idd)
#        left.setModel(list_model)
#        self.mainView.left = left
#        self.mainView.left.setModel(model)

        self.loadTreeView(objects, groups)



#        model = IDFListModel(self)
#        model.setObjects(self.idd)
#        self.mainView.left.setModel(model)

        self.mainView.topright.setText(str(object_count))

#        group = groups[1]
#        obj_list = []
#        for obj in self.idd:
#            if group != obj['group']:
#                obj_list.append()

#        item1= QtGui.QAbstractListItem()
#        self.mainView.left.addItems([['1','test'],['2','test2'],['3','test3']])


#        table_model = MyTableModel(self, objects['Building'], [1,2,3])
#        self.mainView.bottomright.setModel(table_model)

#        root = self.mainView.left

#        groupItems = {}
#        groups = ['Buildings', 'SimulationParameters', 'Surfaces']
#        for group in groups:
#            groupItems[group] = QtGui.QTreeWidgetItem(root)


#        for obj_name, obj in objects.items():
##            print str(obj[0]['group'])
#            group_name = obj[0]['group']
#            group =  QtGui.QTreeWidgetItem(root)
#            group.setText(0, obj_name)
#
##            group_obj =  QtGui.QTreeWidgetItem(group)
##            group_obj.setText(0, name)
#
#            if not group_name in groupItems:
#                groupItems[group_name] = QtGui.QTreeWidgetItem(root)
#
#            groupItems[group_name].addChild(group)



#        group1 =  QtGui.QTreeWidgetItem(root)
#        group1.setText(1, "Group1")
#        group1.setText(0, "[31]")
#
#        osloItem =  QtGui.QTreeWidgetItem(group1)
#        osloItem.setText(1, "Oslo")
#        osloItem.setText(0, "[3]")
#
#        planets =  QtGui.QTreeWidgetItem(root, group1)
##        planets.setText(0, "Planets")
#        planets.setData(0, QtCore.Qt.DisplayRole, '[1]')
#        planets.setData(1, QtCore.Qt.DisplayRole, 'Saturn')
    def loadTreeView(self, objects, groups):

#        for obj in objects:
        left = self.mainView.left
        group = ''
#        group_root = QtGui.QTreeWidgetItem([group,''])

        for name, obj in objects.iteritems():
            if group != obj[0]['group']:
                group = obj[0]['group']
                group_root = QtGui.QTreeWidgetItem([group,''])
                group_root.setFirstColumnSpanned(True)
                left.addTopLevelItem(group_root)
                left.setItemExpanded(group_root, True)
                left.setFirstItemColumnSpanned(group_root, True)
            child = QtGui.QTreeWidgetItem([name, str(len(obj))])
            child.setTextAlignment(1, QtCore.Qt.AlignRight)
            group_root.addChild(child)


class IDFListModel(QtCore.QAbstractListModel):
    numberPopulated = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(IDFListModel, self).__init__(parent)

        self.objCount = 0
        self.objList = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.objCount

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() >= len(self.objList) or index.row() < 0:
            return None

        if role == QtCore.Qt.DisplayRole:
            return self.objList[index.row()]

        if role == QtCore.Qt.BackgroundRole:
            batch = (index.row() // 100) % 2
            if batch == 0:
                return QtGui.qApp.palette().base()

            return QtGui.qApp.palette().alternateBase()

        return None

    def canFetchMore(self, index):
        return self.objCount < len(self.objList)

    def fetchMore(self, index):
        remainder = len(self.objList) - self.objCount
        itemsToFetch = min(100, remainder)

        self.beginInsertRows(QtCore.QModelIndex(), self.objCount,
                             self.objCount + itemsToFetch)

        self.objCount += itemsToFetch

        self.endInsertRows()

        self.numberPopulated.emit(itemsToFetch)

    def setObjects(self, objects):
#        dir = QtCore.QDir(path)

#        self.objList = list(dir.entryList())
        self.objList = objects.keys
        self.objCount = 0
        self.reset()

class IDFPanes(QtGui.QWidget):

    def __init__(self, parent):
        super(IDFPanes, self).__init__()

        self.initUI()

    def initUI(self):

        hbox = QtGui.QVBoxLayout(self)

        bottomright = QtGui.QTableView(self)
        bottomright.setFrameShape(QtGui.QFrame.StyledPanel)

        topright = QtGui.QTextEdit(self)
        topright.setFrameShape(QtGui.QFrame.StyledPanel)

#        left = QtGui.QTreeView()
        left = QtGui.QTreeWidget()
        left.setColumnCount(2)
#        left.setHeaderLabels(['Count', 'Object Class'])
        header = QtGui.QTreeWidgetItem(['Object Class', 'Count'])
#        header.setSizeHint(1, QtCore.QSize(20, 20))
        header.setFirstColumnSpanned(True)



        left.setHeaderItem(header)
        left.header().resizeSection(0, 250)
        left.header().resizeSection(1, 10)
#        header.setTextAlignment(QtCore.Qt.AlignRight)
#        left.setItemHidden(header, True)


#        left = QtGui.QListWidget()
#        left.setModel(model)


#        left = cities#QtGui.QTreeView()
#        left.setFrameShape(QtGui.QFrame.StyledPanel)

        splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter1.addWidget(topright)
        splitter1.addWidget(bottomright)
        splitter1.setSizes([100, 100])

        splitter2 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter2.addWidget(left)
        splitter2.addWidget(splitter1)
        splitter2.setSizes([70, 100])

        hbox.addWidget(splitter2)
        self.setLayout(hbox)

        self.topright = topright
        self.left = left

        self.c = Communicate()


class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, mylist, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.mylist = mylist
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        return len(self.mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Horizontal and role == QtCore.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mylist = sorted(self.mylist,
                             key=operator.itemgetter(col))
        if order == QtCore.DescendingOrder:
            self.mylist.reverse()
        self.emit(SIGNAL("layoutChanged()"))


# This is our model. It will maintain, modify, and present data to our view(s).
# For more information on list models, take a look at:
# http://doc.trolltech.com/4.6/qabstractitemmodel.html
class SimpleTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, objects, idd, parent=None):
        super(SimpleTreeModel, self).__init__(parent)

        self.rootItem = TreeItem(("Count", "Object Class"))
#        self.setupModelData(objects, self.rootItem)
        self.setupModelData(objects, idd, self.rootItem)
#        self.idd = idd

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, objects, idd, root):

#        idd = self.idd
#        parents = [parent]
#        indentations = [0]

#        number = 0
        group = idd['groups'][0]
        group_root = TreeItem([group, ''], root)

#        group.appendChild(TreeItem(data, parent))
        root.appendChild(group_root)

        for name, obj in objects.iteritems():
            if group != obj[0]['group']:
                group = obj[0]['group']
                group_root = TreeItem([group, ''])
                root.appendChild(group_root)
            data = [str(len(obj)), name]
            group_root.appendChild(TreeItem(data, group_root))


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


# This widget is our view of the readonly list.
# For more information, see:
# http://doc.trolltech.com/4.6/qlistview.html
class SimpleListView(QtGui.QListView):
    def __init__(self, parent = None):
        QtGui.QListView.__init__(self, parent)

        # unlike the previous tutorial, we'll do background colours 'properly'. ;)
        self.setAlternatingRowColors(True)

        # we want our listview to have a context menu taken from the actions on this widget
        # those actions will be to delete an item :)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # create a menu item for our context menu that will delete the selected item.
        a = QtGui.QAction("Delete Selected", self)

        # hook up the triggered() signal on the menu item to the slot below.
#        QtCore.QObject.connect(a, QtCore.Signal("triggered()"), self, QtCore.Slot("onTriggered()"))
        self.addAction(a)

        # this is a slot! we covered signals and slots in tutorial #2,
        # but this is the first time we've created one ourselves.
#        @pyqtSlot()
#        def onTriggered(self):
            # tell our model to remove the selected row.
#            self.model().removeRows(self.currentIndex().row(), 1)


def main():

    app = QtGui.QApplication(sys.argv)
    t = IDFPlus()
    t.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
