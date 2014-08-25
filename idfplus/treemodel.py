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
from PySide import QtCore
from PySide import QtGui


class TreeItem(object):
    """Low level item for a custom tree view"""

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0


class CustomTreeModel(QtCore.QAbstractItemModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def __init__(self, data, root, parent=None):
        super(CustomTreeModel, self).__init__(parent)
        self.rootItem = TreeItem(root)
        self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return int(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if not parentItem or parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, data, parent):
        pass


class ObjectClassTreeModel(CustomTreeModel):
    """Qt object that handles interaction between the object class list and the data
    displayed in the tree view.
    """

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        item = index.internalPointer()
        if item.data(0) == '' and item.data(1) == '':
            data = QtCore.Qt.NoItemFlags
        elif item.parent().data(0) == 'Object Class' and item.data(0) != '':
            data = QtCore.Qt.ItemIsEnabled
        else:
            data = int(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        return data

    def data(self, index, role):
        if not index.isValid():
            return None

        data = None
        if role == QtCore.Qt.DisplayRole:
            data = index.internalPointer().data(index.column())
        elif role == QtCore.Qt.BackgroundRole:
            item = index.internalPointer()
            if item.parent().data(0) == 'Object Class' and item.data(0) != '':
                data = QtGui.QColor(205, 192, 176)  # light grey
        elif role == QtCore.Qt.TextAlignmentRole and index.column() == 1:
            data = QtCore.Qt.AlignRight

        return data

    def setupModelData(self, data, parent):
        if data:
            group = ''
            group_root = None

            for obj_class, obj in data._idd.iteritems():
                if group != obj.group:

                    group = obj.group
                    group_root = TreeItem((group,''), parent)
                    parent.appendChild(group_root)

                    blank = TreeItem(('',''), parent)
                    parent.appendChild(blank)
                    # blank.setDisabled(True)

                objs = data.get(obj_class, None)
                obj_count = len(objs or []) or ''

                child = TreeItem((obj_class, str(obj_count)), group_root)
                group_root.appendChild(child)


class ReferenceTreeModel(CustomTreeModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def setupModelData(self, data, parent):
        if data:
            if data[0]:
                ancestor_root = TreeItem(('Incoming References',''), parent)
                parent.appendChild(ancestor_root)
                for item in data[0]:
                    tree_data = (str(item._outer[0].value), item._outer._obj_class)
                    ancestor_root.appendChild(TreeItem(tree_data, ancestor_root))
            if data[1]:
                descendant_root = TreeItem(('Outgoing References',''), parent)
                parent.appendChild(descendant_root)
                for item in data[1]:
                    tree_data = (str(item._outer[0].value), item._outer._obj_class)
                    descendant_root.appendChild(TreeItem(tree_data, descendant_root))