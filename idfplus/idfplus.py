#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
IDF Plus
Improved IDF editor

@author = Matt Doiron <mattdoiron@gmail.com>
"""

# Prepare for Python 3
from __future__ import (print_function, division,
                        absolute_import)

# Standard library imports
import sys
import os
import shelve
import platform

# PySide import
import PySide
from PySide import QtGui
from PySide import QtCore

# Custom imports
import idfdelegates
import idfobject
import idfparse

# Resource imports
import icons_qr  # Used for icons (in text format)
import misc_icons_qr  # Used for icons (in text format)

# Global variables
__version__ = '0.0.1'


class IDFPlus(QtGui.QMainWindow):
    '''Main GUI window for IDFPlus program.'''

    def __init__(self):
        super(IDFPlus, self).__init__()

        # Create application UI (call this first)
        self.createUI()

        # Load settings (call this second)
        self.readSettings()

        # Set some instance variables
        self.filename = None
#        myPath = os.path.abspath(os.path.curdir)
        self.idd = shelve.open('data/myIDD.dat')  # How can this be avoided?!
        self.idf = None
        self.groups = None
        self.fullTree = True
        self.dirty = False
        self.obj_orientation = QtCore.Qt.Vertical
        self.current_obj = None
        self.com = Communicate()

        # Create main application elements
        self.createActions()
        self.createToolBars()
        self.createMenus()
        self.createShortcuts()
        self.createTrayMenu()

        # Connect some slots and signals
        self.classTree.currentItemChanged.connect(self.iWasChanged)

    def closeEvent(self, event):
        '''Called when the application is closed.'''
        if self.okToContinue():
            self.writeSettings()
            self.idd.close()
            event.accept()
        else:
            event.ignore()

    def newFile(self):
        '''Called when a new file is to being created'''
        if self.okToContinue():
            self.addRecentFile(self.filename)
            self.setCurrentFile('')

    def openFile(self):
        '''Called by the open file action.'''
        if self.okToContinue():
            directory = os.path.dirname(self.filename) if self.filename else "."
            formats = "EnergyPlus Files (*.idf)"
            fileDialog = QtGui.QFileDialog()
            fileDialog.setFileMode(QtGui.QFileDialog.ExistingFile)
            filename, filt = fileDialog.getOpenFileName(self, 'Open file',
                                                        directory, formats)
            if filename:
                self.loadFile(filename)

    def loadFile(self, filename=None):
        '''Loads a specified file or gets the filename from the sender.'''
        if filename is None:
            action = self.sender()
            if isinstance(action, QtGui.QAction):
                filename = action.data()
                if not self.okToContinue():
                    return
            else:
                return

        if filename:
            total_size = os.path.getsize(filename)
            self.progressDialog = QtGui.QProgressDialog("Loading File", "", 0,
                                                        total_size, self)
            message = "Loading {}...".format(filename)
            self.progressDialog.setLabelText(message)
            self.progressDialog.setWindowModality(QtCore.Qt.WindowModal)
            self.progressDialog.setMinimumDuration(500)
            self.progressDialog.setCancelButton(None)
            self.progressDialog.show()

            self.statusBar().showMessage(message, 5000)
            parser = idfparse.Parser(self.com)
            parser.msg.msg.connect(self.testSignal)
            (object_count, eol_char,
             options, groups, objects) = parser.parseIDD(filename)
            self.idd = shelve.open('data/myIDD.dat')
            # TODO: find vesion of idf file and load appropriate idd file!
            self.idf = objects
            self.groups = groups
            self.loadTreeView(self.fullTree)
            self.classTable.setModel(None)
            self.commentView.setText(str(object_count))  # test only
            self.dirty = False  # Move this into idfObjectContainer
            self.filename = filename
            self.addRecentFile(filename)
            message = "Loaded %s" % os.path.basename(filename)
            self.updateStatus(message)
            self.setCurrentFile(filename)

    def save(self):
        '''Called by save action.'''
        if self.filename:
            return self.saveFile()
        return self.saveAs()

    def saveAs(self):
        '''Called by the save as action.'''
        directory = os.path.dirname(self.filename) if self.filename is not None else '.'
        formats = 'EnergyPlus Files (*.idf)'
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(self, 'Save As',
                                                            directory, formats)
        if fileName:
            return self.saveFile(fileName, self.idf)
        return False

    def saveFile(self):
        '''Called by action to save the current file to disk.'''
#        try:
        if not self.filename or not self.idf:
            return False
        filename = self.filename
        writer = idfparse.Writer()
        if writer.writeIDF(filename, None, self.idf):
            self.setCurrentFile(filename)
            self.addRecentFile(filename)
            self.statusBar().showMessage("File saved", 2000)
            return True
        else:
            return False
#        except:
#            QtGui.QMessageBox.warning(self, "Application",
#                                      "Cannot write file %s." % (fileName))
#            return False

    def undo(self):
        '''Called by the undo action. Not yet implemented'''
        pass

    def redo(self):
        '''Called by the redo action. Not yet implemented'''
        pass

    def about(self):
        '''Called by the about action.'''
#        QtGui.QMessageBox.about(self, "About Application",
#                "<b>IDFPlus</b> is an improved IDF file editor with enhanced "
#                "features and capabilities.")

        QtGui.QMessageBox.about(self, "About IDFPlus",
                """<b>IDFPlus</b> v{0}
                <p>Copyright &copy; 2014 No Name Ltd.
                All rights reserved.
                <p>This is an improved IDF file editor with enhanced featues
                and capabilities.
                <p>Python {1} - Qt {2} - PyQt {3} on {4}""".format(
                __version__, platform.python_version(),
                PySide.QtCore.qVersion(), PySide.__version__,
                platform.system()))

    def createActions(self):
        '''Creates appropriate actions for use in menus and toolbars.'''

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

        self.undoAct = QtGui.QAction("&Undo", self,
                shortcut=QtGui.QKeySequence.Undo,
                statusTip="Undo the last operation", triggered=self.undo)

        self.redoAct = QtGui.QAction("&Redo", self,
                shortcut=QtGui.QKeySequence.Redo,
                statusTip="Redo the last operation", triggered=self.redo)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.maximizeAction = QtGui.QAction("Ma&ximize", self,
                triggered=self.showMaximized)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.transposeAct = QtGui.QAction("Transpose", self,
                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Transpose rows and columns in object display.",
                triggered=self.transposeTable)

        self.newObjAct = QtGui.QAction("New Obj", self,
                statusTip="Create a new object in the current class.",
                triggered=self.newObject)

        self.dupObjAct = QtGui.QAction("Dup Obj", self,
#                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Duplicate the current Object.",
                triggered=self.duplicateObject)

        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.pasteAct.setEnabled(False)
        self.transposeAct.setEnabled(False)
        self.newObjAct.setEnabled(False)
        self.dupObjAct.setEnabled(False)

    def createMenus(self):
        '''Create all required items for menus.'''

        # File Menu
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (self.newAct, self.openAct, self.saveAct,
                                self.saveAsAct, None, self.exitAct)
        self.updateFileMenu()
        self.fileMenu.aboutToShow.connect(self.updateFileMenu)

        # Edit Menu
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.newObjAct)
        self.editMenu.addAction(self.dupObjAct)
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.classTree.parent().toggleViewAction())
        self.viewMenu.addAction(self.infoView.parent().toggleViewAction())
        self.viewMenu.addAction(self.commentView.parent().toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fileToolBar.toggleViewAction())
        self.viewMenu.addAction(self.editToolBar.toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def updateFileMenu(self):
        '''Called to update the recent files portion of the file menu'''
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
        '''Creates the necessary toolbars.'''
        self.fileToolBar = self.addToolBar("File Toolbar")
        self.fileToolBar.setObjectName('fileToolbar')
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        self.editToolBar = self.addToolBar("Edit Toolbar")
        self.editToolBar.setObjectName('editToolbar')
        self.editToolBar.addAction(self.newObjAct)
        self.editToolBar.addAction(self.dupObjAct)
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)
        self.editToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        self.viewToolBar = self.addToolBar("View Toolbar")
        self.viewToolBar.setObjectName('viewToolBar')
        self.viewToolBar.addAction(self.transposeAct)
        self.viewToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

    def createShortcuts(self):
        '''Creates keyboard shortcuts.'''
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+v'),self).activated.connect(self._handlePaste)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'),self).activated.connect(self.copytest)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'),self).activated.connect(self.toggleFullTree)

    def readSettings(self):
        '''Reads application settings and restores them.'''
        settings = QtCore.QSettings()

        size = settings.value("MainWindow/Size", QtCore.QSize(600, 500))
        position = settings.value("MainWindow/Position", QtCore.QPoint(200, 200))
        state = settings.value("MainWindow/State", QtCore.QState())
        geometry = settings.value("MainWindow/Geometry", QtCore.QRect())

        self.recentFiles = settings.value("RecentFiles", ['']) or ['']
        self.resize(size)
        self.move(position)
        self.restoreState(state)
        self.restoreGeometry(geometry)
#        self.restoreDockWidget(self.ui.classTree.parent())
##        self.restoreDockWidget(self.ui.classTable.parent())
#        self.restoreDockWidget(self.ui.infoView.parent())
#        self.restoreDockWidget(self.ui.commentView.parent())

    def writeSettings(self):
        '''Writes application settings to save them.'''
        settings = QtCore.QSettings()

        filename = self.filename  # or '' or None
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
        '''Helper to add actions or a separator easily.'''
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def setCurrentFile(self, fileName):
        '''Sets the current file globaly and updates title, statusbar, etc.'''
        self.filename = fileName
        self.setWindowModified(False)

        if self.filename:
            filename = QtCore.QFileInfo(self.filename).fileName()
            shownName = filename
        else:
            shownName = 'Untitled'

        self.setWindowTitle("%s[*] - Application" % shownName)
        self.updateStatus(shownName)

#    def loadInitialFile(self):
#       '''Loads the previously open file upon program start.'''
#        settings = QtCore.QSettings()
#        fname = settings.value("LastFile")
#        filename = self.filename
#        if filename and QtCore.QFile.exists(filename):
#            self.openFile()

    def okToContinue(self):
        '''Checks if there are unsaved changes and propmpts for action.'''
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

    def addRecentFile(self, filename):
        '''Adds filename to the list of recent files for the file menu.'''
        if not filename:
            return
        if not filename in self.recentFiles:
            self.recentFiles.insert(0, filename)
            while len(self.recentFiles) > 9:
                self.recentFiles.pop()

    def updateStatus(self, message):
        '''Updates the window title and status bar with a message.'''
        self.statusBar().showMessage(message, 5000)
        if self.filename is not None:
            basename = os.path.basename(self.filename)
            self.setWindowTitle("IDFPlus Editor - %s[*]" % basename)
        elif not self.image.isNull():
            self.setWindowTitle("IDFPlus Editor - Unnamed[*]")
        else:
            self.setWindowTitle("IDFPlus Editor[*]")
            self.setWindowModified(self.dirty)

    def copytest(self):
        '''Testing for copy and paste.'''
#        index = self.mainView.bottomright.currentIndex()
        selected = self.classTable.selectionModel()
#        self.mainView.topright.setText(str(index.row()))
#        self.mainView.topright.setText(str(selected.selectedRows()))
        print(str(selected.selectedIndexes()))
#        print str(selected.selectedColumns())

    def setVisible(self, visible):
        '''Integrates system tray with minimize/maximize.'''
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(IDFPlus, self).setVisible(visible)

    def newObject(self):
        pass

    def duplicateObject(self):
        pass

    def toggleFullTree(self):
        '''Called to toggle the full class tree or a partial tree.'''
        self.fullTree = not self.fullTree
        tree = self.classTree
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
        '''Testing for copy and paste.'''
        clipboard_text = QtGui.QApplication.instance().clipboard().text()
#        item = QtGui.QTableWidgetItem()
#        item.setText(clipboard_text)
#        self.tv.setItem(0, 0, item)
        print(clipboard_text)
        self.infoView.setText(clipboard_text)

    def center(self):
        '''Called to center the window on the screen on startup.'''
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

#    def timerEvent(self, event):
#        if self.step >= 100:
#            self.timer.stop()
#            return
#        self.step = self.step + 1
#        self.pbar.setValue(self.step)

    def loadTableView(self, name):
        '''Loads the table of objects for the specified class name.'''
        table = self.classTable

        self.current_obj = name

        if not name:
            return

        iddPart = self.idd['idd'][name][0]
        if name in self.idf:
            idfObjects = self.idf[name]
        else:
            idfObjects = [{'fields':[None for i in iddPart['fields']]}]

        default_model = idfobject.IDFObjectTableModel(idfObjects, iddPart)
        default_model.load()
        model = default_model

        # If objects are vertical, create transposed model
        if self.obj_orientation == QtCore.Qt.Vertical:
            proxyModel = idfobject.TransposeProxyModel()
            proxyModel.setSourceModel(default_model)
            model = proxyModel

        # Assign model to table and set some variables
        table.setModel(model)
#        font = QtGui.QFont("Arial", 10)
#        table.setFont(font)
#        table.setSortingEnabled(True)
#        table.setWordWrap(True)
#        table.resizeColumnsToContents()

        # Create generic delegates for table cells
        delegates = idfdelegates.GenericDelegate(iddPart, self.obj_orientation)
#        delegates.assignDelegates(table, iddPart)

        # Assign delegates depending on object orientation
#        if self.obj_orientation == QtCore.Qt.Horizontal:
#            table.setItemDelegateForRow(delegates)
#        else:
#            table.setItemDelegateForColumn(delegates)

        table.setItemDelegate(delegates)

    def loadTreeView(self, full=True):
        '''Loads the tree of class type names.'''
        tree = self.classTree
        tree.clear()

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

                tree.addTopLevelItem(group_root)
                tree.addTopLevelItem(blank)
                tree.setItemExpanded(group_root, True)
                tree.setFirstItemColumnSpanned(group_root, True)
                tree.setRootIsDecorated(False)

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
        self.transposeAct.setEnabled(True)

    def transposeTable(self):
        if self.obj_orientation == QtCore.Qt.Horizontal:
            self.obj_orientation = QtCore.Qt.Vertical
            print('Setting object orientation to: Vertical')
        else:
            self.obj_orientation = QtCore.Qt.Horizontal
            print('Setting object orientation to: Horizontal')
#        self.classTable.obj_orientation = self.obj_orientation
        self.loadTableView(self.current_obj)

    def testSignal(self, myint):
        '''Test signal'''
        self.progressDialog.setValue(myint)

    def iWasChanged(self, current, previous):
        '''Test call to slot'''
        if current is None:
            return
        if current.parent() is None:
            return
        self.loadTableView(current.text(0))

    def createUI(self):
        '''Setup main UI elements, dock widgets, UI-related elements, etc. '''

        # Class Objects Table widget
#        mainView = QtGui.QWidget(self)
        classTable = QtGui.QTableView(self)
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont("Arial", 10)
        classTable.setFont(font)
        classTable.setSortingEnabled(True)
        classTable.setWordWrap(True)
        classTable.resizeColumnsToContents()
#        layout = QtGui.QVBoxLayout(self)
#        layout.addWidget(self.editToolBar)
#        layout.addWidget(classTable)
#        mainView.setLayout(layout)
#        self.mainView = mainView
#        self.layout = layout

        # Class name tree widget
        classTreeDockWidget = QtGui.QDockWidget("Class Names and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        classTree = QtGui.QTreeWidget(classTreeDockWidget)
        header = QtGui.QTreeWidgetItem(['Object Class', 'Count'])
        header.setFirstColumnSpanned(True)
        classTree.setHeaderItem(header)
        classTree.header().resizeSection(0, 250)
        classTree.header().resizeSection(1, 10)
        classTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        classTree.setAlternatingRowColors(True)
        classTreeDockWidget.setWidget(classTree)

        # Comments widget
        commentDockWidget = QtGui.QDockWidget("Comments", self)
        commentDockWidget.setObjectName("commentDockWidget")
        commentDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        commentView = QtGui.QTextEdit(commentDockWidget)
        commentView.setFrameShape(QtGui.QFrame.StyledPanel)
        commentDockWidget.setWidget(commentView)

        # Info and help widget
        infoDockWidget = QtGui.QDockWidget("Info", self)
        infoDockWidget.setObjectName("infoDockWidget")
        infoDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        infoView = QtGui.QTextEdit(infoDockWidget)
        infoView.setFrameShape(QtGui.QFrame.StyledPanel)
        infoDockWidget.setWidget(infoView)

        # Define corner docking behaviour
        self.setDockNestingEnabled(True)
        self.setCorner(QtCore.Qt.TopLeftCorner,
                       QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner,
                       QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner,
                       QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner,
                       QtCore.Qt.RightDockWidgetArea)

        # Assign main widget and dockwidgets to QMainWindow
        self.setCentralWidget(classTable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, classTreeDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, commentDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, infoDockWidget)

        # Store widgets for access by other objects
        self.classTable = classTable
        self.commentView = commentView
        self.infoView = infoView
        self.classTree = classTree

        # Perform other UI-related initialization tasks
        self.center()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowTitle('IDFPlus Editor')
        self.statusBar().showMessage('Status: Ready')
        self.setWindowIcon(QtGui.QIcon(':/eplussm.gif'))

    def createTrayMenu(self):
        '''Creates an icon and menu for the system tray'''

        # Menu for the system tray
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.exitAct)

        # System tray itself
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QtGui.QIcon(':/eplussm.gif'))
        self.trayIcon.setToolTip('IDFPlus')
        self.trayIcon.show()

#class MyTableView(QtGui.QTableView):
#    '''Subclass of QTableView used to override mousePressEvent'''
#    def __init__(self):
#        super(MyTableView, self).__init__()
#
#    # Ads single-click editing
#    def mousePressEvent(self, event):
#        if event.button() == QtCore.Qt.LeftButton:
#            index = self.indexAt(event.pos())
#            if index.isValid():
#                self.edit(index)
#        QtGui.QTableView.mousePressEvent(self, event)


class Communicate(QtCore.QObject):
    '''Class used to communicate with other objects in the application'''

    msg = QtCore.Signal(int)


def main():

    app = QtGui.QApplication(sys.argv)
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    app.setOrganizationName("IDF Plus Inc.")
    app.setOrganizationDomain("idfplus.com")
    app.setApplicationName("IDFPlus Editor")

    idfPlus = IDFPlus()
    idfPlus.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
