#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

from PySide import QtGui, QtCore


class GenericDelegateGroup(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(GenericDelegateGroup, self).__init__(parent)
        self.delegates = {}

    def insertColumnDelegate(self, column, delegate):
        delegate.setParent(self)
        self.delegates[column] = delegate

    def removeColumnDelegate(self, column):
        if column in self.delegates:
            del self.delegates[column]

    def paint(self, painter, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            QtGui.QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QtGui.QItemDelegate.createEditor(self, parent,
                                                    option, index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QtGui.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            QtGui.QItemDelegate.setModelData(self, editor, model, index)

    def assignDelegates(self, table, idd_obj):
        # cycle through table and assign delegates as needed
        # This will depend on the type of idd object!

        # All delegates are combo boxes!
        # examine the idd object and assemble combo box choices
        # the following fields need to have their values added:
        #       minimum, minimum>, maximum, maximum<, default, autosizable,
        #       autocalculatable,

        # Other fields to be passed to the delegate include:
        #       field, note, units, ip-units, required-field, key(s)

        # pass the type as well (integer, real, alpha)

        # examine the 'type' field in the idd object
        # if it's 'choice' add the choices
        # if it's 'object-list' assemble the list of objects

        fieldTags = ['\\field',
                     '\\note',
                     '\\required-field',
                     '\\begin-extensible',
                     '\\units',
                     '\\ip-units',
                     '\\unitsBasedOnField',
                     '\\minimum',
                     '\\minimum>',
                     '\\maximum',
                     '\\maximum<',
                     '\\default',
                     '\\deprecated',
                     '\\autosizeable',
                     '\\autocalculatable',
                     '\\type',
                     '\\retaincase',
                     '\\key',
                     '\\object-list',
                     '\\reference',
                     '\\memo',
                     '\\unique-object',
                     '\\required-object',
                     '\\min-fields',
                     '\\obsolete',
                     '\\extensible:',
                     '\\begin-extensible',
                     '\\format',
                     '\\group']

        comboFields = ['\\minimum',
                       '\\minimum>',
                       '\\maximum',
                       '\\maximum<',
                       '\\default',
                       '\\autosizeable',
                       '\\autocalculatable',
                       '\\key']

        for i, tags in enumerate(idd_obj['field_tags'][1:]):

            model = QtGui.QStandardItemModel()
            tag_list = []
            tag_count = 0

            for tag in tags:
                if tag['tag'] in comboFields:
                    value_item = QtGui.QStandardItem(tag['value'])
                    tag_item = QtGui.QStandardItem(tag['tag'].strip('\\'))
                    model.appendRow([value_item, tag_item])
                    tag_list.append(tag['tag'])
                    tag_count += 1

            if tag_count > 0:
                self.insertColumnDelegate(i, ChoiceColumnDelegate(model))
            else:
#                if '\\type' in tag_list:
#                    if type is integer use integer delegate...etc
                fieldName = idd_obj['fields'][i - 1]
                if fieldName.startswith('A'):
                    self.insertColumnDelegate(i, AlphaColumnDelegate())
                elif fieldName.startswith('N'):
                    self.insertColumnDelegate(i, RealColumnDelegate())

#        self.insertColumnDelegate(0, ChoiceColumnDelegate(model))
#        self.insertColumnDelegate(1, RealColumnDelegate())
#        self.insertColumnDelegate(2, AlphaColumnDelegate())
        table.setItemDelegate(self)


class IntegerColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, minimum=0, maximum=100, parent=None):
        super(IntegerColumnDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        spinbox = QtGui.QSpinBox(parent)
        spinbox.setRange(self.minimum, self.maximum)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        return spinbox

    def setEditorData(self, editor, index):
        value = int(index.data(QtCore.Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        model.setData(index, editor.value(), QtCore.Qt.EditRole)


class RealColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, minimum=0, maximum=100, default=0, decimals=10, parent=None):
        super(RealColumnDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals
        self.default = default

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        validator = QtGui.QDoubleValidator(self)
        validator.setRange(self.minimum, self.maximum, self.decimals)
        validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
        lineedit.setValidator(validator)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), QtCore.Qt.EditRole)


#class DateColumnDelegate(QtGui.QItemDelegate):
#
#    def __init__(self, minimum=QtCore.QDate(),
#                 maximum=QtCore.QDate.currentDate(),
#                 format="yyyy-MM-dd", parent=None):
#        super(DateColumnDelegate, self).__init__(parent)
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


#class TimeColumnDelegate(QTGui.QItemDelegate):
#
#  def getEditWidget(self):
#    e = QtGui.QLineEdit()
#    rx = QtCore.QRegExp('[0-9]{2}:[0-6]{2}')
#    e.setValidator(QtGui.QRegExpValidator(rx,e))
#    return e


class AlphaColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(AlphaColumnDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setFrame(False)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), QtCore.Qt.EditRole)


class ChoiceColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, model, parent=None):
        super(ChoiceColumnDelegate, self).__init__(parent)
        self.model = model

    def imActivated(self, index):
#        self.combo.showPopup()
        print 'i was activated'

    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        combo.setFrame(False)
        combo.setEditable(True)
#        self.combo = combo
        combo.editTextChanged.connect(self.imActivated)
#        combo.setMinimumContentsLength(30)
#        combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

#        current = index.data(QtCore.Qt.DisplayRole)
#        model = QtGui.QStandardItemModel(4, 2)
#
#        index = model.index(0, 0, QtCore.QModelIndex())
#        model.setData(index, current)
#        index = model.index(0, 1, QtCore.QModelIndex())
#        model.setData(index, 'Current')
#        index = model.index(1, 0, QtCore.QModelIndex())
#        model.setData(index, '123')
#        index = model.index(1, 1, QtCore.QModelIndex())
#        model.setData(index, 'Default')
#        index = model.index(2, 0, QtCore.QModelIndex())
#        model.setData(index, 'New')
#        index = model.index(2, 1, QtCore.QModelIndex())
#        model.setData(index, '')
#        index = model.index(3, 0, QtCore.QModelIndex())
#        model.setData(index, 'New From Library asd asd asd')
#        index = model.index(3, 1, QtCore.QModelIndex())
#        model.setData(index, '')

        myitem = self.model.findItems('current', column=1)
        if len(myitem) > 0:
            self.model.removeRow(myitem[0].row())

        value = index.data(QtCore.Qt.DisplayRole)
        current_item = QtGui.QStandardItem('current')
        value_item = QtGui.QStandardItem(value)
        self.model.insertRow(0, [value_item, current_item])

        tableView = QtGui.QTableView(parent)
        tableView.setModel(self.model)
        tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        tableView.setAutoScroll(False)
        tableView.resizeColumnsToContents()
        tableView.resizeRowsToContents()
#        tableView.setContentsMargins(0,0,0,0)
#        tableView.setSortingEnabled(True)
        tableView.verticalHeader().setVisible(False)
        tableView.horizontalHeader().setVisible(False)
        tableView.setMinimumWidth(tableView.horizontalHeader().length())
#        tableView.setFrameShape(QtGui.QFrame.NoFrame)

        combo.setModel(self.model)
        combo.setView(tableView)
#        combo.setContentsMargins(0,0,0,0)
#        combo.showPopup()
        return combo

    def setEditorData(self, editor, index):
#        editor.showPopup()
        value = index.data(QtCore.Qt.DisplayRole)
        comboIndex = editor.findText(value)
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), QtCore.Qt.EditRole)
