#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module to manage configuration files and preferences

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os
import appdirs
import logging

# PySide2 imports
from PySide2.QtCore import QDir, QSettings, QSize, QPoint, QByteArray
from PySide2.QtWidgets import QStyleFactory, QApplication

# Constants
LOG_LEVEL = 'DEBUG'
DEFAULT_COLUMN_WIDTH = 120
FILE_ENCODING = 'latin_1'
IDD_FILE_NAME_ROOT = 'EnergyPlus_IDD_v{}.dat'
COMPANY_NAME_FULL = "Mindful Modeller"
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
DATA_DIR = appdirs.user_data_dir(APP_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME)
CONFIG_DIR = appdirs.user_config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, APP_NAME)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, APP_NAME, "{}.{}".format(APP_NAME, "ini"))
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
        QSettings.setPath(QSettings.IniFormat,
                                 QSettings.UserScope,
                                 CONFIG_DIR)
        self.settings = QSettings(CONFIG_FILE_PATH, QSettings.IniFormat)
        self.read_settings()

    def read_settings(self):
        """Reads application settings and restores them.
        """

        settings = self.settings

        # Retrieve settings and store them in the prefs dict
        settings.beginGroup("Appearance")
        self['style'] = settings.value("style", default_style())
        self['base_font'] = settings.value("base_font", "Arial,9")
        self['comments_font'] = settings.value("comments_font", "Courier,9")
        self['hide_groups'] = int(settings.value("hide_groups", 1))
        self['hide_empty_classes'] = int(settings.value("hide_empty_classes", 1))
        self['show_ip_units'] = int(settings.value("show_ip_units", 0))
        settings.endGroup()

        settings.beginGroup("Files")
        self['recent_files'] = list(settings.value("recent_files") or [''])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        self['class_tree_font'] = settings.value("class_tree_font", "Arial,9")
        settings.endGroup()

        settings.beginGroup("ClassTable")
        self['default_column_width'] = int(settings.value("default_column_width", 120))
        self['class_table_font'] = settings.value("class_table_font", "Arial,9")
        self['show_units_in_headers'] = int(settings.value("show_units_in_headers", 0))
        self['show_units_in_cells'] = int(settings.value("show_units_in_cells", 0))
        settings.endGroup()

        settings.beginGroup("Global")
        self['log_level'] = settings.value("log_level", 'DEBUG')
        self['sort_order'] = settings.value("sort_order", "SortedOrder")
        self['special_formatting'] = settings.value("special_formatting", "UseSpecialFormat")
        self['obey_idf_options'] = int(settings.value("obey_idf_options", 1))
        self['save_units'] = int(settings.value("save_units", 0))
        self['save_hidden_classes'] = int(settings.value("save_hidden_classes", 0))
        self['save_hide_groups'] = int(settings.value("save_hide_groups", 0))
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
        settings.setValue("base_font", self['base_font'])
        settings.setValue("comments_font", self['comments_font'])
        settings.setValue("hide_groups", self['hide_groups'])
        settings.setValue("hide_empty_classes", self['hide_empty_classes'])
        settings.setValue("show_ip_units", self['show_ip_units'])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        settings.setValue("class_tree_font", self['class_tree_font'])
        settings.endGroup()

        settings.beginGroup("ClassTable")
        settings.setValue("default_column_width", self['default_column_width'])
        settings.setValue("class_table_font", self['class_table_font'])
        settings.setValue("show_units_in_headers", self['show_units_in_headers'])
        settings.setValue("show_units_in_cells", self['show_units_in_cells'])
        settings.endGroup()

        settings.beginGroup("Global")
        # settings.setValue("file_encoding", self['file_encoding'])
        settings.setValue("log_level", self['log_level'])
        settings.setValue("sort_order", self['sort_order'])
        settings.setValue("special_formatting", self['special_formatting'])
        settings.setValue("obey_idf_options", self['obey_idf_options'])
        settings.setValue("save_units", self['save_units'])
        settings.setValue("save_hidden_classes", self['save_hidden_classes'])
        settings.setValue("save_hide_groups", self['save_hide_groups'])
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
        self['size'] = settings.value("size", QSize(1024, 768))
        self['pos'] = settings.value("pos", QPoint(200, 200))
        self['state'] = settings.value("state", QByteArray())
        self['geometry'] = settings.value("geometry", QByteArray())
        settings.endGroup()

        settings.beginGroup("Appearance")
        self['style'] = settings.value("style", default_style())
        settings.endGroup()

        window.resize(self['size'])
        window.move(self['pos'])
        window.restoreGeometry(self['geometry'])
        window.restoreState(self['state'])
        QApplication.setStyle(QStyleFactory.create(self['style']))

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
        style = 'GTK+'
    return style


def get_os():
    """Returns the current operating system.

    :return: :rtype:
    """

    import platform
    system = platform.system()
    return system


def idd_versions():

    data_dir = QDir(DATA_DIR)
    data_dir.setFilter(QDir.Files | QDir.Hidden | QDir.Readable |
                       QDir.NoSymLinks | QDir.NoDotAndDotDot)
    prefix, sep, postfix = IDD_FILE_NAME_ROOT.partition("{}")
    versions = []

    for file_name in data_dir.entryList():
        name = file_name.replace(prefix, '')
        name = name.replace(postfix, '')
        versions.append(name)

    return versions
