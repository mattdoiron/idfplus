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
import logging

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .. import config

# Setup logging
log = logging.getLogger(__name__)


class PrefsDialog(QtGui.QDialog):
    """Form used to view and edit global program options
    """

    def __init__(self, parent, prefs):
        super(PrefsDialog, self).__init__(parent)
        self.prefs = prefs
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        # Create the tab widget and assign its tabs
        tab_widget = QtGui.QTabWidget()
        tab_widget.addTab(AppearanceTab(self), "Appearance")
        tab_widget.addTab(SaveTab(self), "Save Options")
        tab_widget.addTab(AdvancedTab(self), "Advanced")

        # Create layout and assign it to self
        layout = QtGui.QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addWidget(button_box)
        self.resize(350, 350)
        self.setLayout(layout)
        self.setWindowTitle("IDF+ Options")

        # Connect gui elements to events
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        """Override default accept method to save settings
        """
        self.prefs.write_settings()
        super(PrefsDialog, self).accept()


class AppearanceTab(QtGui.QWidget):
    def __init__(self, parent):
        super(AppearanceTab, self).__init__(parent)

        self.prefs = parent.prefs

        col_width_label = QtGui.QLabel("Default Column Width:")
        self.col_width_edit = QtGui.QLineEdit(str(self.prefs['default_column_width']))
        self.col_width_edit.setMinimumWidth(40)
        self.col_width_edit.setMaximumWidth(100)
        validator = QtGui.QIntValidator(10, 200, self)
        self.col_width_edit.setValidator(validator)

        style_label = QtGui.QLabel("Visual Style of Application:")
        self.style_edit = QtGui.QComboBox(self)
        self.style_edit.addItems(QtGui.QStyleFactory.keys())
        self.style_edit.setMaximumWidth(200)
        self.style_edit.setCurrentIndex(self.style_edit.findText(self.prefs['style']))

        units_header_label = QtGui.QLabel("Units Display:")
        self.header_units_check = QtGui.QCheckBox('Show Units in Table Headers', self)
        checked_header = QtCore.Qt.Checked if self.prefs['show_units_in_headers'] == 1 else QtCore.Qt.Unchecked
        self.header_units_check.setCheckState(checked_header)
        self.cells_units_check = QtGui.QCheckBox('Show Units in Table Cells', self)
        checked_cells = QtCore.Qt.Checked if self.prefs['show_units_in_cells'] == 1 else QtCore.Qt.Unchecked
        self.cells_units_check.setCheckState(checked_cells)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(col_width_label)
        mainLayout.addWidget(self.col_width_edit)
        mainLayout.addSpacing(15)
        mainLayout.addWidget(style_label)
        mainLayout.addWidget(self.style_edit)
        mainLayout.addSpacing(15)
        mainLayout.addWidget(units_header_label)
        mainLayout.addWidget(self.header_units_check)
        mainLayout.addWidget(self.cells_units_check)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        self.col_width_edit.textChanged.connect(self.update)
        self.style_edit.currentIndexChanged.connect(self.update)
        self.header_units_check.stateChanged.connect(self.update)
        self.cells_units_check.stateChanged.connect(self.update)

    def update(self):
        self.prefs['default_column_width'] = self.col_width_edit.text()
        self.prefs['style'] = self.style_edit.currentText()
        self.prefs['show_units_in_headers'] = 1 if self.header_units_check.checkState() else 0
        self.prefs['show_units_in_cells'] = 1 if self.cells_units_check.checkState() else 0


