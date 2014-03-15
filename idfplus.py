#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
IDF Plus
Improved IDF editor

@author = Matt Doiron <mattdoiron@gmail.com>
"""

import sys
import os
from PySide import QtGui, QtCore
from parseIDF import parseIDD, writeIDF
import shelve
import genericdelegates as gd
import idfobject
import resources


class IDFPlus(QtGui.QMainWindow):

    def __init__(self):
        super(IDFPlus, self).__init__()

        settings = QtCore.QSettings()
        self.recentFiles = settings.value("RecentFiles") or []
        self.filename = None

        self.createActions()
        self.createMenus()
        self.createToolBars()
#        self.recentFiles = []
#
        self.readSettings()

        self.createStatusBar('Status: Ready')
        self.setCurrentFile('')
        QtCore.QTimer.singleShot(0, self.loadInitialFile)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowTitle('IDFPlus Editor')
        self.setWindowIcon(QtGui.QIcon('eplus_sm.gif'))

        self.mainView = IDFPanes(self)
        self.setCentralWidget(self.mainView)

        self.idd = shelve.open('myIDD.dat')
        self.idf = None
        self.groups = None
        self.fullTree = True


        self.mainView.left.currentItemChanged.connect(self.iWasChanged)
        self.dirty = False

#        self.updateFileMenu()
#        self.timer = QtCore.QBasicTimer()
#        self.step = 0

        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+v'),self).activated.connect(self._handlePaste)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'),self).activated.connect(self.copytest)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'),self).activated.connect(self.toggleFullTree)

    def closeEvent(self, event):
        if self.okToContinue():
            self.writeSettings()
            event.accept()
        else:
            event.ignore()

    def newFile(self):
        if self.okToContinue():
            self.addRecentFile(self.filename)
            self.setCurrentFile('')

    def openFile(self):
        if self.okToContinue():
            directory = os.path.dirname(self.filename) if self.filename is not None else "."
            formats = "EnergyPlus Files (*.idf)"
            filename, _ = QtGui.QFileDialog.getOpenFileName(self,
                   'Open file', directory, formats)
#            fileName, filtr = QtGui.QFileDialog.getOpenFileName(self)
            if filename:
                self.loadFile(filename)

    def loadFile(self, filename=None):
        if filename is None:
            action = self.sender()
            if isinstance(action, QtGui.QAction):
                filename = action.data()
                if not self.okToContinue():
                    return
            else:
                return

        if filename:

#        if not self.okToContinue():
#            return

#        self.pbar = QtGui.QProgressBar(self)
#        self.pbar.setGeometry(130, 140, 200, 25)
#        self.pbar.show()
#        progress = QProgressDialog("Opening File...", "Abort", 0, percentProgress, self)
#        progress.setWindowModality(Qt.WindowModal)

            object_count, eol_char, options, groups, objects = parseIDD(filename)

            self.idf = objects
            self.groups = groups
            self.loadTreeView(self.fullTree)
            self.mainView.topright.setText(str(object_count))  # test only
            self.dirty = False
            self.filename = filename
            self.addRecentFile(filename)
            message = "Loaded %s" % os.path.basename(filename)
            self.updateStatus(message)
            self.setCurrentFile(filename)

    def save(self):
        if self.filename:
            return self.saveFile(self.filename)
        return self.saveAs()

    def saveAs(self):
        directory = os.path.dirname(self.filename) if self.filename is not None else "."
        formats = "EnergyPlus Files (*.idf)"
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(self, 'Save As',
                                                            directory, formats)
        if fileName:
            return self.saveFile(fileName)
        return False

    def about(self):
        QtGui.QMessageBox.about(self, "About Application",
                "<b>IDFPlus</b> is an improved IDF file editor with enhanced "
                "features and capabilities.")

    def createActions(self):
        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'), "&New",
                self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.openFile)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QtGui.QAction("Save &As...", self,
                shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.saveAs)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard")
#                triggered=self.textEdit.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard")
#                triggered=self.textEdit.copy)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection")
#                triggered=self.textEdit.paste)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.pasteAct.setEnabled(False)
#        self.textEdit.copyAvailable.connect(self.cutAct.setEnabled)
#        self.textEdit.copyAvailable.connect(self.copyAct.setEnabled)

    def createMenus(self):

        self.fileMenu = self.menuBar().addMenu("&File")
#        self.fileMenu.addAction(self.newAct)
#        self.fileMenu.addAction(self.openAct)
#        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.saveAsAct)
#        self.fileMenu.addSeparator()
#        self.fileMenu.addAction(self.exitAct)
        self.fileMenuActions = (self.newAct, self.openAct, self.saveAct,
                                self.saveAsAct, None, self.exitAct)
        self.updateFileMenu()
        self.fileMenu.aboutToShow.connect(self.updateFileMenu)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def updateFileMenu(self):
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = self.filename or None
        recentFiles = []
        if self.recentFiles:
            for fname in self.recentFiles:
#                print 'fname: ', fname
                if fname != current and QtCore.QFile.exists(fname):
                    recentFiles.append(fname)
#                    print 'appending recentfile: ' + fname
        if recentFiles:
            self.fileMenu.addSeparator()
#            print 'recent files length: ' + str(len(recentFiles))
            for i, fname in enumerate(recentFiles):
#                print 'recent file name in loop: ' + fname
                action = QtGui.QAction(QtGui.QIcon(":/icon.png"),
                                        "&%d %s" % (i + 1, QtCore.QFileInfo(fname).fileName()),
                                        self)
                action.setData(fname)
                action.triggered.connect(self.loadFile)
                self.fileMenu.addAction(action)
#                print 'adding action: ' + fname
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])

    def createToolBars(self):
        self.fileToolBar = self.addToolBar("File")
        self.fileToolBar.setObjectName('fileToolbar')
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)

        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.setObjectName('editToolbar')
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)

    def createStatusBar(self, status):
        self.statusBar().showMessage(status)

    def readSettings(self):
        settings = QtCore.QSettings()

        size = settings.value("MainWindow/Size", QtCore.QSize(600, 500))
        position = settings.value("MainWindow/Position", QtCore.QPoint(200, 200))
        state = settings.value("MainWindow/State", QtCore.QState())
        geometry = settings.value("MainWindow/Geometry", QtCore.QRect())

        self.recentFiles = settings.value("RecentFiles", ['']) or ['']
        print 'recentfiles type: ', str(type(self.recentFiles))
        print 'recentfiles ' + str(self.recentFiles)
        self.resize(size)
        self.move(position)
        self.restoreState(state)
        self.restoreGeometry(geometry)

    def writeSettings(self):
        settings = QtCore.QSettings()

        filename = self.filename # or '' or None
        recentFiles = self.recentFiles or ['']

        settings.setValue("LastFile", filename)
        settings.setValue("RecentFiles", recentFiles)
        settings.setValue("MainWindow/Size", self.size())
        settings.setValue("MainWindow/Position", self.pos())
        settings.setValue("MainWindow/State", self.saveState())
        settings.setValue("MainWindow/Geometry", self.saveGeometry())

#    def createAction(self, text, slot=None, shortcut=None, icon=None,
#                     tip=None, checkable=False, signal="triggered()"):
#        action = QtGui.QAction(text, self)
#        if icon is not None:
#            action.setIcon(QtGui.QIcon(":/%s.png" % icon))
#        if shortcut is not None:
#            action.setShortcut(shortcut)
#        if tip is not None:
#            action.setToolTip(tip)
#            action.setStatusTip(tip)
#        if slot is not None:
#            self.connect(action, QtCore.SIGNAL(signal), slot)
#        if checkable:
#            action.setCheckable(True)
#        return action
#
    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def saveFile(self, fileName):
        try:
            if writeIDF(fileName):
                self.setCurrentFile(fileName)
                self.addRecentFile(filename)
                self.statusBar().showMessage("File saved", 2000)
                return True
            else:
                return False
        except:
            QtGui.QMessageBox.warning(self, "Application",
                    "Cannot write file %s." % (fileName))
            return False

    def setCurrentFile(self, fileName):
        self.filename = fileName
        self.setWindowModified(False)

        if self.filename:
            shownName = self.strippedName(self.filename)
        else:
            shownName = 'Untitled'

        self.setWindowTitle("%s[*] - Application" % shownName)
        self.updateStatus(shownName)

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def loadInitialFile(self):
#        settings = QtCore.QSettings()
#        fname = settings.value("LastFile")
        filename = self.filename
        if filename and QtCore.QFile.exists(filename):
            self.openFile()

#    def close_current_dockwidget(self):
#        pass

    def okToContinue(self):
        if self.dirty:
            reply = QtGui.QMessageBox.warning(self,
                                               "Application",
                    "The document has been modified.\nDo you want to save your changes?",
                                               QtGui.QMessageBox.Save |
                                               QtGui.QMessageBox.Discard |
                                               QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Cancel:
                return False
            elif reply == QtGui.QMessageBox.Save:
                self.fileSave()
        return True

    def addRecentFile(self, fname):
        if not fname:
            return
        if not fname in self.recentFiles:
            self.recentFiles.insert(0, fname)
            while len(self.recentFiles) > 9:
                self.recentFiles.pop()
#            print 'added file ' + fname

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
#        self.listWidget.addItem(message)
        if self.filename is not None:
            basename = os.path.basename(self.filename)
            self.setWindowTitle("IDFPlus Editor - %s[*]" % basename)
        elif not self.image.isNull():
            self.setWindowTitle("IDFPlus Editor - Unnamed[*]")
        else:
            self.setWindowTitle("IDFPlus Editor[*]")
            self.setWindowModified(self.dirty)

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

#    def center(self):
#        screen = QtGui.QDesktopWidget().screenGeometry()
#        size = self.geometry()
#        self.move((screen.width() - size.width()) / 2,
#                  (screen.height() - size.height()) / 2)

#    def timerEvent(self, event):
#
#        if self.step >= 100:
#            self.timer.stop()
#            return
#        self.step = self.step + 1
#        self.pbar.setValue(self.step)

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

        delegates = gd.GenericDelegateGroup(self)
#        delegates.insertColumnDelegate(0, gd.ComboBoxColumnDelegate())
#        delegates.insertColumnDelegate(1, gd.PlainTextColumnDelegate())
#        delegates.insertColumnDelegate(2, gd.PlainTextColumnDelegate())
#        table.setItemDelegate(delegates)
        delegates.assignDelegates(table)

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

        bottomright = MyTableView()
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

#        self.c = Communicate()


class MyTableView(QtGui.QTableView):
    def __init__(self):
        super(MyTableView, self).__init__()

    # Ads single-click editing
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                self.edit(index)
        QtGui.QTableView.mousePressEvent(self, event)


def main():

    app = QtGui.QApplication(sys.argv)
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    app.setOrganizationName("IDF Plus Inc.")
    app.setOrganizationDomain("idfplus.com")
    app.setApplicationName("IDFPlus Editor")

    idfPlus = IDFPlus()
#    idfPlus.setup()
    idfPlus.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
