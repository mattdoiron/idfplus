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

        import shelve
        self.idd = shelve.open('myIDD.dat')
        self.idf = None
        self.groups = None
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
                   'Open file', '/home', "EnergyPlus Files (*.idf *.imf)")

        from parseIDF import parseIDD
        object_count, eol_char, options, groups, objects = parseIDD(fname)

        self.idf = objects
        self.groups = groups
        self.loadTreeView()
#        self.loadTableView('SizingPeriod:DesignDay', objects)
        self.mainView.topright.setText(str(object_count))

    def loadTableView(self, name):

        objs = self.idf[name]
        idd = self.idd['idd']
        cols = len(objs)
        print cols
        rows = len(objs[0]['fields'])
        print rows
        table = self.mainView.bottomright
        table.setColumnCount(cols)
        table.setRowCount(rows)

        vlabels = []
        for tag_item in idd[name][0]['field_tags']:
            for tag in tag_item:
                if tag['tag'] == '\\field':
                    vlabels.append(tag['value'])
        hlabels = ['Obj' + str(i) for i in range(cols)]

        vheader = QtGui.QHeaderView(QtCore.Qt.Orientation.Vertical)
#        vheader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        table.setVerticalHeader(vheader)
        table.setVerticalHeaderLabels(vlabels)
        table.verticalHeader().setVisible(True)

        hheader = QtGui.QHeaderView(QtCore.Qt.Orientation.Horizontal)
#        hheader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        table.setHorizontalHeader(hheader)
        table.setHorizontalHeaderLabels(hlabels)
        table.horizontalHeader().setVisible(True)

        for i in range(cols):
            for j in range(rows):
                item = QtGui.QTableWidgetItem(objs[i]['fields'][j])
                table.setItem(j, i, item)


    def loadTreeView(self, full=True):

        left = self.mainView.left
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

        left.itemClicked.connect(self.iWasClicked)

    def iWasClicked(self, item, column):

        self.loadTableView(item.text(0))

class IDFPanes(QtGui.QWidget):

    def __init__(self, parent):
        super(IDFPanes, self).__init__()

        self.initUI()

    def initUI(self):

        hbox = QtGui.QVBoxLayout(self)

        bottomright = QtGui.QTableWidget(self)
        bottomright.setFrameShape(QtGui.QFrame.StyledPanel)

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
