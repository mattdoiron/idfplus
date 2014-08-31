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
from . import gui

# Resource imports for icons
from . import icons_rc

# Global variables
__version__ = '0.0.1'
log = logger.setup_logging(c.LOG_LEVEL, __name__)

class IDFPlus(QtGui.QMainWindow, gui.UI_MainWindow):
    """Main GUI window for IDFPlus program."""

    def __init__(self):
        super(IDFPlus, self).__init__()

        # Create application UI (call this first)
        self.create_ui()

        # Load settings (call this second)
        self.settings = c.Settings(self)
        self.settings.read_settings()

        # TODO should only start this when the log viewer window is visible?
        self.start_log_watcher()

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
        # self.clipboard = QtGui.QApplication.instance().clipboard()
        # self.obj_clipboard = []

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
            dialog_name = 'Open file'
            file_dialog = QtGui.QFileDialog()
            file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
            file_name, filt = file_dialog.getOpenFileName(self, dialog_name,
                                                          directory, formats)
            if file_name:
                self.load_file(file_name)

    def find_idd_file(self):
        """Called to open an idd file location."""
        # print('find idd file was called')
        if self.ok_to_continue():
            home_dir = os.path.expanduser('~')
            directory = os.path.dirname(self.file_path) if self.file_path else home_dir
            formats = "EnergyPlus IDD Files (*.idd)"
            dialog_name = 'Open EnergyPlus Installation Directory'
            file_dialog = QtGui.QFileDialog()
            file_dialog.setFileMode(QtGui.QFileDialog.Directory)
            file_name, filt = file_dialog.getOpenFileName(self, dialog_name,
                                                          directory, formats)
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

        # idd = datamodel.IDDFile()
        idd_parser = parser.IDDParser()

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
                if fname != current and QtCore.QFile.exists(fname):
                    recentFiles.append(fname)
        if recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"),
                                       "&%d %s" % (i + 1, QtCore.QFileInfo(fname).fileName()),
                                       self)
                action.setData(fname)
                action.triggered.connect(self.load_file)
                self.fileMenu.addAction(action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])

    def table_clicked(self, index):
        if not index.isValid():
            return

        try:
            G = self.idf._graph
            node = self.idf[self.current_obj_class][index.column()][index.row()]

            ancestors = nx.ancestors(G, node)
            descendants = nx.descendants(G, node)

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

        self.default_model.sourceModel().dataChanged.connect(self.update_tree_view)

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

    def update_tree_view(self):
        print('updated tree view')
        self.classTree.sourceModel().setData(0, 123123)

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
