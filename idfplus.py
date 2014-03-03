#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
IDF Plus
"""

import sys
from PySide import QtGui, QtCore
from parseIDF import parseIDD
import shelve
import genericdelegates as gd
import idfobject
#import simpletreemodel_rc


class Communicate(QtCore.QObject):

    msgToSB = QtCore.Signal(str)


class IDFPlus(QtGui.QMainWindow):

    def __init__(self):
        super(IDFPlus, self).__init__()

        self.setGeometry(100, 100, 800, 680)
        self.setWindowTitle('idfPlus Testing')
        self.mainView = IDFPanes(self)

        self.setCentralWidget(self.mainView)
        self.setWindowIcon(QtGui.QIcon('eplus_sm.gif'))
        self.statusBar().showMessage('Status: Ready')
        self.showMaximized()

#        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

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

        self.idd = shelve.open('myIDD.dat')
        self.idf = None
        self.groups = None
        self.fullTree = True
        self.mainView.left.currentItemChanged.connect(self.iWasChanged)

#        self.timer = QtCore.QBasicTimer()
#        self.step = 0

        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+v'),self).activated.connect(self._handlePaste)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'),self).activated.connect(self.copytest)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'),self).activated.connect(self.toggleFullTree)
#        self.idd = db['idd']

    def copytest(self):

#        index = self.mainView.bottomright.currentIndex()
        selected = self.mainView.bottomright.selectionModel()
#        self.mainView.topright.setText(str(index.row()))
#        self.mainView.topright.setText(str(selected.selectedRows()))
        print str(selected.selectedIndexes())
#        print str(selected.selectedColumns())

    def toggleFullTree(self):
        self.fullTree = not self.fullTree
        tree = self.mainView.left
        current = tree.currentIndex()

        for item in QtGui.QTreeWidgetItemIterator(tree):
            obj = item.value().text(0)
            count = item.value().text(1)
            disabled = item.value().isDisabled()
            spanned = item.value().isFirstColumnSpanned()
            if obj is not None and count == '' and not disabled and not spanned:
                item.value().setHidden(not self.fullTree)
        tree.scrollTo(current)

    def _handlePaste(self):
        clipboard_text = QtGui.QApplication.instance().clipboard().text()
#        item = QtGui.QTableWidgetItem()
#        item.setText(clipboard_text)
#        self.tv.setItem(0, 0, item)
        print clipboard_text
        self.mainView.topright.setText(clipboard_text)

    def center(self):

        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

#    def timerEvent(self, event):
#
#        if self.step >= 100:
#            self.timer.stop()
#            return
#        self.step = self.step + 1
#        self.pbar.setValue(self.step)

    def closeEvent(self, event):

        reply = QtGui.QMessageBox.question(self,
                                           'Message',
                                           "Are you sure to quit?",
                                           (QtGui.QMessageBox.Yes |
                                               QtGui.QMessageBox.No),
                                           QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def openFile(self):
#        self.pbar = QtGui.QProgressBar(self)
#        self.pbar.setGeometry(130, 140, 200, 25)
#        self.pbar.show()

#        progress = QProgressDialog("Opening File...", "Abort", 0, percentProgress, self)
#        progress.setWindowModality(Qt.WindowModal)

#        self.center(self.pbar)
#        self.timer.start(100, self)
        filename, _ = QtGui.QFileDialog.getOpenFileName(self,
                   'Open file', '/home', "EnergyPlus Files (*.idf)")

        object_count, eol_char, options, groups, objects = parseIDD(filename)

        self.idf = objects
        self.groups = groups
        self.loadTreeView(self.fullTree)
        self.mainView.topright.setText(str(object_count))  # test only

    def loadTableView(self, name):

        table = self.mainView.bottomright

        iddPart = self.idd['idd'][name][0]
        if name in self.idf:
            idfObjects = self.idf[name]
        else:
            idfObjects = [{'fields':[None for i in iddPart['fields']]}]

        myModel = idfobject.IDFObjectTableModel(idfObjects, iddPart)
        myModel.load()
        table.setModel(myModel)
        font = QtGui.QFont("Arial", 10)
        table.setFont(font)
        table.setSortingEnabled(True)
        table.setWordWrap(True)
        table.resizeColumnsToContents()

        delegate = gd.GenericDelegateGroup(self)
        delegate.insertColumnDelegate(0, gd.ComboBoxColumnDelegate())
        delegate.insertColumnDelegate(1, gd.PlainTextColumnDelegate())
        delegate.insertColumnDelegate(2, gd.PlainTextColumnDelegate())
        table.setItemDelegate(delegate)

    def loadTreeView(self, full=True):

        left = self.mainView.left
        left.clear()
#        groups = self.groups
        objects = self.idf
        group = ''

        # If we want a full list use the idd, otherwise use the idf only
        if full is True:
            obj_list = self.idd['idd']
        else:
            obj_list = objects

        for name, obj in obj_list.iteritems():
            if group != obj[0]['group']:

                group = obj[0]['group']
                group_root = QtGui.QTreeWidgetItem([group])
                group_root.setFirstColumnSpanned(True)
                colour = QtGui.QColor(205, 192, 176)  # light grey
                brush = QtGui.QBrush(colour)
                group_root.setBackground(0, brush)

                blank = QtGui.QTreeWidgetItem([''])
                blank.setDisabled(True)

                left.addTopLevelItem(group_root)
                left.addTopLevelItem(blank)
                left.setItemExpanded(group_root, True)
                left.setFirstItemColumnSpanned(group_root, True)
                left.setRootIsDecorated(False)

            # Populate the object count field
            obj_count = ''
            if name in objects:
                if objects[name]:
                    obj_count = len(objects[name])

            child = QtGui.QTreeWidgetItem([name, str(obj_count)])
            child.setTextAlignment(1, QtCore.Qt.AlignRight)
            group_root.addChild(child)

#            left.setCurrentItem(left.topLevelItem(0))
#        left.itemClicked.connect(self.iWasClicked)
#        left.itemActivated.connect(self.iWasClicked)
#        left.currentItemChanged.connect(self.iWasChanged)
#        left.itemPressed.connect(self.iWasClicked)

    def iWasChanged(self, current, previous):
        if current is None:
            return
        if current.parent() is None:
            return
        self.loadTableView(current.text(0))


class IDFPanes(QtGui.QWidget):

    def __init__(self, parent):
        super(IDFPanes, self).__init__()

        self.initUI()

    def initUI(self):

        hbox = QtGui.QVBoxLayout(self)

        bottomright = QtGui.QTableView(self)
        bottomright.setAlternatingRowColors(True)
#        bottomright.setFrameShape(QtGui.QFrame.StyledPanel)

        topright = QtGui.QTextEdit(self)
        topright.setFrameShape(QtGui.QFrame.StyledPanel)

        left = QtGui.QTreeWidget(self)
#        left.setColumnCount(2)
        header = QtGui.QTreeWidgetItem(['Object Class', 'Count'])
        header.setFirstColumnSpanned(True)

        left.setHeaderItem(header)
        left.header().resizeSection(0, 250)
        left.header().resizeSection(1, 10)
        left.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        left.setAlternatingRowColors(True)

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

        self.bottomright = bottomright
        self.topright = topright
        self.left = left

        self.c = Communicate()


def main():

    app = QtGui.QApplication(sys.argv)
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    t = IDFPlus()
    t.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
