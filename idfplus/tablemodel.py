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

# System imports
from operator import itemgetter
from itertools import groupby
from copy import deepcopy

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .datamodel import IDFObject
from .datamodel import IDFError
from . import config


class IDFObjectTableModel(QtCore.QAbstractTableModel):
    """Qt table model object that links the table widget and its underlying data structure.
    """

    def __init__(self, obj_class, idf, parent):
        """

        :param obj_class: Class of objects the table model will display.
        :type obj_class: str
        """
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        self.idf_objects = idf.idf_objects(obj_class)
        self.idd_object = idf._idd.idd_object(obj_class)
        self.config = config.Settings()
        self._refresh_labels()

        super(IDFObjectTableModel, self).__init__(parent)

    def flags(self, index):
        """Override Qt flags method for custom editing behaviour

        :param index: Target index
        """

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        current_flags = QtCore.QAbstractTableModel.flags(self, index)
        return QtCore.Qt.ItemFlags(current_flags | QtCore.Qt.ItemIsEditable)

    def data(self, index, role):
        """Overrides Qt method to provides various data to QtTable models.

        Tables iterate through columns and rows with different roles to get different types of
        data.

        :param index: QModelIndex of the cell for which data is requested
        :type index: QtCore.QModelIndex()
        :param role: Role being requested
        :type role: int
        """

        # Check for valid qt index
        if not index.isValid():
            return None

        # Get the row and column and prepare a blank data var to return
        index_obj = index.row()
        index_field = index.column()
        data = None
        field = None

        # If the role will require a field, get it now
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole,
                    QtCore.Qt.ToolTipRole, QtCore.Qt.BackgroundRole,
                    QtCore.Qt.StatusTipRole]:
            try:
                field = self.idf.field(self.obj_class, index_obj, index_field)
            except IDFError:
                return None

        # Detect the role being request and return the correct data
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            data = self.idf.converted_value(field, index_obj, index_field)
        elif role == QtCore.Qt.ToolTipRole:
            data = self.idf.units(field)
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.StatusTipRole:
            data = self.idf.units(field)
        elif role == QtCore.Qt.TextAlignmentRole:
            data = int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.TextColorRole or role == QtCore.Qt.ForegroundRole:
            pass
        elif role == QtCore.Qt.BackgroundRole:
            # Highlight the cell's background depending on various states
            ref_node_count = self.idf.reference_count(field)
            if ref_node_count == -1:
                data = None
            elif field.value and ref_node_count == 0:
                data = QtGui.QColor(255, 232, 150)
            else:
                data = None
        return data

    def headerData(self, section, orientation, role, old_orientation=None):
        """Overrides Qt method to provide header text for table model.

        :param section: Index of header being requested
        :param orientation: Vertical or Horizontal header requested
        :param role: QtCore.Qt.Role
        :param old_orientation: (optional) Previous orientation
        :return: Data of various types depending on requested role
        """

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
        elif role == QtCore.Qt.BackgroundRole:
            return QtGui.QColor(244, 244, 244)
        return None

    def rowCount(self, parent=None):
        """Overrides Qt method to provide the number of rows (idf objects).

        :param parent:
        :rtype int:
        """

        return len(self.idf_objects)

    def columnCount(self, parent=None):
        """Overrides Qt method to provide the number of columns (idf fields).

        :param parent:
        :rtype int:
        """

        return len(self.idd_object)

    def setData(self, index, value, role):
        """Overrides Qt method for setting data.

        :param index: Index of field to be set
        :type index: QtCore.QModelIndex()
        :param value: The value to use when setting the field's data
        :param role: QtCore.Qt.Role
        :return: True or False for success or failure respectively
        :rtype: bool
        """

        if not index.isValid():
            return False

        index_obj = index.row()
        index_field = index.column()
        field = self.idf.field(self.obj_class, index_obj, index_field, create=True)

        if not field:
            return False

        converted_value = self.idf.converted_value(field, index_obj, index_field)
        if field.value == converted_value:
            # Don't do anything if the value is unchanged
            return False
        else:
            field.value = converted_value

        return True

    def mapToSource(self, source_index):
        """Dummy to ensure there is always a mapToSource method even when there is no proxy layer.

        :param source_index:
        """

        if not source_index.isValid():
            return QtCore.QModelIndex()
        return self.index(source_index.row(), source_index.column())

    def mapFromSource(self, source_index):
        """Provide an index when this model is used as a source model.

        :param source_index:
        """

        if not source_index.isValid():
            return QtCore.QModelIndex()
        return self.index(source_index.row(), source_index.column())

    def mapSelectionFromSource(self, selection):
        """

        :param selection:
        :return: :rtype:
        """

        return_selection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapFromSource(sel.topLeft())
            bottom_right = self.mapFromSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def mapSelectionToSource(self, selection):
        """Dummy to ensure there is always a mapSelectionToSource method even when there
        is no proxy layer.

        :param selection:
        """

        return selection

    def sourceModel(self):
        """Dummy to ensure there is always a sourceModel method even when there is no
        proxy layer.
        """

        return self

    def removeObjects(self, indexes, offset=None, delete_count=None):
        """Overrides Qt method to remove objects from the table

        :param indexes:
        :param offset:
        :param delete_count:
        :return: :rtype:
        """

        # Detect groups and and offset and ensure there is a value for offset
        if offset is None:
            offset = 0
            groups = self._get_contiguous_rows(indexes, True)
        else:
            groups = indexes

        # Ensure there is a delete count
        if delete_count is None:
            delete_count = 1

        # Delete index ranges in all sub-groups
        for group in groups:

            # If group is empty then remove last object
            if not group:
                last_row = None
                first_row = len(self.idf_objects) - delete_count
                last_row_refresh = len(self.idf_objects) - 1
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, last_row_refresh)

            # If there is no offset, delete starting from first of group
            elif not offset:
                first_row = group[0]
                last_row = group[0] + len(group)
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, last_row - 1)

            # Otherwise delete starting from end of group
            else:
                first_row = group[-1] + offset
                last_row = group[-1] + offset + delete_count
                self.beginRemoveRows(QtCore.QModelIndex(), first_row, last_row - 1)

            # Delete the objects, update labels and inform that we're done inserting
            self.idf.remove_objects(self.obj_class, first_row, last_row)
            self._refresh_labels()
            self.endRemoveRows()

        return True

    def insertObjects(self, indexes, objects=None, offset=None):
        """Overrides Qt method to insert new objects into the table

        :param indexes:
        :param objects:
        :param offset:
        """

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

        # Cycle through each groups of indexes in the object list
        for ind, obj_list in enumerate(objs_to_insert):
            count = len(obj_list)
            if indexes and offset:
                first_row = indexes[ind][-1] + row_offset
            elif indexes:
                first_row = indexes[ind][0]
            else:
                first_row = len(self.idf_objects)
            last_row = first_row + count - 1

            # Warn the model that we're about to add rows, then do it
            self.beginInsertRows(QtCore.QModelIndex(), first_row, last_row)
            self.idf.add_objects(obj_list, first_row)

            # Update labels and inform that we're done inserting
            self._refresh_labels()
            self.endInsertRows()

        return True

    @staticmethod
    def _get_contiguous_rows(indexes, reverse):
        """Creates groups of contiguous rows

        :param indexes:
        :param reverse:
        :return: :rtype:
        """

        # Make a unique set of rows
        row_set = set(index.row() for index in indexes)

        # Create groups of contiguous row indexes in reverse order
        groups = []
        for key, g in groupby(enumerate(row_set), lambda (i, x): i-x):
            groups.append(map(itemgetter(1), g))
        groups.sort(reverse=reverse)
        return groups

    def get_contiguous(self, indexes, reverse):
        """

        :param indexes:
        :param reverse:
        :return: :rtype:
        """

        # Get contiguous, groups of unique indexes
        groups = self._get_contiguous_rows(indexes, reverse)

        # Cycle through each group of row indexes
        sub_list = []
        obj_list = []
        for group in groups:
            # Cycle through each index in the group
            for ind in group:
                sub_list.append(deepcopy(self.idf_objects[ind]))
            obj_list.append(sub_list)
            sub_list = []
        return groups, obj_list

    def _refresh_labels(self):
        """Refreshes header labels after changes to table structure
        """

        field_labels = []
        obj_count = len(self.idf_objects)
        obj_id_labels = ['Obj{}'.format(i) for i in range(1, obj_count + 1)]

        for field in self.idd_object.itervalues():
            field_desc = field.tags.get('field', '')
            if self.config['show_units_in_headers']:
                units = self.idf.units(field)
                unit_tag = ' ({})'.format(units) if units else ''
                label = field_desc + unit_tag
            else:
                label = field_desc
            field_labels.append(label)

        self.objID_labels = obj_id_labels
        self.field_labels = field_labels


