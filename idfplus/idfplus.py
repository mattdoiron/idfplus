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
from __future__ import (print_function, division, absolute_import)

# System imports
import os
import platform
from BTrees.OOBTree import OOBTree
from ZODB import FileStorage
from ZODB import DB
from collections import deque
import tempfile
import appdirs
import networkx as nx

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import delegates
from . import tablemodel
from . import parser
from . import idfsettings as c
from . import datamodel
from . import logger
from . import commands
from . import treemodel

# Resource imports for icons
from . import icons_rc

# Global variables
__version__ = '0.0.1'
log = logger.setup_logging(c.LOG_LEVEL, __name__)

class IDFPlus(QtGui.QMainWindow):
    """Main GUI window for IDFPlus program."""

    def __init__(self):
        super(IDFPlus, self).__init__()

        # Create application UI (call this first)
        self.create_ui()

        # Load settings (call this second)
        self.settings = c.Settings(self)
        self.settings.read_settings()

        # Set some instance variables
        self.file_path = None
        self.idd = None
        self.idf = None
        self.groups = None
        self.fullTree = True
        self.dirty = False
        self.obj_orientation = QtCore.Qt.Vertical
        self.current_obj_class = None
        # self.com = Communicate()
        self.clipboard = QtGui.QApplication.instance().clipboard()
        self.obj_clipboard = []

        # Create main application elements
        self.create_actions()
        self.create_tool_bars()
        self.create_menus()
        self.create_shortcuts()
        self.create_tray_menu()
        self.create_progress_bar()

        # In-memory ZODB databases don't support undo! Use an on-disk cache
        self.db = MyZODB()

        # Create a place to store all open files
        self.db.dbroot.files = OOBTree()
        self.files = self.db.dbroot.files
        self.idd = OOBTree()

    def closeEvent(self, event):
        """Called when the application is closed."""
        if self.ok_to_continue():
            self.settings.write_settings()
            self.db.close()
            del self.watcher
            log.info('Shutting down IDFPlus')
            event.accept()
        else:
            event.ignore()

    def new_file(self):
        """Called when a new file is to being created"""
        if self.ok_to_continue():
            self.add_recent_file(self.file_path)
            self.set_current_file('')

    def open_file(self):
        """Called by the open file action."""
        if self.ok_to_continue():
            home_dir = os.path.expanduser('~')
            directory = os.path.dirname(self.file_path) if self.file_path else home_dir
            formats = "EnergyPlus Files (*.idf)"
            file_dialog = QtGui.QFileDialog()
            file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
            file_name, filt = file_dialog.getOpenFileName(self, 'Open file',
                                                          directory, formats)
            if file_name:
                self.load_file(file_name)

    def find_idd_file(self):
        """Called to open an idd file location."""
        # print('find idd file was called')
        if self.ok_to_continue():
            home_dir = os.path.expanduser('~')
            directory = os.path.dirname(self.file_path) if self.file_path else home_dir
            dialog_name = 'Open EnergyPlus Installation Directory'
            file_dialog = QtGui.QFileDialog()
            file_dialog.setFileMode(QtGui.QFileDialog.Directory)
            file_name, filt = file_dialog.getOpenFileName(self, dialog_name,
                                                          directory)
            if file_name:
                return self.process_idd_file(file_name)
        return False

    def process_idd_file(self, file_path):
        """Loads a given idd file and saves it.
        :rtype : bool
        :param str file_path:
        """
        log.debug('Processing IDD file')

        message = "Loading {}...".format(file_path)
        self.progressDialogIDD.setLabelText(message)
        self.progressDialogIDD.show()
        self.statusBar().showMessage(message, 5000)

        idd = datamodel.IDDFile()
        idd_parser = parser.IDDParser(idd)

        for progress in idd_parser.parse_idd(file_path):
            self.progressDialogIDD.setValue(progress)

        return True

    def load_idf(self, file_path):
        log.info('Trying to load file: {}'.format(file_path))

        idf = datamodel.IDFFile()
        self.files.update({0:idf})
        idf_parser = parser.IDFParser(idf)

        for progress in idf_parser.parse_idf(file_path):
            self.progressDialogIDF.setValue(progress)

        log.info('IDF version detected as: {}'.format(idf.version))

        self.idf = idf
        self.idd = idf.idd

    def load_file(self, file_path=None):
        """Loads a specified file or gets the file_path from the sender.
        :rtype : bool
        :param file_path:
        """

        log.info('Loading file: {}'.format(file_path))
        if file_path:
            log.debug('Loading file from dialog: {}'.format(file_path))
        if file_path is None:
            action = self.sender()
            if isinstance(action, QtGui.QAction):
                file_path = action.data()
                log.debug('Loading file from recent file menu: {}'.format(file_path))
                if not self.ok_to_continue():
                    return False
            else:
                return False

        message = "Loading {}...".format(file_path)
        self.progressDialogIDF.setLabelText(message)
        self.progressDialogIDF.show()
        self.statusBar().showMessage(message, 5000)

        # Try to load the specified IDF file
        try:
            self.load_idf(file_path)
        except datamodel.IDDFileDoesNotExist as e:

            # Load IDD File for the version of this IDF file
            if not self.find_idd_file():
                QtGui.QMessageBox.warning(self, "Processing IDD File Failed",
                                          ("{}\n\nVersion Required: {}\n\nLoading "
                                          "cancelled!".format(e.message, e.version)),
                                          QtGui.QMessageBox.Ok)
                message = ("Loading failed. Could not find "
                           "matching IDD file for version {}.".format(e.version))
                self.progressDialogIDF.cancel()
                self.update_status(message)
                return False
            else:
                self.load_idf(file_path)

        log.debug('Loading tree view...')
        self.groups = self.idd.groups
        self.load_tree_view()
        log.debug('Setting class table model...')
        self.classTable.setModel(None)
        self.commentView.setText(str(len(self.idf)))  # test only
        self.dirty = False  # Move this into tablemodelContainer?
        self.file_path = file_path
        log.debug('Updating recent file list...')
        self.add_recent_file(file_path)
        message = "Loaded %s" % os.path.basename(file_path)
        self.update_status(message)
        self.set_current_file(file_path)
        log.debug('File Loaded Successfully!')
        return True

    def save(self):
        """Called by save action."""
        if self.file_path:
            return self.save_file()
        return self.save_as()

    def save_as(self):
        """Called by the save as action."""
        home_dir = os.path.expanduser('~')
        directory = os.path.dirname(self.file_path) if self.file_path else home_dir
        formats = 'EnergyPlus Files (*.idf)'
        file_name, filtr = QtGui.QFileDialog.getSaveFileName(self, 'Save As',
                                                            directory, formats)
        if file_name:
            return self.save_file()
        return False

    def save_file(self):
        """Called by action to save the current file to disk."""
