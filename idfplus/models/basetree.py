#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tree model used as a base for other tree views

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# PySide6 imports
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel


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

        :param int column: column of desired data
        :rtype: str or None
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


class CustomTreeModel(QAbstractItemModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def data(self, index, role):
        """Returns various data for specified column in the tree

        :param QModelIndex() index: Index of tree item for which data is requested
        :param int role: Qt.Role
        """

        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if not parentItem or parentItem == self.rootItem:
            return QModelIndex()

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
