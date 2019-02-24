#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module to manage search widgets

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging
import re

# PySide2 imports
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItemModel
from PySide2.QtWidgets import (QDialog, QHBoxLayout, QPushButton, QTreeView, QAbstractItemView,
                               QCheckBox, QLineEdit, QLabel, QVBoxLayout, QMessageBox)

# Setup logging
log = logging.getLogger(__name__)


class SearchReplaceDialog(QDialog):
    """Search & Replace window
    """

    def __init__(self, parent, initial_query=None):
        """Initialize the search window
        """

        super(SearchReplaceDialog, self).__init__(parent)

        self.parent = parent
        self.prefs = parent.prefs
        self.items_checked = 0

        self.search_button = QPushButton('Search')
        self.search_text = MySearchField(self.search_button)
        self.search_text.setPlaceholderText("Enter search query here")
        self.search_button.clicked.connect(self.submit_search)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.search_text)
        input_layout.addWidget(self.search_button)

        self.results_tree = QTreeView()
        self.results_tree.setRootIsDecorated(False)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setAllColumnsShowFocus(True)
        self.results_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_tree.doubleClicked.connect(self.go_to_object)

        self.whole_field_checkbox = QCheckBox("Whole Field Only", self)
        self.advanced_search_checkbox = QCheckBox("Advanced Search", self)
        self.advanced_search_checkbox.stateChanged.connect(self.advanced_search_checked)
        self.ignore_geometry_checkbox = QCheckBox("Ignore Geometry", self)
        self.go_button = QPushButton('Go')
        self.go_button.clicked.connect(self.go_to_object)
        checks_layout = QHBoxLayout()
        checks_layout.addWidget(self.whole_field_checkbox)
        checks_layout.addWidget(self.advanced_search_checkbox)
        checks_layout.addWidget(self.ignore_geometry_checkbox)
        checks_layout.addStretch()
        checks_layout.addWidget(self.go_button)

        self.query_label = QLabel("Query:")
        self.query_label.setEnabled(False)
        self.query_text = QLineEdit()
        self.query_text.setEnabled(True)
        self.query_text.setReadOnly(True)
        self.query_text.setFrame(False)
        self.query_text.setStyleSheet("""QLineEdit {
                                   background-color: LightGray;
                                   color: white;
                                   } """)
        query_layout = QHBoxLayout()
        query_layout.addWidget(self.query_label)
        query_layout.addWidget(self.query_text)

        self.select_label = QLabel("Select:")
        self.select_all_button = QPushButton("All")
        self.select_none_button = QPushButton("None")
        self.select_invert_button = QPushButton("Invert")
        self.delete_button = QPushButton("Delete Objects")
        self.select_all_button.clicked.connect(self.select_all_clicked)
        self.select_none_button.clicked.connect(self.select_none_clicked)
        self.select_invert_button.clicked.connect(self.select_invert_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)
        self.delete_button.setEnabled(False)
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(self.select_label)
        selection_layout.addWidget(self.select_all_button)
        selection_layout.addWidget(self.select_none_button)
        selection_layout.addWidget(self.select_invert_button)
        selection_layout.addStretch()
        selection_layout.addWidget(self.delete_button)

        self.replace_with_text = QLineEdit()
        self.replace_with_label = QLabel("Replace With:")
        self.replace_button = QPushButton("Replace")
        self.replace_button.clicked.connect(self.replace_button_clicked)
        self.replace_button.setEnabled(False)
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(self.replace_with_label)
        replace_layout.addWidget(self.replace_with_text)
        replace_layout.addWidget(self.replace_button)

        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(checks_layout)
        layout.addLayout(query_layout)
        layout.addWidget(self.results_tree)
        layout.addLayout(selection_layout)
        layout.addLayout(replace_layout)

        self.resize(650, 450)
        self.setLayout(layout)
        self.setWindowTitle("IDF+ Search & Replace")
        self.search_text.setFocus()
        self.setTabOrder(self.search_text, self.search_button)
        self.setTabOrder(self.search_button, self.whole_field_checkbox)
        self.setTabOrder(self.whole_field_checkbox, self.advanced_search_checkbox)
        self.setTabOrder(self.advanced_search_checkbox, self.select_all_button)
        self.setTabOrder(self.select_all_button, self.select_none_button)
        self.setTabOrder(self.select_none_button, self.select_invert_button)
        self.setTabOrder(self.select_invert_button, self.replace_with_text)
        self.setTabOrder(self.replace_with_text, self.replace_button)
        self.setTabOrder(self.replace_button, self.search_text)

        self.results_tree.setModel(self.create_results_model([]))
        self.results_tree.setColumnHidden(2, True)

        if initial_query is not None:
            self.search_text.setText(initial_query)
            self.search_button.click()

    def create_results_model(self, results):

        def add_result_row(row_model, value, obj_class, uuid):
            row_model.insertRow(0)
            row_model.setData(model.index(0, 0), value)
            row_model.setData(model.index(0, 1), obj_class)
            row_model.setData(model.index(0, 2), uuid)

            item_0 = model.itemFromIndex(model.index(0, 0))
            item_0.setCheckState(Qt.Unchecked)
            item_0.setFlags(item_0.flags() | Qt.ItemIsUserCheckable)
            item_0.setEditable(False)

            item_1 = model.itemFromIndex(model.index(0, 1))
            item_1.setEditable(False)

        model = QStandardItemModel(0, 3, self)
        model.setHeaderData(0, Qt.Horizontal, "Value")
        model.setHeaderData(1, Qt.Horizontal, "Class")
        model.setHeaderData(2, Qt.Horizontal, "UUID")

        for hit in results:
            add_result_row(model, hit['value'], hit['obj_class_display'], hit['uuid'])

        return model

    def submit_search(self):
        """Submits a search based on the current query
        """

        user_query = self.search_text.text()
        idf = self.parent.idf
        if not user_query or len(user_query) < 2 or not idf:
            return [], ""
        results, my_query = idf.search(user_query,
                                       self.whole_field_checkbox.isChecked(),
                                       self.advanced_search_checkbox.isChecked(),
                                       self.ignore_geometry_checkbox.isChecked())
        self.query_text.setText(str(my_query))
        self.results_tree.setModel(self.create_results_model(results))
        self.results_tree.model().itemChanged.connect(self.item_checked)
        # self.results_tree.setColumnHidden(2, True)
        self.results_tree.resizeColumnToContents(0)
        self.results_tree.resizeColumnToContents(1)
        self.results_tree.setSortingEnabled(True)

    def item_checked(self, item):

        if item.checkState() == Qt.Checked:
            self.items_checked += 1
        else:
            self.items_checked -= 1

        if self.items_checked > 0:
            self.delete_button.setEnabled(True)
            self.replace_button.setEnabled(True)
        else:
            self.delete_button.setEnabled(False)
            self.replace_button.setEnabled(False)

    def select_all_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            model.itemFromIndex(model.index(i, 0)).setCheckState(Qt.Checked)

    def select_none_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            model.itemFromIndex(model.index(i, 0)).setCheckState(Qt.Unchecked)

    def select_invert_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            item = model.itemFromIndex(model.index(i, 0))
            if item.checkState() == Qt.Checked:
                new_state = Qt.Unchecked
            else:
                new_state = Qt.Checked
            item.setCheckState(new_state)

    def delete_button_clicked(self):
        model = self.results_tree.model()
        result_count = model.rowCount()
        if result_count <= 0 or self.items_checked <= 0:
            return

        question = "Are you sure you want to perform this deletion?\n" \
                   "Undo is currently NOT supported for this operation."
        response = self.confirm_action(question)
        if response is not True:
            return

        for i in range(result_count):
            item_0 = model.itemFromIndex(model.index(i, 0))
            item_2 = model.itemFromIndex(model.index(i, 2))
            if item_0.checkState() != Qt.Checked:
                continue
            field = self.parent.idf.field_by_uuid(item_2.text())
            obj = field._outer
            obj_class = self.parent.idf.idf_objects(obj.obj_class)
            try:
                index = obj_class.index(obj)
                self.parent.idf.remove_objects(obj.obj_class, index, index + 1)
            except ValueError:
                pass  # already deleted

        self.parent.set_dirty(True)
        self.submit_search()
        self.parent.load_table_view(self.parent.current_obj_class)
        QMessageBox.information(self, "Delete Action", "Deletion Complete!")

    def advanced_search_checked(self):
        if self.advanced_search_checkbox.isChecked():
            self.whole_field_checkbox.setEnabled(False)
            self.whole_field_checkbox.setChecked(True)
            self.ignore_geometry_checkbox.setEnabled(False)
            self.ignore_geometry_checkbox.setChecked(False)
        else:
            self.whole_field_checkbox.setEnabled(True)
            self.whole_field_checkbox.setChecked(False)
            self.ignore_geometry_checkbox.setEnabled(True)
            self.ignore_geometry_checkbox.setChecked(False)

    def replace_button_clicked(self):
        search_text = self.search_text.text()
        replace_with_text = self.replace_with_text.text()
        if not search_text:
            return

        model = self.results_tree.model()
        result_count = model.rowCount()
        if result_count <= 0 or self.items_checked <= 0:
            return

        question = "Are you sure you want to perform this replacement?\n" \
                   "Undo is currently NOT supported for this operation."
        response = self.confirm_action(question)
        if response is not True:
            return

        for i in range(result_count):
            item_0 = model.itemFromIndex(model.index(i, 0))
            item_2 = model.itemFromIndex(model.index(i, 2))
            if item_0.checkState() != Qt.Checked:
                continue
            field = self.parent.idf.field_by_uuid(item_2.text())
            if self.whole_field_checkbox.isChecked() or self.advanced_search_checkbox.isChecked():
                field.value = replace_with_text
            else:
                regex = re.compile(re.escape(search_text), re.IGNORECASE)
                field.value = regex.sub(replace_with_text, field.value)

        self.parent.set_dirty(True)
        self.submit_search()
        self.parent.load_table_view(self.parent.current_obj_class)
        QMessageBox.information(self, "Replacement", "Replacement Complete!")

    def confirm_action(self, question):
        """Confirm user wants to perform action
        """

        flags = QMessageBox.StandardButton.Yes
        flags |= QMessageBox.StandardButton.No
        response = QMessageBox.question(self, "Are you sure?", question, flags)

        if response == QMessageBox.Yes:
            return True
        elif QMessageBox.No:
            return False
        else:
            return False

    def go_to_object(self, index=None):

        if index is None:
            selected = self.results_tree.selectedIndexes()
            if not selected:
                return
            index = selected[0]

        model = self.results_tree.model()
        item = model.itemFromIndex(model.index(index.row(), 2))
        field = self.parent.idf.field_by_uuid(item.text())
        self.parent.activateWindow()
        self.parent.jump_to_field(field)


class MySearchField(QLineEdit):
    """Subclass of QLineEdit used to allow submitting search with return/enter keys.
    """

    def __init__(self, search_button):
        """Initialize the search field class
        """

        super(MySearchField, self).__init__()
        self.search_button = search_button

    def keyPressEvent(self, event):
        """Overrides Qt key press method to filter return or enter keys.

        :param event:
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.search_button.click()
        else:
            super(MySearchField, self).keyPressEvent(event)
