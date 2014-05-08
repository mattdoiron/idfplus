#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, IDFPlus Inc. All rights reserved.

IDFPlus is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDFPlus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDFPlus. If not, see <http://www.gnu.org/licenses/>.
"""

# Prepare for Python 3
from __future__ import (print_function, division,
                        absolute_import)

# Standard library imports
import sys
import os
#import shelve
import platform

# PySide import
import PySide
from PySide import QtGui
from PySide import QtCore

# Custom imports
import idfdelegates
import idfobject as idfObj
import idfparse
import idfsettings

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
        self.settings = idfsettings.Settings(self)
        self.settings.readSettings()

        # Set some instance variables
        self.filename = None
#        myPath = os.path.abspath(os.path.curdir)
#        self.idd = shelve.open('data/myIDD.dat')  # How can this be avoided?!
        self.idd = None
        self.idf = None
        self.groups = None
        self.fullTree = True
        self.dirty = False
        self.obj_orientation = QtCore.Qt.Vertical
        self.current_obj_class = None
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
            self.settings.writeSettings()
            if self.idd:
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

            # Prepare the parser and load the IDD file with it
            parser = idfparse.IDFParser(self.com)
            parser.msg.msg.connect(self.testSignal)
            #(object_count, eol_char,
            # options, groups, objects) = parser.parseIDF(filename)

            try:
                self.idf = parser.parseIDF(filename)
                self.idd = self.idf.idd
            except IDDFileDoesNotExist(message):

            # Load IDD File for the version of this IDF file
#            version = idf.version  # '8.1.0.008'  # Get this from IDF file!
#            self.idd = idf.idd  # idfObj.IDDFile(self, version)
            #if idd.loadIDD():
            #    self.idd = idd.idd
                else:
                    QtGui.QMessageBox.warning(self,
                                              "Application",
                                              ("Could not find IDD file of "
                                               "appropriate version!\nLoading "
                                               "cancelled"),
                                              QtGui.QMessageBox.Ok)
                    message = ("Loading failed. Could not find "
                               "matching IDD version.")
                    self.updateStatus(message)
                    return False

#            self.idf = idf
            self.groups = self.idf.groups
            self.loadTreeView(self.fullTree)
            self.classTable.setModel(None)
            self.commentView.setText(str(len(self.idf)))  # test only
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
#        elif not self.image.isNull():
#            self.setWindowTitle("IDFPlus Editor - Unnamed[*]")
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

    def loadTableView(self, obj_class):
        '''Loads the table of objects for the specified class name.'''
        table = self.classTable
        self.current_obj_class = obj_class

#        if not obj_class:
#            return

#        iddPart = self.idd['idd'][name][0]
#        if name in self.idf:
#            idfObjects = self.idf[name]
#        else:
#            idfObjects = [{'fields':[None for i in iddPart['fields']]}]

#        self.default_model = idfObj.IDFObjectTableModel(idfObjects, iddPart)
#        self.default_model.load()
        self.default_model = idfObj.IDFObjectTableModel(obj_class,
                                                        self.idf,
                                                        self.idd)
        model = self.default_model

        # If objects are vertical, create transposed model
        if self.obj_orientation == QtCore.Qt.Vertical:
            proxyModel = idfObj.TransposeProxyModel(self.default_model)
#            proxyModel.setSourceModel(self.default_model)
            model = proxyModel
#            table.horizontalHeader().sectionClicked.connect(model.sortTable)

        sortable = QtGui.QSortFilterProxyModel()
        sortable.setDynamicSortFilter(True)
        sortable.setSourceModel(model)
        table.setSortingEnabled(True)

        # Assign model to table and set some variables
        table.setModel(sortable)

#        font = QtGui.QFont("Arial", 10)
#        table.setFont(font)
#        table.setSortingEnabled(True)
#        table.setWordWrap(True)
#        table.resizeColumnsToContents()

        # Create generic delegates for table cells
        delegates = idfdelegates.GenericDelegate(obj_class,
                                                 self.idd,
                                                 self.obj_orientation)
        table.setItemDelegate(delegates)

    def loadTreeView(self):
        '''Loads the tree of class type names.'''
        tree = self.classTree
        tree.clear()
        objects = self.idf
        group = ''

        for obj_class, obj in self.idd.iteritems():
            if group != obj.group:

                group = obj.group
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

            obj_count = len(self.idd.get(obj_class, None) or ''
            child = QtGui.QTreeWidgetItem([obj_class, str(obj_count)])
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
        self.loadTableView(self.current_obj_class)
        print(self.search(self.idf, 'Holiday'))

    def search(self, dictionary, searchFor):
        '''Brute force search trial'''
        for key in dictionary:
            for obj in dictionary[key]:
                for val in obj:
                    if searchFor in val:
                        return key
        return None

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
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont("Arial", 10)
        classTable.setFont(font)
        classTable.setWordWrap(True)
        classTable.horizontalHeader().setMovable(True)
        classTable.resizeColumnsToContents()
#        layout = QtGui.QVBoxLayout(self)
#        layout.addWidget(self.editToolBar)
#        layout.addWidget(classTable)
#        mainView.setLayout(layout)
#        self.mainView = mainView
#        self.layout = layout

        # Class name tree widget
        classTreeDockWidget = QtGui.QDockWidget("Object Classes and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        classTree = QtGui.QTreeWidget(classTreeDockWidget)
        header = QtGui.QTreeWidgetItem(['Object Class', 'Count'])
        header.setFirstColumnSpanned(True)
        classTree.setHeaderItem(header)
        classTree.header().resizeSection(0, 200)
        classTree.header().resizeSection(1, 10)
#        classTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
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

        # Store docks for access by other objects
        self.commentDockWidget = commentDockWidget
        self.infoDockWidget = infoDockWidget
        self.classTreeDockWidget = classTreeDockWidget

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
#    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
#    app.setOrganizationName("IDF Plus Inc.")
#    app.setOrganizationDomain("idfplus.com")
#    app.setApplicationName("IDFPlus Editor")

    idfPlus = IDFPlus()
    idfPlus.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
