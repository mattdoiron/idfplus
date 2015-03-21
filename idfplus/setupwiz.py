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

# PySide imports
from PySide import QtGui

# Package imports
from . import idfsettings as c
from . import parser
from . import logger

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class SetupWizIntroPage(QtGui.QWizardPage):

    def __init__(self, parent, version, message):
        super(SetupWizIntroPage, self).__init__(parent)

        self.version = version
        self.message = message
        self.setTitle('IDD+ Processing Wizard')
        self.setSubTitle("This wizard will help you direct IDF+ to the "
                         "necessary IDD file.")
        self.setup_page()

    def setup_page(self):
        # Create intro text
        text = "IDF+ uses EnergyPlus' own IDD file in order to understand " \
               "how to work with IDF files. Each IDD file version is processed " \
               "and stored so that this procedure will be required only once, or " \
               "whenever a new IDD version is needed."
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)
        intro_message = QtGui.QLabel(self.message)
        intro_message.setWordWrap(True)

        # Create and assign layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        layout.addWidget(intro_message)
        self.setLayout(layout)


class SetupWizLoadPage(QtGui.QWizardPage):

    def __init__(self, parent, version):
        super(SetupWizLoadPage, self).__init__(parent)

        self.version = version
        self.complete = False
        self.setTitle('Browse for the IDD file')
        self.setSubTitle('Browse for the specified IDD version below.')
        self.setup_page()

    def setup_page(self):
        # Create intro text
        text = "The file being loaded requires an IDD file of <b>Version {}</b>. " \
               "Please choose the 'Energy+.idd' file from the installation directory " \
               "for this version of EnergyPlus.".format(self.version)
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)

        # Create the button to browse for the idd file
        browse_button = QtGui.QPushButton("Browse for Energy+.idd v{} in the EnergyPlus "
                                          "install directory".format(self.version))
        browse_button.clicked.connect(self.load_idd)

        # Create and configure the progress bar
        self.progress_bar = QtGui.QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()

        # Create and assign layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        layout.addWidget(browse_button)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def load_idd(self):
        # Create and open file dialog
        directory = os.path.expanduser('~')
        formats = "EnergyPlus IDD Files (*.idd)"
        dialog_name = 'Select EnergyPlus IDD File (Version: {})'.format(self.version)
        file_dialog = QtGui.QFileDialog()
        dir_name, filt = file_dialog.getOpenFileName(self, dialog_name,
                                                     directory, formats)

        # Show progress bar and parse IDD file
        self.progress_bar.show()
        log.debug("Processing IDD file")
        idd_parser = parser.IDDParser()
        for progress in idd_parser.parse_idd(dir_name):
            self.progress_bar.setValue(progress)

        # Upon completion set complete status to true and inform object
        self.complete = True
        self.completeChanged.emit()

    def isComplete(self):
        return True if self.complete else False


class SetupWizard(QtGui.QWizard):

    def __init__(self, parent, version, message):
        super(SetupWizard, self).__init__(parent)

        # Add pages to the wizard and set some parameters
        log.debug("Initializing IDD Processing Wizard")
        self.addPage(SetupWizIntroPage(self, version, message))
        self.addPage(SetupWizLoadPage(self, version))
        self.setWindowTitle("IDD Processing Wizard")
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setOptions(QtGui.QWizard.NoBackButtonOnStartPage |
                        QtGui.QWizard.NoBackButtonOnLastPage)
