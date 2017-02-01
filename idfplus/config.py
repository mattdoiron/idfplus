#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
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

# System imports
import os
import appdirs
import logging

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Constants
LOG_LEVEL = 'DEBUG'
DEFAULT_COLUMN_WIDTH = 120
FILE_ENCODING = 'latin_1'
IDD_FILE_NAME_ROOT = 'EnergyPlus_IDD_v{}.dat'
COMPANY_NAME_FULL = "Mindful Modeller"
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
DATA_DIR = appdirs.user_data_dir(APP_NAME, COMPANY_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME, COMPANY_NAME)
LOG_FILE_NAME = "idfplus.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)
MAX_OBJ_HISTORY = 100
DEFAULT_IDD_VERSION = "8.6"

# Make sure necessary folders exist
for directory in [LOG_DIR]:
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise

# Setup logging
log = logging.getLogger(__name__)


class Settings(dict):
    """Object to handle setting and getting settings or info about them.
    """

    def __init__(self, *args, **kwargs):
        """Create the settings object and set some of its own settings.
        """

        super(Settings, self).__init__(*args, **kwargs)
        self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
                                         QtCore.QSettings.UserScope,
                                         COMPANY_NAME,
                                         APP_NAME)
        self.read_settings()

    def read_settings(self):
        """Reads application settings and restores them.
        """

        settings = self.settings

        # Retrieve settings and store them in the prefs dict
        settings.beginGroup("Appearance")
        self['style'] = settings.value("style", default_style())
        self['base_font_size'] = int(settings.value("base_font_size", 9))
        self['base_font'] = settings.value("base_font", "Arial")
        self['comments_font_size'] = int(settings.value("comments_font_size", 10))
        self['comments_font'] = settings.value("comments_font", "Courier")
        settings.endGroup()

        settings.beginGroup("Files")
        self['recent_files'] = list(settings.value("recent_files") or [''])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        self['class_tree_font_size'] = int(settings.value("class_tree_font_size", 9))
        self['class_tree_font'] = settings.value("class_tree_font", "Arial")
        settings.endGroup()

        settings.beginGroup("ClassTable")
        self['default_column_width'] = int(settings.value("default_column_width", 120))
        self['class_table_font_size'] = int(settings.value("class_table_font_size", 9))
        self['class_table_font'] = settings.value("class_table_font", "Arial")
        self['show_units_in_headers'] = int(settings.value("show_units_in_headers", 0))
        self['show_units_in_cells'] = int(settings.value("show_units_in_cells", 0))
        settings.endGroup()

        settings.beginGroup("Global")
        self['log_level'] = settings.value("log_level", 'DEBUG')
        self['sort_order'] = settings.value("sort_order", "SortedOrder")
        self['special_formatting'] = settings.value("special_formatting", "UseSpecialFormat")
        self['format_behaviour'] = int(settings.value("format_behaviour", 1))
        self['save_units'] = int(settings.value("save_units", 0))
        self['save_hidden_classes'] = int(settings.value("save_hidden_classes", 0))
        self['default_idd_version'] = settings.value("default_idd_version", DEFAULT_IDD_VERSION)
        settings.endGroup()
        self.update_log_level()

    def write_settings(self):
        """Writes application settings to QSettings object.
        """

        log.info('Writing settings')
        settings = self.settings

        settings.beginGroup("Files")
        settings.setValue("recent_files", self.get('recent_files', ['']))
        settings.endGroup()

        settings.beginGroup("Appearance")
        settings.setValue("style", self['style'])
        settings.setValue("base_font_size", self['base_font_size'])
        settings.setValue("base_font", self['base_font'])
        settings.setValue("comments_font_size", self['comments_font_size'])
        settings.setValue("comments_font", self['comments_font'])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        settings.setValue("class_tree_font_size", self['class_tree_font_size'])
        settings.setValue("class_tree_font", self['class_tree_font'])
        settings.endGroup()

        settings.beginGroup("ClassTable")
        settings.setValue("default_column_width", self['default_column_width'])
        settings.setValue("class_table_font_size", self['class_table_font_size'])
        settings.setValue("class_table_font", self['class_table_font'])
        settings.setValue("show_units_in_headers", self['show_units_in_headers'])
        settings.setValue("show_units_in_cells", self['show_units_in_cells'])
        settings.endGroup()

        settings.beginGroup("Global")
        # settings.setValue("file_encoding", self['file_encoding'])
        settings.setValue("log_level", self['log_level'])
        settings.setValue("sort_order", self['sort_order'])
        settings.setValue("special_formatting", self['special_formatting'])
        settings.setValue("format_behaviour", self['format_behaviour'])
        settings.setValue("save_units", self['save_units'])
        settings.setValue("save_hidden_classes", self['save_hidden_classes'])
        settings.setValue("default_idd_version", self['default_idd_version'])
        settings.endGroup()
        self.update_log_level()

    def save_state(self, window):
        """Saves application state to QSettings.

        :param window:
        """

        log.info('Saving main window state')
        settings = self.settings
        settings.beginGroup("MainWindow")
        settings.setValue("size", window.size())
        settings.setValue("pos", window.pos())
        settings.setValue("geometry", window.saveGeometry())
        settings.setValue("state", window.saveState())
        settings.endGroup()

    def restore_state(self, window):
        """Restore application state.

        :param window:
        """

        log.info('Restoring main window state')
        settings = self.settings
        settings.beginGroup("MainWindow")
        self['size'] = settings.value("size", QtCore.QSize(1024, 768))
        self['pos'] = settings.value("pos", QtCore.QPoint(200, 200))
        self['state'] = settings.value("state", QtCore.QByteArray())
        self['geometry'] = settings.value("geometry", QtCore.QByteArray())
        settings.endGroup()

        settings.beginGroup("Appearance")
        self['style'] = settings.value("style", default_style())
        settings.endGroup()

        window.resize(self['size'])
        window.move(self['pos'])
        window.restoreGeometry(self['geometry'])
        window.restoreState(self['state'])
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(self['style']))

    def update_log_level(self):
        """Refreshes handlers' log level and global variable
        """

        global LOG_LEVEL
        LOG_LEVEL = self['log_level']
        for handler in log.parent.handlers:
            handler.setLevel(self['log_level'])

    def get_path(self):
        """get path
        """

        return self.settings.fileName()

    def get_file_name(self):
        """get file name
        """

        import os
        return os.path.basename(self.settings.fileName())

    def get_dir_name(self):
        """get dir name
        """

        import os
        return os.path.dirname(self.settings.fileName())


def default_style():
    """Retrieves the default style.

    :return: :rtype:
    """

    system = get_os()
    if system == 'Windows':
        style = 'Cleanlooks'
    elif system == 'Macintosh':
        style = 'Macintosh'
    else:
        style = 'Cleanlooks'
    return style


def get_os():
    """Returns the current operating system.

    :return: :rtype:
    """

    import platform
    system = platform.system()
    return system


def idd_versions():

    data_dir = QtCore.QDir(DATA_DIR)
    data_dir.setFilter(QtCore.QDir.Files | QtCore.QDir.Hidden | QtCore.QDir.Readable |
                       QtCore.QDir.NoSymLinks | QtCore.QDir.NoDotAndDotDot)
    prefix, sep, postfix = IDD_FILE_NAME_ROOT.partition("{}")
    versions = []

    for file_name in data_dir.entryList():
        name = file_name.replace(prefix, '')
        name = name.replace(postfix, '')
        versions.append(name)

    return versions
