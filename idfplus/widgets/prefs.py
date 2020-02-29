#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module to manage the UI for preferences

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging

# PySide2 imports
from PySide2.QtCore import Qt
from PySide2.QtGui import QFontDatabase, QIntValidator
from PySide2.QtWidgets import (QDialog, QDialogButtonBox, QTabWidget, QVBoxLayout, QGroupBox,
                               QApplication, QLabel, QFontComboBox, QComboBox, QHBoxLayout,
                               QWidget, QLineEdit, QStyleFactory, QCheckBox, QRadioButton,
                               QButtonGroup, QPushButton)

# Package imports
from .. import config

# Setup logging
log = logging.getLogger(__name__)


class PrefsDialog(QDialog):
    """Form used to view and edit global program options
    """

    def __init__(self, parent, prefs):
        """Initialize the preferences tab
        """

        super(PrefsDialog, self).__init__(parent)
        self.prefs = prefs
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)

        # Create the tab widget and assign its tabs
        tab_widget = QTabWidget()
        tab_widget.addTab(AppearanceTab(self), "Appearance")
        tab_widget.addTab(FontsTab(self, parent), "Fonts")
        tab_widget.addTab(SaveTab(self), "Save Options")
        tab_widget.addTab(AdvancedTab(self, parent), "Advanced")

        # Create layout and assign it to self
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addWidget(button_box)
        self.resize(350, 350)
        self.setLayout(layout)
        self.setWindowTitle("IDF+ Options")

        # Connect gui elements to events
        button_box.accepted.connect(self.accept)

    def accept(self):
        """Override default accept method to save settings
        """
        self.prefs.write_settings()
        super(PrefsDialog, self).accept()