class SaveTab(QtGui.QWidget):
    def __init__(self, parent):
        super(SaveTab, self).__init__(parent)

        self.prefs = parent.prefs
        self.order_options = {'SortedOrder': 'Sorted (based on IDD file)',
                              'OriginalOrderTop': 'Original order (With new objects on top)',
                              'OriginalOrderBottom': 'Original order (With new objects on bottom)'}
        self.format_options = {'UseSpecialFormat': 'Use special formatting for some objects',
                               'None': 'Do not use special formatting'}

        # Sort Order Code
        order_label = QtGui.QLabel("Save Order for Objects:")
        self.order_edit = QtGui.QComboBox(self)
        self.order_edit.addItems(self.order_options.values())
        self.order_edit.setMaximumWidth(350)
        order_setting = self.order_options[self.prefs['sort_order']]
        self.order_edit.setCurrentIndex(self.order_edit.findText(order_setting))
        self.order_edit.currentIndexChanged.connect(self.update_order)

        format_label = QtGui.QLabel("Special Formatting:")
        self.format_edit = QtGui.QComboBox(self)
        self.format_edit.addItems(self.format_options.values())
        self.format_edit.setMaximumWidth(350)
        format_setting = self.format_options[self.prefs['special_formatting']]
        self.format_edit.setCurrentIndex(self.format_edit.findText(format_setting))
        self.order_edit.currentIndexChanged.connect(self.update_format)

        apply_defaults_button = QtGui.QPushButton("Apply defaults to current file")
        apply_defaults_button.setMaximumWidth(225)
        apply_defaults_button.clicked.connect(self.apply_defaults)

        save_group_box = QtGui.QGroupBox("Default Save Options")
        save_box = QtGui.QVBoxLayout()
        save_box.addWidget(order_label)
        save_box.addWidget(self.order_edit)
        save_box.addSpacing(15)
        save_box.addWidget(format_label)
        save_box.addWidget(self.format_edit)
        save_box.addSpacing(15)
        save_box.addWidget(apply_defaults_button)
        save_box.addStretch(1)
        save_group_box.setLayout(save_box)
        save_group_box.setEnabled(False)

        # Behaviour code
        button_force = QtGui.QRadioButton("Force Defaults:", self)
        force_text = QtGui.QLabel("The above defaults will be used for all files, ignoring any "
                                  "settings saved in the IDF file.")
        force_text.setWordWrap(True)
        force_text.setMaximumWidth(350)
        force_text.setMinimumHeight(40)
        force_text.setIndent(25)
        button_obey = QtGui.QRadioButton("Obey IDF Setting:", self)
        obey_text = QtGui.QLabel("Obey any settings saved in the IDF file. If no settings are "
                                 "present, use the defaults.")
        obey_text.setWordWrap(True)
        obey_text.setMaximumWidth(350)
        obey_text.setMinimumHeight(40)
        obey_text.setIndent(25)

        behaviour_group_box = QtGui.QGroupBox("Default Handling Behaviour")
        behaviour_box = QtGui.QVBoxLayout()
        behaviour_box.addWidget(button_force)
        behaviour_box.addWidget(force_text)
        behaviour_box.addWidget(button_obey)
        behaviour_box.addWidget(obey_text)
        behaviour_box.addStretch(1)
        behaviour_group_box.setLayout(behaviour_box)
        behaviour_group_box.setEnabled(False)

        self.behaviour_button_group = QtGui.QButtonGroup(self)
        self.behaviour_button_group.addButton(button_force)
        self.behaviour_button_group.addButton(button_obey)
        self.behaviour_button_group.setId(button_force, 0)
        self.behaviour_button_group.setId(button_obey, 1)
        self.behaviour_button_group.button(self.prefs['format_behaviour']).setChecked(True)
        self.behaviour_button_group.buttonClicked.connect(self.set_behaviour)

        # Save additional options code
        self.save_units_check = QtGui.QCheckBox('Units to display by default (SI vs IP)', self)
        checked_header = QtCore.Qt.Checked if self.prefs['save_units'] == 1 else QtCore.Qt.Unchecked
        self.save_units_check.setCheckState(checked_header)
        self.save_units_check.stateChanged.connect(self.update)
        self.save_hidden_classes_check = QtGui.QCheckBox('Whether empty classes are hidden', self)
        checked_cells = QtCore.Qt.Checked if self.prefs['save_hidden_classes'] == 1 else QtCore.Qt.Unchecked
        self.save_hidden_classes_check.setCheckState(checked_cells)
        self.save_hidden_classes_check.stateChanged.connect(self.update)
        self.save_groups_check = QtGui.QCheckBox('Whether to hide group headers', self)
        checked_groups = QtCore.Qt.Checked if self.prefs['save_hide_groups'] == 1 else QtCore.Qt.Unchecked
        self.save_groups_check.setCheckState(checked_groups)
        self.save_groups_check.stateChanged.connect(self.update)

        save_additional_group_box = QtGui.QGroupBox("Save Additional Options in IDF File")
        save_additional_box = QtGui.QVBoxLayout()
        save_additional_box.addWidget(self.save_units_check)
        save_additional_box.addWidget(self.save_hidden_classes_check)
        save_additional_box.addWidget(self.save_groups_check)
        save_additional_box.addStretch(1)
        save_additional_group_box.setLayout(save_additional_box)

        # Main layout code
        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(save_group_box)
        main_layout.addSpacing(15)
        main_layout.addWidget(behaviour_group_box)
        main_layout.addSpacing(15)
        main_layout.addWidget(save_additional_group_box)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update_order(self):
        text = self.order_edit.currentText()
        for key, val in self.order_options.iteritems():
            if val == text:
                to_save = key
        self.prefs['sort_order'] = to_save

    def update_format(self):
        text = self.format_edit.currentText()
        for key, val in self.format_options.iteritems():
            if val == text:
                to_save = key
        self.prefs['format'] = to_save

    def apply_defaults(self):
        self.prefs['apply_default_save_behaviour'] = True

    def set_behaviour(self):
        self.prefs['format_behaviour'] = self.behaviour_button_group.checkedId()

    def update(self):
        self.prefs['save_units'] = 1 if self.save_units_check.checkState() else 0
        self.prefs['save_hidden_classes'] = 1 if self.save_hidden_classes_check.checkState() else 0
        self.prefs['save_hide_groups'] = 1 if self.save_groups_check.checkState() else 0


