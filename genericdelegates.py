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

#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
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

    def assignDelegates(self, table):
        # cycle through table and assign delegates as needed
        self.insertColumnDelegate(0, ChoiceColumnDelegate())
        self.insertColumnDelegate(1, RealColumnDelegate())
        self.insertColumnDelegate(2, AlphaColumnDelegate())
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


class AlphaColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(AlphaColumnDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
#        lineedit.setFrame(False)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), QtCore.Qt.EditRole)


class ChoiceColumnDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(ChoiceColumnDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        combo.setMinimumContentsLength(30)
        combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        current = index.data(QtCore.Qt.DisplayRole)

        myModel = QtGui.QStandardItemModel(4, 2)

        index = myModel.index(0, 0, QtCore.QModelIndex())
        myModel.setData(index, current)
        index = myModel.index(0, 1, QtCore.QModelIndex())
        myModel.setData(index, 'Current')
        index = myModel.index(1, 0, QtCore.QModelIndex())
        myModel.setData(index, '123')
        index = myModel.index(1, 1, QtCore.QModelIndex())
        myModel.setData(index, 'Default')
        index = myModel.index(2, 0, QtCore.QModelIndex())
        myModel.setData(index, 'New')
        index = myModel.index(2, 1, QtCore.QModelIndex())
        myModel.setData(index, '')
        index = myModel.index(3, 0, QtCore.QModelIndex())
        myModel.setData(index, 'New From Library')
        index = myModel.index(3, 1, QtCore.QModelIndex())
        myModel.setData(index, '')

        myTable = QtGui.QTableView()
        myTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        myTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        myTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        myTable.setAutoScroll(False)
        myTable.resizeColumnsToContents()
        myTable.resizeRowsToContents()
        #view.setSortingEnabled(True)
        myTable.verticalHeader().setVisible(False)
        myTable.horizontalHeader().setVisible(False)
        myTable.setMinimumWidth(30)

        combo.setModel(myModel)
        combo.setView(myTable)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        comboIndex = editor.findText(value)
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), QtCore.Qt.EditRole)