class FontsTab(QWidget):
    def __init__(self, parent_dialog, parent):
        """Initialize the fonts tab
        """

        super(FontsTab, self).__init__(parent_dialog)

        self.prefs = parent_dialog.prefs
        self.parent = parent

        # Base application font code
        app = QApplication.instance()
        self.font_base = app.font()
        font_label_base = QLabel("Base Application Font:")
        self.font_combo_base = QFontComboBox()
        self.font_combo_base.setMaximumWidth(175)
        self.font_combo_base.setCurrentFont(self.font_base.family())
        self.font_combo_base.currentFontChanged.connect(self.update)
        self.font_size_combo_base = QComboBox()
        points_base = self.font_points(self.font_base)
        self.font_size_combo_base.addItems(points_base)
        self.font_size_combo_base.setMaximumWidth(50)
        self.font_size_combo_base.setCurrentIndex(self.font_size_combo_base.findText(str(self.font_base.pointSize())))
        self.font_size_combo_base.currentIndexChanged.connect(self.update)
        base_layout = QHBoxLayout()
        base_layout.addWidget(font_label_base)
        base_layout.addWidget(self.font_combo_base)
        base_layout.addWidget(self.font_size_combo_base)

        # Class Tree font code
        self.font_classTree = self.parent.classTree.font()
        font_label_classTree = QLabel("Class Tree Font:")
        self.font_combo_classTree = QFontComboBox()
        self.font_combo_classTree.setMaximumWidth(175)
        self.font_combo_classTree.setCurrentFont(self.font_classTree.family())
        self.font_combo_classTree.currentFontChanged.connect(self.update)
        self.font_size_combo_classTree = QComboBox()
        points_classTree = self.font_points(self.font_classTree)
        self.font_size_combo_classTree.addItems(points_classTree)
        self.font_size_combo_classTree.setMaximumWidth(50)
        self.font_size_combo_classTree.setCurrentIndex(self.font_size_combo_classTree.findText(str(self.font_classTree.pointSize())))
        self.font_size_combo_classTree.currentIndexChanged.connect(self.update)
        classTree_layout = QHBoxLayout()
        classTree_layout.addWidget(font_label_classTree)
        classTree_layout.addWidget(self.font_combo_classTree)
        classTree_layout.addWidget(self.font_size_combo_classTree)

        # Class Table font code
        self.font_classTable = self.parent.classTable.font()
        font_label_classTable = QLabel("Class Table Font:")
        self.font_combo_classTable = QFontComboBox()
        self.font_combo_classTable.setMaximumWidth(175)
        self.font_combo_classTable.setCurrentFont(self.font_classTable.family())
        self.font_combo_classTable.currentFontChanged.connect(self.update)
        self.font_size_combo_classTable = QComboBox()
        points_classTable = self.font_points(self.font_classTable)
        self.font_size_combo_classTable.addItems(points_classTable)
        self.font_size_combo_classTable.setMaximumWidth(50)
        self.font_size_combo_classTable.setCurrentIndex(self.font_size_combo_classTable.findText(str(self.font_classTable.pointSize())))
        self.font_size_combo_classTable.currentIndexChanged.connect(self.update)
        classTable_layout = QHBoxLayout()
        classTable_layout.addWidget(font_label_classTable)
        classTable_layout.addWidget(self.font_combo_classTable)
        classTable_layout.addWidget(self.font_size_combo_classTable)

        # Comments view font code
        self.font_comments = self.parent.commentView.font()
        font_label_comments = QLabel("Comments Font:")
        self.font_combo_comments = QFontComboBox()
        self.font_combo_comments.setMaximumWidth(175)
        self.font_combo_comments.setCurrentFont(self.font_comments.family())
        self.font_combo_comments.currentFontChanged.connect(self.update)
        self.font_size_combo_comments = QComboBox()
        points_comments = self.font_points(self.font_comments)
        self.font_size_combo_comments.addItems(points_comments)
        self.font_size_combo_comments.setMaximumWidth(50)
        self.font_size_combo_comments.setCurrentIndex(self.font_size_combo_comments.findText(str(self.font_comments.pointSize())))
        self.font_size_combo_comments.currentIndexChanged.connect(self.update)
        comments_layout = QHBoxLayout()
        comments_layout.addWidget(font_label_comments)
        comments_layout.addWidget(self.font_combo_comments)
        comments_layout.addWidget(self.font_size_combo_comments)

        # Main layout code
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(base_layout)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(classTree_layout)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(classTable_layout)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(comments_layout)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    def update(self):
        self.font_base.setFamily(self.font_combo_base.currentFont().family())
        self.font_base.setPointSize(int(self.font_size_combo_base.currentText()))
        self.font_classTree.setFamily(self.font_combo_classTree.currentFont().family())
        self.font_classTree.setPointSize(int(self.font_size_combo_classTree.currentText()))
        self.font_classTable.setFamily(self.font_combo_classTable.currentFont().family())
        self.font_classTable.setPointSize(int(self.font_size_combo_classTable.currentText()))
        self.font_comments.setFamily(self.font_combo_comments.currentFont().family())
        self.font_comments.setPointSize(int(self.font_size_combo_comments.currentText()))
        self.prefs['base_font'] = self.font_base.toString()
        self.prefs['class_tree_font'] = self.font_classTree.toString()
        self.prefs['class_table_font'] = self.font_classTable.toString()
        self.prefs['comments_font'] = self.font_comments.toString()
        # self.prefs['log_font'] = self.font_base.toString()
        # self.prefs['ref_font'] = self.font_base.toString()
        # self.prefs['info_font'] = self.font_base.toString()
        # self.prefs['undo_font'] = self.font_base.toString()

    def font_points(self, font):
        points = [str(p) for p in QFontDatabase().pointSizes(font.family())]
        if not points:
            points = [str(p) for p in QFontDatabase().standardSizes()]
        return points


