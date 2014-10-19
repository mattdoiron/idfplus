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

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import commands
from . import idfsettings as c
from . import logger

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class GenericDelegate(QtGui.QStyledItemDelegate):
    """Template delegate for the table view."""

    def __init__(self, main_window, idd_objects, obj_orientation):
        super(GenericDelegate, self).__init__(main_window.classTable)
        self.delegates = dict()
        self.main_window = main_window
        self.obj_orientation = obj_orientation
        self.assignDelegates(idd_objects)

    def insertDelegate(self, index, delegate):
        delegate.setParent(self)
        self.delegates[index] = delegate

    def removeDelegate(self, index):
        if index in self.delegates:
            del self.delegates[index]

    def getRowOrCol(self, index):
        if self.obj_orientation == QtCore.Qt.Horizontal:
            return index.column()
        if self.obj_orientation == QtCore.Qt.Vertical:
            return index.row()

    def paint(self, painter, option, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            super(GenericDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return super(GenericDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            super(GenericDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            super(GenericDelegate, self).setModelData(editor, model, index)

    def assignDelegates(self, idd_obj):
        # Cycle through table and assign delegates as needed depending on tags

        # List of tags that would go in a combobox
        combo_fields = ['minimum', 'minimum>', 'maximum', 'maximum<', 'default',
                        'autosizeable', 'autocalculatable', 'key', 'object-list']

        # Cycle through field tags
        for i, field in enumerate(idd_obj):

            # Create a list of tags which would go in a combo box
            matches = set(combo_fields).intersection(set(field.tags))

            # If there are choices then use the choiceDelegate, otherwise check type
            if len(matches) > 0:
                self.insertDelegate(i, ChoiceDelegate(field, self.main_window))
            else:
                self.insertDelegate(i, AlphaNumericDelegate(self.main_window))


class AlphaNumericDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, main_window):
        super(AlphaNumericDelegate, self).__init__()
        self.main_window = main_window

    def createEditor(self, parent, option, index):
        line_edit = QtGui.QLineEdit(parent)
        line_edit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        line_edit.setValidator(CustomValidator(self))
        return line_edit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        if index.data() == editor.text():
            return
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.text())
        self.main_window.undo_stack.push(cmd)


class ChoiceDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, field, main_window):
        super(ChoiceDelegate, self).__init__()
        self.field = field
        self.model = None
        self.main_window = main_window
        self.comboFields = ['minimum>', 'minimum', 'maximum<', 'maximum', 'default',
                            'autosizeable', 'autocalculatable', 'key', 'object-list']

    def createEditor(self, parent, option, index):
        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setEditable(True)
        self.comboBox.setStyleSheet("QComboBox { border: 0px; }")
        self.comboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.comboBox.setValidator(CustomValidator(self))

        if not self.model:
            self.model = QtGui.QStandardItemModel()
            for tag, value in self.field.tags.iteritems():
                if tag in self.comboFields:
                    if tag == 'default':
                        self.model.insertRow(0, [QtGui.QStandardItem(value),
                                                 QtGui.QStandardItem(tag)])
                    elif tag == 'object-list':
                        # Get list of all classes that are part of the object-list
                        class_list = self.main_window.idd.object_lists[value]

                        # Cycle through all classes in the list
                        for cls in class_list:

                            # Get the objects for the current class
                            idf_objects = self.main_window.idf.get(cls)

                            # Cycle through all idf objects in the class
                            for obj in idf_objects:
                                self.model.appendRow([QtGui.QStandardItem(obj[0].value),
                                                      QtGui.QStandardItem(cls)])
                    elif tag == 'node':
                        # Retrieve a list of all nodes?
                        pass
                    elif tag == 'external-list':
                        # Retrieve list from external file
                        pass
                    else:
                        # Need to check if it's a list...is there a better way?
                        # Could make them all lists...would be annoying.
                        if isinstance(value, list):
                            for val in value:
                                self.model.appendRow([QtGui.QStandardItem(val),
                                                      QtGui.QStandardItem(tag)])
                        else:
                            self.model.appendRow([QtGui.QStandardItem(value),
                                                  QtGui.QStandardItem(tag)])

        myitem = self.model.findItems('current', column=1)
        if len(myitem) > 0:
            self.model.removeRow(myitem[0].row())

        value = index.data(QtCore.Qt.DisplayRole)
        current_item = QtGui.QStandardItem('current')
        value_item = QtGui.QStandardItem(value)
        self.model.insertRow(0, [value_item, current_item])

        # Table AND combo get same model (table first!)
        self.tableView = QtGui.QTableView(self.comboBox)
        self.tableView.setModel(self.model)
        self.comboBox.setModel(self.model)
        self.comboBox.setView(self.tableView)

        # Set properties of tableView
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.horizontalHeader().setVisible(False)
        self.tableView.setAutoScroll(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setMinimumWidth(self.tableView.horizontalHeader().length())
        self.tableView.setMinimumHeight(self.tableView.verticalHeader().length())

        return self.comboBox

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        comboIndex = editor.findText(value)
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        if index.data() == editor.currentText():
            return
        cmd = commands.ModifyObjectCmd(self.main_window,
                                       value=editor.currentText())
        self.main_window.undo_stack.push(cmd)


class CustomValidator(QtGui.QValidator):

    def validate(self, input_str, pos):

        # Blanks are ok
        if not input_str:
            return QtGui.QValidator.Intermediate

        # Reject invalid characters
        matches = set(input_str).intersection({';', ',', '#', '!'})
        if len(matches) > 0:
            return QtGui.QValidator.Invalid

        # Accept everything else
        return QtGui.QValidator.Acceptable
