#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
"""

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
import os
import platform
import subprocess
import sys
# from BTrees.OOBTree import OOBTree
# import networkx as nx

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import delegates
from . import tablemodel
from . import parser
from . import config
from . import datamodel
from . import logger
from . import commands
from . import treemodel
from . import gui
from . import setupwiz

# Resource imports for icons
from . import icons_rc

# Global variables
log = logger.setup_logging(config.LOG_LEVEL, __name__, config.LOG_PATH)

class IDFPlus(QtGui.QMainWindow, gui.UI_MainWindow):
    """Main GUI window for IDFPlus program."""

    def __init__(self):
        super(IDFPlus, self).__init__()

        # Load settings (call this first)
        log.info('Reading settings')
        self.prefs = config.Settings()

        # Create application UI (call this second)
        self.create_ui()

        # Set some instance variables
        self.file_path = None
        self.idd = None
        self.idf = None
        self.groups = None
        self.fullTree = True
        self.file_dirty = False
        self.obj_orientation = QtCore.Qt.Vertical
        self.current_obj_class = None
        self.obj_clipboard = []

        # Create main application elements
        self.create_actions()
        self.create_tool_bars()
        self.create_menus()
        self.create_shortcuts()
        self.create_tray_menu()
        self.create_progress_bar()

        self.prefs.restore_state(self)
        # Create a place to store all open files
        # self.db.dbroot.files = OOBTree()
        # self.files = self.db.dbroot.files
        # self.idd = OOBTree()

    def closeEvent(self, event):
        """Called when the application is closed."""
        if self.ok_to_continue():
            self.prefs.write_settings()
            self.prefs.save_state(self)
            log.info('Shutting down IDFPlus')
            event.accept()
        else:
            event.ignore()

    def new_file(self):
        """Called when a new file is to being created"""
        if self.ok_to_continue():
            self.add_recent_file(self.file_path)
            self.set_current_file('')
            self.load_file(None)

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

    def load_idf(self, file_path):
        log.info('Trying to load file: {}'.format(file_path))

        idf = datamodel.IDFFile()
        # self.files.update({0:idf})

        if file_path:
            idf_parser = parser.IDFParser(idf)
            for progress in idf_parser.parse_idf(file_path):
                self.progressDialogIDF.setValue(progress)
        else:
            log.info('Loading blank IDF file...')
            idf.init_blank()
        log.info('IDF version detected as: {}'.format(idf.version))
        self.idf = idf
        self.idd = idf._idd

    def load_file(self, file_path=None):
        """Loads a specified file or gets the file_path from the sender.
        :rtype : bool
        :param file_path:
        """

        # Detect how/if to proceed
        if file_path:
            log.debug('Loading file from dialog: {}'.format(file_path))
        if file_path is None:
            action = self.sender()
            if isinstance(action, QtGui.QAction):
                if action.text() != "&New":
                    file_path = action.data()
                    log.debug('Loading file from recent file menu: {}'.format(file_path))
                    if not self.ok_to_continue():
                        return False
            else:
                return False

        # Update status
        message = "Loading {}...".format(file_path or 'New File')
        self.statusBar().showMessage(message, 5000)
        if file_path:
            self.progressDialogIDF.setLabelText(message)
            self.progressDialogIDF.show()

        try:
            # Try to load the specified IDF file
            self.load_idf(file_path)

        except datamodel.IDDError as e:
            # Required IDD file doesn't exist so launch IDD wizard
            if not self.launch_idd_wizard(file_path, e.version, e.message):
                # Wizard failed, warn use and cancel
                QtGui.QMessageBox.warning(self, "Processing IDD File Failed",
                                          ("{}\n\nVersion Required: {}\n\nLoading "
                                          "cancelled!".format(e.message, e.version)),
                                          QtGui.QMessageBox.Ok)
                message = ("Loading failed. Could not find "
                           "matching IDD file for version {}.".format(e.version))
                self.progressDialogIDF.cancel()
                self.update_status(e.message)
                return False
        except parser.InvalidIDFObject as e:
            # Invalid name of object, warn use and cancel
            QtGui.QMessageBox.warning(self, "Processing IDF File Failed",
                                      "{}\n\nLoading cancelled!".format(e.message),
                                      QtGui.QMessageBox.Ok)
            message = "Loading failed. Invalid idf object."
            self.progressDialogIDF.cancel()
            self.update_status(message)
            return False

        # Everything worked, so set some variables and update status
        log.debug('Loading tree view...')
        self.groups = self.idd.groups
        self.load_tree_view()
        log.debug('Setting class table model...')
        self.classTable.setModel(None)
        log.debug('Updating recent file list...')
        self.file_path = file_path
        self.add_recent_file(file_path)
        self.set_current_file(file_path)
        self.set_dirty(False)
        self.update_idf_options()
        log.debug('File Loaded Successfully! ({})'.format(file_path or "New File"))
        return True

    def launch_idd_wizard(self, file_path, version, message):
        """Launches the IDD wizard to help user point the editor to IDD file
        :param version:
        :param message:
        :param file_path:
        :return: :bool:
        """
        wizard = setupwiz.SetupWizard(self, version, message)
        try:
            if wizard.exec_():
                self.load_idf(file_path)
                return True
        except (AttributeError, datamodel.IDDError):
            return False

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
            if not (file_name.endswith('.idf') or file_name.endswith('.imf')):
                file_name += '.idf'
            self.file_path = file_name
            self.idf.file_path = file_name
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
            self.set_dirty(False)
            return True
        else:
            return False

    def about(self):
        """Called by the about action."""
        import PySide

        QtGui.QMessageBox.about(self, "About IDFPlus",
                """<b>IDFPlus</b> v{0}
                <p>This is an enhanced editor for EnergyPlus simulation input files.
                For more information please see
                <a href="https://bitbucket.org/mattdoiron/idfplus/">
                https://bitbucket.org/mattdoiron/idfplus/
                </a></p>
                <p>Copyright 2015 Matt Doiron (matt@mindfulmodeller.ca)<br/>
                All rights reserved.</p>
                <p>IDF+ is free software: you can redistribute it and/or modify
                it under the terms of the GNU General Public License as published by
                the Free Software Foundation, either version 3 of the License, or
                (at your option) any later version.</p>
                <p>IDF+ is distributed in the hope that it will be useful,
                but WITHOUT ANY WARRANTY; without even the implied warranty of
                MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
                GNU General Public License at <a href="http://www.gnu.org/licenses/">
                http://www.gnu.org/licenses/</a> for more details.</p>
                <p>Built with: Python {1}, Qt {2} and PyQt {3} on {4}</p>""".format(
                config.__version__, platform.python_version(),
                PySide.QtCore.qVersion(), PySide.__version__,
                platform.system()))

    def navForward(self):
        pass

    def navBack(self):
        pass

    def show_in_folder(self):
        """Opens the location of the current IDF file.
        """

        current_platform = sys.platform
        result = 1

        if self.file_path:
            if current_platform.startswith('linux'):
                dir_path = os.path.dirname(self.file_path)
                result = subprocess.check_call(["xdg-open", dir_path])
            elif current_platform.startswith('win'):
                file_path = os.path.normpath(self.file_path)
                result = subprocess.call(["explorer", "/select,", file_path])
                result = 0  # windows returns 1 for some reason...
            else:
                dir_path = os.path.dirname(self.file_path)
                result = subprocess.check_call(["open", dir_path])

        if result != 0:
            log.debug("Failed to show in folder: {} (on platform: {})"
                      .format(self.file_path, current_platform))

    def open_in_text_editor(self):
        """Opens the current IDF file in the default text editor
        """

        current_platform = sys.platform
        result = 1

        if self.file_path:
            if current_platform.startswith('linux'):
                result = subprocess.check_call(["xdg-open", self.file_path])
            elif current_platform.startswith('win'):
                editor_cmd = subprocess.check_output(['cmd', '/c', 'ftype txtfile'])
                # editor_cmd = "txtfile=%SystemRoot%\\system32\\NOTEPAD.EXE %1\r\n"
                editor = editor_cmd.partition('=')[2].partition(' ')[0]
                editor = editor.replace('%SystemRoot%', os.environ['SYSTEMROOT'])
                win_file_path = os.path.normpath(self.file_path)
                result = subprocess.check_call([editor, win_file_path])
            else:
                result = subprocess.check_call(["open", "-R", self.file_path])

        if result != 0:
            log.debug("Failed to open file: {} (on platform: {})"
                      .format(self.file_path, current_platform))

    def toggle_units(self):
        # Toggle the units
        self.idf.si_units = not self.idf.si_units

        if self.idf.si_units is not True:
            self.idf.options.append('ViewInIPunits')
        else:
            try:
                self.idf.options.remove('ViewInIPunits')
            except ValueError:
                pass

        print(self.idf.options)

        # Refresh the view
        self.load_table_view(self.current_obj_class)

    def update_file_menu(self):
        """Called to update the recent files portion of the file menu"""
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = self.file_path or None
        recent_files = []
        if self.prefs['recent_files']:
            for name in self.prefs['recent_files']:
                if name != current and QtCore.QFile.exists(name):
                    recent_files.append(name)
        if recent_files:
            self.fileMenu.addSeparator().setText('Recent Files')
            for i, name in enumerate(recent_files):
                file_name = QtCore.QFileInfo(name).fileName()
                action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"),
                                       '{} - {}'.format(i + 1, file_name),
                                       self)
                action.setData(name)
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
        _index = selected.first().topLeft()
        if not _index or not _index.isValid():
            return

        # Map index to source model
        partially_mapped = self.classTable.model().mapToSource(_index)
        index = self.classTable.model().sourceModel().mapToSource(partially_mapped)

        # Update the refView
        self.update_reference_view(index)

        # Also update the infoview
        obj_info = self.idd[self.current_obj_class].get_info()
        idd_field = self.idd[self.current_obj_class][index.column()]
        field_info = idd_field.get_info()
        self.infoView.setText(obj_info + "\n\n" + field_info)

        # Also update the units label
        units = self.classTable.model().get_units(idd_field)
        self.unitsLabel.setText('Display Units: {}'.format(units))

        # Update the comments view
        current_obj = self.idf[self.current_obj_class][index.row()]
        comments = ''.join(current_obj.comments)
        self.commentView.blockSignals(True)
        self.commentView.setPlainText(comments)
        self.commentView.blockSignals(False)

    def update_reference_view(self, index):
        """Updates the reference tree view widget"""

        data = self.idf.reference_tree_data(self.current_obj_class, index)

        # # Retrieve the node (could be invalid so use try)
        # try:
        #     ref_graph = self.idf._ref_graph
        #     field = self.idf[self.current_obj_class][index.row()][index.column()]
        #     ancestors = nx.ancestors(ref_graph, field._uuid)
        #     descendants = nx.descendants(ref_graph, field._uuid)
        #     data = [[ref_graph.node[ancestor]['data'] for ancestor in ancestors],
        #             [ref_graph.node[descendant]['data'] for descendant in descendants]]
        # except (nx.exception.NetworkXError, IndexError) as e:
        #     data = None

        # Create a new model for the tree view and assign it, then refresh view
        new_model = treemodel.ReferenceTreeModel(data, ("Field", "Class"), self.refView)
        self.refView.setModel(new_model)
        self.refView.expandAll()

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

        # Find the items in the class tree that contain the object class
        matches = tree_model.match(tree_model.index(0, 0),
                                   QtCore.Qt.DisplayRole,
                                   obj_class,
                                   hits=1,
                                   flags=int(QtCore.Qt.MatchRecursive |
                                             QtCore.Qt.MatchExactly |
                                             QtCore.Qt.MatchWrap))

        # Select the resulting found item (this also triggers a load of the table view)
        tree_selection_model.setCurrentIndex(matches[0],
                                             QtGui.QItemSelectionModel.SelectCurrent)

        # Scroll to the matched selection
        self.classTree.scrollTo(matches[0], QtGui.QAbstractItemView.PositionAtCenter)

        # After the table is loaded, get its model and selection model
        table_source_model = self.classTable.model().sourceModel()
        table_model = self.classTable.model()

        # Create an index for the target field with the table's model
        table_index_source = table_source_model.sourceModel().index(obj_index, field_index)
        table_index_partial = table_source_model.mapFromSource(table_index_source)
        table_index = table_model.mapFromSource(table_index_partial)

        # Give focus to the class table and select the target index
        self.classTable.setFocus()
        self.classTable.setCurrentIndex(table_index)

    def addActions(self, target, actions):
        """Helper to add actions or a separator easily."""
        for action in actions:
            if action is not None:
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
        current_class = QtCore.QPersistentModelIndex(self.classTree.currentIndex())
        self.classTree.model().setFilterRegExp(pattern)
        self.classTree.model().invalidateFilter()
        self.classTree.expandAll()
        self.classTree.scrollTo(current_class, QtGui.QAbstractItemView.PositionAtCenter)

        # If the current class was hidden by the filter, clear the tableView
        if not current_class.isValid():
            self.classTable.setModel(None)

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

        self.setWindowTitle('IDFPlus Editor - {}[*]'.format(shownName))

        if self.idd:
            self.versionLabel.setText('EnergyPlus IDD v{}'.format(self.idd.version))

    def ok_to_continue(self):
        """Checks if there are unsaved changes and prompts for action."""
        if self.file_dirty:
            reply = QtGui.QMessageBox.warning(self,
                                              "Application",
                                              "The document has been modified.\nDo you want to save your changes?",
                                              QtGui.QMessageBox.Save |
                                              QtGui.QMessageBox.Discard |
                                              QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Cancel:
                return False
            elif reply == QtGui.QMessageBox.Save:
                self.save_file()
        return True

    def add_recent_file(self, file_name):
        """Adds file_path to the list of recent files for the file menu.
        :param file_name:
        """
        if not file_name:
            return
        if not file_name in self.prefs['recent_files']:
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
        self.setWindowModified(self.file_dirty)
        if self.file_path is not None:
            basename = os.path.basename(self.file_path)
            self.setWindowTitle('IDFPlus Editor - {}[*]'.format(basename))
        else:
            self.setWindowTitle('IDFPlus Editor')

    def setVisible(self, visible):
        """Integrates system tray with minimize/maximize.
        :param visible:
        """
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(IDFPlus, self).setVisible(visible)

    def newObject(self):
        """Creates a new, blank object."""

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self)
        self.undo_stack.push(cmd)

    def duplicateObject(self):
        """Duplicates a given object."""

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_selection=True)
        self.undo_stack.push(cmd)

    def deleteObject(self):
        """Deletes a given object."""

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.DeleteObjectCmd(self)
        self.undo_stack.push(cmd)

    def cutObject(self):
        """Cuts the object after copying it."""

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
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
        """Pastes the currently copied object(s)."""

        # If there is nothing in the clipboard, stop
        if not self.obj_clipboard:
            return False

        # Don't let it paste into a different class
        target_class = self.obj_clipboard[1][0][0].obj_class
        if self.current_obj_class != target_class:
            return False

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
            return False

        # Convert indexes to source indexes for storage
        indexes_part = [model.mapToSource(ind) for ind in indexes]
        indexes_source = [model.sourceModel().mapToSource(ind) for ind in indexes_part]

        # Get list of contiguous indexes and objects
        groups, obj_list = model.get_contiguous(indexes_source, False)

        # Save to the clipboard and return success
        self.obj_clipboard = (groups, obj_list)
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
        current_persistent = QtCore.QPersistentModelIndex(current)

        if self.fullTree is not True:
            self.idf.options.append('HideEmptyClasses')
        else:
            try:
                self.idf.options.remove('HideEmptyClasses')
            except ValueError:
                pass

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

        # Save the previous selection to potential re-apply. Save in terms of source
        selection_model = self.classTable.selectionModel()
        previous_model = self.classTable.model()
        source_sel = None
        if selection_model and previous_model:
            if previous_model.get_obj_class() == obj_class:
                sel = selection_model.selection()
                partial = previous_model.mapSelectionToSource(sel)
                source_sel = previous_model.sourceModel().mapSelectionToSource(partial)

        # Filter out group headers
        if obj_class not in self.idd:
            return
        else:
            self.current_obj_class = obj_class

        # Clear the table filter when changing classes
        self.clearFilterClicked()

        # Create the default table model
        table = self.classTable
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
        # table.setSortingEnabled(True) # Disable for now, CRUD actions won't work!
        table.setModel(sortable)

        # Create generic delegates for table cells
        item_delegates = delegates.GenericDelegate(self,
                                                   self.idd[obj_class],
                                                   self.obj_orientation)
        table.setItemDelegate(item_delegates)

        # Connect some signals
        selection_model = table.selectionModel()
        selection_model.selectionChanged.connect(self.table_selection_changed)

        # Restore previous selection after converting to current model's indexes
        if source_sel:
            partial = sortable.sourceModel().mapSelectionFromSource(source_sel)
            previous_sel = sortable.mapSelectionFromSource(partial)
            selection_model.select(previous_sel, QtGui.QItemSelectionModel.SelectCurrent)
        else:
            self.classTable.setCurrentIndex(self.classTable.model().index(0, 0))
            self.classTable.setFocus()

        # Now that there is a class selected, enable some actions and set some vars
        self.newObjAct.setEnabled(True)
        self.delObjAct.setEnabled(True)
        self.transposeAct.setEnabled(True)
        self.unitsLabel.setText(None)

    def load_tree_view(self):
        """Loads the tree of class type names."""

        # Define the source model
        source_model = treemodel.ObjectClassTreeModel(self.idf,
                                                      ("Object Class", "Count"),
                                                      self.classTree)

        # Create additional proxy model for sorting and filtering
        proxy_model = treemodel.TreeSortFilterProxyModel()
        proxy_model.setSourceModel(source_model)

        # Assign the model and modify some settings
        self.classTree.setModel(proxy_model)
        self.classTree.setRootIsDecorated(False)
        self.classTree.expandAll()
        self.classTree.setColumnWidth(0, 280)
        self.classTree.setColumnWidth(1, 10)

        # Connect some signals
        selection_model = self.classTree.selectionModel()
        selection_model.selectionChanged.connect(self.class_selected)

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

    def class_selected(self, current):
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

    def comment_view_changed(self):
        sel = self.classTable.selectionModel().selection()
        if not sel:
            return
        first = sel.first().topLeft()
        if self.obj_orientation == QtCore.Qt.Horizontal:
            ind = first.row()
        else:
            ind = first.column()

        comment_text = self.commentView.toPlainText()
        comments = comment_text.splitlines(True)
        self.idf[self.current_obj_class][ind].comments = comments
        self.set_dirty(True)

    def fill_right(self):
        # not yet implemented
        # selected_indexes = self.classTable.selectedIndexes()
        pass

    def update_log_viewer(self, log_text):
        self.logView.appendPlainText(log_text)
        self.logView.moveCursor(QtGui.QTextCursor.End)
        self.logView.moveCursor(QtGui.QTextCursor.StartOfLine)

    def start_log_watcher(self):
        # Connect signal to log handler
        log.handlers[1].com.signal.connect(self.update_log_viewer)

        # Populate logView widget with contents of existing log file
        log_path = os.path.join(config.LOG_DIR, config.LOG_FILE_NAME)
        with open(log_path) as f:
            self.logView.clear()
            self.logView.insertPlainText(f.read())
            self.logView.moveCursor(QtGui.QTextCursor.End)
            self.logView.moveCursor(QtGui.QTextCursor.StartOfLine)

    def set_dirty(self, dirty_state):
        self.file_dirty = dirty_state
        self.setWindowModified(dirty_state)
        self.saveAct.setEnabled(dirty_state)

    def update_idf_options(self):
        if 'ViewInIPunits' in self.idf.options:
            self.idf.si_units = False
            self.setIPUnitsAction.setChecked(True)
        if 'HideEmptyClasses' in self.idf.options:
            self.fullTree = False
            self.toggle_full_tree()