class AppearanceTab(QWidget):
    def __init__(self, parent):
        """Initialize the appearance tab
        """

        super(AppearanceTab, self).__init__(parent)

        self.prefs = parent.prefs

        # Default column width code
        col_width_label = QLabel("Default Column Width:")
        self.col_width_edit = QLineEdit(str(self.prefs['default_column_width']))
        self.col_width_edit.setMinimumWidth(40)
        self.col_width_edit.setMaximumWidth(100)
        validator = QIntValidator(10, 200, self)
        self.col_width_edit.setValidator(validator)

        # Visual style code
        style_label = QLabel("Visual Style of Application:")
        self.style_edit = QComboBox(self)
        self.style_edit.addItems(list(QStyleFactory.keys()))
        self.style_edit.setMaximumWidth(200)
        self.style_edit.setCurrentIndex(self.style_edit.findText(self.prefs['style']))

        # Units display code
        units_header_label = QLabel("Units Display:")
        self.header_units_check = QCheckBox('Show Units in Table Headers', self)
        checked_header = Qt.Checked if self.prefs['show_units_in_headers'] == 1 else Qt.Unchecked
        self.header_units_check.setCheckState(checked_header)
        self.cells_units_check = QCheckBox('Show Units in Table Cells', self)
        checked_cells = Qt.Checked if self.prefs['show_units_in_cells'] == 1 else Qt.Unchecked
        self.cells_units_check.setCheckState(checked_cells)

        # Handling of file options code
        default_handling_text = QLabel("Select how options saved directly within an IDF "
                                             "file are treated. See \"Save Options\" tab "
                                             "for the options in question.")
        default_handling_text.setWordWrap(True)
        default_handling_text.setMaximumWidth(450)
        self.button_force = QRadioButton("Force Session Options:", self)
        force_text = QLabel("Options from the current session will be used for all "
                                  "files, ignoring any options saved in the IDF file.")
        force_text.setWordWrap(True)
        force_text.setMaximumWidth(450)
        force_text.setMinimumHeight(30)
        force_text.setIndent(25)
        self.button_obey = QRadioButton("Obey IDF Options if Present:", self)
        obey_text = QLabel("Obey options saved in the IDF file. If none are "
                                 "present, use the current session's options.")
        obey_text.setWordWrap(True)
        obey_text.setMaximumWidth(450)
        obey_text.setMinimumHeight(30)
        obey_text.setIndent(25)

        # Handling of file options group box
        self.behaviour_group_box = QGroupBox("Handling of File-based Options")
        self.behaviour_group_box.setMinimumHeight(220)
        self.behaviour_group_box.setMinimumWidth(450)
        behaviour_box = QVBoxLayout()
        behaviour_box.addWidget(default_handling_text)
        behaviour_box.addWidget(self.button_force)
        behaviour_box.addWidget(force_text)
        behaviour_box.addSpacing(5)
        behaviour_box.addWidget(self.button_obey)
        behaviour_box.addWidget(obey_text)
        behaviour_box.addStretch(1)
        self.behaviour_group_box.setLayout(behaviour_box)

        self.behaviour_button_group = QButtonGroup(self)
        self.behaviour_button_group.addButton(self.button_force)
        self.behaviour_button_group.addButton(self.button_obey)
        self.behaviour_button_group.setId(self.button_force, 0)
        self.behaviour_button_group.setId(self.button_obey, 1)
        self.behaviour_button_group.button(self.prefs['obey_idf_options']).setChecked(True)

        # Main layout code
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(col_width_label)
        mainLayout.addWidget(self.col_width_edit)
        mainLayout.addSpacing(10)
        mainLayout.addWidget(style_label)
        mainLayout.addWidget(self.style_edit)
        mainLayout.addSpacing(10)
        mainLayout.addWidget(self.behaviour_group_box)
        mainLayout.addSpacing(10)
        mainLayout.addWidget(units_header_label)
        mainLayout.addWidget(self.header_units_check)
        mainLayout.addWidget(self.cells_units_check)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        # Update settings
        self.behaviour_button_group.buttonClicked.connect(self.update)
        self.col_width_edit.textChanged.connect(self.update)
        self.style_edit.currentIndexChanged.connect(self.update)
        self.header_units_check.stateChanged.connect(self.update)
        self.cells_units_check.stateChanged.connect(self.update)

    def update(self):
        self.prefs['default_column_width'] = self.col_width_edit.text()
        self.prefs['style'] = self.style_edit.currentText()
        self.prefs['obey_idf_options'] = self.behaviour_button_group.checkedId()
        self.prefs['show_units_in_headers'] = 1 if self.header_units_check.checkState() else 0
        self.prefs['show_units_in_cells'] = 1 if self.cells_units_check.checkState() else 0


