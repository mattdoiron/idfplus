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
from persistent.list import PersistentList
from operator import itemgetter
from itertools import groupby
from copy import deepcopy

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .datamodel import IDFObject
from .datamodel import IDFField

# Package imports
from . import logger

# Constants
from . import config

# Setup logging
log = logger.setup_logging(config.LOG_LEVEL, __name__, config.LOG_PATH)


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
        self.ureg = config.UNITS_REGISTRY
        self.config = config.Settings()
        self.get_labels()

        super(IDFObjectTableModel, self).__init__(parent)

    def get_obj_class(self):
        """
        :return: :rtype:
        """

        return self.obj_class

    def flags(self, index):
        """
        :param index:
        :return: :rtype:
        """

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        current_flags = QtCore.QAbstractTableModel.flags(self, index)
        return QtCore.Qt.ItemFlags(current_flags | QtCore.Qt.ItemIsEditable)

    def data(self, index, role):
        """Provides various data to Table models. Tables iterate through
        columns and rows with different roles to get different types of data.
        :param index:
        :param role:
        """

        # Check for valid qt index
        if not index.isValid():
            return None

        # Get the row and column and prepare a blank data var to return
        row = index.row()
        column = index.column()
        data = None

        # Pre-fetch this only once to save lookups
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole,
                    QtCore.Qt.ToolTipRole, QtCore.Qt.BackgroundRole]:
            # Grab the correct field. Return None if it's blank.
            try:
                field = self.idf_objects[row][column]
                # print('field returned as: {}'.format(field))
            except IndexError:
                return None

        # Detect the role being request and return the correct data
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            data = self.get_data(field, row, column)
        elif role == QtCore.Qt.ToolTipRole:
            data = self.get_units(field)
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.StatusTipRole:
            pass
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
        """
        :param section:
        :param orientation:
        :param role:
        :param old_orientation:
        :return: :rtype:
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
        """
        :param parent:
        :return: :rtype:
        """

        return len(self.idf_objects)

    def columnCount(self, parent=None):
        """
        :param parent:
        :return: :rtype:
        """

        return len(self.idd_object)

    def setData(self, index, value, role):
        """
        :param index:
        :param value:
        :param role:
        :return: :rtype:
        """

        if not index.isValid():
            return False
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            # Try to assign the value
            try:
                field = self.idf_objects[row][column]
                old_value = field.value
                self.set_data(field, value, row, column)
                self.update_reference_names(field, old_value)
                self.update_references(field)
            except (AttributeError, IndexError):
                # An invalid index means that we're trying to assign a value
                # to a field that has not yet been 'allocated'. Check for max
                # allowable fields and allocate more if necessary.
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
                # TODO FIXME this new field needs a key! Once IDDObjects are dicts
                # should be able to lookup the key. Until then, unit conversion
                # is broken because all fields need a key to lookup units,
                new_field = IDFField(self.idf_objects[row])
                self.idf_objects[row][column] = new_field
                self.set_data(new_field, value, row, column)
            return True
        return False

    def mapToSource(self, source_index):
        """Dummy to ensure there is always a mapToSource method even when there is no
        :param source_index:
        proxy layer."""

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
        :param selection:
        is no proxy layer."""

        return selection

    def sourceModel(self):
        """Dummy to ensure there is always a sourceModel method even when there is no
         proxy layer."""

        return self

    def removeObjects(self, indexes, offset=None, delete_count=None):
        """
        :param indexes:
        :param offset:
        :param delete_count:
        :return: :rtype:
        """

        # Detect groups and and offset and ensure there is a value for offset
        if offset is None:
            offset = 0
            groups = self.get_contiguous_rows(indexes, True)
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

            # # Remove the fields from graph also
            # ref_graph = self.idf._references
            # objects_to_delete = self.idf_objects[first_row:last_row]
            # idd_obj = self.idd[self.obj_class]
            # # log.debug('nodes before delete: {}'.format(ref_graph.number_of_nodes()))
            #
            # # Delete objects and update reference list
            # self.idf._references.remove_references(objects_to_delete)
            # # for obj in objects_to_delete:
            # #     field_uuids = [field._uuid for field in obj]
            # #     ref_graph.remove_nodes_from(field_uuids)
            # #
            # #     # Also update reference list if required
            # #     for j, field in enumerate(obj):
            # #         tags = idd_obj[j].tags
            # #
            # #         if 'reference' in tags:
            # #             object_list_names = tags['reference']
            # #             if not isinstance(object_list_names, list):
            # #                 object_list_names = [tags['reference']]
            # #             for object_list in object_list_names:
            # #                 tup_list = self.idf.ref_lists[object_list][field.value]
            # #                 for id_tup in tup_list:
            # #                     if id_tup[0] == field._uuid:
            # #                         # Should only be one so it's ok to modify list here!
            # #                         tup_list.remove(id_tup)
            #
            # # Delete the objects, update labels and inform that we're done inserting
            # del self.idf_objects[first_row:last_row]
            self.idf.remove_objects(first_row, last_row)
            self.get_labels()
            self.endRemoveRows()
        # print('--------')
        # import pprint
        # pprint.pprint(self.idf.ref_lists['ScheduleTypeLimitsNames'])
        # log.debug('nodes after delete: {}'.format(ref_graph.number_of_nodes()))
        return True

    def insertObjects(self, indexes, objects=None, offset=None):
        """
        :param indexes:
        :param objects:
        :param offset:
        :return: :rtype:
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
            # self.idf_objects[first_row:first_row] = obj_list
            self.idf.add_objects(obj_list, first_row)

            # Add the fields to graph also
            # ref_graph = self.idf._references._ref_graph
            # log.debug('nodes before add: {}'.format(ref_graph.number_of_nodes()))
            # ref_set = {'object-list', 'reference'}
            # idd_obj = self.idd[self.obj_class]

            # # Add nodes for each field that requires one.
            # for obj in obj_list:
            #     for j, field in enumerate(obj):
            #         tags = idd_obj[j].tags
            #         tag_set = set(tags)
            #
            #         if field and len(tag_set & ref_set) > 0:
            #             ref_graph.add_node(field._uuid, data=field)
            #             self.update_references(field)
            #
            #             # Update the reference list if required
            #             if 'reference' in tags:
            #                 object_list_names = tags['reference']
            #                 if not isinstance(object_list_names, list):
            #                     object_list_names = [tags['reference']]
            #                 for object_list in object_list_names:
            #                     id_tup = (field._uuid, field)
            #                     val = field.value
            #                     try:
            #                         self.idf.ref_lists[object_list][val].append(id_tup)
            #                     except (AttributeError, KeyError):
            #                         self.idf.ref_lists[object_list][val] = [id_tup]

            # Update labels and inform that we're done inserting
            self.get_labels()
            self.endInsertRows()
        # print('--------')
        # import pprint
        # pprint.pprint(self.idf.ref_lists['ScheduleTypeLimitsNames'])
        # log.debug('nodes after add: {}'.format(ref_graph.number_of_nodes()))
        return True

    @staticmethod
    def get_contiguous_rows(indexes, reverse):
        """
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
        groups = self.get_contiguous_rows(indexes, reverse)

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

    def get_labels(self):
        """Returns axis labels
        """

        field_labels = []
        obj_count = len(self.idf_objects)
        obj_id_labels = ['Obj{}'.format(i) for i in range(1, obj_count + 1)]

        for field in self.idd_object:
            field_desc = field.tags.get('field', '')
            if self.config['show_units_in_headers']:
                units = self.get_units(field)
                unit_tag = ' ({})'.format(units) if units else ''
                label = field_desc + unit_tag
            else:
                label = field_desc
            field_labels.append(label)

        self.objID_labels = obj_id_labels
        self.field_labels = field_labels

    def get_units(self, field):
        """Returns the given IDDField's current units.
        :param field:
        """

        if field is None:
            return None

        # Look-up the default units
        units = field.tags.get('units')

        # If SI units are requested, return now (SI is always the default)
        if self.idf.si_units is True:
            return units
        else:
            # Otherwise check for special ip-units exceptions
            ip_units = field.tags.get('ip-units')
            if ip_units:
                return ip_units
            else:
                unit_dict = self.ureg.get(units)
                if unit_dict:
                    return unit_dict.keys()[0]
                else:
                    return units

    def get_unit_conversion(self, row, column):
        """Gets the appropriate unit conversion value(s)
        :param row:
        :param column:
        """

        # Get the idd field corresponding to this idf field
        idd_field = self.idd_object[column]

        # Look-up the default units and any ip-unit exceptions
        units = idd_field.tags.get('units')
        ip_units = idd_field.tags.get('ip-units')

        if units:
            # Check for the special case of units based on another field
            if units.startswith('BasedOnField'):
                based_on_field_key = units.split()[-1]
                based_on_field = None

                # Find which idd object has the specified key
                for f in self.idd_object:
                    if f.key == based_on_field_key:
                        ind = self.idd_object.index(f)
                        if ind >= len(self.idf_objects[row]):
                            return None
                        based_on_field = self.idf_objects[row][ind]
                        break

                # Use these results to find the actual units to use
                actual_units = config.UNIT_TYPES.get(based_on_field.value)

                if actual_units:
                    units = actual_units

            # Lookup the dict of unit conversions for this SI unit.
            conv = self.ureg.get(units)
            if conv:
                # Lookup the desired ip_units in the dict if specified, otherwise get the
                # 'first' (only) one in the dict.
                return conv.get(ip_units, conv.get(conv.keys()[0]))

        return None

    @staticmethod
    def to_si(value, conv):
        """Accepts a value and a conversion factor, and returns the value in SI units.
        :param conv: Conversion factor to use to convert units
        :param value: string value from IDFField object
        """

        # If the units were found, perform the conversion
        try:
            # Convert units and force it back to a string
            data = str(float(value) / conv)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conv[0]
            adder = conv[1]
            data = str((float(value) - adder) / multiplier)
        return data

    @staticmethod
    def to_ip(value, conv):
        """Accepts a value and a conversion factor, and returns the value in IP units.
        :param value: string value from IDFField object
        :param conv: Conversion factor to use to convert units
        """

        # If the units were found, perform the conversion
        try:
            # Convert units and force it back to a string
            data = str(float(value) * conv)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conv[0]
            adder = conv[1]
            data = str(float(value) * multiplier + adder)
        except ValueError:
            data = value
        return data

    def set_data(self, field, value, row, column):
        """Sets the value of the specified field taking into account units
        :param row:
        :param column:
        :param field: IDFField object whose value will be updated
        :param value: string value from IDFField object
        """

        # If SI units are requested, return now (SI is always the default)
        if self.idf.si_units is True:
            field.value = value
            return True

        # Get the unit conversion
        ip_unit_conversion = self.get_unit_conversion(row, column)

        # If the units were found, perform the conversion
        if ip_unit_conversion:
            field.value = self.to_si(value, ip_unit_conversion)
        else:
            field.value = value
        return True

    def get_data(self, field, row, column):
        """Retrieves data from the model and converts it to the desired units.
        :param row:
        :param column:
        :param field: IDFField object for which the value will be returned
        """

        # If SI units are requested, return now (SI is always the default)
        if self.idf.si_units is True:
            if field:
                return field.value
            else:
                return None

        # Get the unit conversion
        ip_unit_conversion = self.get_unit_conversion(row, column)

        # If the units were found, perform the conversion
        if ip_unit_conversion:
            return self.to_ip(field.value, ip_unit_conversion)
        return field.value


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

    def get_units(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return: :rtype:
        """

        return self.sourceModel().get_units(*args, **kwargs)

    def get_obj_class(self):
        """
        :return: :rtype:
        """

        return self.sourceModel().get_obj_class()


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

    def get_units(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return: :rtype:
        """

        return self.sourceModel().get_units(*args, **kwargs)

    def get_obj_class(self):
        """
        :return: :rtype:
        """

        return self.sourceModel().get_obj_class()


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
