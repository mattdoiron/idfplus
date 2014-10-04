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
# from BTrees.OOBTree import OOBTree
# from ZODB import FileStorage
# from ZODB import DB
# from collections import deque
# import tempfile
# import appdirs
import networkx as nx

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import delegates
from . import tablemodel
from . import parser
from . import idfsettings
from . import datamodel
from . import logger
from . import commands
from . import treemodel
from . import gui

# Resource imports for icons
from . import icons_rc

# Global variables
__version__ = '0.0.1'
log = logger.setup_logging(idfsettings.LOG_LEVEL, __name__)

class IDFPlus(QtGui.QMainWindow, gui.UI_MainWindow, idfsettings.Settings):
    """Main GUI window for IDFPlus program."""

    def __init__(self):
        super(IDFPlus, self).__init__()

        # Create application UI (call this first)
        self.create_ui()

        # Load settings (call this second)
        # self.settings = idfsettings.Settings()
        self.init_settings(self)
        self.read_settings()

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
        self.obj_clipboard = []

        # Create main application elements
        self.create_actions()
        self.create_tool_bars()
        self.create_menus()
        self.create_shortcuts()
        self.create_tray_menu()
        self.create_progress_bar()

        # In-memory ZODB databases don't support undo! Use an on-disk cache
        # self.db = MyZODB()

        # Create a place to store all open files
        # self.db.dbroot.files = OOBTree()
        # self.files = self.db.dbroot.files
        # self.idd = OOBTree()

    def closeEvent(self, event):
        """Called when the application is closed."""
        if self.ok_to_continue():
            self.write_settings()
            # self.db.close()
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

    def find_idd_file(self, version):
        """Called to open an idd file location."""
        # print('find idd file was called')
        if self.ok_to_continue():
            home_dir = os.path.expanduser('~')
            directory = os.path.dirname(self.file_path) if self.file_path else home_dir
            formats = "EnergyPlus IDD Files (*.idd)"
            dialog_name = 'Select EnergyPlus IDD File (Version: {})'.format(version)
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
        # self.files.update({0:idf})
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
            if not self.find_idd_file(e.version):
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
        self.commentView.setText("".join(self.idf['Version'][0].comments))
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
        if self.prefs['recent_files']:
            for fname in self.prefs['recent_files']:
                if fname != current and QtCore.QFile.exists(fname):
                    recentFiles.append(fname)
        if recentFiles:
            # self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"),
                                       '{} - {}'.format(i + 1, QtCore.QFileInfo(fname).fileName()),
                                       # "&%d %s" % (i + 1, QtCore.QFileInfo(fname).fileName()),
                                       self)
                action.setData(fname)
                action.triggered.connect(self.load_file)
                self.fileMenu.addAction(action)
            self.fileMenu.addAction(self.clearRecentAct)
            self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])

    def clear_recent(self):
        self.prefs['recent_files'] = []
        self.update_file_menu()

    def table_selection_changed(self, selected, deselected):
        if not selected:
            return
        index = selected.first().topLeft()
        if not index or not index.isValid():
            return

        try:
            G = self.idf._graph
            if self.obj_orientation == QtCore.Qt.Vertical:
                node = self.idf[self.current_obj_class][index.column()][index.row()]
            else:
                node = self.idf[self.current_obj_class][index.row()][index.column()]

            ancestors = nx.ancestors(G, node)
            descendants = nx.descendants(G, node)
            # print('degree: {}'.format(nx.degree(G, node)))
            # print('node value: {}'.format(node.value))
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

        # Also update the infoview
        if self.obj_orientation == QtCore.Qt.Vertical:
            info_index = index.row()
        else:
            info_index = index.column()
        obj_info = self.idd[self.current_obj_class].get_info()
        field_info = self.idd[self.current_obj_class][info_index].get_info()
        self.infoView.setText(obj_info + "\n\n" + field_info)

    def ref_tree_double_clicked(self, index):
        """Responds when the reference tree widget is double-clicked.
        """
        if not index.isValid():
            return
        field = self.refView.model().get_field(index)
        obj_class, obj_index, field_index = field.field_id

        # Get the tree selection model and model
        tree_model = self.classTree.model()
        tree_selection_model = self.classTree.selectionModel()

        # Create an index to serve as the starting point for the tree search
        start_index = tree_model.index(0, 0)

        # Find the items in the class tree that contain the object class
        matches = tree_model.match(start_index,
                                   QtCore.Qt.DisplayRole,
                                   obj_class,
                                   hits=1,
                                   flags=int(QtCore.Qt.MatchRecursive |
                                             QtCore.Qt.MatchExactly |
                                             QtCore.Qt.MatchWrap))

        # Select the resulting found item (this also triggers a load of the table view)
        tree_selection_model.setCurrentIndex(matches[0],
                                             QtGui.QItemSelectionModel.SelectCurrent)

        # Scroll to the new selection
        self.classTree.scrollTo(matches[0], QtGui.QAbstractItemView.PositionAtCenter)

        # After the table is loaded, get its model and selection model
        table_selection_model = self.classTable.selectionModel()
        table_model = self.classTable.model().sourceModel()

        # Create an index for the target field with the table's model
        if self.obj_orientation == QtCore.Qt.Vertical:
            table_index = table_model.createIndex(field_index, obj_index,
                                                  QtCore.QModelIndex().internalId())
        else:
            table_index = table_model.createIndex(obj_index, field_index,
                                                  QtCore.QModelIndex().internalId())

        # Give focus to the class table
        self.classTable.setFocus()

        # Scroll to the target field (shouldn't need this!)
        self.classTable.selectColumn(obj_index)

        # Select the target index
        table_selection_model.setCurrentIndex(table_index,
                                              QtGui.QItemSelectionModel.SelectCurrent)

    def custom_table_context_menu(self, position):

        # Create a menu and populate it with actions
        menu = QtGui.QMenu(self)
        menu.addAction(self.undoAct)
        menu.addAction(self.redoAct)
        menu.addSeparator()
        menu.addAction(self.copyObjAct)
        menu.addAction(self.dupObjAct)
        menu.addAction(self.delObjAct)
        menu.addAction(self.newObjAct)
        menu.addAction(self.cutAct)
        menu.popup(self.classTable.viewport().mapToGlobal(position))

    def addActions(self, target, actions):
        """Helper to add actions or a separator easily."""
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def tableFilterRegExpChanged(self):
        pattern = self.filterBox.text()
        if len(pattern) < 3:
            pattern = None
        if not self.classTable.model():
            return
        self.classTable.model().setFilterRegExp(pattern)
        self.classTable.model().invalidateFilter()
        self.classTable.selectionModel().reset()

    def treeFilterRegExpChanged(self):
        pattern = self.filterTreeBox.text()
        if len(pattern) < 3:
            pattern = None
        if not self.classTree.model():
            return
        self.classTree.model().setFilterRegExp(pattern)
        self.classTree.model().invalidateFilter()
        self.classTree.expandAll()

    def clearFilterClicked(self):
        self.filterBox.clear()
        self.tableFilterRegExpChanged()

    def clearTreeFilterClicked(self):
        self.filterTreeBox.clear()
        self.treeFilterRegExpChanged()

    def caseSensitivityChanged(self):
        if self.caseSensitivity.isChecked() == True:
            sensitivity = QtCore.Qt.CaseSensitive
        else:
            sensitivity = QtCore.Qt.CaseInsensitive
        self.classTable.model().setFilterCaseSensitivity(sensitivity)
        self.tableFilterRegExpChanged()

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
            try:
                self.prefs['recent_files'].insert(0, file_name)
            except AttributeError as e:
                self.prefs['recent_files'] = [file_name]
            while len(self.prefs['recent_files']) > 9:
                self.prefs['recent_files'].pop()

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

        if len(self.classTable.selectedIndexes()) <= 0:
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_selection=True)
        self.undo_stack.push(cmd)

    def deleteObject(self):

        if len(self.classTable.selectedIndexes()) <= 0:
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.DeleteObjectCmd(self)
        self.undo_stack.push(cmd)

    def cutObject(self):

        if len(self.classTable.selectedIndexes()) <= 0:
            return False

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

    def copyObject(self, save=None):
        """Copies object(s) to the clipboard for pasting to other programs."""

        # Get the selected indexes then map them to the source model
        indexes = self.classTable.selectedIndexes()
        model = self.classTable.model()

        # Make sure there was something selected
        if len(indexes) <= 0:
            return False, None

        # Get list of contiguous indexes and objects
        groups, obj_list = model.get_contiguous(indexes, False)

        # Copy the object(s) to the clipboard or delete them
        if save is False:
            return groups, obj_list
        else:
            self.obj_clipboard = obj_list
            return True, None

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
        current_persistent = QtCore.QPersistentModelIndex(current)

        tree_model = self.classTree.model()
        if tree_model:
            tree_model.filter_empty = not self.classTree.model().filter_empty
            self.treeFilterRegExpChanged()

        #TODO need to find a way to handle what happens when 'currentIndex' disappears
        #     during the filtering.

        tree.scrollTo(current_persistent, QtGui.QAbstractItemView.PositionAtCenter)

    def load_table_view(self, obj_class):
        """Loads the table of objects for the specified class name.
        :param obj_class:
        """
        #TODO instantiate TransposeProxyModel and IDFObjectTableModel elsewhere?

        # Filter out group headers
        if obj_class not in self.idd:
            return

        # Clear the table filter when changing classes
        self.clearFilterClicked()

        # Save some variables
        table = self.classTable

        # Create the default table model
        default_model = tablemodel.IDFObjectTableModel(obj_class, self.idf, table)

        # If objects are vertical, create transposed model
        if self.obj_orientation == QtCore.Qt.Vertical:
            model = tablemodel.TransposeProxyModel(default_model)
            model.setSourceModel(default_model)
        else:
            model = default_model

        # Create additional proxy for sorting and filtering
        sortable = tablemodel.SortFilterProxyModel(self.obj_orientation, table, model)
        sortable.setSourceModel(model)

        # Assign model to table (enable sorting FIRST)
        table.setSortingEnabled(True)
        # sortable.setDynamicSortFilter(True)
        table.setModel(sortable)

        # Create generic delegates for table cells
        my_delegates = delegates.GenericDelegate(self,
                                                 obj_class,
                                                 self.idd,
                                                 self.obj_orientation)
        table.setItemDelegate(my_delegates)

        # Connect some signals
        # default_model.sourceModel().dataChanged.connect(self.update_tree_view)
        selection_model = table.selectionModel()
        selection_model.selectionChanged.connect(self.table_selection_changed)

        # Grab the comments
        comments = ''
        if self.idf[obj_class]:
            comment_list = self.idf[obj_class][0].comments
            if comment_list:
                comments = "".join(self.idf[obj_class][0].comments)

        # Now that there is a class selected, enable some actions and set some vars
        self.newObjAct.setEnabled(True)
        self.delObjAct.setEnabled(True)
        self.transposeAct.setEnabled(True)
        self.infoView.setText(self.idd[obj_class].get_info())
        self.commentView.setText(comments)
        self.current_obj_class = obj_class

    def load_tree_view(self):
        """Loads the tree of class type names."""

        source_model = treemodel.ObjectClassTreeModel(self.idf,
                                                      ("Object Class", "Count"),
                                                      self.classTree)

        # Create additional proxy for sorting and filtering
        proxy_model = treemodel.TreeSortFilterProxyModel()
        proxy_model.setSourceModel(source_model)

        self.classTree.setModel(proxy_model)
        self.classTree.setRootIsDecorated(False)
        self.classTree.expandAll()
        self.classTree.setColumnWidth(0, 280)
        self.classTree.setColumnWidth(1, 10)

        selection_model = self.classTree.selectionModel()
        selection_model.selectionChanged.connect(self.classSelected)

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

        # If nothing is selected, return
        if not current:
            return

        # Find the index of the first selection
        index = current.first().topLeft()

        # If the index is not valid, return
        if not index or not index.isValid():
            return

        # Get the class name from the tree's data method
        data = self.classTree.model().data(index, QtCore.Qt.DisplayRole)

        # If there is no data, return
        if not data:
            return

        # Load the corresponding class in the tableView
        self.load_table_view(data)

    def update_log_viewer(self, changed_path):
        with open(changed_path) as f:
            text=f.read()
            self.logView.clear()
            self.logView.insertPlainText(text)
        self.logView.centerCursor()

    def start_log_watcher(self):
        self.watcher = QtCore.QFileSystemWatcher()
        log_path = os.path.join(idfsettings.LOG_DIR, idfsettings.LOG_FILE_NAME)
        self.watcher.addPath(log_path)
        self.watcher.fileChanged.connect(self.update_log_viewer)
