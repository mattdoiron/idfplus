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
import appdirs

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
LOG_LEVEL = 'DEBUG'
DEFAULT_COLUMN_WIDTH = 120
FILE_ENCODING = 'latin_1'
IDD_FILE_NAME_ROOT = 'EnergyPlus_IDD_v{}.dat'
COMPANY_NAME_FULL = "Mindful Modeller Inc."
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
LOG_FILE_NAME = "idfplus.log"
DATA_DIR = appdirs.user_data_dir(APP_NAME, COMPANY_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME, COMPANY_NAME)
MAX_OBJ_HISTORY = 100

# Make sure necessary folders exist
for dir in [DATA_DIR, LOG_DIR]:
    try:
        os.makedirs(dir)
    except OSError:
        if not os.path.isdir(dir):
            raise


class Settings(object):
    """Object to handle setting and getting settings or info about them."""

    def init_settings(self, parent=None):
        """Create the settings object and set some of its own settings."""
        from . import logger
        self.log = logger.setup_logging(LOG_LEVEL, __name__)
        self.parent = parent
        self.prefs = dict()
        self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
                                         QtCore.QSettings.UserScope,
                                         COMPANY_NAME,
                                         APP_NAME,
                                         parent)

    def read_settings(self):
        """Reads application settings and restores them."""

        self.log.info('Reading settings')
        settings = self.settings

        # Retrieve settings and store them in the prefs dict
        settings.beginGroup("MainWindow")
        self.prefs['size'] = settings.value("size", QtCore.QSize(600, 500))
        self.prefs['pos'] = settings.value("pos", QtCore.QPoint(200, 200))
        self.prefs['state'] = settings.value("state", QtCore.QByteArray())
        self.prefs['style'] = settings.value("style", default_style())
        settings.endGroup()

        settings.beginGroup("Files")
        self.prefs['recent_files'] = list(settings.value("recent_files") or [''])
        settings.endGroup()

        settings.beginGroup("ClassTable")
        self.prefs['default_column_width'] = settings.value("default_column_width", 120)
        global DEFAULT_COLUMN_WIDTH
        DEFAULT_COLUMN_WIDTH = self.prefs['default_column_width']
        settings.endGroup()

        settings.beginGroup("Global")
        # self.prefs['file_encoding'] = settings.value("file_encoding", 'latin_1')
        self.prefs['log_level'] = settings.value("log_level", 'INFO')
        global LOG_LEVEL
        LOG_LEVEL = self.prefs['log_level']
        settings.endGroup()

        # Apply some settings immediately
        self.parent.resize(self.prefs['size'])
        self.parent.move(self.prefs['pos'])
        self.parent.restoreState(self.prefs['state'])
        self.parent.recentFiles = self.prefs['recent_files']
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(self.prefs['style']))

    def write_settings(self):
        """Writes application settings to disk."""

        self.log.info('Writing settings')
        settings = self.settings
        prefs = self.parent.prefs

        settings.beginGroup("Files")
        settings.setValue("recent_files", prefs.get('recent_files', ['']))
        settings.endGroup()

        settings.beginGroup("MainWindow")
        settings.setValue("size", prefs['size'])
        settings.setValue("pos", prefs['pos'])
        settings.setValue("state", self.parent.saveState())
        settings.setValue("style", prefs['style'])
        settings.endGroup()

        settings.beginGroup("ClassTable")
        settings.setValue("default_column_width", prefs['default_column_width'])
        settings.endGroup()

        settings.beginGroup("Global")
        # settings.setValue("file_encoding", prefs['file_encoding'])
        settings.setValue("log_level", prefs['log_level'])
        settings.endGroup()

    def show_prefs_dialog(self):
        """Handles showing the settings dialog and setting its values."""
        dlg = PrefsDialog(self)
        if dlg.exec_():
            result = dlg.prefs
            print('saved')

    def get_path(self):
        """get path"""
        return self.settings.fileName()

    def get_file_name(self):
        """get file name"""
        import os
        return os.path.basename(self.settings.fileName())

    def get_dir_name(self):
        """get dir name"""
        import os
        return os.path.dirname(self.settings.fileName())


class PrefsDialog(QtGui.QDialog):
    """ Form used to view and edit global program options
    """

    def __init__(self, parent):
        super(PrefsDialog, self).__init__(parent)

        # self.parent = parent
        self.settings = parent.settings
        self.prefs = parent.prefs
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        # Create the tab widget and assign its tabs
        tab_widget = QtGui.QTabWidget()
        tab_widget.addTab(AppearanceTab(self), "Appearance")
        tab_widget.addTab(LogTab(self), "Logging")

        # Create layout and assign it to self
        layout = QtGui.QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setWindowTitle("IDF+ Options")

        # Connect gui elements to events
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        """ Override default accept method to save settings
        """
        self.parent().write_settings()
        super(PrefsDialog, self).accept()


class AppearanceTab(QtGui.QWidget):
    def __init__(self, parent=None):
        super(AppearanceTab, self).__init__(parent)

        self.prefs = parent.prefs

        col_width_label = QtGui.QLabel("Default Column Width:")
        self.col_width_edit = QtGui.QLineEdit(self.prefs['default_column_width'])
        self.col_width_edit.setMinimumWidth(40)
        validator = QtGui.QIntValidator(10, 200, self)
        self.col_width_edit.setValidator(validator)

        style_label = QtGui.QLabel("Visual Style:")
        self.style_edit = QtGui.QComboBox(self)
        self.style_edit.addItems(QtGui.QStyleFactory.keys())
        self.style_edit.setCurrentIndex(self.style_edit.findText(self.prefs['style']))

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(col_width_label)
        mainLayout.addWidget(self.col_width_edit)
        mainLayout.addWidget(style_label)
        mainLayout.addWidget(self.style_edit)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        self.col_width_edit.textChanged.connect(self.update)
        self.style_edit.currentIndexChanged.connect(self.update)

    def update(self):
        self.prefs['default_column_width'] = self.col_width_edit.text()
        self.prefs['style'] = self.style_edit.currentText()


class LogTab(QtGui.QWidget):
    def __init__(self, parent=None):
        super(LogTab, self).__init__(parent)

        self.prefs = parent.prefs

        log_label = QtGui.QLabel("Log Detail Level:")
        self.log_edit = QtGui.QComboBox(self)
        self.log_edit.addItems(['INFO', 'DEBUG', 'WARNING'])
        self.log_edit.setCurrentIndex(self.log_edit.findText(self.prefs['log_level']))

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(log_label)
        mainLayout.addWidget(self.log_edit)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        self.log_edit.currentIndexChanged.connect(self.update)

    def update(self):
        self.prefs['log_level'] = self.log_edit.currentText()


def default_style():
    system = get_os()
    if system == 'Windows':
        style = 'WindowsXP'
    elif system == 'Macintosh':
        style = 'Macintosh'
    else:
        style = 'Cleanlooks'
    return style

def get_os():
    import platform
    system = platform.system()
    return system