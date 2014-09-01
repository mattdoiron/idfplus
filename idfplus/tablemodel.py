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
from persistent.list import PersistentList

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .datamodel import IDFObject
from .datamodel import IDFField


class IDFObjectTableModel(QtCore.QAbstractTableModel):
    """Qt object that handles interaction between the table and the data
    displayed in the table.
    """

    def __init__(self, obj_class, idf):
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        self.idf_objects = idf.get(obj_class, PersistentList())
        self.idd_object = idf._idd.get(obj_class, PersistentList())
        # self.dirty = False
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
            except (AttributeError, IndexError):
                data = None
        elif role == QtCore.Qt.ToolTipRole:
            data = self.idd_object.tags.get('units', '')
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.StatusTipRole:
            data = self.idd_object.tags.get('units', '')
        elif role == QtCore.Qt.TextAlignmentRole:
            data = int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.TextColorRole or role == QtCore.Qt.ForegroundRole:
            pass
        elif role == QtCore.Qt.BackgroundColorRole:
            #TODO Colour cells differently depending on things like if they are required
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

            # Try to assign the value
            try:
                self.idf_objects[row][column].value = value
            except (AttributeError, IndexError):
                # An invalid index could mean that we're trying to assign a value
                # to a field that has not yet been 'allocated'. Check for max
                # allowable fields
                max_field_count = len(self.idd.get(self.obj_class, []))
                current_field_count = len(self.idf_objects[row])

                # If within limits allowed, allocate additional field 'slots'
                if index.column() < max_field_count:
                    extra_field_count = index.column() - current_field_count + 1
                    extra_fields = extra_field_count*[None]
                    self.idf_objects[row].extend(extra_fields)
                else:
                    return False

                # Create a new field object, give it a value and save it
                new_field = IDFField(self.idf_objects[row])
                new_field.value = value
                self.idf_objects[row][column] = new_field

            # Note: We do NOT commit the transaction here. This allows multiple fields
            # to be edited within a single transaction. The transaction is committed
            # by the function calling setData.
            return True
        return False

    def commitData(self, *args, **kwargs):
        print('item committed')
        super(IDFObjectTableModel, self).submit(*args, **kwargs)

    def sourceModel(self):
        """Ensures that the sourceModel method is always available as a method even
        when there is no proxy layer."""
        return self

    def removeObjects(self, index, count):

        # Set the position for the removal
        position = index.row()

        # Warn the model that we're about to remove rows
        self.beginRemoveRows(QtCore.QModelIndex(),
                             position,
                             position - 1 + count)

        # Delete the range
        del self.idf_objects[position:position + count]

        # Update state
        self.getLabels()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.endRemoveRows()
        return True

    def insertObjects(self, index, objects=None):

        # Set the position for the insertion
        if index.row() == -1:
            position = len(self.idf_objects)
        else:
            position = index.row() + 1

        # If there are no objects to add, make new blank ones
        if objects is None:
            new_obj = IDFObject(self.idf, obj_class=self.obj_class)
            new_obj.set_defaults(self.idd)
            obj_to_insert = [new_obj]
            count = 1
        else:
            obj_to_insert = objects
            count = len(objects)

        # Warn the model that we're about to add rows
        self.beginInsertRows(QtCore.QModelIndex(),
                             position,
                             position - 1 + count)

        # Insert the new object(s)
        self.idf_objects[position:position] = obj_to_insert

        # Update state
        self.getLabels()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.endInsertRows()
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

    def setSourceModel(self, source):
        super(TransposeProxyModel, self).setSourceModel(source)

        # Connect signals in a transposed way as well
        self.sourceModel().columnsAboutToBeInserted.connect(self.rowsAboutToBeInserted.emit)
        self.sourceModel().columnsInserted.connect(self.rowsInserted.emit)
        self.sourceModel().columnsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
        self.sourceModel().columnsRemoved.connect(self.rowsRemoved.emit)
        self.sourceModel().rowsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().rowsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().rowsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().rowsRemoved.connect(self.columnsRemoved.emit)

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

    def insertObjects(self, index, objects):
        return self.sourceModel().insertObjects(self.mapToSource(index), objects)

    def removeObjects(self, index, count):
        return self.sourceModel().removeObjects(self.mapToSource(index), count)

    def setData(self, index, value, role):
        return self.sourceModel().setData(self.mapToSource(index), value, role)


class SortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """Proxy layer to sort and filter"""

    def __init__(self, obj_orientation, *args, **kwargs):
        super(SortFilterProxyModel, self).__init__(*args, **kwargs)

        self.obj_orientation = obj_orientation
        syntax = QtCore.QRegExp.PatternSyntax(QtCore.QRegExp.Wildcard)
        caseSensitivity = QtCore.Qt.CaseInsensitive

        self.setFilterRegExp(QtCore.QRegExp('', caseSensitivity, syntax))
        self.setFilterCaseSensitivity(caseSensitivity)

    def filterAcceptsColumn(self, col, parent):

        if self.obj_orientation == QtCore.Qt.Horizontal:
            return True

        model = self.sourceModel()
        row_count = model.rowCount(col)
        regExp = self.filterRegExp()

        for row in range(row_count):
            data = model.index(row, col, parent).data()
            if regExp.indexIn(data) != -1:
                return True

        return False

    def filterAcceptsRow(self, row, parent):

        if self.obj_orientation == QtCore.Qt.Vertical:
            return True

        model = self.sourceModel()
        column_count = model.columnCount(row)
        regExp = self.filterRegExp()

        for col in range(column_count):
            data = model.index(row, col, parent).data()
            if regExp.indexIn(data) != -1:
                return True

        return False


class IDFClassTableModel(QtCore.QAbstractTableModel):
    """Qt object that handles interaction between the table and the data
    displayed in the table.
    """

    def __init__(self, idf):
        # self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        # self.idf_objects = idf.get(obj_class, PersistentList())
        # self.idd_object = idf._idd.get(obj_class, PersistentList())
        # self.dirty = False
        # self.getLabels()
        super(IDFClassTableModel, self).__init__()

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
            except (AttributeError, IndexError):
                data = None
        elif role == QtCore.Qt.ToolTipRole:
            data = self.idd_object.tags.get('units', '')
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.StatusTipRole:
            data = self.idd_object.tags.get('units', '')
        elif role == QtCore.Qt.TextAlignmentRole:
            data = int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.TextColorRole or role == QtCore.Qt.ForegroundRole:
            pass
        elif role == QtCore.Qt.BackgroundColorRole:
            #TODO Colour cells differently depending on things like if they are required
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


class TableView(QtGui.QTableView):
   '''Subclass of QTableView used to override mousePressEvent'''

   def __init__(self, *args, **kwargs):
       super(TableView, self).__init__(*args, **kwargs)

   # # Ads single-click editing
   # def mousePressEvent(self, event):
   #     if event.button() == QtCore.Qt.LeftButton:
   #         index = self.indexAt(event.pos())
   #         if index.isValid():
   #             self.edit(index)
   #     QtGui.QTableView.mousePressEvent(self, event)

   # def commitData(self, *args, **kwargs):
   #     print('data committed')
   #     #TODO put transaction commit in here?
   #     #TODO catch multiple paste and commit only once?
   #     super(TableView, self).commitData(*args, **kwargs)

    # def clear(self):
    #     self.model().beginResetModel()
    #     self.model().clear()
    #     self.model().endResetModel()