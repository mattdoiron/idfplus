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

# PySide imports
from PySide import QtCore
from PySide import QtGui

# Package imports
from .basetree import TreeItem
from .basetree import CustomTreeModel


class ObjectClassTreeModel(CustomTreeModel):
    """Qt object that handles interaction between the object class list and the data
    displayed in the tree view.
    """

    def __init__(self, data, root, parent=None):
        super(ObjectClassTreeModel, self).__init__(parent)
        self.rootItem = TreeItem(root)
        self.setupModelData(data, self.rootItem)

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

    def data(self, index, role=QtCore.Qt.DisplayRole):
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

    def setupModelData(self, idf, parent):
        if idf:
            group = ''
            group_root = None

            for obj_class, obj in idf._idd.iteritems():
                if group != obj.group:

                    group = obj.group
                    group_root = TreeItem((group, ''), parent)
                    parent.appendChild(group_root)

                    blank = TreeItem(('', ''), parent)
                    parent.appendChild(blank)

                objs = idf.get(obj_class, None)

                child = TreeItem((obj_class, objs), group_root)
                group_root.appendChild(child)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result


class TreeSortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """Proxy layer to sort and filter
    """

    def __init__(self, *args, **kwargs):
        super(TreeSortFilterProxyModel, self).__init__(*args, **kwargs)

        syntax = QtCore.QRegExp.PatternSyntax(QtCore.QRegExp.Wildcard)
        case_sensitivity = QtCore.Qt.CaseInsensitive

        self.setFilterRegExp(QtCore.QRegExp('', case_sensitivity, syntax))
        self.setFilterCaseSensitivity(case_sensitivity)

        self.filter_empty = False

    def filterAcceptsRow(self, row, parent):
        """Filters rows
        http://gaganpreet.in/blog/2013/07/04/qtreeview-and-custom-filter-models/
        https://qt-project.org/forums/viewthread/7782/#45740
        """

        # Filter out classes without and objects in them
        if self.filter_empty and parent.data():
            model = self.sourceModel()
            index = model.index(row, 1, parent)
            data = model.data(index)
            if data == '':
                return False

        # Check if the current row matches
        if self.filter_accepts_row_itself(row, parent):
            return True

        # Finally, check if any of the children match
        return self.has_accepted_children(row, parent)

    def filter_accepts_row_itself(self, row, parent):
        return super(TreeSortFilterProxyModel, self).filterAcceptsRow(row, parent)

    def has_accepted_children(self, row, parent):
        """Starting from the current node as root, traverse all the descendants and test if
        any of the children match
        """

        model = self.sourceModel()
        source_index = model.index(row, 0, parent)

        children_count = model.rowCount(source_index)
        for i in xrange(children_count):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False
