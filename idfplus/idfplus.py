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
import transaction
import tempfile

# PySide imports
import PySide
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import delegates
from . import tablemodel
from . import parser
from . import idfsettings as c
from . import datamodel
from . import logger

# Resource imports
from . import icons_qr  # Used for icons (in text format)
from . import misc_icons_qr  # Used for icons (in text format)

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

        # Create main application elements
        self.create_actions()
        self.create_tool_bars()
        self.create_menus()
        self.create_shortcuts()
        self.create_tray_menu()

        # Connect some slots and signals
        self.classTree.currentItemChanged.connect(self.iWasChanged)

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
            directory = os.path.dirname(self.file_path) if self.file_path else "."
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
            directory = os.path.dirname(self.file_path) if self.file_path else "."
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

        total_size = os.path.getsize(file_path)
        self.progressDialogIDD = QtGui.QProgressDialog("Loading IDD File", "", 0,
                                                       total_size, self)
        message = "Loading {}...".format(file_path)
        self.progressDialogIDD.setLabelText(message)
        self.progressDialogIDD.setWindowTitle('Loading IDD File')
        self.progressDialogIDD.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDD.setMinimumDuration(500)
        self.progressDialogIDD.setCancelButton(None)
        self.progressDialogIDD.show()
        self.statusBar().showMessage(message, 5000)

        idd = datamodel.IDDFile()
        idd_parser = parser.IDDParser(idd)

        for progress in idd_parser.parse_idd(file_path):
            self.progressDialogIDD.setValue(progress)

        return True #parser.save_idd(idd)

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

        total_size = os.path.getsize(file_path)
        self.progressDialogIDF = QtGui.QProgressDialog("Loading IDF File", "", 0,
                                                       total_size, self)
        message = "Loading {}...".format(file_path)
        self.progressDialogIDF.setLabelText(message)
        self.progressDialogIDF.setWindowTitle('Loading IDF File')
        self.progressDialogIDF.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDF.setMinimumDuration(500)
        self.progressDialogIDF.setCancelButton(None)
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

        self.groups = self.idd.groups
        self.load_tree_view()
        self.classTable.setModel(None)
        self.commentView.setText(str(len(self.idf)))  # test only
        self.dirty = False  # Move this into tablemodelContainer?
        self.file_path = file_path
        self.add_recent_file(file_path)
        message = "Loaded %s" % os.path.basename(file_path)
        self.update_status(message)
        self.set_current_file(file_path)
        return True

    def save(self):
        """Called by save action."""
        if self.file_path:
            return self.save_file()
        return self.save_as()

    def save_as(self):
        """Called by the save as action."""
        directory = os.path.dirname(self.file_path) if self.file_path is not None else '.'
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

    def undo(self):
        """Called by the undo action. Not yet implemented"""

        print('calling undo')
        import sys
        no_initial = lambda tx: True if tx['description'] not in ['initial database creation','Load file'] else False
        undo_log = self.db.db.undoLog(0, sys.maxint, no_initial)

        if len(undo_log) <= 0:
            print('nothing to undo!')
            return

        # self.classTable.model().layoutAboutToBeChanged.emit()

        self.db.db.undo(undo_log[0]['id'])
        transaction.get().note('Undo {}'.format(undo_log[0]['description']))
        transaction.commit()
        self.db.connection.sync()

        # Let the table model know that something has changed. For now, the whole
        # table must be reloaded because undo could do any number of things, all which
        # need different update operations (like insert rows, remove columns, etc).
        # self.classTable.model().dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.load_table_view(self.current_obj_class)

        # self.classTable.model().dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        # self.classTable.model().layoutChanged.emit()

        print('undo complete')


    def redo(self):
        """Called by the redo action. Not yet implemented"""
        import sys
        import pprint
        no_initial = lambda tx: True if tx['description'] not in ['initial database creation'] else False
        undo_log = self.db.db.undoLog(0, sys.maxint, no_initial)
        pprint.pprint(undo_log)
        self.commentView.setText('undo log: {}'.format(undo_log))

    def about(self):
        """Called by the about action."""
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

    def create_actions(self):
        """Creates appropriate actions for use in menus and toolbars."""

        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'), "&New",
                self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.new_file)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open_file)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QtGui.QAction("Save &As...", self,
                shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.save_as)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard")
