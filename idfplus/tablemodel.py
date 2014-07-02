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

# System imports
import shelve
import os

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from .idfmodel import IDFObject


class IDFObjectTableModel(QtCore.QAbstractTableModel):
    """Qt object that handles interaction between the table and the data
    displayed in the table.
    """

    def __init__(self, obj_class, idf):
        self.obj_class = obj_class
        self.idf = idf
        self.idd = idf._idd
        # print('setting obj_class: {}'.format(obj_class))
        self.idf_objects = idf.get(obj_class, [])
        self.idd_object = idf._idd.get(obj_class)
        # print('loading idd object: {}'.format(self.idd_object))
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
                # print('data: {}'.format(data))
            except IndexError:
                return None
        elif role == QtCore.Qt.ToolTipRole:
            data = "tooltip test"
        elif role == QtCore.Qt.DecorationRole:
            pass
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        elif role == QtCore.Qt.TextColorRole:
            return QtGui.QColor(QtCore.Qt.black)
        elif role == QtCore.Qt.BackgroundColorRole:
            return QtGui.QColor(250, 230, 250)
        return data

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.field_labels[section]
            if orientation == QtCore.Qt.Vertical:
                return self.objID_lables[section]
        return None

    def rowCount(self, index):
        return len(self.idf_objects)

    def columnCount(self, index):
        if len(self.idf_objects) > 0:
            return len(self.idf_objects[0])
        else:
            return 0

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
                return True
            except IndexError:
                return False
        return False

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(),
                             position,
                             position + rows - 1)
        for row in range(rows):
            new_obj = IDFObject(self.obj_class, self.idf, self.idd)
            self.idf_objects.insert(position + row, new_obj)
        self.endInsertRows()
        self.dirty = True
        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(),
                             position,
                             position + rows - 1)
        self.idf_objects = self.idf_objects[:position] + \
                           self.idf_objects[position + rows:]
        self.endRemoveRows()
        self.dirty = True
        return True

    def getLabels(self):
        field_labels = []
        obj_count = len(self.idf_objects) + 1
        objID_lables = ['Obj{}'.format(i) for i in range(1, obj_count)]
        # print(self.idd_object.items())
        for field in self.idd_object:
            # print('idd_obj type: {}'.format(type(field)))
            # print('field: {}'.format(field.tags))
            field_labels.append(field.tags.get('field'))
        self.objID_lables = objID_lables
        self.field_labels = field_labels
        # print(objID_lables)
        # print(field_labels)


class TransposeProxyModel(QtGui.QAbstractProxyModel):
    """Translates columns to rows or vice versa"""

    def __init__(self, source_model, parent=None):
        super(TransposeProxyModel, self).__init__(parent)
        self.source_model = source_model
        self.setSourceModel(self.source_model)

    def setSourceModel(self, source):
        super(TransposeProxyModel, self).setSourceModel(source)

        # connect signals
        self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)
#        self.sourceModel().rowsInserted.connect(self._rowsInserted)
#        self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
#        self.sourceModel().dataChanged.connect(self._dataChanged)

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
        return self.createIndex(row, col)

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent):
        if self.sourceModel():
            return self.sourceModel().columnCount(QtCore.QModelIndex())
        else:
            return 0

    def columnCount(self, parent):
        if self.sourceModel():
            return self.sourceModel().rowCount(QtCore.QModelIndex())
        else:
            return 0

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        return self.sourceModel().headerData(section, new_orientation, role)


# class IDDFile(object):
#     """Object to handle all interaction with idd files."""
#
#     def __init__(self, parent, version):
#
#         if not version or not parent:
#             raise ValueError("Missing version number when defining IDD.")
#
#         self.parent = parent
#         self.version = version
#         self.idd = None
#         self.settings = parent.settings
#
#     def loadIDD(self):
#         '''Loads the idd file of the appropriate version for use later.'''
#
#         idd_file = os.path.join(self.settings.get_dir_name(),
#                                 'data',
#                                 'EnergyPlus_IDD_v') + self.version + '.dat'
#
#         try:
#             print('Loading IDD file: {}'.format(idd_file))
#             self.idd = shelve.open(idd_file)
#             return True
#         except Exception as e:
#             print("Can't open file: {} ({})".format(idd_file, e))
#             return False