#        try:
        if not self.file_path or not self.idf:
            return False
        file_name = self.file_path
        writer = parser.Writer()
        if writer.write_idf(self.idf):
            self.set_current_file(file_name)
            self.add_recent_file(file_name)
            self.statusBar().showMessage("File saved", 2000)
            return True
        else:
            return False
#        except:
#            QtGui.QMessageBox.warning(self, "Application",
#                                      "Cannot write file %s." % (file_path))
#            return False

    def about(self):
        """Called by the about action."""
        import PySide

        QtGui.QMessageBox.about(self, "About IDFPlus",
                """<b>IDFPlus</b> v{0}
                <p>Copyright &copy; 2014 No Name Ltd.
                All rights reserved.
                <p>This is an improved IDF file editor with enhanced features
                and capabilities.
                <p>Python {1} - Qt {2} - PyQt {3} on {4}""".format(
                __version__, platform.python_version(),
                PySide.QtCore.qVersion(), PySide.__version__,
                platform.system()))

    def create_actions(self):
        """Creates appropriate actions for use in menus and toolbars."""

        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new1.png'),
                "&New", self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file",
                triggered=self.new_file)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file",
                triggered=self.open_file)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk",
                triggered=self.save)

        self.saveAsAct = QtGui.QAction(QtGui.QIcon(':/images/saveas.png'),
                "Save &As...", self, shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.save_as)

        self.exitAct = QtGui.QAction(QtGui.QIcon(':/images/quit.png'),
                "E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'),
                "Cu&t", self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.cutObject)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+c'),
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.copySelected)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+v'),
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.pasteSelected)

        self.transposeAct = QtGui.QAction("Transpose", self,
                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Transpose rows and columns in object display.",
                triggered=self.transpose_table)

        self.newObjAct = QtGui.QAction(QtGui.QIcon(':/images/new2.png'),
                "New Obj", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+n'),
                statusTip="Create a new object in the current class.",
                triggered=self.newObject)

        self.copyObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Copy Obj", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current Object(s).",
                triggered=self.copyObject)

        self.pasteObjAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "Paste Obj", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the currently copies Object(s).",
                triggered=self.pasteObject)

        self.dupObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Dup Obj", self, shortcut=QtGui.QKeySequence('Ctrl+d'),
                statusTip="Duplicate the current Object(s).",
                triggered=self.duplicateObject)

        self.delObjAct = QtGui.QAction(QtGui.QIcon(':/images/delete.png'),
                "Del Obj", self, shortcut=QtGui.QKeySequence('Del'),
                statusTip="Delete the current Object(s).",
                triggered=self.deleteObject)

        self.navForwardAct = QtGui.QAction("Forward", self,
                shortcut=QtGui.QKeySequence('Ctrl+Plus'),
                statusTip="Go forward to the next object.",
                triggered=self.navForward)

        self.navBackAct = QtGui.QAction("Back", self,
                shortcut=QtGui.QKeySequence('Ctrl+Minus'),
                statusTip="Go back to the previous object.",
                triggered=self.navBack)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.maximizeAction = QtGui.QAction("Ma&ximize", self,
                triggered=self.showMaximized)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.undoAct = self.undo_stack.createUndoAction(self.undo_stack)
        self.undoAct.setShortcut(QtGui.QKeySequence.Undo)
        self.undoAct.setIcon(QtGui.QIcon(':/images/undo.png'))

        self.redoAct = self.undo_stack.createRedoAction(self.undo_stack)
        self.redoAct.setShortcut(QtGui.QKeySequence.Redo)
        self.redoAct.setIcon(QtGui.QIcon(':/images/redo.png'))

        self.transposeAct.setEnabled(False)

    def create_menus(self):
        """Create all required items for menus."""

        # File Menu
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (self.newAct, self.openAct, self.saveAct,
                                self.saveAsAct, None, self.exitAct)
        self.update_file_menu()
        self.fileMenu.aboutToShow.connect(self.update_file_menu)

        # Edit Menu
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.newObjAct)
        self.editMenu.addAction(self.dupObjAct)
        self.editMenu.addAction(self.delObjAct)
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.copyObjAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addAction(self.pasteObjAct)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.classTree.parent().toggleViewAction())
        self.viewMenu.addAction(self.infoView.parent().toggleViewAction())
        self.viewMenu.addAction(self.commentView.parent().toggleViewAction())
        self.viewMenu.addAction(self.logView.parent().toggleViewAction())
        self.viewMenu.addAction(self.undoView.parent().toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fileToolBar.toggleViewAction())
        self.viewMenu.addAction(self.editToolBar.toggleViewAction())
        self.viewMenu.addAction(self.navToolBar.toggleViewAction())
        self.viewMenu.addAction(self.filterToolBar.toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def navForward(self):
        pass

    def navBack(self):
        pass

    def update_file_menu(self):
        """Called to update the recent files portion of the file menu"""
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = self.file_path or None
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
                action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"),
                                       "&%d %s" % (i + 1, QtCore.QFileInfo(fname).fileName()),
                                       self)
                action.setData(fname)
                action.triggered.connect(self.load_file)
                self.fileMenu.addAction(action)
