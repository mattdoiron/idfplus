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
from operator import itemgetter
from itertools import groupby

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

    def __init__(self, obj_class, idf, parent):
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        self.idf_objects = idf.get(obj_class, PersistentList())
        self.idd_object = idf._idd.get(obj_class, PersistentList())
        # self.dirty = False
        self.get_labels()
        super(IDFObjectTableModel, self).__init__(parent)

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
        elif role == QtCore.Qt.BackgroundRole:
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
                try:
                    return self.objID_labels[section]
                except IndexError:
                    print(section)
                    return '123'
        elif role == QtCore.Qt.BackgroundRole:
            return QtGui.QColor(244, 244, 244)
        return None

    def rowCount(self, parent=None):
        return len(self.idf_objects)

    def columnCount(self, parent=None):
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

            return True
        return False

    def mapToSource(self, indexes):
        """Dummy to ensure there is always a mapToSource method even when there is no
        proxy layer."""
        return indexes

    def mapFromSource(self, indexes):
        """Dummy to ensure there is always a mapFromSource method even when there is no
        proxy layer."""
        return indexes

    def sourceModel(self):
        """Dummy to ensure there is always a sourceModel method even when there is no
         proxy layer."""
        return self

    def removeObjects(self, indexes, offset=None):

        # Detect groups and and offset and ensure there is a value for offset
        if offset:
            groups = indexes
        else:
            offset = 0
            groups = self.get_contiguous_rows(indexes, True)

        # Delete index ranges in all sub-groups
        for group in groups:
            delete_count = len(group)
            if not group:
                last_row = None
                first_row = len(self.idf_objects) - 1
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, first_row)
            elif not offset:
                first_row = group[0]
                last_row = group[0] + delete_count
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, last_row)
            else:
                first_row = group[-1] + offset
                last_row = group[-1] + offset + delete_count
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, last_row - 1)
            del self.idf_objects[first_row:last_row]
            self.get_labels()
            self.endRemoveRows()
        return True

    def insertObjects(self, indexes, objects=None, offset=None):

        # If there are no objects to add, make new blank ones
        if not objects:
            new_obj = IDFObject(self.idf, obj_class=self.obj_class)
            new_obj.set_defaults(self.idd)
            objs_to_insert = [[new_obj]]
        else:
            objs_to_insert = objects

        # Ensure there is a row_offset
        if offset:
            row_offset = offset
        else:
            row_offset = 0

        # Cycle through each index in the object dictionary
        for ind, obj_list in enumerate(objs_to_insert):
            count = len(obj_list)
            if indexes and offset:
                first_row = indexes[ind][-1] + row_offset
            elif indexes:
                first_row = indexes[ind][-1] + 1
            else:
                first_row = len(self.idf_objects)
            insert_count = first_row - 1 + count

            # Warn the model that we're about to add rows, then do it
            self.beginInsertRows(QtCore.QModelIndex(), first_row, insert_count)
            self.idf_objects[first_row:first_row] = obj_list
            self.get_labels()
            self.endInsertRows()
        return True

    def get_contiguous_rows(self, indexes, reverse):

        # Make a unique set of rows to be deleted
        row_set = set(index.row() for index in indexes)

        # Create groups of contiguous row indexes in reverse order
        groups = []
        for key, g in groupby(enumerate(row_set), lambda (i, x): i-x):
            groups.append(map(itemgetter(1), g))
        groups.sort(reverse=reverse)
        return groups

    def get_contiguous(self, indexes, reverse):

        # Get contiguous, groups of unique indexes
        groups = self.get_contiguous_rows(indexes, reverse)

        # Cycle through each group of row indexes
        sub_list = []
        obj_list = []
        for group in groups:
            # Cycle through each index in the group
            for ind in group:
                sub_list.append(self.idf_objects[ind])
            obj_list.append(sub_list)
            sub_list = []
        return groups, obj_list

    def get_labels(self):
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
        self.sourceModel().dataChanged.connect(self.data_changed)
        self.sourceModel().headerDataChanged.connect(self.header_data_changed)

    def mapFromSource(self, sourceIndex):
        if not sourceIndex.isValid():
            return QtCore.QModelIndex()
        return self.index(sourceIndex.column(), sourceIndex.row())

    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return QtCore.QModelIndex()
        return self.sourceModel().index(proxyIndex.column(), proxyIndex.row())

    def mapSelectionToSource(self, selection):
        returnSelection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapToSource(sel.topLeft())
            bottom_right = self.mapToSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            returnSelection.append(sel_range)
        return returnSelection

    # def mapSelectionFromSource(self, selection):
    #     returnSelection = QtGui.QItemSelection()
    #     for sel in selection:
    #         top_left = self.mapFromSource(sel.topLeft())
    #         bottom_right = self.mapFromSource(sel.bottomRight())
    #         sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
    #         returnSelection.append(sel_range)
    #     return returnSelection

    def index(self, row, col, parent=None):
        return self.createIndex(row, col)

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent=None):
        return self.sourceModel().columnCount(parent)

    def columnCount(self, parent=None):
        return self.sourceModel().rowCount(parent)

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        return self.sourceModel().headerData(section, new_orientation, role, orientation)

    def removeObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def get_contiguous(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().get_contiguous(*args, **kwargs)

    def setData(self, index, value, role):
        return self.sourceModel().setData(self.mapToSource(index), value, role)

    def data_changed(self, top_left, bottom_right):
        self.dataChanged.emit(self.mapFromSource(top_left),
                              self.mapFromSource(bottom_right))

    def header_data_changed(self, orientation, first, last):
        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        self.headerDataChanged.emit(new_orientation, first, last)


class SortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """Proxy layer to sort and filter"""

    def __init__(self, obj_orientation, parent_view, parent):
        super(SortFilterProxyModel, self).__init__(parent)

        self.obj_orientation = obj_orientation
        self.parent_view = parent_view
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

    def removeObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def get_contiguous(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().get_contiguous(*args, **kwargs)

# class TableView(QtGui.QTableView):
#     '''Subclass of QTableView used to override mousePressEvent'''
#
#     def __init__(self, *args, **kwargs):
#         super(TableView, self).__init__(*args, **kwargs)
#
#     def visualIndex(self, index):
#         super(TableView, self).visualIndex(index)
#
#    # # Ads single-click editing
#    # def mousePressEvent(self, event):
#    #     if event.button() == QtCore.Qt.LeftButton:
#    #         index = self.indexAt(event.pos())
#    #         if index.isValid():
#    #             self.edit(index)
#    #     QtGui.QTableView.mousePressEvent(self, event)
#
#    # def commitData(self, *args, **kwargs):
#    #     print('data committed')
#    #     super(TableView, self).commitData(*args, **kwargs)
#
#     # def clear(self):
#     #     self.model().beginResetModel()
#     #     self.model().clear()
#     #     self.model().endResetModel()