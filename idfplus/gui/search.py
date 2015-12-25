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
import re

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Setup logging
log = logging.getLogger(__name__)


class SearchReplaceDialog(QtGui.QDialog):
    """Search & Replace window
    """

    def __init__(self, parent, prefs, initial_query=None):
        super(SearchReplaceDialog, self).__init__(parent)

        self.parent = parent

        self.search_button = QtGui.QPushButton('Search')
        self.search_text = MySearchField(self.search_button)
        self.search_text.setPlaceholderText("Enter search query here")
        self.search_button.clicked.connect(self.submit_search)
        input_layout = QtGui.QHBoxLayout()
        input_layout.addWidget(self.search_text)
        input_layout.addWidget(self.search_button)

        self.results_tree = QtGui.QTreeView()
        self.results_tree.setRootIsDecorated(False)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setAllColumnsShowFocus(True)
        self.results_tree.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.results_tree.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.results_tree.doubleClicked.connect(self.go_to_object)

        self.whole_field_checkbox = QtGui.QCheckBox("Whole Field Only", self)
        self.advanced_search_checkbox = QtGui.QCheckBox("Advanced Search", self)
        self.advanced_search_checkbox.stateChanged.connect(self.advanced_search_checked)
        self.ignore_geometry_checkbox = QtGui.QCheckBox("Ignore Geometry", self)
        self.go_button = QtGui.QPushButton('Go')
        self.go_button.clicked.connect(self.go_to_object)
        checks_layout = QtGui.QHBoxLayout()
        checks_layout.addWidget(self.whole_field_checkbox)
        checks_layout.addWidget(self.advanced_search_checkbox)
        checks_layout.addWidget(self.ignore_geometry_checkbox)
        checks_layout.addStretch()
        checks_layout.addWidget(self.go_button)

        self.query_label = QtGui.QLabel("Query:")
        self.query_label.setEnabled(False)
        self.query_text = QtGui.QLineEdit()
        self.query_text.setEnabled(False)
        query_layout = QtGui.QHBoxLayout()
        query_layout.addWidget(self.query_label)
        query_layout.addWidget(self.query_text)

        self.select_label = QtGui.QLabel("Select:")
        self.select_all_button = QtGui.QPushButton("All")
        self.select_none_button = QtGui.QPushButton("None")
        self.select_invert_button = QtGui.QPushButton("Invert")
        self.select_delete_button = QtGui.QPushButton("Delete Objects")
        self.select_all_button.clicked.connect(self.select_all_clicked)
        self.select_none_button.clicked.connect(self.select_none_clicked)
        self.select_invert_button.clicked.connect(self.select_invert_clicked)
        self.select_delete_button.clicked.connect(self.select_delete_clicked)
        self.select_delete_button.setEnabled(False)
        selection_layout = QtGui.QHBoxLayout()
        selection_layout.addWidget(self.select_label)
        selection_layout.addWidget(self.select_all_button)
        selection_layout.addWidget(self.select_none_button)
        selection_layout.addWidget(self.select_invert_button)
        selection_layout.addStretch()
        selection_layout.addWidget(self.select_delete_button)

        self.replace_with_text = QtGui.QLineEdit()
        self.replace_with_label = QtGui.QLabel("Replace With:")
        self.replace_button = QtGui.QPushButton("Replace")
        self.replace_button.clicked.connect(self.replace_button_clicked)
        replace_layout = QtGui.QHBoxLayout()
        replace_layout.addWidget(self.replace_with_label)
        replace_layout.addWidget(self.replace_with_text)
        replace_layout.addWidget(self.replace_button)

        layout = QtGui.QVBoxLayout()
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
            item_0.setCheckState(QtCore.Qt.Unchecked)
            item_0.setFlags(item_0.flags() | QtCore.Qt.ItemIsUserCheckable)
            item_0.setEditable(False)

            item_1 = model.itemFromIndex(model.index(0, 1))
            item_1.setEditable(False)

        model = QtGui.QStandardItemModel(0, 3, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Value")
        model.setHeaderData(1, QtCore.Qt.Horizontal, "Class")
        model.setHeaderData(2, QtCore.Qt.Horizontal, "UUID")

        for hit in results:
            add_result_row(model, hit['value'], hit['obj_class'], hit['uuid'])

        return model

    def submit_search(self):
        """Submits a search based on the current query
        """

        user_query = self.search_text.text().lower()
        idf = self.parent.idf
        if not user_query or len(user_query) < 2 or not idf:
            return [], ""
        results, my_query = idf.search(user_query,
                                       self.whole_field_checkbox.isChecked(),
                                       self.advanced_search_checkbox.isChecked())
        self.query_text.setText(str(my_query))
        self.results_tree.setModel(self.create_results_model(results))
        self.results_tree.setColumnHidden(2, True)
        self.results_tree.resizeColumnToContents(0)
        self.results_tree.resizeColumnToContents(1)
        self.results_tree.setSortingEnabled(True)

    def select_all_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            model.itemFromIndex(model.index(i, 0)).setCheckState(QtCore.Qt.Checked)

    def select_none_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            model.itemFromIndex(model.index(i, 0)).setCheckState(QtCore.Qt.Unchecked)

    def select_invert_clicked(self):

        model = self.results_tree.model()
        result_count = model.rowCount()

        for i in range(result_count):
            item = model.itemFromIndex(model.index(i, 0))
            if item.checkState() == QtCore.Qt.Checked:
                new_state = QtCore.Qt.Unchecked
            else:
                new_state = QtCore.Qt.Checked
            item.setCheckState(new_state)

    def select_delete_clicked(self):
        pass

    def advanced_search_checked(self):
        if self.advanced_search_checkbox.isChecked():
            self.replace_button.setEnabled(False)
            self.replace_with_text.setEnabled(False)
            self.whole_field_checkbox.setEnabled(False)
        else:
            self.replace_button.setEnabled(True)
            self.replace_with_text.setEnabled(True)
            self.whole_field_checkbox.setEnabled(True)

    def replace_button_clicked(self):
        advanced_mode = self.advanced_search_checkbox.isChecked()
        search_text = self.search_text.text()
        replace_with_text = self.replace_with_text.text()
        if advanced_mode or not search_text or not replace_with_text:
            return

        question = "Are you sure you want to perform this replacement?\n" \
                   "Undo is currently NOT supported for this operation."
        response = self.confirm_action(question)
        if response is not True:
            return

        model = self.results_tree.model()
        result_count = model.rowCount()
        for i in range(result_count):
            item_0 = model.itemFromIndex(model.index(i, 0))
            item_2 = model.itemFromIndex(model.index(i, 2))
            if item_0.checkState() != QtCore.Qt.Checked:
                continue
            field = self.parent.idf.field_by_uuid(item_2.text())
            if self.whole_field_checkbox.isChecked():
                field.value = replace_with_text
            else:
                regex = re.compile(re.escape(search_text), re.IGNORECASE)
                field.value = regex.sub(replace_with_text, field.value)

        QtGui.QMessageBox.information(self, "Replacement", "Replacement Complete!")

    def confirm_action(self, question):
        """Confirm user wants to perform action
        """

        flags = QtGui.QMessageBox.StandardButton.Yes
        flags |= QtGui.QMessageBox.StandardButton.No
        response = QtGui.QMessageBox.question(self, "Are you sure?", question, flags)

        if response == QtGui.QMessageBox.Yes:
            return True
        elif QtGui.QMessageBox.No:
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


class MySearchField(QtGui.QLineEdit):
    """Subclass of QLineEdit used to allow submitting search with return/enter keys.
    """

    def __init__(self, search_button):
        super(MySearchField, self).__init__()
        self.search_button = search_button

    def keyPressEvent(self, event):
        """Overrides Qt key press method to filter return or enter keys.

        :param event:
        """
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.search_button.click()
        else:
            super(MySearchField, self).keyPressEvent(event)