#                print 'adding action: ' + fname
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])

    def create_tool_bars(self):
        """Creates the necessary toolbars."""

        # File Toolbar
        self.fileToolBar = self.addToolBar("File Toolbar")
        self.fileToolBar.setObjectName('fileToolbar')
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Edit Toolbar
        self.editToolBar = self.addToolBar("Edit Toolbar")
        self.editToolBar.setObjectName('editToolbar')
        self.editToolBar.addAction(self.undoAct)
        self.editToolBar.addAction(self.redoAct)
        self.editToolBar.addAction(self.newObjAct)
        self.editToolBar.addAction(self.dupObjAct)
        self.editToolBar.addAction(self.delObjAct)
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyObjAct)
        self.editToolBar.addAction(self.pasteObjAct)
        self.editToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Object history navigation toolbar
        self.navToolBar = self.addToolBar("Navigation Toolbar")
        self.navToolBar.setObjectName('viewToolBar')
        self.navToolBar.addAction(self.navForwardAct)
        self.navToolBar.addAction(self.navBackAct)
        self.navToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Object filter toolbar
        self.filterToolBar = self.addToolBar("Filter Toolbar")
        self.filterToolBar.setObjectName('filterToolBar')
        self.filterBox = QtGui.QLineEdit()
        self.filterBox.setMaximumWidth(160)
        self.filterBox.setFixedWidth(160)
        filterLabel = QtGui.QLabel("Filter Obj:", self)
        filterLabel.setBuddy(self.filterBox)
        self.filterToolBar.addWidget(filterLabel)
        self.filterBox.textChanged.connect(self.filterRegExpChanged)
        clearFilterButton = QtGui.QPushButton('Clear Filter')
        clearFilterButton.clicked.connect(self.clearFilterClicked)
        self.filterToolBar.addWidget(self.filterBox)
        self.filterToolBar.addWidget(clearFilterButton)
        self.caseSensitivity = QtGui.QCheckBox('Case Sensitive')
        self.caseSensitivity.stateChanged.connect(self.caseSensitivityChanged)
        self.filterToolBar.addWidget(self.caseSensitivity)
        self.filterToolBar.addSeparator()
        self.filterToolBar.addAction(self.transposeAct)

    def create_shortcuts(self):
        """Creates keyboard shortcuts."""
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'),self).activated.connect(self.toggle_full_tree)

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

    def table_clicked(self, index):
        if not index.isValid():
            return

        try:
            G = self.idf._graph
            node = self.idf[self.current_obj_class][index.column()][index.row()]

            # print("Node ID: {}".format(id(node)))
            ancestors = nx.ancestors(G, node)
            descendants = nx.descendants(G, node)

            # print("Node Ancestors: {}".format(ancestors))
            new_model = treemodel.ReferenceTreeModel([ancestors, descendants],
                                                     ("Field", "Class"),
                                                     self.refView)
            self.refView.setModel(new_model)
            self.refView.expandAll()

        except (nx.exception.NetworkXError, IndexError) as e:
            empty_model = treemodel.ReferenceTreeModel(None,
                                                       ("Field", "Class"),
                                                       self.refView)
            self.refView.setModel(empty_model)

    def create_context_menu(self, pos):
        menu = QtGui.QMenu()
        openAction = menu.addAction("Test 1")
        delAction = menu.addAction("Clear")
        renaAction = menu.addAction("Test 2")
        self.classTable.setContextMenuPolicy()

    def addActions(self, target, actions):
        """Helper to add actions or a separator easily."""
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def filterRegExpChanged(self):
        pattern = self.filterBox.text()
        if len(pattern) < 3:
            pattern = ''
        self.classTable.model().setFilterRegExp(pattern)
        self.classTable.model().invalidate()
        # self.classTable.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def clearFilterClicked(self):
        self.filterBox.clear()
        self.filterRegExpChanged()

    def caseSensitivityChanged(self):
        if self.caseSensitivity.isChecked() == True:
            sensitivity = QtCore.Qt.CaseSensitive
        else:
            sensitivity = QtCore.Qt.CaseInsensitive
        self.classTable.model().setFilterCaseSensitivity(sensitivity)
        self.filterRegExpChanged()

    def set_current_file(self, file_name):
        """Sets the current file globally and updates title, statusbar, etc."""
        self.file_path = file_name
        self.setWindowModified(False)

        if self.file_path:
            file_name = QtCore.QFileInfo(self.file_path).fileName()
            shownName = file_name
        else:
            shownName = 'Untitled'

        self.setWindowTitle("%s[*] - Application" % shownName)
        self.update_status(shownName)

    def ok_to_continue(self):
        """Checks if there are unsaved changes and prompts for action."""
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

    def add_recent_file(self, file_name):
        """Adds file_path to the list of recent files for the file menu.
        :param file_name:
        """
        if not file_name:
            return
        if not file_name in self.recentFiles:
            self.recentFiles.insert(0, file_name)
            while len(self.recentFiles) > 9:
                self.recentFiles.pop()

    def update_status(self, message):
        """Updates the window title and status bar with a message.
        :param message:
        """
        self.statusBar().showMessage(message, 5000)
        if self.idd:
            self.versionLabel.setText('EnergyPlus IDD v{}'.format(self.idd.version))
        if self.file_path is not None:
            basename = os.path.basename(self.file_path)
            self.setWindowTitle("IDFPlus Editor - %s[*]" % basename)
        else:
            self.setWindowTitle("IDFPlus Editor[*]")
            self.setWindowModified(self.dirty)

    def setVisible(self, visible):
        """Integrates system tray with minimize/maximize.
        :param visible:
        """
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(IDFPlus, self).setVisible(visible)

    def newObject(self):

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self)
        self.undo_stack.push(cmd)

    def duplicateObject(self):

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_selection=True)
        self.undo_stack.push(cmd)

    def deleteObject(self):

        # Create undo command and push it to the undo stack
        cmd = commands.DeleteObjectCmd(self)
        self.undo_stack.push(cmd)

    def cutObject(self):

        # Copy object then delete it
        if not self.copyObject():
            return False
        self.deleteObject()

    def pasteSelected(self):
        """Pastes clipboard into cells starting at selected cell."""

        # Create undo command and push it to the undo stack
        cmd = commands.PasteSelectedCmd(self)
        self.undo_stack.push(cmd)

    def pasteObject(self):
        """Pastes the currently copies object(s)."""

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_clipboard=True)
        self.undo_stack.push(cmd)

    def copyObject(self):
        """Copies object(s) to the clipboard for pasting to other programs."""
        indexes = self.classTable.selectedIndexes()
        if len(indexes) <= 0:
            return False

        # Make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in indexes])
        else:
            index_set = set([index.row() for index in indexes])
        count = len(list(index_set))
        start = list(index_set)[0]
        end = start + count

        # Copy object to the clipboard
        self.obj_clipboard = self.idf[self.current_obj_class][start:end]
        return True

    def copySelected(self):
        """Copies the selected cells to the clipboard for pasting to other programs."""

        # Find the selection and it's last row
        indexes = self.classTable.selectedIndexes()
        if len(indexes) <= 0:
            return False
        last = indexes[-1].row()

        # Iterate through indexes saving the columns
        range_to_copy = []
        col = []
        for i in indexes:
            col.append(i.data() or '')
            if i.row() == last:
                range_to_copy.append(col)
                col = []

        # Qt seems to always traverses by column so transpose rows/cols here
        range_copied = zip(*range_to_copy)

        # Convert to text for clipboard
        text_copied = ''
        for row in range_copied:
            text_copied += '\t'.join(row)
            text_copied += '\n'

        # Save converted text to the clipboard
        mode = QtGui.QClipboard.Clipboard
        self.clipboard.setText(text_copied, mode)
        return True

    def toggle_full_tree(self):
        """Called to toggle the full class tree or a partial tree."""
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

    def center(self):
        """Called to center the window on the screen on startup."""
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def load_table_view(self, obj_class):
        """Loads the table of objects for the specified class name.
        :param obj_class:
        """
        #TODO instantiate TransposeProxyModel and IDFObjectTableModel elsewhere?

        # Filter out group headers
        if obj_class not in self.idd:
            return

        # Save some variables
        table = self.classTable
        self.current_obj_class = obj_class

        # Create the default table model
        self.default_model = tablemodel.IDFObjectTableModel(obj_class,
                                                            self.idf)

        # If objects are vertical, create transposed model
        if self.obj_orientation == QtCore.Qt.Vertical:
            model = tablemodel.TransposeProxyModel(self.default_model)
            model.setSourceModel(self.default_model)
        else:
            model = self.default_model

        # Create additional proxy for sorting and filtering
        sortable = tablemodel.SortFilterProxyModel(self.obj_orientation)
        sortable.setSourceModel(model)

        # Assign model to table (enable sorting FIRST)
        table.setSortingEnabled(True)
        table.setModel(sortable)

        # Create generic delegates for table cells
        my_delegates = delegates.GenericDelegate(self,
                                                 obj_class,
                                                 self.idd,
                                                 self.obj_orientation)
        table.setItemDelegate(my_delegates)

        # Now that there is a class selected, enable some actions
        self.newObjAct.setEnabled(True)
        self.delObjAct.setEnabled(True)
        self.transposeAct.setEnabled(True)
        self.infoView.setText(self.idd[self.current_obj_class].get_info)

    def load_tree_view(self):
        """Loads the tree of class type names."""

        new_model = treemodel.ObjectClassTreeModel(self.idf,
                                                   ("Object Class", "Count"),
                                                   self.classTree)
        self.classTree.setModel(new_model)
        self.classTree.setRootIsDecorated(False)
        self.classTree.expandAll()
        self.classTree.setColumnWidth(0, 280)
        self.classTree.setColumnWidth(1, 10)

    def transpose_table(self):
        """Transposes the table"""
        if self.obj_orientation == QtCore.Qt.Horizontal:
            self.obj_orientation = QtCore.Qt.Vertical
            self.classTable.model().obj_orientation = QtCore.Qt.Vertical
            # self.classTable.horizontalHeader().setMovable(True)
            # self.classTable.verticalHeader().setMovable(False)
            # log.info('Setting object orientation to vertical.')
        else:
            self.obj_orientation = QtCore.Qt.Horizontal
            self.classTable.model().obj_orientation = QtCore.Qt.Horizontal
            # self.classTable.horizontalHeader().setMovable(False)
            # self.classTable.verticalHeader().setMovable(True)
            # print('Setting object orientation to: Horizontal')

        self.load_table_view(self.current_obj_class)

    def classSelected(self, current):
        """Loads the table view when a new class is selected"""
        if (current or current.parent()) is None:
            return
        cls = current.internalPointer().data(0)
        self.load_table_view(cls)

    def create_progress_bar(self):

        # Setup idf progress dialog
        self.progressDialogIDF = QtGui.QProgressDialog("Loading IDF File", "", 0,
                                                       100, self)
        self.progressDialogIDF.setWindowTitle('Loading IDF File')
        self.progressDialogIDF.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDF.setMinimumDuration(500)
        self.progressDialogIDF.setCancelButton(None)

        # Setup idd progress dialog
        self.progressDialogIDD = QtGui.QProgressDialog("Loading IDD File", "", 0,
                                                       100, self)
        self.progressDialogIDD.setWindowTitle('Loading IDD File')
        self.progressDialogIDD.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDD.setMinimumDuration(500)
        self.progressDialogIDD.setCancelButton(None)


    def create_ui(self):
        """Setup main UI elements, dock widgets, UI-related elements, etc. """

        log.debug('Loading UI')

        # Undo Stack
        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(100)

        # Object navigation history
        self.obj_history = deque([], c.MAX_OBJ_HISTORY)

        # Object class table widget
        classTable = TableView(self)
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont("Arial", 9)
        classTable.setFont(font)
        fm = classTable.fontMetrics()
        classTable.setWordWrap(True)
        classTable.setEditTriggers(QtGui.QAbstractItemView.EditKeyPressed |
                                   QtGui.QAbstractItemView.DoubleClicked |
                                   QtGui.QAbstractItemView.AnyKeyPressed |
                                   QtGui.QAbstractItemView.SelectedClicked)
        # classTable.horizontalHeader().setMovable(True)
        # classTable.verticalHeader().setMovable(False)
        # classTable.horizontalHeader().setContentsMargins(0, 0, 0, 0)
        # classTable.verticalHeader().setContentsMargins(0, 0, 0, 0)
        classTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.horizontalHeader().setDefaultSectionSize(c.DEFAULT_COLUMN_WIDTH)
        classTable.verticalHeader().setDefaultSectionSize(fm.height() + 5)
        # classTable.setStyleSheet("QTableView {padding: 0px; border: 0px;} ")

        classTable.clicked.connect(self.table_clicked)
        classTable.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)

        # These are currently broken
        # classTable.horizontalHeader().sectionMoved.connect(self.moveObject)
        # classTable.verticalHeader().sectionMoved.connect(self.moveObject)

        # Object class tree widget
        classTreeDockWidget = QtGui.QDockWidget("Object Classes and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        # classTree = QtGui.QTreeWidget(classTreeDockWidget)
        classTree = QtGui.QTreeView(classTreeDockWidget)
        classTree.setUniformRowHeights(True)
        classTree.setExpandsOnDoubleClick(False)
        classTree.setFont(font)
        classTree.setAlternatingRowColors(True)
        palette = classTree.palette()
        palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.darkCyan)
        classTree.setPalette(palette)
        classTreeDockWidget.setWidget(classTree)
        classTree.clicked.connect(self.classSelected)

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

        # Node list and jump menu widget
        refDockWidget = QtGui.QDockWidget("Field References", self)
        refDockWidget.setObjectName("refDockWidget")
        refDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        ref_model = treemodel.ReferenceTreeModel(None, ("", ""), refDockWidget)
        refView = QtGui.QTreeView(refDockWidget)
        refView.setModel(ref_model)
        refView.setUniformRowHeights(True)
        refView.setRootIsDecorated(False)
        refView.setIndentation(15)
        # refView.setHeaderHidden(True)
        refView.setFrameShape(QtGui.QFrame.StyledPanel)
        refDockWidget.setWidget(refView)

        # Logging and debugging widget
        logDockWidget = QtGui.QDockWidget("Log Viewer", self)
        logDockWidget.setObjectName("logDockWidget")
        logDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        logView = QtGui.QPlainTextEdit(logDockWidget)
        logView.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        logView.setReadOnly(True)
        logView.ensureCursorVisible()
        logDockWidget.setWidget(logView)

        # Undo view widget
        undoDockWidget = QtGui.QDockWidget("Undo History", self)
        undoDockWidget.setObjectName("undoDockWidget")
        undoDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        undoView = QtGui.QUndoView(self.undo_stack)
        undoDockWidget.setWidget(undoView)

        # TODO should only start this when the log viewer window is visible?
        self.start_log_watcher()

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

        # Assign main widget and dock widgets to QMainWindow
        self.setCentralWidget(classTable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, classTreeDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, commentDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, infoDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, refDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, logDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, undoDockWidget)

        # Store widgets for access by other objects
        self.classTable = classTable
        self.commentView = commentView
        self.infoView = infoView
        self.classTree = classTree
        self.logView = logView
        self.undoView = undoView
        self.refView = refView

        # Store docks for access by other objects
        self.commentDockWidget = commentDockWidget
        self.infoDockWidget = infoDockWidget
        self.classTreeDockWidget = classTreeDockWidget
        self.logDockWidget = logDockWidget
        self.undoDockWidget = undoDockWidget
        self.refDockWidget = refDockWidget

        # Perform other UI-related initialization tasks
        self.center()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowTitle('IDFPlus Editor')
        self.setWindowIcon(QtGui.QIcon(':/images/eplus_sm.png'))

        # Status bar setup
        self.statusBar().showMessage('Status: Ready')
        self.statusBar().setSizeGripEnabled(True)
        self.versionLabel = QtGui.QLabel()
        self.versionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.versionLabel.setMinimumSize(self.versionLabel.sizeHint())
        self.versionLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.versionLabel)

    def create_tray_menu(self):
        """Creates an icon and menu for the system tray"""

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
        self.trayIcon.setIcon(QtGui.QIcon(':/images/eplus_sm.png'))
        self.trayIcon.setToolTip('IDFPlus')
        self.trayIcon.show()

    def update_log_viewer(self, changed_path):
        with open(changed_path) as f:
            text=f.read()
            self.logView.clear()
            self.logView.insertPlainText(text)
        self.logView.centerCursor()

    def start_log_watcher(self):
        self.watcher = QtCore.QFileSystemWatcher()
        log_path = os.path.join(c.LOG_DIR, c.LOG_FILE_NAME)
        self.watcher.addPath(log_path)
        self.watcher.fileChanged.connect(self.update_log_viewer)

    def getRowOrCol(self, index):
        #TODO use this throughout?
        if self.obj_orientation == QtCore.Qt.Horizontal:
            return index.column()
        if self.obj_orientation == QtCore.Qt.Vertical:
            return index.row()