class SaveTab(QWidget):
    def __init__(self, parent):
        """Initialize the save tab
        """

        super(SaveTab, self).__init__(parent)

        self.prefs = parent.prefs
        self.order_options = {'SortedOrder': 'Sorted (based on IDD file)',
                              'OriginalOrderTop': 'Original order (With new objects on top)',
                              'OriginalOrderBottom': 'Original order (With new objects on bottom)'}
        self.format_options = {'UseSpecialFormat': 'Use special formatting for some objects',
                               'None': 'Do not use special formatting'}

        # Sort Order Code
        order_label = QLabel("Save Order for Objects:")
        self.order_edit = QComboBox(self)
        self.order_edit.addItems(list(self.order_options.values()))
        self.order_edit.setMaximumWidth(350)
        order_setting = self.order_options[self.prefs['sort_order']]
        self.order_edit.setCurrentIndex(self.order_edit.findText(order_setting))
        self.order_edit.currentIndexChanged.connect(self.update_order)

        format_label = QLabel("Special Formatting:")
        self.format_edit = QComboBox(self)
        self.format_edit.addItems(list(self.format_options.values()))
        self.format_edit.setMaximumWidth(350)
        format_setting = self.format_options[self.prefs['special_formatting']]
        self.format_edit.setCurrentIndex(self.format_edit.findText(format_setting))
        self.order_edit.currentIndexChanged.connect(self.update_format)

        self.save_group_box = QGroupBox("Default Save Options")
        save_box = QVBoxLayout()
        save_box.addWidget(order_label)
        save_box.addWidget(self.order_edit)
        save_box.addSpacing(10)
        save_box.addWidget(format_label)
        save_box.addWidget(self.format_edit)
        save_box.addStretch(1)
        self.save_group_box.setLayout(save_box)
        self.save_group_box.setEnabled(False)

        # Save additional options code
        self.save_units_check = QCheckBox('Units to display by default (SI vs IP)', self)
        checked_header = Qt.Checked if self.prefs['save_units'] == 1 else Qt.Unchecked
        self.save_units_check.setCheckState(checked_header)
        self.save_units_check.stateChanged.connect(self.update)
        self.save_hidden_classes_check = QCheckBox('Whether empty classes are hidden', self)
        checked_cells = Qt.Checked if self.prefs['save_hidden_classes'] == 1 else Qt.Unchecked
        self.save_hidden_classes_check.setCheckState(checked_cells)
        self.save_hidden_classes_check.stateChanged.connect(self.update)
        self.save_groups_check = QCheckBox('Whether to hide group headers', self)
        checked_groups = Qt.Checked if self.prefs['save_hide_groups'] == 1 else Qt.Unchecked
        self.save_groups_check.setCheckState(checked_groups)
        self.save_groups_check.stateChanged.connect(self.update)

        # Save additional options group box code
        self.save_additional_group_box = QGroupBox("Save Additional Options in IDF File")
        save_additional_box = QVBoxLayout()
        save_additional_box.addWidget(self.save_units_check)
        save_additional_box.addWidget(self.save_hidden_classes_check)
        save_additional_box.addWidget(self.save_groups_check)
        save_additional_box.addStretch(1)
        self.save_additional_group_box.setLayout(save_additional_box)

        # Main layout code
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.save_additional_group_box)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.save_group_box)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update_order(self):
        text = self.order_edit.currentText()
        for key, val in list(self.order_options.items()):
            if val == text:
                to_save = key
        self.prefs['sort_order'] = to_save

    def update_format(self):
        text = self.format_edit.currentText()
        for key, val in self.format_options.items():
            if val == text:
                to_save = key
        self.prefs['format'] = to_save

    def update(self):
        self.prefs['save_units'] = 1 if self.save_units_check.checkState() else 0
        self.prefs['save_hidden_classes'] = 1 if self.save_hidden_classes_check.checkState() else 0
        self.prefs['save_hide_groups'] = 1 if self.save_groups_check.checkState() else 0


