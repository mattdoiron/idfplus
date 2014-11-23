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
COMPANY_NAME_FULL = "Mindful Modeller"
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
LOG_FILE_NAME = "idfplus.log"
DATA_DIR = appdirs.user_data_dir(APP_NAME, COMPANY_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME, COMPANY_NAME)
MAX_OBJ_HISTORY = 100
# UNITS_REGISTRY_PATH = os.path.join(APP_ROOT, DATA_DIR, 'units.dat')
DEFAULT_IDD_VERSION = '8.1'
__version__ = 'v0.0.1'

# Make sure necessary folders exist
for dir in [DATA_DIR, LOG_DIR]:
    try:
        os.makedirs(dir)
        print('created dir: {}'.format(dir))
    except OSError:
        print('dir already exists: {}'.format(dir))
        if not os.path.isdir(dir):
            print('dir is not a directory: {}'.format(dir))
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
        self.prefs['size'] = settings.value("size", QtCore.QSize(1024, 768))
        self.prefs['pos'] = settings.value("pos", QtCore.QPoint(200, 200))
        self.prefs['state'] = settings.value("state", QtCore.QByteArray())
        self.prefs['geometry'] = settings.value("geometry", QtCore.QByteArray())
        self.prefs['style'] = settings.value("style", default_style())
        self.prefs['base_font_size'] = int(settings.value("base_font_size", 9))
        self.prefs['base_font'] = settings.value("base_font", "Arial")
        self.prefs['comments_font_size'] = int(settings.value("comments_font_size", 10))
        self.prefs['comments_font'] = settings.value("comments_font", "Courier")
        settings.endGroup()

        settings.beginGroup("Files")
        self.prefs['recent_files'] = list(settings.value("recent_files") or [''])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        self.prefs['class_tree_font_size'] = int(settings.value("class_tree_font_size", 9))
        self.prefs['class_tree_font'] = settings.value("class_tree_font", "Arial")
        settings.endGroup()

        settings.beginGroup("ClassTable")
        self.prefs['default_column_width'] = int(settings.value("default_column_width", 120))
        self.prefs['class_table_font_size'] = int(settings.value("class_table_font_size", 9))
        self.prefs['class_table_font'] = settings.value("class_table_font", "Arial")
        settings.endGroup()

        settings.beginGroup("Global")
        # self.prefs['file_encoding'] = settings.value("file_encoding", 'latin_1')
        self.prefs['log_level'] = settings.value("log_level", 'INFO')
        global LOG_LEVEL
        LOG_LEVEL = self.prefs['log_level']
        settings.endGroup()

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
        settings.setValue("geometry", self.parent.saveGeometry())
        settings.setValue("state", self.parent.saveState())
        settings.setValue("style", prefs['style'])
        settings.setValue("base_font_size", prefs['base_font_size'])
        settings.setValue("base_font", prefs['base_font'])
        settings.setValue("comments_font_size", prefs['comments_font_size'])
        settings.setValue("comments_font", prefs['comments_font'])
        settings.endGroup()

        settings.beginGroup("ClassTree")
        settings.setValue("class_tree_font_size", prefs['class_tree_font_size'])
        settings.setValue("class_tree_font", prefs['class_tree_font'])
        settings.endGroup()

        settings.beginGroup("ClassTable")
        settings.setValue("default_column_width", prefs['default_column_width'])
        settings.setValue("class_table_font_size", prefs['class_table_font_size'])
        settings.setValue("class_table_font", prefs['class_table_font'])
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

    def restore_state(self):
        # Apply some settings immediately
        self.parent.resize(self.prefs['size'])
        self.parent.move(self.prefs['pos'])
        self.parent.restoreGeometry(self.prefs['geometry'])
        self.parent.restoreState(self.prefs['state'])
        self.parent.recentFiles = self.prefs['recent_files']
        self.parent.start_log_watcher()
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(self.prefs['style']))

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

