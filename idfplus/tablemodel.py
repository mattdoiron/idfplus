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

# System imports
import shelve
import os
import transaction
from persistent.list import PersistentList

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .datamodel import IDFObject


class IDFObjectTableModel(QtCore.QAbstractTableModel):
    """Qt object that handles interaction between the table and the data
    displayed in the table.
    """

    def __init__(self, obj_class, idf):
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        # print('setting obj_class: {}'.format(obj_class))
        self.idf_objects = idf.get(obj_class, PersistentList())
        self.idd_object = idf._idd.get(obj_class, PersistentList())
        # print('loading idd object: {}'.format(self.idd_object))
        # print('idf type: {}'.format(type(idf)))
        # print('idf_objects type: {}'.format(type(self.idf_objects)))
        self.dirty = False
        self.getLabels()
        super(IDFObjectTableModel, self).__init__()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        current_flags = QtCore.QAbstractTableModel.flags(self, index)
        return QtCore.Qt.ItemFlags(current_flags | QtCore.Qt.ItemIsEditable)

    def data(self, index, role):
        """Provides various data to Table models. Tables iterate through
        columns and rows with different roles to get different types of data.
        """

        # Check for valid qt index
        if not index.isValid():
            return None

        # Get the row and column and prepare a blank data var to return
        row = index.row()
        column = index.column()
        data = None

        # Detect the role being request and return the correct data
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            try:
                data = self.idf_objects[row][column].value
            except IndexError:
                return None
        elif role == QtCore.Qt.ToolTipRole:
            data = "tooltip test"
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.StatusTipRole:
            pass
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.TextColorRole or role == QtCore.Qt.ForegroundRole:
            # return QtGui.QColor(QtCore.Qt.black)
            pass
        elif role == QtCore.Qt.BackgroundColorRole:
            #TODO Colour cells differently depending on things like if they are required
            # return QtGui.QColor(250, 250, 250)
            pass
        return data

    def headerData(self, section, orientation, role, old_orientation=None):
        if role == QtCore.Qt.TextAlignmentRole:
            if old_orientation is None:
                if orientation == QtCore.Qt.Vertical:
                    return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            else:
                if orientation == QtCore.Qt.Vertical:
                    return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.field_labels[section]
            if orientation == QtCore.Qt.Vertical:
                return self.objID_labels[section]
        return None

    def rowCount(self, index):
        return len(self.idf_objects)

    def columnCount(self, index):
        return len(self.idd_object)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            try:
                self.idf_objects[row][column].value = value
                self.dirty = True
                self.dataChanged.emit(index, index)
                transaction.get().note('Modify field')
                transaction.commit()
                return True
            except IndexError:
                return False
        return False

    def insertRows(self, position, rows=None, index=QtCore.QModelIndex()):
        if rows is None:
            rows = 1

        self.beginInsertRows(QtCore.QModelIndex(),
                             position,
                             position - 1 + rows)

        for row in range(rows):
            new_obj = IDFObject(self.idf, obj_class=self.obj_class)
            new_obj.set_defaults(self.idd)
            self.idf_objects.insert(position + row, new_obj)

        # Update state
        self.getLabels()
        transaction.get().note('Insert object')
        transaction.commit()
        self.endInsertRows()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def removeRows(self, position, rows=None, index=QtCore.QModelIndex()):
        if rows is None:
            rows = 1
        self.beginRemoveRows(QtCore.QModelIndex(),
                             position,
                             position - 1 + rows)
        start = position
        end = position + rows

        # self.idf_objects[start:end] = []
        del self.idf_objects[start:end]

        # Update state
        self.getLabels()
        if rows > 1:
            transaction.get().note('Remove multiple objects')
        else:
            transaction.get().note('Remove object')
        transaction.commit()
        self.endRemoveRows()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def moveRows(self, position, rows, index):

        self.beginMoveRows(QtCore.QModelIndex(),
                           position,
                           position - 1 + rows,
                           QtCore.QModelIndex(),
                           index)

        # move code goes here - note implemented yet
        to_move = self.idf_objects[position:position + rows]
        self.idf_objects.insert(index, to_move)

        if position >= index:
            del self.idf_objects[position + rows:position + rows + rows]
        else:
            del self.idf_objects[position:position + rows]

        # Update state
        self.getLabels()
        if rows > 1:
            transaction.get().note('Move multiple objects')
        else:
            transaction.get().note('Move object')
        transaction.commit()
        self.endMoveRows()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def insertColumns(self, position, cols=None, index=QtCore.QModelIndex()):
        if cols is None:
            cols = 1

        self.beginInsertColumns(QtCore.QModelIndex(),
                                position,
                                position - 1 + cols)

        for col in range(cols):
            new_obj = IDFObject(self.idf, obj_class=self.obj_class)
            new_obj.set_defaults(self.idd)
            self.idf_objects.insert(position + col, new_obj)

        # Update state
        self.getLabels()
        transaction.get().note('Insert object')
        transaction.commit()
        self.endInsertColumns()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def removeColumns(self, position, cols=None, index=QtCore.QModelIndex()):
        #TODO is this EXACTLY the same as removeRows? Merge them? Make a removeObjects?
        if cols is None:
            cols = 1

        self.beginRemoveColumns(QtCore.QModelIndex(),
                                position,
                                position - 1 + cols)
        start = position
        end = position + cols

        # self.idf_objects[start:end] = []
        del self.idf_objects[start:end]

        # Update state
        self.getLabels()
        if cols > 1:
            transaction.get().note('Remove multiple objects')
        else:
            transaction.get().note('Remove object')
        transaction.commit()
        self.endRemoveColumns()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def moveColumns(self, position, cols, index):

        self.beginMoveColumns(QtCore.QModelIndex(),
                              position,
                              position - 1 + cols,
                              QtCore.QModelIndex(),
                              index)

        # move code goes here - note implemented yet

        self.getLabels()
        if cols > 1:
            transaction.get().note('Move multiple objects')
        else:
            transaction.get().note('Move object')
        transaction.commit()
        self.endMoveColumns()
        self.dirty = True
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def getLabels(self):
        field_labels = []
        obj_count = len(self.idf_objects)
        objID_labels = ['Obj{}'.format(i) for i in range(1, obj_count + 1)]

        for field in self.idd_object:
            field_labels.append(field.tags.get('field'))

        self.objID_labels = objID_labels
        self.field_labels = field_labels


