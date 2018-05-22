#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tree model used as a base for other tree views

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# PySide imports
from PySide import QtCore


class BaseTreeItem(object):
    """Low level item for a custom tree views
    """

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
        return 2

    def data(self, column):
        # Must implement in a sub-class
        pass

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    def item(self):
        return self.itemData


class TreeItem(BaseTreeItem):
    """Low level item for a custom class tree view
    """

    def data(self, column):
        """Returns data for specified column in the tree

        :type column: int
        :return:
        """

        data = self.itemData[column]
        try:
            if column == 1:
                if data == '#':
                    return data
                if data:
                    count = len(data)
                else:
                    count = 0
                if count <= 0:
                    return ''
                else:
                    return count
            else:
                return data
        except IndexError:
            return None


class CustomTreeModel(QtCore.QAbstractItemModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def data(self, index, role):
        """Returns data for specified column in the tree

        :param index: Index of tree item for which data is requested
        :type index: QtCore.QModelIndex()
        :param role: QtCore.Qt.Role
        :type role: int
        :return: Various data related to the tree item
        """

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

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

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

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def setupModelData(self, data, parent):
        pass
