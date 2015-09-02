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

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import commands
from . import config
from .config import log


class GenericDelegate(QtGui.QStyledItemDelegate):
    """Template delegate for the table view.
    """

    def __init__(self, main_window, idd_objects, obj_orientation):
        super(GenericDelegate, self).__init__(main_window.classTable)
        self.delegates = dict()
        self.main_window = main_window
        self.obj_orientation = obj_orientation
        self.assignDelegates(idd_objects)

    def insertDelegate(self, index, delegate):
        """

        :param index:
        :param delegate:
        """

        delegate.setParent(self)
        self.delegates[index] = delegate

    def removeDelegate(self, index):
        """

        :param index:
        """

        if index in self.delegates:
            del self.delegates[index]

    def getRowOrCol(self, index):
        """

        :param index:
        :return: :rtype:
        """

        if self.obj_orientation == QtCore.Qt.Horizontal:
            return index.column()
        if self.obj_orientation == QtCore.Qt.Vertical:
            return index.row()

    def paint(self, painter, option, index):
        """

        :param painter:
        :param option:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            super(GenericDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """

        :param parent:
        :param option:
        :param index:
        :return: :rtype:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return super(GenericDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            super(GenericDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """

        :param editor:
        :param model:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            super(GenericDelegate, self).setModelData(editor, model, index)

    def assignDelegates(self, idd_obj):
        """Cycle through table and assign delegates as needed depending on tags

        :param idd_obj:
        """

        # List of tags that would go in a combobox
        combo_fields = ['minimum', 'minimum>', 'maximum', 'maximum<', 'default',
                        'key', 'object-list']

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
    """

    :param main_window:
    :type main_window:
    """

    def __init__(self, main_window):
        super(AlphaNumericDelegate, self).__init__()
        self.main_window = main_window

    def createEditor(self, parent, option, index):
        """

        :param parent:
        :param option:
        :param index:
        :return: :rtype:
        """

        line_edit = QtGui.QLineEdit(parent)
        line_edit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        line_edit.setValidator(CustomValidator(self))
        line_edit.setFont(QtGui.QFont(self.main_window.prefs['class_table_font'],
                                      self.main_window.prefs['class_table_font_size']))
        return line_edit

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        """Create undo command and push it to the undo stack

        :param editor:
        :param model:
        :param index:
        :return: :rtype:
        """

        if index.data() == editor.text():
            return
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.text())
        self.main_window.undo_stack.push(cmd)


class ChoiceDelegate(QtGui.QStyledItemDelegate):
    """

    :param field:
    :type field:
    :param main_window:
    :type main_window:
    """

    def __init__(self, field, main_window):
        super(ChoiceDelegate, self).__init__()
        self.field = field
        self.model = None
        self.main_window = main_window
        self.combo_fields = ['minimum>', 'minimum', 'maximum<', 'maximum', 'default',
                             'key', 'object-list']

    def createEditor(self, parent, option, index):
        """Creates a custom editor based on an extended QCombobox

        :param parent:
        :param option:
        :param index:
        """

        # If there isn't already a model, populate it
        if not self.model:
            self.model = QtGui.QStandardItemModel()
            for tag, value in self.field.tags.iteritems():
                if tag in self.combo_fields:
                    if tag == 'default':
                        self.model.insertRow(0, [QtGui.QStandardItem(value),
                                                 QtGui.QStandardItem(tag)])
                    elif tag == 'object-list':
                        # Get list of all classes that are part of the object-list
                        class_list = []
                        if isinstance(value, set):
                            for val in value:
                                class_list.extend(self.main_window.idd.object_lists[val])
                        else:
                            class_list.extend(self.main_window.idd.object_lists[value])

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

        if self.model.rowCount() > 0:
            # Check for and remove the 'current' item so it can be replace (at the top)
            myitem = self.model.findItems('current', column=1)
            if len(myitem) > 0:
                self.model.removeRow(myitem[0].row())

            # Make a special item for the 'current' item
            value = index.data(QtCore.Qt.DisplayRole)
            current_item = QtGui.QStandardItem('current')
            value_item = QtGui.QStandardItem(value)
            self.model.insertRow(0, [value_item, current_item])

        # Table AND combo get same model (table first!)
        if 'object-list' in self.field.tags.keys():
            auto_complete = True
        else:
            auto_complete = False
        font = QtGui.QFont(self.main_window.prefs['class_table_font'],
                           self.main_window.prefs['class_table_font_size'])
        self.comboBox = ExtendedComboBox(parent, auto_complete)
        self.tableView = QtGui.QTableView(self.comboBox)
        self.tableView.setModel(self.model)
        self.comboBox.setModel(self.model)
        self.comboBox.setView(self.tableView)
        self.comboBox.setFont(font)
        self.comboBox.lineEdit().selectAll()  # TODO should depend on trigger!
        self.comboBox.lineEdit().setFont(font)

        # Set properties of tableView and the combobox
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.horizontalHeader().setVisible(False)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setFont(font)
        header_width = self.tableView.horizontalHeader().length()
        col_width = self.tableView.columnWidth(0)
        scroll_width = self.tableView.verticalScrollBar().width()
        self.tableView.setMinimumWidth(header_width + scroll_width)
        self.comboBox.set_popup_width(col_width + scroll_width)

        return self.comboBox

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        value = index.data(QtCore.Qt.DisplayRole)
        combo_index = editor.findText(value)
        if combo_index >= 0:
            editor.setCurrentIndex(combo_index)

    def setModelData(self, editor, model, index):
        """Create undo command and push it to the undo stack

        :param editor:
        :param model:
        :param index:
        :return: :rtype:
        """

        if index.data() == editor.currentText():
            return
        cmd = commands.ModifyObjectCmd(self.main_window,
                                       value=editor.currentText())
        self.main_window.undo_stack.push(cmd)


class CustomValidator(QtGui.QValidator):
    """Customized validator for preventing certain inputs
    """

    def validate(self, input_str, pos):
        """

        :param input_str:
        :param pos:
        :return: :rtype:
        """

        # Blanks are ok
        if not input_str:
            return QtGui.QValidator.Intermediate

        # Reject invalid characters
        matches = set(input_str).intersection({';', ',', '#', '!'})
        if len(matches) > 0:
            return QtGui.QValidator.Invalid

        # Accept everything else
        return QtGui.QValidator.Acceptable


class ExtendedComboBox(QtGui.QComboBox):
    """Customized QComboBox which adds a filtered, popup auto-completer
    """

    def __init__(self, parent, auto_complete):
        super(ExtendedComboBox, self).__init__(parent)

        # Set some properties
        # self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.setStyleSheet("QComboBox { border: 0px; }")
        self.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.setValidator(CustomValidator(self))
        self.setMaxVisibleItems(15)
        self.auto_complete = auto_complete

        if auto_complete is True:
            # Add a filter model to filter matching items
            self.filter_model = QtGui.QSortFilterProxyModel(self)
            self.filter_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.filter_model.setSourceModel(self.model())

            # Create and add a completer, which uses the filter model. Always show
            # all (filtered) completions
            self.completer = QtGui.QCompleter(self)
            self.completer.setModel(self.filter_model)
            self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
            self.completer.setMaxVisibleItems(15)
            self.setCompleter(self.completer)

            # Connect signals
            self.lineEdit().textEdited[str].connect(self.filter_model.setFilterFixedString)
            # self.completer.activated.connect(self.on_completer_activated)
        else:
            self.setCompleter(None)

    def set_popup_width(self, width):
        """

        :param width:
        """

        if self.auto_complete:
            self.completer.popup().setMinimumWidth(width)

    # def on_completer_activated(self, text):
    #     """On selection of an item from the completer, select the corresponding
    #     item from combobox"""
    #     if text:
    #         index = self.findText(text)
    #         self.setCurrentIndex(index)
    #         self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        """On model change, update the models of the filter and completer as well

        :param model:
        """

        super(ExtendedComboBox, self).setModel(model)
        if self.auto_complete:
            self.filter_model.setSourceModel(model)
            self.completer.setModel(self.filter_model)

    def setModelColumn(self, column):
        """On model column change, update the model column of the filter and completer

        :param column:
        """

        if self.auto_complete:
            self.completer.setCompletionColumn(column)
            self.filter_model.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)