class AdvancedTab(QtGui.QWidget):
    def __init__(self, parent):
        super(AdvancedTab, self).__init__(parent)

        self.prefs = parent.prefs

        log_label = QtGui.QLabel("Log Detail Level:")
        self.log_edit = QtGui.QComboBox(self)
        self.log_edit.addItems(['INFO', 'DEBUG', 'WARNING'])
        self.log_edit.setCurrentIndex(self.log_edit.findText(self.prefs['log_level']))
        self.log_edit.currentIndexChanged.connect(self.log_level)
        self.log_edit.setMaximumWidth(100)

        clear_idd_label = QtGui.QLabel("Clear pre-processed IDD cache:")
        self.clear_idd_button = QtGui.QPushButton("Clear IDD cache")
        self.clear_idd_button.setMaximumWidth(200)
        self.clear_idd_button.clicked.connect(self.clear_idd_cache)
        clear_text = QtGui.QLabel("This will delete the pre-processed IDD files and force "
                                  "IDF+ to reprocess them the next time they are required. "
                                  "This should happen automatically when required, but if "
                                  "there are problems after updating to a new version of "
                                  "IDF+, it can sometimes help to force it here.")
        clear_text.setWordWrap(True)
        clear_text.setMaximumWidth(350)
        clear_text.setMinimumHeight(40)

        idd_label = QtGui.QLabel("Default IDF File Version:")
        idd_label.setToolTip('Default version to use if none is detected.')
        self.idd_edit = QtGui.QComboBox(self)
        self.idd_edit.addItems(config.idd_versions())
        self.idd_edit.setMaximumWidth(100)
        self.idd_edit.setCurrentIndex(self.idd_edit.findText(self.prefs['default_idd_version']))
        self.idd_edit.currentIndexChanged.connect(self.update_idd_version)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(idd_label)
        main_layout.addWidget(self.idd_edit)
        main_layout.addSpacing(15)
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_edit)
        main_layout.addSpacing(15)
        main_layout.addWidget(clear_idd_label)
        main_layout.addWidget(self.clear_idd_button)
        main_layout.addWidget(clear_text)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def log_level(self):
        self.prefs['log_level'] = self.log_edit.currentText()

    def clear_idd_cache(self):
        self.prefs['clear_idd_cache'] = True

    def update_idd_version(self):
        self.prefs['default_idd_version'] = self.idd_edit.currentText()