class TransposeProxyModel(QtGui.QAbstractProxyModel):
    """Translates columns to rows or vice versa"""

    # def __init__(self, parent=None):
    #     super(TransposeProxyModel, self).__init__(parent)
    #     # self.source_model = source_model
    #     # self.setSourceModel(source_model)

    def setSourceModel(self, source):
        super(TransposeProxyModel, self).setSourceModel(source)

        # Connect signals
        self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)
        # self.sourceModel().rowsInserted.connect(self._rowsInserted)
        # self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
        # self.sourceModel().dataChanged.connect(self.dataChanged)
        # self.sourceModel().sort.connect(self.sort)

    def mapFromSource(self, sourceIndex):
        if not sourceIndex.isValid():
            return QtCore.QModelIndex()
        return self.createIndex(sourceIndex.column(),
                                sourceIndex.row(),
                                QtCore.QModelIndex())

    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return QtCore.QModelIndex()
        return self.sourceModel().createIndex(proxyIndex.column(),
                                              proxyIndex.row(),
                                              QtCore.QModelIndex())

    def index(self, row, col, parent):
        return self.createIndex(row, col, QtCore.QModelIndex())

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent):
        return self.sourceModel().columnCount(QtCore.QModelIndex())

    def columnCount(self, parent):
        return self.sourceModel().rowCount(QtCore.QModelIndex())

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        return self.sourceModel().headerData(section, new_orientation, role, orientation)

    def insertRows(self, position, rows):
        print('proxy inserting rows')
        return self.sourceModel().insertRows(position, rows)

    def insertColumns(self, position, cols):
        print('proxy inserting cols')
        return self.sourceModel().insertColumns(position, cols)

    def removeRows(self, position, rows):
        print('proxy removing rows')
        return self.sourceModel().removeRows(position, rows)

    def removeColumns(self, position, cols):
        print('proxy removing cols')
        return self.sourceModel().removeColumns(position, cols)

class SortFilterProxyModel(QtGui.QSortFilterProxyModel):

    def setSourceModel(self, source):
        super(SortFilterProxyModel, self).setSourceModel(source)

        # connect signals
        # self.sourceModel().rowsAboutToBeInserted.connect(self.rowsAboutToBeInserted.emit)
        # self.sourceModel().rowsInserted.connect(self.rowsInserted.emit)
        # self.sourceModel().rowsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
        # self.sourceModel().rowsRemoved.connect(self.rowsRemoved.emit)
        # self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        # self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
        # self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        # self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)
        # self.sourceModel().rowsInserted.connect(self._rowsInserted)
        # self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
        # self.sourceModel().dataChanged.connect(self.dataChanged)