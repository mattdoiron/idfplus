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

# PySide imports
from PySide import QtGui

# Package imports
from . import idfsettings as c
from . import logger

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class SetupWizIntroPage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizIntroPage, self).__init__(*args, **kwargs)
        self.setTitle('IDF+ Setup Wizard Introduction')
        self.setSubTitle('This wizard will help you with some necessary setup tasks.')
        self.setup_page()

    def setup_page(self):
        text = "IDF+ uses EnergyPlus' own IDD file in order to understand " \
               "how to work with IDF files. Each IDD file version is processed once " \
               "and stored so that this procedure will be required only once, or " \
               "whenever new IDD versions are needed."
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        self.setLayout(layout)


class SetupWizChoicePage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizChoicePage, self).__init__(*args, **kwargs)
        self.setTitle('Make a selection')
        self.setSubTitle('Choose from one of the options below.')

    def nextId(self):
        if self.field("search_method_automatic").isChecked():
            return SetupWizard.Page_Auto
        else:
            return SetupWizard.Page_Manual

    def setup_page(self):
        radio_auto = QtGui.QRadioButton("Automatic")
        radio_auto.setChecked(True)
        radio_manual = QtGui.QRadioButton("Manual")
        self.registerField("search_method_automatic", radio_auto)
        self.registerField("search_method_manual", radio_manual)

        label_auto = QtGui.QLabel("This will have IDF+ search for installed "
                                  "EnergyPlus versions and process all of their IDD "
                                  "files automatically. (Recommended)")
        label_manual = QtGui.QLabel("Choose this if you know the location of the "
                                    "desired IDD file.")
        label_auto.setBuddy(radio_auto)
        label_manual.setBuddy(radio_manual)
        label_auto.setWordWrap(True)
        label_manual.setWordWrap(True)

        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)

        layout = QtGui.QGridLayout()
        layout.addWidget(radio_auto, 0, 0)
        layout.addWidget(label_auto, 0, 1)
        layout.addWidget(line, 1, 0, 1, 2)
        layout.addWidget(radio_manual, 2, 0)
        layout.addWidget(label_manual, 2, 1)
        self.setLayout(layout)


class SetupWizAutoPage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizAutoPage, self).__init__(*args, **kwargs)
        self.setTitle('Automatic IDD Processing')
        self.setSubTitle('The wizard will automatically detect available IDD files.')
        self.setup_page()

    def setup_page(self):
        text = "The wizard will automatically detect available IDD files."
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        self.setLayout(layout)


class SetupWizManualPage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizManualPage, self).__init__(*args, **kwargs)
        self.setTitle('Manual IDD Processing')
        self.setSubTitle('The wizard will automatically detect available IDD files.')
        self.setup_page()

    def setup_page(self):
        text = "The wizard will automatically detect available IDD files."
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        self.setLayout(layout)


class SetupWizProgressPage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizProgressPage, self).__init__(*args, **kwargs)
        self.setTitle('Searching for and Loading IDD Files')
        self.setSubTitle('The progress of the IDD processing is shown below.')
        self.setup_page()

    def setup_page(self):
        pass


class SetupWizFinishPage(QtGui.QWizardPage):

    def __init__(self, *args, **kwargs):
        super(SetupWizFinishPage, self).__init__(*args, **kwargs)
        self.setTitle('Setup Wizard Finished')
        self.setSubTitle('The setup wizard is now complete.')
        self.setup_page()

    def setup_page(self):
        text = "The wizard is now complete. You can launch this wizard again" \
               "from the tools menu if necessary. It will also launch automatically " \
               "whenever it is detected that a new, unprocessed IDD file is required."
        intro_text = QtGui.QLabel(text)
        intro_text.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro_text)
        self.setLayout(layout)


class SetupWizard(QtGui.QWizard):

    Page_Intro = 1
    Page_Choice = 2
    Page_Auto = 3
    Page_Manual = 4
    Page_Progress = 5
    Page_Finish = 6

    def __init__(self, *args, **kwargs):
        super(SetupWizard, self).__init__(*args, **kwargs)

        self.setPage(self.Page_Intro, SetupWizIntroPage())
        self.setPage(self.Page_Choice, SetupWizChoicePage())
        self.setPage(self.Page_Auto, SetupWizAutoPage())
        self.setPage(self.Page_Manual, SetupWizManualPage())
        self.setPage(self.Page_Progress, SetupWizProgressPage())
        self.setPage(self.Page_Finish, SetupWizFinishPage())
        self.setWindowTitle("IDF+ Setup Wizard")
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setOptions(QtGui.QWizard.NoBackButtonOnStartPage |
                        QtGui.QWizard.NoBackButtonOnLastPage)
