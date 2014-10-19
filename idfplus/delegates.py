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

    def __init__(self, main_window, obj_class, idd, obj_orientation, *args, **kwargs):
        super(GenericDelegate, self).__init__(main_window.classTable, *args, **kwargs)
        self.obj_class = obj_class
        self.idd = idd
        self.delegates = {}
        self.main_window = main_window
        # self.parent = main_window.classTable
        self.obj_orientation = obj_orientation
        self.assignDelegates(idd[obj_class])

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
            QtGui.QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QtGui.QItemDelegate.createEditor(self, parent,
                                                    option, index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QtGui.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.setModelData(editor, model, index)
        else:
            QtGui.QItemDelegate.setModelData(self, editor, model, index)

    def assignDelegates(self, idd_obj):
        # Cycle through table and assign delegates as needed
        # This will depend on the type of idd object!

        # List of tags that would go in a combobox
        combo_fields = ['minimum', 'minimum>',
                       'maximum', 'maximum<',
                       'default',
                       'autosizeable', 'autocalculatable',
                       'key', 'object-list']

        # Cycle through field tags
        for i, field in enumerate(idd_obj):

            tag_list = []
            tag_count = 0
            field_type = ''

            # Create a list of tags which would go in a combo box
            matches = set(combo_fields).intersection(set(field.tags))

            for key in matches:
                tag_list.append(key)
                tag_count += 1
                if key == 'type':
                    field_type = field.tags[key]

            min = float(field.tags.get('minimum', 0))
            max = float(field.tags.get('maximum', 100))
            min_inc = float(field.tags.get('minimum>', min))
            max_inc = float(field.tags.get('maximum<', max))

            # If there are choices then use the choiceDelegate, otherwise check type
            if tag_count > 0:
                self.insertDelegate(i, ChoiceDelegate(field, self.main_window,
                                                      min_inc, max_inc))
            else:
                if field_type == 'integer':
                    self.insertDelegate(i, IntegerDelegate(field, self.main_window,
                                                           min_inc, max_inc))
                elif field_type == 'real':
                    self.insertDelegate(i, RealDelegate(field, self.main_window,
                                                        min_inc, max_inc))
                elif field_type == 'alpha':
                    self.insertDelegate(i, AlphaDelegate(field, self.main_window))
                elif field.key.startswith('A'):
                    self.insertDelegate(i, AlphaDelegate(field, self.main_window))
                elif field.key.startswith('N'):
                    self.insertDelegate(i, RealDelegate(field, self.main_window,
                                                        min_inc, max_inc))
                else:
                    self.insertDelegate(i, AlphaDelegate(field, self.main_window))


class IntegerDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, field, main_window, minimum, maximum, *args, **kwargs):
        super(IntegerDelegate, self).__init__(main_window.classTable, *args, **kwargs)
        self.main_window = main_window
        self.minimum = int(minimum)
        self.maximum = int(maximum)
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        spinbox = QtGui.QSpinBox(parent)
        spinbox.setRange(self.minimum, self.maximum)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        spinbox.setStyleSheet("QSpinBox { qproperty-frame: false; }")
        print('creating integer delegate')
        return spinbox

    def setEditorData(self, editor, index):
        value = int(index.data(QtCore.Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        editor.interpretText()
        if index.data() == editor.value():
            return
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.value())
        self.main_window.undo_stack.push(cmd)


class RealDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, field, main_window, minimum, maximum, *args, **kwargs):
        super(RealDelegate, self).__init__(main_window.classTable, *args, **kwargs)
        self.main_window = main_window
        self.minimum = minimum
        self.maximum = maximum
        # self.decimals = decimals
        # self.default = default
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        # validator = QtGui.QDoubleValidator(self)
        # validator.setRange(self.minimum, self.maximum, 10)
        # validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
        # lineedit.setValidator(validator)
        print('creating real delegate')
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        if index.data() == editor.text():
            return
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.text())
        self.main_window.undo_stack.push(cmd)


class AlphaDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, field, main_window, *args, **kwargs):
        super(AlphaDelegate, self).__init__(main_window.classTable, *args, **kwargs)
        self.main_window = main_window

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setFrame(False)
        lineedit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        print('creating alpha delegate')
        return lineedit

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

    def __init__(self, field, main_window, minimum, maximum, *args, **kwargs):
        super(ChoiceDelegate, self).__init__(main_window.classTable, *args, **kwargs)
        self.field = field
        self.model = None
        self.main_window = main_window
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.comboFields = ['minimum>',
                            'minimum',
                            'maximum<',
                            'maximum',
                            'default',
                            'autosizeable',
                            'autocalculatable',
                            'key',
                            'object-list']

    def createEditor(self, parent, option, index):
        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setEditable(True)
        self.comboBox.setStyleSheet("QComboBox { border: 0px; }")
        # self.comboBox.setFrame(False)
        self.comboBox.setContentsMargins(0, 0, 0, 0)
        # self.comboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.comboBox.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLengthWithIcon)

        print('creating choice delegate')

        # Detect field type
        field_type = self.field.tags.get('type')
        if not field_type:
            if self.field.key.startswith('N'):
                field_type = 'real'
            else:
                field_type = 'alpha'
        # print('field type: {}'.format(field_type))

        # Set an appropriate validator
        validator = None
        if field_type == 'real':
            # validator = QtGui.QDoubleValidator(self.minimum, self.maximum, 10, self)
            validator = CustomValidator(self.minimum, self.maximum, self)
            # validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
            # print('min: {}, max: {}'.format(self.minimum, self.maximum))
            # print('validator set to real')
        elif field_type == 'integer':
            validator = QtGui.QIntValidator(int(self.minimum), int(self.maximum), self)
            print('validator set to integer')
        if validator:
            self.comboBox.setValidator(validator)

        # self.comboBox.setValidator(CustomValidator(self))

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
        # self.tableView.setFrameStyle(QtGui.QFrame.NoFrame)
        # self.tableView.setFrameShape(QtGui.QFrame.NoFrame)
        # self.tableView.setLineWidth(0)
        # self.tableView.setContentsMargins(0, 0, 0, 0)
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

    # def updateEditorGeometry(self, editor, option, index):
    #     editor.setGeometry(option.rect)

    # def paint(self, painter, option, index):
    #     my_option = QtGui.QStyleOptionViewItemV4(option)
    #     # text = Items[index.row()].c_str()
    #     value = index.data(QtCore.Qt.DisplayRole)
    #
    #     my_option.text = value
    #     app = QtGui.QApplication.instance()
    #     app.style().drawControl(QtGui.QStyle.CE_ItemViewItem, my_option, painter)

#class DateDelegate(QtGui.QItemDelegate):
#
#    def __init__(self, minimum=QtCore.QDate(),
#                 maximum=QtCore.QDate.currentDate(),
#                 format="yyyy-MM-dd", parent=None):
#        super(DateDelegate, self).__init__(parent)
#        self.minimum = minimum
#        self.maximum = maximum
#        self.format = format
#
#    def createEditor(self, parent, option, index):
#        dateedit = QtGui.QDateEdit(parent)
#        dateedit.setDateRange(self.minimum, self.maximum)
#        dateedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#        dateedit.setDisplayFormat(self.format)
#        dateedit.setCalendarPopup(True)
#        return dateedit
#
#    def setEditorData(self, editor, index):
#        value = index.model().data(index, QtCore.Qt.DisplayRole).toDate()
#        editor.setDate(value)
#
#    def setModelData(self, editor, model, index):
#        model.setData(index, editor.date(), QtCore.Qt.EditRole)


#class TimeDelegate(QTGui.QItemDelegate):
#
#  def getEditWidget(self):
#    e = QtGui.QLineEdit()
#    rx = QtCore.QRegExp('[0-9]{2}:[0-6]{2}')
#    e.setValidator(QtGui.QRegExpValidator(rx,e))
#    return e


class CustomValidator(QtGui.QValidator):
    def __init__(self, minimum, maximum, *args, **kwargs):
        super(CustomValidator, self).__init__(*args, **kwargs)
        self.minimum = minimum
        self.maximum = maximum

    def validate(self, input_str, pos):

        # Blanks are sort of ok...
        if not input_str:
            return QtGui.QValidator.Intermediate

        # Reject invalid characters
        for pattern in [';', ',', '#']:
            if input_str.find(pattern) != -1:
                return QtGui.QValidator.Invalid

        return QtGui.QValidator.Acceptable

        # # Detect actual valid status
        # input_float = float(input_str)
        # if self.minimum <= input_float <= self.maximum:
        #     return QtGui.QValidator.Acceptable
        # else:
        #     # Check for scientific notation
        #     for pattern in ['e', 'E']:
        #         if input_str.find(pattern) != -1:
        #             return QtGui.QValidator.Intermediate
        #
        #     return QtGui.QValidator.Invalid
