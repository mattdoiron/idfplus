#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Classes that manage the class table

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging
from itertools import groupby

# PySide2 imports
from PySide2.QtCore import (Qt, QAbstractTableModel, QItemSelection, QItemSelectionRange,
                            QAbstractProxyModel, QRegExp, QItemSelectionModel, QModelIndex,
                            QSortFilterProxyModel, QRect, QPoint)
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QTableView, QAbstractItemView

# Package imports
from ..eplusio.idfmodel import IDFError

# Setup logging
log = logging.getLogger(__name__)


class IDFObjectTableModel(QAbstractTableModel):
    """Qt table model object that links the table widget and its underlying data structure.
    """

    def __init__(self, parent, obj_orientation=None):
        """Initialises table model

        :param QTableView parent: Parent qt object to which this model belongs
        :param int obj_orientation: Qt.Vertical or Qt.Horizontal
        """

        self.obj_class = ''
        self.idf = None
        self.idd = None
        self.idf_objects = None
        self.idd_object = None
        self.obj_orientation = obj_orientation or Qt.Vertical
        self.prefs = parent.prefs
        self.parent = parent
        super(IDFObjectTableModel, self).__init__(parent)

    def setObjectClass(self, obj_class, idf):
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf.idd
        self.idf_objects = idf.idf_objects(obj_class)
        self.idd_object = idf.idd.idd_object(obj_class)
        self._refresh_labels()


    def flags(self, index):
        """Override Qt flags method for custom editing behaviour

        :param QModelIndex index: Target index
        """

        if not index.isValid():
            return Qt.ItemIsEnabled

        current_flags = QAbstractTableModel.flags(self, index)
        return Qt.ItemFlags(current_flags | Qt.ItemIsEditable)

    def data(self, index, role):
        """Overrides Qt method to provides various data to QtTable models.

        Tables iterate through columns and rows with different roles to get different types of
        data.

        :param QModelIndex index: QModelIndex of the cell for which data is requested
        :param int role: Role being requested (Qt.Role)
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
        if role in [Qt.DisplayRole, Qt.EditRole,
                    Qt.ToolTipRole, Qt.BackgroundRole,
                    Qt.StatusTipRole]:
            try:
                field = self.idf.field(self.obj_class, index_obj, index_field)
            except IDFError:
                return None

        # Detect the role being request and return the correct data
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if not field:
                data = None
            else:
                if role != Qt.EditRole and self.prefs['show_units_in_cells']:
                    text_units = self.idf.units(field) or ''
                    spacing = ' ' if text_units else ''
                else:
                    text_units = ''
                    spacing = ''
                if not field.value:
                    text_units = ''
                    spacing = ''
                if self.idf.si_units is True:
                    data = '{}{}{}'.format(field.value, spacing, text_units)
                else:
                    data = '{}{}{}'.format(self.idf.to_ip(field), spacing, text_units)
        elif role == Qt.ToolTipRole:
            data = self.idf.units(field)
        elif role == Qt.DecorationRole:
            pass
        elif role == Qt.StatusTipRole:
            data = self.idf.units(field)
        elif role == Qt.TextAlignmentRole:
            data = Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.TextColorRole or role == Qt.ForegroundRole:
            pass
        elif role == Qt.BackgroundRole:
            # Highlight the cell's background depending on various states
            ref_node_count = 1  # self.idf.reference_count(field)
            if not field:
                data = None
            elif field.value and ref_node_count == 0:
                data = QColor(255, 232, 150)
            else:
                data = None
        return data

    def headerData(self, section, orientation, role):
        """Overrides Qt method to provide header text for table model.

        :param int section: Index of header being requested
        :param int orientation: Vertical or Horizontal header requested
        :param int role: Qt.Role
        :returns: Data of various types depending on requested role
        """

        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return Qt.AlignLeft | Qt.AlignVCenter
            elif orientation == Qt.Vertical:
                return Qt.AlignRight | Qt.AlignVCenter
        elif role == Qt.DisplayRole or role == Qt.ToolTipRole:
            if orientation == Qt.Horizontal:
                try:
                    return self.field_labels[section] or None
                except IndexError:
                    return None
            elif orientation == Qt.Vertical:
                try:
                    return self.object_labels[section]
                except IndexError:
                    return None
        elif role == Qt.BackgroundRole:
            return QColor(244, 244, 244)
        elif role == Qt.FontRole:
            return self.parent.font()
        return None

    def rowCount(self, parent=None):
        """Overrides Qt method to provide the number of rows (idf objects).

        :rtype: int
        """

        return len(self.idf_objects or [])

    def columnCount(self, parent=None):
        """Overrides Qt method to provide the number of columns (idf fields).

        :rtype: int
        """

        if self.idf_objects:
            idf_max_length = max([len(obj) for obj in self.idf_objects])
            return max(idf_max_length, len(self.idd_object))
        else:
            return len(self.idd_object or [])

    def setData(self, index, value, role):
        """Overrides Qt method for setting data.

        :param QModelIndex index: Index of field to be set
        :param str value: The value to use when setting the field's data
        :param int role: Qt.Role
        :returns: True or False for success or failure respectively
        :rtype: bool
        """

        # Check for valid qt index
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            index_obj = index.row()
            index_field = index.column()

            field = self.idf.field(self.obj_class, index_obj, index_field)

            if not field:
                self.idf.allocate_fields(self.obj_class, index_obj, index_field)
                field = self.idf.field(self.obj_class, index_obj, index_field)

            if not field:
                return False

            # Convert the value only if required
            if self.idf.si_units is True or value == '':
                converted_value = value
            else:
                converted_value = self.idf.to_si(field, override_value=value)

            # Don't overwrite unless the value is new
            if field.value != converted_value:
                field.value = converted_value
                return True

        return False

    def removeObjects(self, indexes, offset=None, delete_count=None):
        """Overrides Qt method to remove objects from the table

        :param list indexes:
        :param int offset:
        :param int delete_count:
        """

        # Detect groups and and offset and ensure there is a value for offset
        if offset is None:
            offset = 0
            groups = self.contiguous_rows(indexes, True)
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
                self.beginRemoveRows(QModelIndex(), first_row, last_row_refresh)

            # If there is no offset, delete starting from first of group
            elif not offset:
                first_row = group[0]
                last_row = group[0] + len(group)
                self.beginRemoveRows(QModelIndex(), first_row, last_row - 1)

            # Otherwise delete starting from end of group
            else:
                first_row = group[-1] + offset
                last_row = group[-1] + offset + delete_count
                self.beginRemoveRows(QModelIndex(), first_row, last_row - 1)

            # Delete the objects, update labels and inform that we're done inserting
            self.idf.remove_objects(self.obj_class, first_row, last_row)
            self._refresh_labels()
            self.endRemoveRows()

        return True

    def insertObjects(self, indexes, objects=None, offset=None):
        """Overrides Qt method to insert new objects into the table

        :param list indexes:
        :param objects:
        :param int offset:
        """

        # Make sure we're dealing with a list of object lists
        if not objects:
            objects_to_insert = [[objects]]
        else:
            objects_to_insert = objects

        # Ensure there is a row_offset
        if offset:
            row_offset = offset
        else:
            row_offset = 0

        # Cycle through each groups of indexes in the object list
        for ind, obj_list in enumerate(objects_to_insert):
            count = len(obj_list)
            if indexes and offset:
                first_row = indexes[ind][-1] + row_offset
            elif indexes:
                first_row = indexes[ind][0]
            else:
                first_row = len(self.idf_objects)
            last_row = first_row + count - 1

            # Warn the model that we're about to add rows, then do it
            self.beginInsertRows(QModelIndex(), first_row, last_row)
            self.idf.add_objects(self.obj_class, obj_list, first_row)

            # Update labels and inform that we're done inserting
            self._refresh_labels()
            self.endInsertRows()

        return True

    @staticmethod
    def contiguous_rows(indexes, reverse):
        """Creates groups of contiguous rows from the provided indexes.

        :param list indexes: List of indexes
        :param bool reverse: Whether or not to reverse the order of the groups
        """

        # Make a unique set of rows
        row_set = set(index.row() for index in indexes)

        # Create groups of contiguous row indexes in reverse order
        groups = []
        for key, g in groupby(enumerate(row_set), lambda val: val[1]-val[0]):
            groups.append([item[1] for item in g])
        groups.sort(reverse=reverse)
        return groups

    def contiguous(self, indexes, reverse, duplicates=False):
        """Gets contiguous groups of rows and objects.

        :param bool duplicates:
        :param list indexes:
        :param bool reverse:
        """

        # Get contiguous, groups of unique indexes
        groups = self.contiguous_rows(indexes, reverse)

        # Cycle through each group of row indexes
        sub_list = []
        obj_list = []
        for group in groups:
            # Cycle through each index in the group
            for ind in group:
                idf_obj = self.idf_objects[ind]
                sub_list.append(idf_obj.duplicate() if duplicates else idf_obj)
            obj_list.append(sub_list)
            sub_list = []
        return groups, obj_list

    def _refresh_labels(self):
        """Refreshes header labels after changes to table structure
        """

        field_labels = []
        obj_count = len(self.idf_objects)
        obj_id_labels = ['Obj{}'.format(i) for i in range(1, obj_count + 1)]

        for key in self.idd_object._ordered_fields:
            field = self.idd_object[key]
            field_desc = field.tags.get('field', '')
            if self.prefs['show_units_in_headers']:
                units = self.idf.units(field)
                unit_tag = ' ({})'.format(units) if units else ''
                label = field_desc + unit_tag
            else:
                label = field_desc
            field_labels.append(label)

        self.object_labels = obj_id_labels
        self.field_labels = field_labels


class TransposeProxyModel(QAbstractProxyModel):
    """Translates columns to rows or vice versa
    """

    def __init__(self, *args, **kwargs):
        self._obj_orientation = kwargs.pop('obj_orientation', Qt.Vertical)
        super(TransposeProxyModel, self).__init__(*args, **kwargs)

    @property
    def obj_orientation(self):
        return self._obj_orientation

    @obj_orientation.setter
    def obj_orientation(self, value):
        self._obj_orientation = value
        self.sourceModel().obj_orientation = value

    def setObjectClass(self, obj_class, idf):
        self.sourceModel().setObjectClass(obj_class, idf)

    def setSourceModel(self, source):
        """Defines the source model to use and connects some signals.

        :param source: QAbstractModel to use
        """

        super(TransposeProxyModel, self).setSourceModel(source)

        # Connect signals in a transposed way as well
        if self.obj_orientation == Qt.Vertical:
            self.sourceModel().rowsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
            self.sourceModel().rowsInserted.connect(self.columnsInserted.emit)
            self.sourceModel().rowsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
            self.sourceModel().rowsRemoved.connect(self.columnsRemoved.emit)
        else:
            self.sourceModel().rowsAboutToBeInserted.connect(self.rowsAboutToBeInserted.emit)
            self.sourceModel().rowsInserted.connect(self.rowsInserted.emit)
            self.sourceModel().rowsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
            self.sourceModel().rowsRemoved.connect(self.rowsRemoved.emit)

        self.sourceModel().dataChanged.connect(self.data_changed)
        self.sourceModel().headerDataChanged.connect(self.header_data_changed)

    def mapFromSource(self, source_index):
        """

        :param source_index:
        """

        if not source_index.isValid():
            return QModelIndex()

        if self.obj_orientation == Qt.Vertical:
            return self.index(source_index.column(), source_index.row())
        else:
            return self.index(source_index.row(), source_index.column())

    def mapToSource(self, proxy_index):
        """

        :param proxy_index:
        """

        if not proxy_index.isValid():
            return QModelIndex()

        if self.obj_orientation == Qt.Vertical:
            return self.sourceModel().index(proxy_index.column(), proxy_index.row())
        else:
            return self.sourceModel().index(proxy_index.row(), proxy_index.column())

    def mapSelectionFromSource(self, selection):
        """

        :param selection:
        """

        return_selection = QItemSelection()
        for sel in selection:
            top_left = self.mapFromSource(sel.topLeft())
            bottom_right = self.mapFromSource(sel.bottomRight())
            sel_range = QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def mapSelectionToSource(self, selection):
        """

        :param selection:
        """

        return_selection = QItemSelection()
        for sel in selection:
            top_left = self.mapToSource(sel.topLeft())
            bottom_right = self.mapToSource(sel.bottomRight())
            sel_range = QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def index(self, row, col, parent=None):
        """

        :param int row:
        :param int col:
        """

        return self.createIndex(row, col)

    def parent(self, index):
        """

        :param index:
        """

        return QModelIndex()

    def rowCount(self, parent=None):
        """

        :param parent:
        """

        if self.obj_orientation == Qt.Vertical:
            return self.sourceModel().columnCount(parent)
        else:
            return self.sourceModel().rowCount(parent)

    def columnCount(self, parent=None):
        """

        :param parent:
        """

        if self.obj_orientation == Qt.Vertical:
            return self.sourceModel().rowCount(parent)
        else:
            return self.sourceModel().columnCount(parent)

    def data(self, index, role):
        """

        :param index:
        :param int role:
        """

        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        """Gets header data

        :param int section:
        :param int orientation:
        :param int role:
        """

        new_orientation = orientation
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            transposed = True if self.obj_orientation == Qt.Vertical else False
            if orientation == Qt.Horizontal:
                new_orientation = Qt.Vertical if transposed else orientation
            else:
                new_orientation = Qt.Horizontal if transposed else orientation
        return self.sourceModel().headerData(section, new_orientation, role)

    def removeObjects(self, *args, **kwargs):
        """Calls source model's removeObjects
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        """Calls source model's insertObjects
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def contiguous(self, *args, **kwargs):
        """Calls source model's contiguous function
        """

        # Do NOT map to source. Pass through only.
        return self.sourceModel().contiguous(*args, **kwargs)

    def setData(self, index, value, role):
        """Calls source model's setData function
        """

        return self.sourceModel().setData(self.mapToSource(index), value, role)

    def data_changed(self, top_left, bottom_right):
        """Emits signals in source model

        :param int top_left:
        :param int bottom_right:
        """

        self.dataChanged.emit(self.mapFromSource(top_left),
                              self.mapFromSource(bottom_right))

    def header_data_changed(self, orientation, first, last):
        transposed = True if self.obj_orientation == Qt.Vertical else False
        if orientation == Qt.Horizontal:
            new_orientation = Qt.Vertical if transposed else orientation
        else:
            new_orientation = Qt.Horizontal if transposed else orientation
        self.headerDataChanged.emit(new_orientation, first, last)

    @property
    def obj_class(self):
        """Calls source model obj_class
        """

        return self.sourceModel().obj_class

    @property
    def idd_object(self):
        return self.sourceModel().idd_object

class SortFilterProxyModel(QSortFilterProxyModel):
    """Proxy layer to sort and filter
    """

    def __init__(self, *args, obj_orientation=None, **kwargs):
        super(SortFilterProxyModel, self).__init__(*args, **kwargs)

        self.idf = None
        self._obj_orientation = obj_orientation or Qt.Vertical
        syntax = QRegExp.PatternSyntax(QRegExp.Wildcard)
        case_sensitivity = Qt.CaseInsensitive

        self.setFilterRegExp(QRegExp('', case_sensitivity, syntax))
        self.setFilterCaseSensitivity(case_sensitivity)

    @property
    def obj_orientation(self):
        return self._obj_orientation

    @obj_orientation.setter
    def obj_orientation(self, value):
        self._obj_orientation = value
        self.sourceModel().obj_orientation = value

    def setObjectClass(self, obj_class, idf):
        self.sourceModel().setObjectClass(obj_class, idf)
        self.invalidate()
        self.idf = idf
        self.resized_rows = []

    def filterAcceptsColumn(self, col, parent):
        if self.obj_orientation == Qt.Horizontal:
            return True

        reg_exp = self.filterRegExp()
        if not self.idf:
            return True
        objects = self.idf.idf_objects(self.obj_class)
        obj = objects[col]
        if reg_exp.indexIn(str(obj)) != -1:
            return True

        return False

    def filterAcceptsRow(self, row, parent):
        if self.obj_orientation == Qt.Vertical:
            return True

        reg_exp = self.filterRegExp()
        if not self.idf:
            return True
        objects = self.idf.idf_objects(self.obj_class)
        obj = objects[row]
        if reg_exp.indexIn(str(obj)) != -1:
            return True

        return False

    def mapSelectionFromSource(self, selection):
        return_selection = QItemSelection()
        for sel in selection:
            top_left = self.mapFromSource(sel.topLeft())
            bottom_right = self.mapFromSource(sel.bottomRight())
            sel_range = QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def mapSelectionToSource(self, selection):
        return_selection = QItemSelection()
        for sel in selection:
            top_left = self.mapToSource(sel.topLeft())
            bottom_right = self.mapToSource(sel.bottomRight())
            sel_range = QItemSelectionRange(top_left, bottom_right)
            return_selection.append(sel_range)
        return return_selection

    def removeObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().removeObjects(*args, **kwargs)

    def insertObjects(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().insertObjects(*args, **kwargs)

    def contiguous(self, *args, **kwargs):
        # Do NOT map to source. Pass through only.
        return self.sourceModel().contiguous(*args, **kwargs)

    @property
    def obj_class(self):
        return self.sourceModel().obj_class

    @property
    def idd_object(self):
        return self.sourceModel().idd_object

class TableView(QTableView):
    """Subclass of QTableView to allow custom editing behaviour.
    """

    def __init__(self, parent, **kwargs):
        super(TableView, self).__init__(parent, **kwargs)
        self.prefs = parent.prefs

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.state() != QAbstractItemView.EditingState:
                event.accept()
                self.edit(self.selectedIndexes()[0])
                return
        if event.modifiers() & Qt.ControlModifier:
            selection_keys = [Qt.Key_PageUp, Qt.Key_Up,
                              Qt.Key_PageDown, Qt.Key_Down,
                              Qt.Key_Left, Qt.Key_Right]
            if event.key() in selection_keys:
                if event.modifiers() & Qt.ShiftModifier:
                    event.accept()
                    self.select_in_direction(event.key())
                    return
                else:
                    event.accept()
                    self.select_first_in_direction(event.key())
                    return
            else:
                return super(TableView, self).keyPressEvent(event)
        else:
            return super(TableView, self).keyPressEvent(event)

    def select_in_direction(self, key):
        """Selects fields in one direction.

        :param Qt.Key key:
        """

        model = self.model()
        selection_model = self.selectionModel()
        selection = selection_model.selection()[0]  # There should only ever be one
        top_left_current = selection.topLeft()
        bottom_right_current = selection.bottomRight()
        top_left = top_left_current
        bottom_right = bottom_right_current

        if key in [Qt.Key_PageUp, Qt.Key_Up]:
            top_left = model.index(0, top_left_current.column())
            bottom_right = model.index(bottom_right_current.row(), bottom_right_current.column())
        elif key in [Qt.Key_PageDown, Qt.Key_Down]:
            top_left = model.index(top_left_current.row(), top_left_current.column())
            bottom_right = model.index(model.rowCount()-1, bottom_right_current.column())
        elif key in [Qt.Key_Left]:
            top_left = model.index(top_left_current.row(), 0)
            bottom_right = model.index(bottom_right_current.row(), bottom_right_current.column())
        elif key in [Qt.Key_Right]:
            top_left = model.index(top_left_current.row(), top_left_current.column())
            bottom_right = model.index(bottom_right_current.row(), model.columnCount()-1)

        selection = QItemSelection()
        sel_range = QItemSelectionRange(top_left, bottom_right)
        selection.append(sel_range)
        selection_model.reset()
        selection_model.select(selection, QItemSelectionModel.SelectCurrent)

    def select_first_in_direction(self, key):
        """Selects the first field in one direction.

        :param Qt.Key key:
        """

        selected = self.selectedIndexes()
        model = self.model()

        if len(selected) > 1:
            return

        to_select = selected[0]
        row = selected[0].row()
        column = selected[0].column()

        if key in [Qt.Key_PageUp, Qt.Key_Up]:
            to_select = model.index(0, column)
        elif key in [Qt.Key_PageDown, Qt.Key_Down]:
            to_select = model.index(model.rowCount()-1, column)
        elif key in [Qt.Key_Left]:
            to_select = model.index(row, 0)
        elif key in [Qt.Key_Right]:
            to_select = model.index(row, model.columnCount()-1)

        self.setCurrentIndex(to_select)

    def resize_visible_rows(self):
        viewport_rect = QRect(QPoint(0, 0), self.viewport().size())
        for row in range(self.model().rowCount()):
            rect = self.visualRect(self.model().index(row, 0))
            is_visible = viewport_rect.contains(rect)
            if is_visible:
                self.resizeRowToContents(row)