class TableView(QtGui.QTableView):
   '''Subclass of QTableView used to override mousePressEvent'''

   def __init__(self, *args, **kwargs):
       super(TableView, self).__init__(*args, **kwargs)

   # # Ads single-click editing
   # def mousePressEvent(self, event):
   #     if event.button() == QtCore.Qt.LeftButton:
   #         index = self.indexAt(event.pos())
   #         if index.isValid():
   #             self.edit(index)
   #     QtGui.QTableView.mousePressEvent(self, event)

   # def commitData(self, *args, **kwargs):
   #     print('data committed')
   #     #TODO put transaction commit in here?
   #     #TODO catch multiple paste and commit only once?
   #     super(TableView, self).commitData(*args, **kwargs)


class MyZODB(object):
    """Wrapper for ZODB connection"""

    def __init__(self):
        log.info('Setting up database...')
        import transaction
        self.transaction = transaction
        tempfile.tempdir = appdirs.user_cache_dir(c.APP_NAME, c.COMPANY_NAME)

        try:
            os.makedirs(tempfile.tempdir)
        except OSError:
            if not os.path.isdir(tempfile.tempdir):
                raise

        self.tmp = tempfile.NamedTemporaryFile(prefix='idfplus_cache_', delete=True)
        self.storage = FileStorage.FileStorage(self.tmp.name)
        self.db = DB(self.storage)
        self.connection = self.db.open()
        self.dbroot = self.connection.root

    def close(self):
        """Closes connections/files and cleans up."""
        log.info('Closing database...')
        import os
        self.transaction.commit()
        self.connection.close()
        self.db.close()
        self.storage.close()
        self.tmp.close()
        for extension in ['.lock', '.index', '.tmp']:
            os.remove(self.tmp.name + extension)
