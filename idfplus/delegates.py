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
import transaction
from . import commands
from . import idfsettings as c
from . import logger

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class GenericDelegate(QtGui.QItemDelegate):
    """Template delegate for the table view."""

    def __init__(self, main_window, obj_class, idd, obj_orientation):
        super(GenericDelegate, self).__init__(main_window.classTable)
        self.obj_class = obj_class
        self.idd = idd
        self.delegates = {}
        self.main_window = main_window
        self.parent = main_window.classTable
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

    # def sizeHint(self, option, index):
    #     fm = option.fontMetrics()
    #     delegate = self.delegates.get(self.getRowOrCol(index))
    #     if delegate is not None:
    #         return QtCore.QSize(c.DEFAULT_COLUMN_WIDTH, fm.height() + 2)
    #         # return delegate.sizeHint(option, index)
    #     else:
    #         return QtGui.QItemDelegate.sizeHint(self, option, index)

    def assignDelegates(self, idd_obj):
        # Cycle through table and assign delegates as needed
        # This will depend on the type of idd object!

        # Other fields to be passed to the delegate include:
        #       field, note, units, ip-units, required-field, key(s)

        #TODO all delegates should be choice delegates if they have comboFields
        #tags in them!

        # List of tags that would go in a combobox
        comboFields = ['minimum',
                       'minimum>',
                       'maximum',
                       'maximum<',
                       'default',
                       'autosizeable',
                       'autocalculatable',
                       'key']

        # Cycle through field tags
        for i, field in enumerate(idd_obj):

            tag_list = []
            tag_count = 0
            field_type = ''

            # Create a list of tags which would go in a combo box
            matches = set(comboFields).intersection(set(field.tags))

            for key in matches:
                tag_list.append(key)
                tag_count += 1
                if key == 'type':
                    field_type = field.tags[key]

            # If there are choices then use the choiceDelegate
            if tag_count > 0:
                self.insertDelegate(i, ChoiceDelegate(field, self.main_window))
            else:
                # Otherwise check the type field
                min = field.tags.get('minimum', 0)
                max = field.tags.get('maximum', 100)
                min_inc = field.tags.get('minimum>', min)
                max_inc = field.tags.get('maximum<', max)
                if field_type == 'integer':
                    self.insertDelegate(i, IntegerDelegate(field, self.main_window,
                                                           min_inc, max_inc))
                elif field_type == 'real':
                    self.insertDelegate(i, RealDelegate(field, self.main_window,
                                                        min_inc, max_inc))
                elif field_type == 'alpha':
                    self.insertDelegate(i, AlphaDelegate(field, self.main_window))
                else:
                    # The type field is not always present so check fieldname
                    idd_field = idd_obj[i - 1]
                    if idd_field.key.startswith('A'):
                        self.insertDelegate(i, AlphaDelegate(field, self.main_window))
                    elif idd_field.key.startswith('N'):
                        self.insertDelegate(i, RealDelegate(field, self.main_window,
                                                            min_inc, max_inc))
                    else:
                        self.insertDelegate(i, AlphaDelegate(field, self.main_window))


class IntegerDelegate(QtGui.QItemDelegate):

    def __init__(self, field, main_window, minimum=0, maximum=100):
        super(IntegerDelegate, self).__init__()
        self.main_window = main_window
        self.minimum = minimum
        self.maximum = maximum
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        spinbox = QtGui.QSpinBox(parent)
        spinbox.setRange(self.minimum, self.maximum)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        spinbox.setStyleSheet("QSpinBox { qproperty-frame: false; }")
        return spinbox

    def setEditorData(self, editor, index):
        value = int(index.data(QtCore.Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        editor.interpretText()
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.value())
        self.main_window.undo_stack.push(cmd)


class RealDelegate(QtGui.QItemDelegate):

    def __init__(self, field, main_window, minimum=0, maximum=100, default=0, decimals=10):
        super(RealDelegate, self).__init__()
        self.main_window = main_window
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals
        self.default = default
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        validator = QtGui.QDoubleValidator(self)
        validator.setRange(self.minimum, self.maximum, self.decimals)
        validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
        lineedit.setValidator(validator)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.text())
        self.main_window.undo_stack.push(cmd)


class AlphaDelegate(QtGui.QItemDelegate):

    def __init__(self, field, main_window):
        super(AlphaDelegate, self).__init__()
        self.main_window = main_window

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setFrame(False)
        lineedit.setStyleSheet("QLineEdit { qproperty-frame: false; }")
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        cmd = commands.ModifyObjectCmd(self.main_window, value=editor.text())
        self.main_window.undo_stack.push(cmd)

    # def sizeHint(self, option, index):
    #     fm = option.fontMetrics
    #     # log.debug('size hint called')
    #     # print('size hint called')
    #     delegate = self.delegates.get(self.getRowOrCol(index))
    #     if delegate is not None:
    #         # return QtCore.QSize(fm.width("9,999,999,999"), fm.height())
    #         return delegate.sizeHint(self, option, index)
    #     else:
    #         return QtGui.QItemDelegate.sizeHint(self, option, index)

class ChoiceDelegate(QtGui.QItemDelegate):

    def __init__(self, field, main_window):
        super(ChoiceDelegate, self).__init__()
        self.field = field
        self.model = QtGui.QStandardItemModel()
        self.main_window = main_window
        self.comboFields = ['minimum>',
                            'minimum',
                            'maximum<',
                            'maximum',
                            'default',
                            'autosizeable',
                            'autocalculatable',
                            'key']

    # def imActivated(self, index):
#        self.combo.showPopup()
#        print 'i was activated'
#         pass

    def createEditor(self, parent, option, index):
        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setEditable(True)
        # self.comboBox.editTextChanged.connect(self.imActivated)
        self.comboBox.setStyleSheet("QComboBox { border: 0px; }")
        self.comboBox.setFrame(False)

        for tag, value in self.field.tags.iteritems():
            if tag in self.comboFields:
                if tag == 'default':
                    self.model.insertRow(0, [QtGui.QStandardItem(value),
                                             QtGui.QStandardItem(tag)])
                elif tag == 'object-list':
                    #Retrieve object list and use it to populate the dropdown
                    pass
                else:
                    # Need to check if it's a list...is there a better way?
                    # Could make them all lists...would be annoying.
                    if type(value) is list:
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

        self.tableView = QtGui.QTableView(self.comboBox)
        self.tableView.setModel(self.model)
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.horizontalHeader().setVisible(False)
        self.tableView.setAutoScroll(False)

        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setMinimumWidth(self.tableView.horizontalHeader().length())
        self.tableView.setFrameShape(QtGui.QFrame.NoFrame)

        # Table AND combo get same model (table first!)
        self.comboBox.setModel(self.model)
        self.comboBox.setView(self.tableView)

        return self.comboBox

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        comboIndex = editor.findText(value)
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

    def setModelData(self, editor, model, index):
        # Create undo command and push it to the undo stack
        cmd = commands.ModifyObjectCmd(self.main_window,
                                       model=model,
                                       index=index,
                                       value=editor.currentText())
        self.main_window.undo_stack.push(cmd)


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
