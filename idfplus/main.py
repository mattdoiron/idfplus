#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Main entry point for IDFPlus editor

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import errno
import glob
import os
import platform
import subprocess
import sys
import errno
import codecs
from cStringIO import StringIO

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import delegates
from . import commands
from . import config
from . import logger
from . import __version__
from . import icons_rc
from .models import classtree
from .models import reftree
from .eplusio import idfmodel
from .eplusio import iddmodel
from .eplusio import parser
from .widgets import setupwiz, main, help

# Setup logging
log = logger.setup_logging(config.LOG_LEVEL, 'idfplus', config.LOG_PATH)
log.info('----==== Launching IDF+ ====----')


class IDFPlus(QtGui.QMainWindow, main.UIMainWindow):
    """Main GUI window for IDF+ program.
    """

    def __init__(self, args=None):
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
        self.file_dirty = False
        self.obj_orientation = QtCore.Qt.Vertical
        self.current_obj_class = None
        self.obj_clipboard = []
        self.args = args
        self.check_file_changed = False

        # Create main application elements
        self.create_actions()
        self.create_tool_bars()
        self.create_menus()
        self.create_shortcuts()
        self.create_tray_menu()
        self.start_focus_watcher()

        # Restore preferences
        self.hide_empty_classes = True if self.prefs['hide_empty_classes'] == 1 else False
        self.classWithObjsAction.setChecked(self.hide_empty_classes)
        self.hide_groups = True if self.prefs['hide_groups'] == 1 else False
        self.groupAct.setChecked(self.hide_groups)
        self.si_units = True if self.prefs['show_ip_units'] == 0 else False
        self.setIPUnitsAction.setChecked(0 if self.si_units else 1)
        self.prefs.restore_state(self)
        # Create a place to store all open files
        # self.db.dbroot.files = OOBTree()
        # self.files = self.db.dbroot.files
        # self.idd = OOBTree()

        self.help_file_names = {
            "EnergyPlus Acknowledgments": "Acknowledgements.pdf",
            "EnergyPlus Auxiliary Programs": "AuxiliaryPrograms.pdf",
            "EnergyPlus EMS Application Guide": "EMS_Application_Guide.pdf",
            "EnergyPlus Engineering Reference": "EngineeringReference.pdf",
            "External Interface Application Guide": "ExternalInterfaces_Application_Guide.pdf",
            "EnergyPlus Getting Started": "GettingStarted.pdf",
            "EnergyPlus I/O Reference": "InputOutputReference.pdf",
            "EnergyPlus Output Details and Examples": "OutputDetailsAndExamples.pdf",
            "EnergyPlus Plant Application Guide": "PlantApplicationGuide.pdf",
            "Tips and Tricks Using EnergyPlus": "Tips_and_Tricks_Using_EnergyPlus.pdf",
            "Using EnergyPlus for Compliance": "Using_EnergyPlus_for_Compliance.pdf"
        }

        # Open a file immediately if specified by command-line. Timer allows UI to load fist.
        if self.args.filename:
            QtCore.QTimer.singleShot(0, self.load_file)

    def app_focus_changed(self, old_focus_widget, new_focus_widget):
        # Should we check for file change? Only if required and if main window is regaining focus
        if self.check_file_changed and not old_focus_widget:
            file_time_last_modified_new = os.path.getmtime(self.idf.file_path)
            if self.file_time_last_modified != file_time_last_modified_new:
                log.debug('File change detected!')
                self.file_changed()

    def start_focus_watcher(self):
        app = QtGui.QApplication.instance()
        app.focusChanged.connect(self.app_focus_changed)

    def closeEvent(self, event):
        """Called when the application is closed.

        :param event:
        """

        if self.ok_to_continue():
            self.prefs.write_settings()
            self.prefs.save_state(self)
            log.info('Shutting down IDF+')
            event.accept()
        else:
            event.ignore()

    def new_file(self):
        """Called when a new file is to being created
        """

        if self.ok_to_continue():
            self.add_recent_file(self.file_path)
            self.set_current_file('')
            self.load_file()

    def open_file(self):
        """Called by the open file action.
        """

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
        """

        :param file_path:
        """

        log.info('Trying to load file: {}'.format(file_path))
        if not os.path.isfile(file_path):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
        idf = idfmodel.IDFFile()
        # self.files.update({0:idf})

        # Open the specified file in a safe way
        with codecs.open(file_path, 'r',
                         encoding=config.FILE_ENCODING,
                         errors='backslashreplace') as raw_idf:
            if file_path:
                idf_parser = parser.IDFParser(idf,
                                              default_version=self.prefs['default_idd_version'])
                for progress in idf_parser.parse_idf(raw_idf, file_path):
                    self.progressBarIDF.setValue(progress)
            else:
                log.info('Loading blank IDF file...')
                idf.init_blank()

        self.idf = idf
        self.idd = idf._idd
        self.file_time_last_modified = os.path.getmtime(file_path)
        self.check_file_changed = True

    def load_file(self, file_path=None):
        """Loads a specified file or gets the file_path from the sender.

        :rtype : bool
        :param file_path:
        """

        if self.args.filename and not file_path:
            file_path = self.args.filename

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
        self.pathLabel.setText("")
        self.progressBarIDF.show()

        # Try to load the specified IDF file
        try:
            self.load_idf(file_path)
        except iddmodel.IDDError as e:
            # Required IDD file doesn't exist so launch IDD wizard
            if not self.launch_idd_wizard(file_path, e.version, e.message):
                # Wizard failed, warn user and cancel
                QtGui.QMessageBox.warning(self, "Processing IDD File Failed",
                                          ("{}\n\nVersion Required: {}\n\nLoading "
                                           "cancelled!".format(e.message, e.version)),
                                          QtGui.QMessageBox.Ok)
                message = ("Loading failed. Could not find "
                           "matching IDD file for version {}.".format(e.version))
                return False
        except parser.InvalidIDFObject as e:
            # Invalid name of object, warn use and cancel
            QtGui.QMessageBox.warning(self, "Processing IDF File Failed",
                                      "{}\n\nLoading cancelled!".format(e.message),
                                      QtGui.QMessageBox.Ok)
            message = "Loading failed. Invalid idf object."
            return False
        except OSError as e:
            if e.errno == errno.ENOENT:
                message = "Loading failed. No such IDF file found."
                return False
            else:
                raise OSError(e.errno, e.strerror, e.filename)
        finally:
            self.reset_progress_bar()
            self.update_status(message)

        # Everything worked, so set some variables and update status
        log.debug('Loading tree view...')
        self.groups = self.idd.groups
        self.update_idf_options()
        self.load_tree_view()
        self.undo_stack.clear()
        log.debug('Updating recent file list...')
        self.file_path = file_path
        self.add_recent_file(file_path)
        self.set_current_file(file_path)
        self.set_dirty(False)
        self.select_tree_class("Version")
        self.classTable.setCurrentIndex(self.classTable.model().index(0, 0))
        self.update_status('File Loaded Successfully!')
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
        except (AttributeError, iddmodel.IDDError):
            return False

    def save(self):
        """Called by save action.
        """

        if self.file_path:
            self.save_file()
        else:
            self.save_as()

    def save_as(self):
        """Called by the save as action.
        """

        home_dir = os.path.expanduser('~')
        directory = self.file_path if self.file_path else home_dir
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
        """Called by action to save the current file to disk.
        """

        if not self.file_path or not self.idf:
            return False
        file_name = self.file_path
        writer = parser.Writer()
        if writer.write_idf(self.idf):
            self.set_current_file(file_name)
            self.add_recent_file(file_name)
            self.statusBar().showMessage("File saved", 2000)
            self.set_dirty(False)
            self.check_file_changed = True
            return True
        else:
            return False

    def format_save(self):
        """Manually set the dirty flag and save the file. Convenience function for reformatting
        """

        self.set_dirty(True)
        self.save()

    def idfplus_help(self):
        """"""
        pass

    def energyplus_help(self):
        """"""

        # self.viewer = help.HelpWindow(self)
        # self.viewer.show()

        help_url = "http://bigladdersoftware.com/epx/docs/"
        current_platform = sys.platform
        if current_platform.startswith('linux'):
            result = subprocess.check_call(["xdg-open", help_url])
        elif current_platform.startswith('win'):
            # result = subprocess.check_call(["start", help_url])
            os.startfile(help_url)
        else:
            result = subprocess.check_call(["open", "-R", help_url])

        pass

    def about(self):
        """Called by the about action.
        """

        import PySide

        QtGui.QMessageBox.about(self, "About IDF+",
                """<b>IDF+</b> v{0}
                <p>This is an enhanced editor for EnergyPlus simulation input files.
                For more information please see
                <a href="https://bitbucket.org/mattdoiron/idfplus/">
                https://bitbucket.org/mattdoiron/idfplus/
                </a></p>
                <p>Copyright &copy; 2014-2017 Matt Doiron (matt@mindfulmodeller.ca).
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
                <p>Built with: Python {1}, Qt {2} and PySide {3} on {4}</p>""".format(
                __version__, platform.python_version(),
                PySide.QtCore.qVersion(), PySide.__version__,
                platform.system()))

    def navForward(self):
        """Forward navigation, not yet implemented
        """

        pass

    def navBack(self):
        """Backwards navigation, not yet implemented
        """

        pass

    def show_in_folder(self):
        """Opens the location of the current IDF file.
        """

        current_platform = sys.platform
        result = 1

        if self.file_path:
            if current_platform.startswith('linux'):
                try:
                    result = subprocess.check_call(["nautilus", self.file_path])
                except (subprocess.CalledProcessError, OSError):
                    try:
                        dir_path = os.path.dirname(self.file_path)
                        result = subprocess.check_call(["xdg-open", dir_path])
                    except (subprocess.CalledProcessError, OSError):
                        log.debug('Not supported on this OS')
                        result = 1
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
        """Toggles units
        """

        self.si_units = not self.si_units
        self.prefs['show_ip_units'] = 1 if not self.si_units else 0
        self.prefs.write_settings()

        if not self.idf:
            return

        self.idf.si_units = not self.idf.si_units

        if self.prefs['save_units'] == 1 and self.idf.si_units is False:
            save_units = 'ViewInIPunits'
        else:
            save_units = ''
        self.idf.set_options({'save_units': save_units})

        # Refresh the view
        self.load_table_view(self.current_obj_class)

    def update_file_menu(self):
        """Called to update the recent files portion of the file menu
        """

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

    def update_jump_menu(self):
        """Called to update the jump menu with list of references.
        """

        # Prepare menu
        self.jumpToMenu.clear()
        self.jumpToMenu.addAction(self.jumpFilterGeometry)

        # Helper to insert a blank action
        def insert_blank():
            action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"), 'No references', self)
            self.jumpToMenu.addAction(action)

        # Get selection and indexes
        selection_model = self.classTable.selectionModel()
        if not selection_model:
            insert_blank()
            return
        selected = selection_model.selection()
        if not selected:
            insert_blank()
            return
        _index = selected.first().topLeft()
        if not _index or not _index.isValid():
            insert_blank()
            return

        # Map index to source model
        partially_mapped = self.classTable.model().mapToSource(_index)
        index = self.classTable.model().sourceModel().mapToSource(partially_mapped)

        # Get reference data
        if not self.idf or not index:
            insert_blank()
            return
        refs = self.idf.reference_tree_data(self.current_obj_class, index)
        if not refs:
            insert_blank()
            return

        # Add actions for references
        for field in refs:
            action = QtGui.QAction(QtGui.QIcon(":/images/icon.png"),
                                   '{} ({})'.format(field._outer[0].value, field.obj_class), self)
            action.triggered.connect(lambda: self.jump_to_field(field))
            self.jumpToMenu.addAction(action)

    def jump_to_filter_geometry(self):
        """

        :return:
        """

    def clear_recent(self):
        """Clears recent files
        """

        self.prefs['recent_files'] = []
        self.update_file_menu()

    def reset_comment_view(self):
        """Clears the comment view without triggering signals
        """

        self.commentView.clearFocus()
        self.commentView.setPlainText('')

    def table_selection_changed(self, selected):
        """

        :param selected:
        :return: :rtype:
        """

        if not selected:
            self.reset_comment_view()
            return
        _index = selected.first().topLeft()
        if not _index or not _index.isValid():
            self.reset_comment_view()
            return

        # Map index to source model
        partially_mapped = self.classTable.model().mapToSource(_index)
        index = self.classTable.model().sourceModel().mapToSource(partially_mapped)

        # Update various views and labels
        self.update_reference_view(index)
        self.update_info_view(index)
        self.update_units_label(index)
        self.update_comments(index)

    def update_units_label(self, index):
        """Updates the units label

        :param QtCore.QModelIndex index:
        """

        field = self.idf.field(self.current_obj_class, index.row(), index.column())
        units = self.idf.units(field)
        self.unitsLabel.setText('Units: {}'.format(units))

    def update_comments(self, index):
        """Updates the comments view widget

        :param QtCore.QModelIndex index:
        """

        current_obj = self.idf[self.current_obj_class][index.row()]
        comments = ''.join(current_obj.comments)
        self.commentView.blockSignals(True)
        self.commentView.setPlainText(comments)
        self.commentView.blockSignals(False)

    def update_info_view(self, index):
        """Updates the info view widget

        :param QtCore.QModelIndex index:
        """

        obj_info = self.idd[self.current_obj_class].get_info()
        idd_field = self.idd.field(self.current_obj_class, index.column())
        field_info = idd_field.get_info()

        html = """
            <html>
                <head>
                    <style>
                        h2 {
                            background-color: silver;
                        }
                    </style>
                </head>
                <h2>Class Info</h2>
                <p>CLASS_INFO</p>
                <h2>Field Info</h2>
                <p>FIELD_INFO</p>
            </html>
        """

        html = html.replace('CLASS_INFO', obj_info)
        html = html.replace('FIELD_INFO', field_info)
        self.infoView.setText(html)

    def update_reference_view(self, index):
        """Updates the reference tree view widget

        :param QtCore.QModelIndex index:
        """

        # Create a new model for the tree view and assign it, then refresh view
        data = self.idf.reference_tree_data(self.current_obj_class, index)
        new_model = reftree.ReferenceTreeModel(data, self.refView)
        self.refView.setModel(new_model)
        self.refView.expandAll()

    def ref_tree_double_clicked(self, index):
        """Responds when the reference tree widget is double-clicked.

        :param index:
        """

        if not index.isValid():
            return
        field_uuid = self.refView.model().field_uuid(index)
        field = self.idf.field_by_uuid(field_uuid)
        self.jump_to_field(field)

    def jump_to_field(self, field):
        """Jump to the specified field, updating views as required.

        :param field:
        :return:
        """

        obj_class_display, obj_index, field_index = field.field_id
        self.select_tree_class(obj_class_display)

        # After the table is loaded, get its model and selection model
        table_source_model = self.classTable.model().sourceModel()
        table_model = self.classTable.model()

        # Create an index for the target field with the table's model
        table_index_source = table_source_model.sourceModel().index(obj_index,
                                                                    field_index)
        table_index_partial = table_source_model.mapFromSource(table_index_source)
        table_index = table_model.mapFromSource(table_index_partial)

        # Give focus to the class table and select the target index
        self.classTable.setFocus()
        self.classTable.setCurrentIndex(table_index)

    def select_tree_class(self, obj_class):
        """Selects the specified object class and scroll the class to its location.

        :param str obj_class: Target object class. Capitalization must match IDD file.
        """

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
                                             int(QtGui.QItemSelectionModel.SelectCurrent |
                                                 QtGui.QItemSelectionModel.Rows))

        # Scroll to the matched selection
        self.classTree.scrollTo(matches[0], QtGui.QAbstractItemView.PositionAtCenter)

    def addActions(self, target, actions):
        """Helper to add actions or a separator easily.

        :param target:
        :param actions:
        """

        for action in actions:
            if action is not None:
                target.addAction(action)

    def tableFilterRegExpChanged(self):
        """

        :return: :rtype:
        """

        pattern = self.filterBox.text()
        if len(pattern) < 3:
            pattern = None
        if not self.classTable.model():
            return
        self.classTable.model().setFilterRegExp(pattern)
        self.classTable.model().invalidateFilter()
        self.classTable.selectionModel().reset()

    def treeFilterRegExpChanged(self):
        """

        :return: :rtype:
        """

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
            self.classTable.model().reset_model()

    def clearFilterClicked(self):
        """Triggered when filter is cleared by button
        """

        self.filterBox.clear()
        self.tableFilterRegExpChanged()

    def clearTreeFilterClicked(self):
        """Triggered when tree filter is cleared
        """

        self.filterTreeBox.clear()
        self.treeFilterRegExpChanged()

    def caseSensitivityChanged(self):
        """Triggered when case sensitivity is changed
        """

        if not self.classTable.model():
            return

        if self.caseSensitivity.isChecked():
            sensitivity = QtCore.Qt.CaseSensitive
        else:
            sensitivity = QtCore.Qt.CaseInsensitive
        self.classTable.model().setFilterCaseSensitivity(sensitivity)
        self.tableFilterRegExpChanged()

    def set_current_file(self, file_name):
        """Sets the current file globally and updates title, statusbar, etc.

        :param file_name:
        """

        self.file_path = file_name
        self.setWindowFilePath(file_name)
        self.setWindowModified(False)

        if self.file_path:
            shown_name = self.file_path
        else:
            shown_name = 'Untitled'

        self.pathLabel.setText(shown_name)

        if self.idd:
            self.versionLabel.setText('EnergyPlus IDD v{}'.format(self.idd.version))

    def ok_to_continue(self):
        """Checks if there are unsaved changes and prompts for action.
        """

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
        if file_name not in self.prefs['recent_files']:
            try:
                self.prefs['recent_files'].insert(0, file_name)
            except AttributeError:
                self.prefs['recent_files'] = [file_name]
            while len(self.prefs['recent_files']) > 9:
                self.prefs['recent_files'].pop()

    def update_status(self, message):
        """Updates the window title and status bar with a message.

        :param message:
        """

        self.statusBar().showMessage(message, 5000)
        self.setWindowFilePath(self.file_path)
        self.setWindowModified(self.file_dirty)

    def setVisible(self, visible):
        """Integrates system tray with minimize/maximize.

        :param visible:
        """

        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(IDFPlus, self).setVisible(visible)

    def editComments(self, init_text, init_cursor):
        """Creates commands for undo stack when comments are modified
        """

        cmd = commands.EditCommentCmd(self, self.commentView, init_text, init_cursor)
        self.undo_stack.push(cmd)

    def newObject(self):
        """Creates a new, blank object.
        """

        # If there is no idf file, stop
        if not self.idf:
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self)
        self.undo_stack.push(cmd)

    def duplicateObject(self):
        """Duplicates a given object.
        """

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_selection=True)
        self.undo_stack.push(cmd)

    def deleteObject(self):
        """Deletes a given object.
        """

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
            return False

        # Create undo command and push it to the undo stack
        cmd = commands.DeleteObjectCmd(self)
        self.undo_stack.push(cmd)

    def cutObject(self):
        """Cuts the object after copying it.
        """

        # If there is no selection, stop
        if not self.classTable.selectedIndexes():
            return False

        # Copy object then delete it
        if not self.copyObject():
            return False
        self.deleteObject()

    def pasteSelected(self):
        """Pastes clipboard into cells starting at selected cell.
        """

        # Create undo command and push to undo stack, but only if there is text in clipboard
        mime_data = self.clipboard.mimeData()
        if not mime_data.hasText():
            return
        cmd = commands.PasteSelectedCmd(self)
        self.undo_stack.push(cmd)

    def paste_from_external(self):
        """Grabs system clipboard and attempts to parse it as an IDF file for pasting.
        """

        # Grab system clipboard and continue only if it's text
        mime_data = self.clipboard.mimeData()
        if not mime_data.hasText():
            return

        # Create a idf file and parser, and parse the incoming text
        idf = idfmodel.IDFFile()
        idf.set_idd(self.idd)
        my_parser = parser.IDFParser(idf=idf, idd=self.idd)
        to_parse = StringIO(mime_data.text())
        result = [prog for prog in my_parser.parse_idf(to_parse)]

        # Create an undo object for each class of new objects
        for obj_class, idf_objects in idf.iteritems():
            if not idf_objects:
                continue

            # Set the class tree and object clipboard so that the undo command can grab them
            obj_class_display = idf_objects[0].obj_class_display
            self.select_tree_class(obj_class_display)
            self.obj_clipboard = ([[-1]], [idf_objects])

            # Create undo command and push it to the undo stack
            cmd = commands.NewObjectCmd(self, from_clipboard=True)
            self.undo_stack.push(cmd)

    def pasteObject(self):
        """Pastes the currently copied object(s).
        """

        # If there is nothing in the clipboard, stop
        if not self.obj_clipboard:
            return False

        # Set the class tree so that the undo command can grab it
        target_class = self.obj_clipboard[1][0][0].obj_class_display
        self.select_tree_class(target_class)

        # Create undo command and push it to the undo stack
        cmd = commands.NewObjectCmd(self, from_clipboard=True)
        self.undo_stack.push(cmd)

    def copyObject(self):
        """Copies object(s) to the clipboard for pasting to other programs.
        """

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
        groups, obj_lists = model.contiguous(indexes_source, False, duplicates=True)

        # Create a string containing the string representations of each obj
        objects = [str(item) for sublist in obj_lists for item in sublist]
        str_objects = '\n'.join(objects)

        # Save to the clipboard and return success
        self.obj_clipboard = (groups, obj_lists)
        self.clipboard.setText(str_objects)
        return True

    def copySelected(self):
        """Copies the selected cells to the clipboard for pasting to other programs.
        """

        # Find the selection and it's last row
        indexes = self.classTable.selectedIndexes()
        if len(indexes) <= 0:
            return False
        last = indexes[-1].row()

        # Iterate through indexes saving the columns
        range_to_copy = []
        col = []
        for i in indexes:
            col.append(i.data(QtCore.Qt.EditRole) or '')
            if i.row() == last:
                range_to_copy.append(col)
                col = []

        # Qt seems to always traverses by column so transpose rows/cols here
        range_copied = zip(*range_to_copy)

        # Convert to text for clipboard
        text_copied = ''
        for row in range_copied:
            text_copied += ','.join(row)
            text_copied += '\n'

        # Save converted text to the clipboard
        self.clipboard.setText(text_copied, QtGui.QClipboard.Clipboard)
        self.obj_clipboard = None
        return True

    def toggle_groups(self):
        """Called to toggle the display of group headers in the tree view
        """

        self.hide_groups = not self.hide_groups
        self.prefs['hide_groups'] = 1 if self.hide_groups else 0
        self.prefs.write_settings()

        if not self.idf:
            return

        if self.prefs['save_hide_groups'] == 1 and self.hide_groups is True:
            hide_groups = 'HideGroups'
        else:
            hide_groups = ''
        self.idf.set_options({'save_hide_groups': hide_groups})
        self.load_tree_view()

    def toggle_full_tree(self):
        """Called to toggle the full class tree or a partial tree.
        """

        self.hide_empty_classes = not self.hide_empty_classes
        self.prefs['hide_empty_classes'] = 1 if self.hide_empty_classes else 0
        self.prefs.write_settings()
        tree = self.classTree
        current = tree.currentIndex()
        current_persistent = QtCore.QPersistentModelIndex(current)

        if self.idf:
            if self.prefs['save_hidden_classes'] == 1 and self.hide_empty_classes is True:
                save_hidden = 'HideEmptyClasses'
            else:
                save_hidden = ''
            self.idf.set_options({'save_hidden_classes': save_hidden})

        tree_model = self.classTree.model()
        if tree_model:
            tree_model.hide_empty_classes = not self.classTree.model().hide_empty_classes
            self.treeFilterRegExpChanged()

        # TODO need to find a way to handle what happens when 'currentIndex' disappears
        #     during the filtering.

        tree.scrollTo(current_persistent, QtGui.QAbstractItemView.PositionAtCenter)

    def load_table_view(self, obj_class):
        """Loads the table of objects for the specified class name.

        :param obj_class:
        """

        if not self.idf:
            return

        # Clear the comments and reference views safely
        self.reset_comment_view()
        self.update_reference_view(None)

        # Save the previous selection to potential re-apply. Save in terms of source
        selection_model = self.classTable.selectionModel()
        previous_model = self.classTable.model()
        source_sel = None
        if selection_model and previous_model:
            if previous_model.obj_class == obj_class:
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

        # Tell the model about the new object class and idf file. This also resets the model.
        self.classTable.model().setObjectClass(obj_class, self.idf)

        # Create generic delegates for table cells and assign them
        item_delegates = delegates.GenericDelegate(self, self.idd[obj_class], self.obj_orientation)
        self.classTable.setItemDelegate(item_delegates)

        # Restore previous selection after converting to current model's indexes
        if source_sel:
            partial = self.classTable.model().mapSelectionFromSource(source_sel)
            previous_sel = self.classTable.model().mapSelectionFromSource(partial)
            selection_model.select(previous_sel, QtGui.QItemSelectionModel.SelectCurrent)
        else:
            self.classTable.setCurrentIndex(self.classTable.model().index(0, 0))
            # self.classTable.setFocus()

        # Resize rows for text wrap
        self.classTable.resizeRowsToContents()

        # Now that there is a class selected, enable some actions and set some vars
        self.newObjAct.setEnabled(True)
        self.delObjAct.setEnabled(True)
        self.transposeAct.setEnabled(True)
        self.unitsLabel.setText(None)

    def load_tree_view(self):
        """Loads the tree of class type names.
        """

        # Define the source model
        source_model = classtree.ObjectClassTreeModel(self.idf, self.classTree,
                                                      hide_groups=self.hide_groups)

        # Create additional proxy model for sorting and filtering
        proxy_model = classtree.TreeSortFilterProxyModel(hide_groups=self.hide_groups,
                                                         hide_empty_classes=self.hide_empty_classes)
        proxy_model.setSourceModel(source_model)

        # Assign the model and modify some settings
        self.classTree.setModel(proxy_model)
        self.classTree.expandAll()
        widget_width = self.classTree.parent().width()
        scrollbar_width = self.classTree.verticalScrollBar().sizeHint().width()
        min_count_width = 20
        padding = 10
        class_width = widget_width - scrollbar_width - min_count_width - padding
        header = self.classTree.header()
        header.setResizeMode(QtGui.QHeaderView.Interactive)
        header.setMinimumSectionSize(min_count_width)
        self.classTree.resizeColumnToContents(1)
        self.classTree.setColumnWidth(0, class_width)

        # Connect some signals
        selection_model = self.classTree.selectionModel()
        selection_model.selectionChanged.connect(self.class_selected)

    def transpose_table(self):
        """Transposes the table
        """

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
        """Loads the table view when a new class is selected

        :param current:
        """

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

    def fill_right(self):
        """Fills cells to the right of selected cell with same value as selected cell.
        """

        model = self.classTable.model()
        selection_model = self.classTable.selectionModel()
        if not selection_model:
            return
        selections = selection_model.selection()
        if not selections:
            return
        selection = selections[0]  # There should only ever be one
        top_left_current = selection.topLeft()
        stored_values = []
        to_paste = ''

        # Store values of the selected fields of the first column/row in the selection
        if self.obj_orientation == QtCore.Qt.Vertical:
            sel_range = selection.height()
            fill_range = selection.width()
            for i in range(sel_range):
                index = model.index(top_left_current.row() + i, top_left_current.column())
                value = model.data(index, QtCore.Qt.EditRole) or ''
                for j in range(fill_range):
                    to_paste += value + ','
                to_paste = to_paste[:-1]
                to_paste += '\n'
        else:
            sel_range = selection.width()
            fill_range = selection.height()
            for i in range(sel_range):
                index = model.index(top_left_current.row(), top_left_current.column() + i)
                value = model.data(index, QtCore.Qt.EditRole) or ''
                stored_values.append(value)
            for j in range(fill_range):
                values = [val for val in stored_values]
                to_paste += ','.join(values)
                to_paste += '\n'

        # Send the stored values to the clipboard and call the paste command
        self.clipboard.setText(to_paste)
        cmd = commands.PasteSelectedCmd(self)
        self.undo_stack.push(cmd)

    def update_log_viewer(self, log_text):
        """

        :param log_text:
        """

        self.logView.appendPlainText(log_text)
        self.logView.moveCursor(QtGui.QTextCursor.End)
        self.logView.moveCursor(QtGui.QTextCursor.StartOfLine)

    def start_log_watcher(self):
        """Start the log watcher and connect signals
        """

        # Connect signal to log handler
        log.handlers[1].com.signal.connect(self.update_log_viewer)

        # Populate logView widget with contents of existing log file
        log_path = os.path.join(config.LOG_DIR, config.LOG_FILE_NAME)
        with open(log_path) as f:
            self.logView.setPlainText(f.read().strip())
            self.logView.moveCursor(QtGui.QTextCursor.End)
            self.logView.moveCursor(QtGui.QTextCursor.StartOfLine)

    def set_dirty(self, dirty_state):
        """

        :param dirty_state:
        """

        self.file_dirty = dirty_state
        self.setWindowFilePath(self.file_path)
        self.setWindowModified(dirty_state)
        self.saveAct.setEnabled(dirty_state)

    def update_idf_options(self):
        """Update options associated with the idf file
        """

        self.idf.si_units = self.si_units

        if self.prefs['obey_idf_options']:
            if 'ViewInIPunits' in self.idf.options:
                self.si_units = False
                self.idf.si_units = False
                self.setIPUnitsAction.setChecked(True)
            if 'HideEmptyClasses' in self.idf.options:
                self.hide_empty_classes = True
                self.classWithObjsAction.setChecked(True)
            if 'HideGroups' in self.idf.options:
                self.hide_groups = True
                self.groupAct.setChecked(True)

    def clear_idd_cache(self):
        """Clears the idd cache by deleting pre-processed idd files.
        """

        self.prefs['clear_idd_cache'] = False
        try:
            pattern = config.IDD_FILE_NAME_ROOT.replace('{}', '*')
            files = os.path.join(config.DATA_DIR, pattern)
            for f in glob.glob(files):
                os.remove(f)
            log.info('Successfully removed all cached idd files.')
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def energy_plus_docs(self):
        if not self.idd:
            return

        if not self.idd.file_path:
            return

        calling_action = self.sender()
        doc_to_load = self.help_file_names[calling_action.text()]
        install_dir = os.path.dirname(self.idd.file_path)
        doc_path = os.path.join(install_dir, 'Documentation', doc_to_load)
        current_platform = sys.platform
        result = 1

        if current_platform.startswith('linux'):
            try:
                result = subprocess.check_call(["xdg-open", doc_path])
            except (subprocess.CalledProcessError, OSError):
                log.debug('Not supported on this OS')
                result = 1
        elif current_platform.startswith('win'):
            try:
                win_doc_path = os.path.normpath(doc_path)
                result = subprocess.call(["start", win_doc_path], shell=True)
                result = 0  # windows returns 1 for some reason...
            except WindowsError as e:
                result = 1
        else:
            dir_path = os.path.dirname(self.file_path)
            result = subprocess.check_call(["open", dir_path])

        if result != 0:
            log.debug("Failed to open the specified help file: {} (on platform: {})"
                      .format(win_doc_path, current_platform))

    def file_changed(self):
        """Responds to signal from focus watcher that a file has changed.

        :return:
        """

        message = "This file has be changed by another program! Would you like" \
                  "to reload it now? Any unsaved changes will be lost!"
        flags = QtGui.QMessageBox.StandardButton.Yes
        flags |= QtGui.QMessageBox.StandardButton.No
        response = QtGui.QMessageBox.question(self, "File Change detected!", message, flags)
        self.check_file_changed = False

        if response == QtGui.QMessageBox.Yes:
            self.load_file(self.idf.file_path)
        elif QtGui.QMessageBox.No:
            return False
        else:
            return False