class AdvancedTab(QWidget):
    def __init__(self, parent_dialog, parent):
        """Initialize the advanced tab
        """

        super(AdvancedTab, self).__init__(parent)

        self.prefs = parent_dialog.prefs
        self.parent = parent

        # Log Details
        log_label = QLabel("Log Detail Level:")
        self.log_edit = QComboBox(self)
        self.log_edit.addItems(['INFO', 'DEBUG', 'WARNING'])
        self.log_edit.setCurrentIndex(self.log_edit.findText(self.prefs['log_level']))
        self.log_edit.currentIndexChanged.connect(self.log_level)
        self.log_edit.setMaximumWidth(100)

        # Clear IDD cache
        self.clear_idd_button = QPushButton("Clear IDD Cache")
        self.clear_idd_button.setMaximumWidth(200)
        self.clear_idd_button.clicked.connect(self.clear_idd_cache)
        clear_text = QLabel("This will delete the pre-processed IDD files and force "
                                  "IDF+ to reprocess them the next time they are required. "
                                  "This should happen automatically when necessary, but if "
                                  "there are problems after updating to a new version of "
                                  "IDF+, it can sometimes help to force it here.")
        clear_text.setWordWrap(True)
        clear_text.setMaximumWidth(450)
        clear_text.setMinimumHeight(40)

        # Clear IDD cache group box code
        self.clear_idd_group_box = QGroupBox("Clear Pre-processed IDD Cache:")
        clear_group_box = QVBoxLayout()
        clear_group_box.addWidget(clear_text)
        clear_group_box.addSpacing(10)
        clear_group_box.addWidget(self.clear_idd_button)
        clear_group_box.addStretch(1)
        self.clear_idd_group_box.setLayout(clear_group_box)

        # Open dirs code
        self.open_settings_button = QPushButton("Open Settings Directory")
        self.open_settings_button.setMaximumWidth(175)
        self.open_settings_button.clicked.connect(lambda: self.parent.show_in_folder(config.CONFIG_FILE_PATH))
        self.open_log_button = QPushButton("Open Log Directory")
        self.open_log_button.setMaximumWidth(175)
        self.open_log_button.clicked.connect(lambda: self.parent.show_in_folder(config.LOG_DIR))
        self.open_data_button = QPushButton("Open Data Directory")
        self.open_data_button.setMaximumWidth(175)
        self.open_data_button.clicked.connect(lambda: self.parent.show_in_folder(config.DATA_DIR))

        # Default IDF file version code
        idd_label = QLabel("Default IDF File Version:")
        idd_label.setToolTip('Default version to use if none is detected.')
        self.idd_edit = QComboBox(self)
        self.idd_edit.addItems(config.idd_versions())
        self.idd_edit.setMaximumWidth(100)
        self.idd_edit.setCurrentIndex(self.idd_edit.findText(self.prefs['default_idd_version']))
        self.idd_edit.currentIndexChanged.connect(self.update_idd_version)

        # Main layout code
        main_layout = QVBoxLayout()
        main_layout.addWidget(idd_label)
        main_layout.addWidget(self.idd_edit)
        main_layout.addSpacing(10)
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_edit)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.clear_idd_group_box)
        main_layout.addStretch(1)
        main_layout.addWidget(self.open_settings_button)
        main_layout.addWidget(self.open_log_button)
        main_layout.addWidget(self.open_data_button)
        self.setLayout(main_layout)

    def log_level(self):
        self.prefs['log_level'] = self.log_edit.currentText()

    def clear_idd_cache(self):
        self.prefs['clear_idd_cache'] = True

    def update_idd_version(self):
        self.prefs['default_idd_version'] = self.idd_edit.currentText()