# Unit Registry
# Eventually store this somewhere else - put it here for now
UNITS_REGISTRY = {
    '$': {'$': 1},
    '$/(m3/s)': {'$/(ft3/min)': 0.000472000059660808},
    '$/(W/K)': {'$/(Btu/h-F)': 0.52667614683731},
    '$/kW': {'$/(kBtuh/h)': 0.293083235638921},
    '$/m2': {'$/ft2': 0.0928939733269818},
    '$/m3': {'$/ft3': 0.0283127014102352},
    '(kg/s)/W': {'(lbm/sec)/(Btu/hr)': 0.646078115385742},
    '1/hr': {'1/hr': 1},
    '1/K': {'1/F': 0.555555555555556},
    '1/m': {'1/ft': 0.3048},
    'A': {'A': 1},
    'A/K': {'A/F': 0.555555555555556},
    'A/V': {'A/V': 1},
    'Ah': {'Ah': 1},
    'Availability': {'Availability': 1},
    'C': {'F': (1.8, 32)},
    'cm': {'in': 0.3937},
    'cm2': {'inch2': 0.15500031000062},
    'Control': {'Control': 1},
    'cycles/hr': {'cycles/hr': 1},
    'days': {'days': 1},
    'deg': {'deg': 1},
    'deltaC': {'deltaF': 1.8},
    'deltaC/hr': {'deltaF/hr': 1.8},
    'deltaJ/kg': {'deltaBtu/lb': 0.0004299},
    'dimensionless': {'dimensionless': 1},
    'eV': {'eV': 1},
    'g/GJ': {'lb/MWh': 0.00793664091373665},
    'g/kg': {'grains/lb': 7},
    'g/MJ': {'lb/MWh': 7.93664091373665},
    'g/mol': {'lb/mol': 0.0022046},
    'g/m-s': {'lb/ft-s': 0.000671968949659},
    'g/m-s-K': {'lb/ft-s-F': 0.000373574867724868},
    'GJ': {'ton-hrs': 78.9889415481832},
    'hr': {'hr': 1},
    'J': {'Wh': 0.000277777777777778},
    'J/J': {'J/J': 1},
    'J/K': {'Btu/F': 526.565},
    'J/kg': {'Btu/lb': 0.00042986},
    'J/kg-K': {'Btu/lb-F': 0.000239005736137667},
    'J/kg-K2': {'Btu/lb-F2': 0.000132889924714692},
    'J/kg-K3': {'Btu/lb-F3': 7.38277359526066E-05},
    'J/m2-K': {'Btu/ft2-F': 4.89224766847393E-05},
    'J/m3': {'Btu/ft3': 2.68096514745308E-05},
    'J/m3-K': {'Btu/ft3-F': 1.49237004739337E-05},
    'K': {'R': 1.8},
    'K/m': {'F/ft': 0.54861322767449},
    'kg': {'lb': 2.2046},
    'kg/J': {'lb/Btu': 2325.83774250441},
    'kg/kg': {'kg/kg': 1},
    'kg/kg-K': {'lb/lb-F': 0.555555555555556},
    'kg/m': {'lb/ft': 0.67196893069637},
    'kg/m2': {'lb/ft2': 0.204794053596664},
    'kg/m3': {'lb/ft3': 0.062428},
    'kg/m-s': {'lb/ft-s': 0.67196893069637},
    'kg/m-s-K': {'lb/ft-s-F': 0.373316072609094},
    'kg/m-s-K2': {'lb/ft-s-F2': 0.207397818116164},
    'kg/Pa-s-m2': {'lb/psi-s-ft2': 1412.00523459398},
    'kg/s': {'lb/s': 2.20462247603796},
    'kg/s2': {'lb/s2': 2.2046},
    'kg/s-m': {'lb/s-ft': 0.67196893069637},
    'kg-H2O/kg-air': {'kg-H2O/kg-air': 1},
    'kJ/kg': {'Btu/lb': 0.429925},
    'kmol': {'kmol': 1},
    'kmol/s': {'kmol/s': 1},
    'kPa': {'psi': 0.145038, 'inHg': 0.29523},
    'L/day': {'pint/day': 2.11337629827348},
    'L/GJ': {'gal/kWh': 0.000951022349025202},
    'L/kWh': {'pint/kWh': 2.11337629827348},
    'L/MJ': {'gal/kWh': 0.951022349025202},
    'lux': {'foot-candles': 0.092902267},
    'm': {'ft': 3.28083989501312, 'in': 39.3700787401575},
    'm/hr': {'ft/hr': 3.28083989501312},
    'm/s': {'ft/min': 196.850393700787, 'miles/hr': 2.2369362920544},
    'm/yr': {'inch/yr': 39.3700787401575},
    'm2': {'ft2': 10.7639104167097},
    'm2/m': {'ft2/ft': 3.28083989501312},
    'm2/person': {'ft2/person': 10.764961},
    'm2/s': {'ft2/s': 10.7639104167097},
    'm2-K/W': {'ft2-F-hr/Btu': 5.678263},
    'm3': {'ft3': 35.3146667214886, 'gal': 264.172037284185},
    'm3/GJ': {'ft3/MWh': 127.13292},
    'm3/hr': {'ft3/hr': 35.3146667214886},
    'm3/hr-m2': {'ft3/hr-ft2': 3.28083989501312},
    'm3/hr-person': {'ft3/hr-person': 35.3146667214886},
    'm3/kg': {'ft3/lb': 16.018},
    'm3/m2': {'ft3/ft2': 3.28083989501312},
    'm3/m3': {'m3/m3': 1},
    'm3/MJ': {'ft3/kWh': 127.13292},
    'm3/person': {'ft3/person': 35.3146667214886},
    'm3/s': {'ft3/min': 2118.88000328931, 'gal/min': 15850.3222370511},
    'm3/s-m': {'ft3/min-ft': 645.89},
    'm3/s-m2': {'ft3/min-ft2': 196.85},
    'm3/s-person': {'ft3/min-person': 2118.6438},
    'm3/s-W': {'(ft3/min)/(Btu/h)': 621.099127332943},
    'micron': {'micron': 1},
    'minutes': {'minutes': 1},
    'Mode': {'Mode': 1},
    'ms': {'ms': 1},
    'N-m': {'lbf-in': 8.85074900525547},
    'N-s/m2': {'lbf-s/ft2': 0.0208857913669065},
    'Pa': {'psi': 0.000145037743897283, 'ftH2O': 0.00033455, 'inH2O': 0.00401463, 'inHg': 0.00029613, 'Pa': 1},
    'Percent': {'Percent': 1.0},
    'percent/K': {'percent/F': 0.555555555555556},
    'person/m2': {'person/ft2': 0.0928939733269818},
    's/m': {'s/ft': 0.3048},
    'V/K': {'V/F': 0.555555555555556},
    'W': {'Btu/h': 3.4121412858518, 'W': 1},
    'W/(m3/s)': {'W/(ft3/min)': 0.0004719475},
    'W/K': {'Btu/h-F': 1.89563404769544},
    'W/m': {'Btu/h-ft': 1.04072},
    'W/m2': {'Btu/h-ft2': 0.316957210776545, 'W/ft2': 0.09290304, 'W/m2': 1},
    'W/m2-K': {'Btu/h-ft2-F': 0.176110194261872},
    'W/m2-K2': {'Btu/h-ft2-F2': 0.097826},
    'W/m-K': {'Btu-in/h-ft2-F': 6.93481276005548, 'Btu/h-ft-F': 0.577796066000163},
    'W/m-K2': {'Btu/h-F2-ft': 0.321418310071648},
    'W/m-K3': {'Btu/h-F3-ft': 0.178565727817582},
    'W/person': {'Btu/h-person': 3.4121412858518, 'W/person': 1},
}

UNIT_TYPES = {
    'Dimensionless': 'dimensionless',
    'Temperature': 'C',
    'DeltaTemperature': 'C',
    'PrecipitationRate': 'm/hr',
    'Angle': 'degrees',
    'ConvectionCoefficient': 'W/m2-K',
    'ActivityLevel': 'W/person',
    'Velocity': 'm/s',
    'Capacity': 'W',
    'Power': 'W',
    'Availability': 'Availability',
    'Percent': 'Percent',
    'Control': 'Control',
    'Mode': 'Mode'
}