#                triggered=self.textEdit.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.copySelected)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.pasteSelected)

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
                triggered=self.transpose_table)

        self.newObjAct = QtGui.QAction("New Obj", self,
                statusTip="Create a new object in the current class.",
                triggered=self.newObject)

        self.dupObjAct = QtGui.QAction("Dup Obj", self,
#                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Duplicate the current Object.",
                triggered=self.duplicateObject)

        self.delObjAct = QtGui.QAction("Del Obj", self,
               # shortcut=QtGui.QKeySequence('Del'),
                statusTip="Delete the current Object.",
                triggered=self.deleteObject)

        self.cutAct.setEnabled(False)
        # self.copyAct.setEnabled(False)
        # self.pasteAct.setEnabled(False)
        self.transposeAct.setEnabled(False)
        self.newObjAct.setEnabled(False)
        self.dupObjAct.setEnabled(False)
        self.delObjAct.setEnabled(False)

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
        self.editMenu.addAction(self.pasteAct)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.classTree.parent().toggleViewAction())
        self.viewMenu.addAction(self.infoView.parent().toggleViewAction())
        self.viewMenu.addAction(self.commentView.parent().toggleViewAction())
        self.viewMenu.addAction(self.logView.parent().toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fileToolBar.toggleViewAction())
        self.viewMenu.addAction(self.editToolBar.toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

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
                action = QtGui.QAction(QtGui.QIcon(":/icon.png"),
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
        self.editToolBar.addAction(self.delObjAct)
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)
        self.editToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        self.viewToolBar = self.addToolBar("View Toolbar")
        self.viewToolBar.setObjectName('viewToolBar')
        self.viewToolBar.addAction(self.transposeAct)
        self.viewToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

    def create_shortcuts(self):
        """Creates keyboard shortcuts."""
        # QtGui.QShortcut(QtGui.QKeySequence('Ctrl+v'),self).activated.connect(self._handle_paste)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'),self).activated.connect(self.copy_test)
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
    def addActions(self, target, actions):
        """Helper to add actions or a separator easily."""
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def set_current_file(self, file_name):
        """Sets the current file globaly and updates title, statusbar, etc."""
        self.file_path = file_name
        self.setWindowModified(False)

        if self.file_path:
            file_name = QtCore.QFileInfo(self.file_path).fileName()
            shownName = file_name
        else:
            shownName = 'Untitled'

        self.setWindowTitle("%s[*] - Application" % shownName)
        self.update_status(shownName)

#    def loadInitialFile(self):
#       '''Loads the previously open file upon program start.'''
#        settings = QtCore.QSettings()
#        fname = settings.value("LastFile")
#        file_path = self.file_path
#        if file_path and QtCore.QFile.exists(file_path):
#            self.open_file()

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
        if self.file_path is not None:
            basename = os.path.basename(self.file_path)
            self.setWindowTitle("IDFPlus Editor - %s[*]" % basename)
#        elif not self.image.isNull():
#            self.setWindowTitle("IDFPlus Editor - Unnamed[*]")
        else:
            self.setWindowTitle("IDFPlus Editor[*]")
            self.setWindowModified(self.dirty)

    def copy_test(self):
        """Testing for copy and paste."""
#        index = self.mainView.bottomright.currentIndex()
        selected = self.classTable.selectionModel()
#        self.mainView.topright.setText(str(index.row()))
#        self.mainView.topright.setText(str(selected.selectedRows()))
        print(str(selected.selectedIndexes()))
#        print str(selected.selectedColumns())

    def setVisible(self, visible):
        """Integrates system tray with minimize/maximize.
        :param visible:
        """
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(IDFPlus, self).setVisible(visible)

    def newObject(self):
        #TODO change from insertColumns/Rows to insertObject in IDFFile class?
        selected = self.classTable.selectionModel()
        indexes = selected.selectedIndexes()

        # Detect orientation, then make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in indexes])
            index_list = list(index_set)
            model = self.classTable.model().sourceModel()

            if len(indexes) <= 0:
                # No selection, so add to end of object list
                position = model.columnCount(QtCore.QModelIndex())
            else:
                # Selection made so insert at end of selection
                position = index_list[-1] + 1

            model.insertColumns(position, 1)
        else:
            index_set = set([index.row() for index in indexes])
            index_list = list(index_set)
            model = self.classTable.model()

            if len(indexes) <= 0:
                position = model.rowCount(QtCore.QModelIndex())
            else:
                position = index_list[-1] + 1

            model.insertRows(position, 1)

        print('new obj added')

    def duplicateObject(self):
        print('duplicate object called')

    def moveObject(self, position, source, destination):
        """Moves (reorders) objects."""
        if self.obj_orientation == QtCore.Qt.Vertical:
            model = self.classTable.model().sourceModel()
            model.moveRows(self, position, source, destination)
        else:
            model = self.classTable.model()
            model.moveColumns(self, position, source, destination)

        print('move object called')

    def copyObject(self):
        """Copies object(s) to the clipboard for pasting to other programs."""
        print('copy object called')

    def copySelected(self):
        """Copies the selected cells to the clipboard for pasting to other programs."""
        print('copySelected call started')


        # selection_model = self.classTable.selectionModel()
        # indexes = selection_model.selectedIndexes()
        indexes = self.classTable.selectedIndexes()

        # selection = selection_model.selection().first()
        # selection_indexes = selection.indexes() # crashes!

        if self.obj_orientation == QtCore.Qt.Vertical:
            first = indexes[0].column()
            last = indexes[-1].column()
        else:
            first = indexes[0].row()
            last = indexes[-1].row()

        print('selection size: first: {} last: {}'.format(first, last))

        # for item in selection_indexes:
        #     print('item: {}'.format(item.data()))

        # print('items: {}'.format(selection_indexes))
        # print('number selected: {}'.format(selection.count()))

        to_copy_list = [i.data() for i in indexes if i.column() == first]
        print(to_copy_list)

        to_copy = ''
        for i in indexes:
            to_copy += i.data()
            to_copy += '\n'

            if self.obj_orientation == QtCore.Qt.Vertical:
                if i.column() == last:
                    to_copy += '\t'
            else:
                if i.row() == last:
                    to_copy += '\t'

        # to_copy = '\n'.join(to_copy_list)

        print(to_copy)

        # mimeData = self.clipboard.mimeData()
        mode = QtGui.QClipboard.Clipboard
        self.clipboard.clear(mode)
        self.clipboard.setText(to_copy, mode)

        # if self.clipboard.mimeData().hasHtml():
        #     self.clipboard.setText(mimeData.html(), mode=mode)
        #     self.clipboard.setTextFormat(QtCore.Qt.RichText)
        # else:
        #     self.clipboard.setText(mimeData.text(), mode=mode)
        #     self.clipboard.setTextFormat(QtCore.Qt.PlainText)

        # self.infoView.setText()
        print('copySelected call ended')

    def pasteSelected(self):
        print('paste selected called')
        # clipboard = QtGui.QApplication.clipboard()
        # mimeData = clipboard.mimeData()
        self.infoView.setPlainText(self.clipboard.mimeData().text())

        # if mimeData.hasHtml():
        #     self.infoView.setText(mimeData.html())
        # else:
        #     self.infoView.setPlainText(mimeData.text())

        # self.infoView.setText()
        print('paste selected called')

    def deleteObject(self):
        #TODO change from removeColumns/Rows to removeObject in IDFFile class?
        selected = self.classTable.selectionModel()
        indexes = selected.selectedIndexes()
        if len(indexes) <= 0:
            return

        # Make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in indexes])
        else:
            index_set = set([index.row() for index in indexes])
        count = len(list(index_set))

        if self.obj_orientation == QtCore.Qt.Vertical:
            model = self.classTable.model().sourceModel()
            position = indexes[0].column()
            model.removeColumns(position, count)
        else:
            model = self.classTable.model()
            position = indexes[0].row()
            model.removeRows(position, count)

        print('obj deleted: pos {}, count {}'.format(position, count))

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

    def _handle_paste(self):
        """Testing for copy and paste."""
        clipboard_text = QtGui.QApplication.instance().clipboard().text()
#        item = QtGui.QTableWidgetItem()
#        item.setText(clipboard_text)
#        self.tv.setItem(0, 0, item)
        print(clipboard_text)
        self.infoView.setText(clipboard_text)

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
        sortable = tablemodel.SortFilterProxyModel()
        sortable.setSourceModel(model)
        # sortable.setDynamicSortFilter(True)  # Needed?

        # Assign model to table and set some variables (enable sorting FIRST)
        table.setSortingEnabled(True)
        table.setModel(sortable)

        # Create generic delegates for table cells
        my_delegates = delegates.GenericDelegate(obj_class,
                                                 self.idd,
                                                 self.obj_orientation)
        table.setItemDelegate(my_delegates)

        self.newObjAct.setEnabled(True)
        self.delObjAct.setEnabled(True)
        self.transposeAct.setEnabled(True)
        self.infoView.setText(self.idd[self.current_obj_class].get_info)

    def load_tree_view(self):
        """Loads the tree of class type names."""
        #TODO modify this to use a custom datamodel linking to the same
        # IDFFile object, but interpreting it differently. This way when
        # the object counts change, they will automatically update. Would
        # this method also be faster?

        tree = self.classTree
        tree.clear()
        group = ''
        group_root = None

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

            objs = self.idf.get(obj_class, None)
            obj_count = len(objs or []) or ''

            child = QtGui.QTreeWidgetItem([obj_class, str(obj_count)])
            child.setTextAlignment(1, QtCore.Qt.AlignRight)
            group_root.addChild(child)

#            left.setCurrentItem(left.topLevelItem(0))
#        left.itemClicked.connect(self.iWasClicked)
#        left.itemActivated.connect(self.iWasClicked)
#        left.currentItemChanged.connect(self.iWasChanged)
#        left.itemPressed.connect(self.iWasClicked)

    def transpose_table(self):
        """Transposes the table"""
        if self.obj_orientation == QtCore.Qt.Horizontal:
            self.obj_orientation = QtCore.Qt.Vertical
            self.classTable.horizontalHeader().setMovable(True)
            self.classTable.verticalHeader().setMovable(False)
            log.info('Setting object orientation to vertical.')
        else:
            self.obj_orientation = QtCore.Qt.Horizontal
            self.classTable.horizontalHeader().setMovable(False)
            self.classTable.verticalHeader().setMovable(True)
            # print('Setting object orientation to: Horizontal')

        self.load_table_view(self.current_obj_class)

    def search(self, dictionary, searchFor):
        """Brute force search trial
        :param dictionary:
        :param searchFor:
        """
        for key in dictionary:
            for obj in dictionary[key]:
                for val in obj:
                    if searchFor in val.value:
                        return key
        return None

    def testSignal(self, myint):
        """Test signal"""
        self.progressDialog.setValue(myint)

    def iWasChanged(self, current, previous):
        """Test call to slot"""
        if (current or current.parent()) is None:
            return
        # if current.parent() is None:
        #     return
        self.load_table_view(current.text(0))

    def iWasChanged2(self, current, previous):
        """Test call to slot"""
        print('test iwaschanged2')

    def create_ui(self):
        """Setup main UI elements, dock widgets, UI-related elements, etc. """

        log.debug('Loading UI')
        # Object class table widget
        classTable = QtGui.QTableView(self)
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont("Arial", 9)
        classTable.setFont(font)
        fm = classTable.fontMetrics()
        classTable.setWordWrap(True)

        classTable.horizontalHeader().setMovable(True)
        classTable.verticalHeader().setMovable(False)
        # classTable.horizontalHeader().setContentsMargins(0, 0, 0, 0)
        # classTable.verticalHeader().setContentsMargins(0, 0, 0, 0)
        classTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.horizontalHeader().setDefaultSectionSize(c.DEFAULT_COLUMN_WIDTH)
        classTable.verticalHeader().setDefaultSectionSize(fm.height() + 5)
        # classTable.setStyleSheet("QTableView {padding: 0px; border: 0px;} ")

        # classTable.resizeColumnsToContents()
        # classTable.resizeRowsToContents()
        classTable.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
        # classTable.columnMoved.connect(self.moveObject)
        classTable.horizontalHeader().sectionMoved.connect(self.moveObject)
        classTable.verticalHeader().sectionMoved.connect(self.moveObject)

        # Object class tree widget
        classTreeDockWidget = QtGui.QDockWidget("Object Classes and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        classTree = QtGui.QTreeWidget(classTreeDockWidget)
        header = QtGui.QTreeWidgetItem(['Object Class', 'Count'])
        header.setFirstColumnSpanned(True)
        classTree.setHeaderItem(header)
        classTree.setUniformRowHeights(True)
        classTree.setFont(font)
        # classTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        classTree.setAlternatingRowColors(True)
        classTreeDockWidget.setWidget(classTree)
        classTree.setColumnWidth(0, 280)
        classTree.setColumnWidth(1, 10)
        classTree.header().resizeSection(0, 280)
        classTree.header().resizeSection(1, 10)

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

        # Logging and debugging widget
        logDockWidget = QtGui.QDockWidget("Log Viewer", self)
        logDockWidget.setObjectName("logDockWidget")
        logDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        logView = QtGui.QPlainTextEdit(logDockWidget)
        logView.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        logView.setReadOnly(True)
        logView.ensureCursorVisible()
        logDockWidget.setWidget(logView)

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
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, logDockWidget)

        # Store widgets for access by other objects
        self.classTable = classTable
        self.commentView = commentView
        self.infoView = infoView
        self.classTree = classTree
        self.logView = logView

        # Store docks for access by other objects
        self.commentDockWidget = commentDockWidget
        self.infoDockWidget = infoDockWidget
        self.classTreeDockWidget = classTreeDockWidget
        self.logDockWidget = logDockWidget

        # Perform other UI-related initialization tasks
        self.center()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowTitle('IDFPlus Editor')
        self.statusBar().showMessage('Status: Ready')
        self.setWindowIcon(QtGui.QIcon(':/images/eplussm.gif'))

        testLabel = QtGui.QLabel('test label')
        testLabel.setAlignment(QtCore.Qt.AlignCenter)
        testLabel.setMinimumSize(testLabel.sizeHint())

        testLabel1 = QtGui.QLabel('test label 123')
        testLabel1.setAlignment(QtCore.Qt.AlignCenter)
        testLabel1.setMinimumSize(testLabel1.sizeHint())

        self.statusBar().addWidget(testLabel)
        self.statusBar().addWidget(testLabel1)

        testLabel.setText('this is some text')
        testLabel1.setText('some more text')

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
        self.trayIcon.setIcon(QtGui.QIcon(':/eplussm.gif'))
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
        log_path = os.path.join(c.APP_ROOT, 'data', 'logs', 'idfplus.log')
        self.watcher.addPath(log_path)
        self.watcher.fileChanged.connect(self.update_log_viewer)

    def getRowOrCol(self, index):
        #TODO use this throughout?
        if self.obj_orientation == QtCore.Qt.Horizontal:
            return index.column()
        if self.obj_orientation == QtCore.Qt.Vertical:
            return index.row()


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


class MyZODB(object):
    """Wrapper for ZODB connection"""

    def __init__(self):
        log.info('Setting up database...')
        import transaction
        self.transaction = transaction
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


# class Communicate(QtCore.QObject):
#     """Class used to communicate with other objects in the application"""
#
#     msg = QtCore.Signal(int)