class TransposeProxyModel(QtGui.QAbstractProxyModel):
    """Translates columns to rows or vice versa
    """

    def setSourceModel(self, source):
        """

        :param source:
        """

        super(TransposeProxyModel, self).setSourceModel(source)

        # Connect signals in a transposed way as well
        # self.sourceModel().columnsAboutToBeInserted.connect(self.rowsAboutToBeInserted.emit)
        # self.sourceModel().columnsInserted.connect(self.rowsInserted.emit)
        # self.sourceModel().columnsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
        # self.sourceModel().columnsRemoved.connect(self.rowsRemoved.emit)
        self.sourceModel().rowsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().rowsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().rowsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().rowsRemoved.connect(self.columnsRemoved.emit)
        self.sourceModel().dataChanged.connect(self.data_changed)
        self.sourceModel().headerDataChanged.connect(self.header_data_changed)

    def mapFromSource(self, source_index):
        """

        :param source_index:
        :return: :rtype:
        """

        if not source_index.isValid():
            return QtCore.QModelIndex()
        return self.index(source_index.column(), source_index.row())

    def mapToSource(self, proxy_index):
        """

        :param proxy_index:
        :return: :rtype:
        """

        if not proxy_index.isValid():
            return QtCore.QModelIndex()
        return self.sourceModel().index(proxy_index.column(), proxy_index.row())

    def mapSelectionFromSource(self, selection):
        """

        :param selection:
        :return: :rtype:
        """

        return_selection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapFromSource(sel.topLeft())
            bottom_right = self.mapFromSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def mapSelectionToSource(self, selection):
        """

        :param selection:
        :return: :rtype:
        """

        return_selection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapToSource(sel.topLeft())
            bottom_right = self.mapToSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def index(self, row, col, parent=None):
        """

        :param row:
        :param col:
        :param parent:
        :return: :rtype:
        """

        return self.createIndex(row, col)

    def parent(self, index):
        """

        :param index:
        :return: :rtype:
        """

        return QtCore.QModelIndex()

    def rowCount(self, parent=None):
        """

        :param parent:
        :return: :rtype:
        """

        return self.sourceModel().columnCount(parent)

    def columnCount(self, parent=None):
        """

        :param parent:
        :return: :rtype:
        """
        return self.sourceModel().rowCount(parent)

    def data(self, index, role):
        """

        :param index:
        :param role:
        :return: :rtype:
        """

        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        """

        :param section:
        :param orientation:
        :param role:
        :return: :rtype:
        """

        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        return self.sourceModel().headerData(section, new_orientation, role, orientation)

    def removeObjects(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def get_contiguous(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().get_contiguous(*args, **kwargs)

    def setData(self, index, value, role):
        """

        :param index:
        :param value:
        :param role:
        :return: :rtype:
        """

        return self.sourceModel().setData(self.mapToSource(index), value, role)

    def data_changed(self, top_left, bottom_right):
        """

        :param top_left:
        :param bottom_right:
        """

        self.dataChanged.emit(self.mapFromSource(top_left),
                              self.mapFromSource(bottom_right))

    def header_data_changed(self, orientation, first, last):
        """

        :param orientation:
        :param first:
        :param last:
        """

        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        self.headerDataChanged.emit(new_orientation, first, last)

    @property
    def obj_class(self):
        """

        :return: :rtype:
        """

        return self.sourceModel().obj_class


class SortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """Proxy layer to sort and filter
    """

    def __init__(self, obj_orientation, parent_view, parent):
        super(SortFilterProxyModel, self).__init__(parent)

        self.obj_orientation = obj_orientation
        self.parent_view = parent_view
        syntax = QtCore.QRegExp.PatternSyntax(QtCore.QRegExp.Wildcard)
        case_sensitivity = QtCore.Qt.CaseInsensitive

        self.setFilterRegExp(QtCore.QRegExp('', case_sensitivity, syntax))
        self.setFilterCaseSensitivity(case_sensitivity)

    def filterAcceptsColumn(self, col, parent):
        """

        :param col:
        :param parent:
        :return: :rtype:
        """

        if self.obj_orientation == QtCore.Qt.Horizontal:
            return True

        model = self.sourceModel()
        row_count = model.rowCount(col)
        reg_exp = self.filterRegExp()

        for row in range(row_count):
            data = model.index(row, col, parent).data()
            if reg_exp.indexIn(data) != -1:
                return True

        return False

    def filterAcceptsRow(self, row, parent):
        """

        :param row:
        :param parent:
        :return: :rtype:
        """

        if self.obj_orientation == QtCore.Qt.Vertical:
            return True

        model = self.sourceModel()
        column_count = model.columnCount(row)
        reg_exp = self.filterRegExp()

        for col in range(column_count):
            data = model.index(row, col, parent).data()
            if reg_exp.indexIn(data) != -1:
                return True

        return False

    def mapSelectionFromSource(self, selection):
        """

        :param selection:
        :return: :rtype:
        """

        return_selection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapFromSource(sel.topLeft())
            bottom_right = self.mapFromSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def mapSelectionToSource(self, selection):
        """

        :param selection:
        :return: :rtype:
        """

        return_selection = QtGui.QItemSelection()
        for sel in selection:
            top_left = self.mapToSource(sel.topLeft())
            bottom_right = self.mapToSource(sel.bottomRight())
            sel_range = QtGui.QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def removeObjects(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def get_contiguous(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: :rtype:
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().get_contiguous(*args, **kwargs)

    @property
    def obj_class(self):
        """

        :return: :rtype:
        """

        return self.sourceModel().obj_class


class TableView(QtGui.QTableView):
    """Subclass of QTableView used to allow editing with return/enter keys.
    """

    def keyPressEvent(self, event):
        """

        :param event:
        """
        if (event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter) \
                and (self.state() != QtGui.QAbstractItemView.EditingState):
            self.edit(self.selectedIndexes()[0])
        else:
            super(TableView, self).keyPressEvent(event)
