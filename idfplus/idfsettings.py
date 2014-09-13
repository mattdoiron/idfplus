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

    def __init__(self, parent=None):
        '''Create the settings object and set some of its own settings.'''
        from . import logger
        self.log = logger.setup_logging(LOG_LEVEL, __name__)
        self.parent = parent
        self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
                                         QtCore.QSettings.UserScope,
                                         COMPANY_NAME,
                                         APP_NAME,
                                         parent)

    def read_settings(self):
        """Reads application settings and restores them."""

        self.log.info('Reading settings')
#        print("file: {}".format(self.get_file_name()))
#        print("directory: {}".format(self.get_dir_name()))
        settings = self.settings
        parent = self.parent

        settings.beginGroup("MainWindow")
        size = settings.value("size", QtCore.QSize(600, 500))
        position = settings.value("pos", QtCore.QPoint(200, 200))
        state = settings.value("state", QtCore.QByteArray())
#        geometry = settings.value("geometry", QtCore.QByteArray())
        style = settings.value("style", default_style())
        settings.endGroup()

        settings.beginGroup("Files")
        parent.recentFiles = list(settings.value("recent_files", ['']))
        settings.endGroup()

        settings.beginGroup("ClassTable")
        global DEFAULT_COLUMN_WIDTH
        DEFAULT_COLUMN_WIDTH = settings.value("default_column_width", 120)
        settings.endGroup()

        settings.beginGroup("Global")
        global FILE_ENCODING
        FILE_ENCODING = settings.value("file_encoding", 'latin_1')
        settings.endGroup()

        parent.resize(size)
        parent.move(position)
        parent.restoreState(state)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(style))
#        parent.restoreGeometry(geometry)
#        parent.restoreDockWidget(parent.classTree.parent())
#        parent.restoreDockWidget(parent.infoView.parent())
#        parent.restoreDockWidget(parent.commentView.parent())

    def write_settings(self):
        """Writes application settings to save them."""

        self.log.info('Writing settings')
        parent = self.parent
        settings = self.settings

#        filename = self.filename  # or '' or None
        recentFiles = parent.recentFiles or ['']

        settings.beginGroup("Files")
#        settings.setValue("LastFile", filename)
        settings.setValue("recent_files", recentFiles)
        settings.endGroup()

        settings.beginGroup("MainWindow")
        settings.setValue("size", parent.size())
        settings.setValue("pos", parent.pos())
        settings.setValue("state", parent.saveState())
#        settings.setValue("geometry", parent.saveGeometry())
        settings.setValue("style", default_style())
        settings.endGroup()

        settings.beginGroup("ClassTable")
        settings.setValue("default_column_width", 120)
        settings.endGroup()

        settings.beginGroup("Global")
        settings.setValue("file_encoding", 'latin_1')
        settings.endGroup()

    def show_settings_dialog(self):
        """Handles showing the settings dialog and setting its values."""
        pass

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

def default_style():
    system = get_os()
    if system == 'Windows':
        style = 'WindowsVista'
    elif system == 'Macintosh':
        style = 'Macintosh'
    else:
        style = 'Cleanlooks'
    return style

def get_os():
    import platform
    system = platform.system()
    return system