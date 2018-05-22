#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Classes that manage the class tree

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
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

    def __init__(self, idf, parent=None, hide_groups=True):
        super(ObjectClassTreeModel, self).__init__(parent)
        self.rootItem = TreeItem(("Object Class", "#"))
        self.show_groups = not hide_groups
        self.setupModelData(idf, self.rootItem)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        item = index.internalPointer()
        if item.data(0) == '' and item.data(1) == '':
            data = QtCore.Qt.NoItemFlags
        elif item.parent().data(0) == 'Object Class' and item.data(0) != '' and self.show_groups:
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
            if item.parent().data(0) == 'Object Class' and item.data(0) != '' and self.show_groups:
                data = QtGui.QColor(205, 192, 176)  # light grey for group headers
        elif role == QtCore.Qt.TextAlignmentRole and index.column() == 1:
            data = QtCore.Qt.AlignRight

        return data

    def setupModelData(self, idf, parent):
        if self.show_groups:
            group = ''
            for obj_class, obj in idf.idd.iteritems():
                if group != obj.group:
                    group = obj.group
                    group_root = TreeItem((group, ''), parent)
                    parent.appendChild(group_root)
                objs = idf.get(obj_class, None)
                child = TreeItem((obj.obj_class_display, objs), group_root)
                group_root.appendChild(child)
        else:
            for obj_class, obj in idf.idd.iteritems():
                objs = idf.get(obj.obj_class_display, None)
                child = TreeItem((obj.obj_class, objs), parent)
                parent.appendChild(child)

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
        self.hide_empty_classes = kwargs.pop('hide_empty_classes', False)
        self.show_groups = not kwargs.pop('hide_groups', True)
        super(TreeSortFilterProxyModel, self).__init__(*args, **kwargs)

        syntax = QtCore.QRegExp.PatternSyntax(QtCore.QRegExp.Wildcard)
        case_sensitivity = QtCore.Qt.CaseInsensitive

        self.setFilterRegExp(QtCore.QRegExp('', case_sensitivity, syntax))
        self.setFilterCaseSensitivity(case_sensitivity)

    def filterAcceptsRow(self, row, parent):
        """Filters rows
        http://gaganpreet.in/blog/2013/07/04/qtreeview-and-custom-filter-models/
        https://qt-project.org/forums/viewthread/7782/#45740
        """

        # Filter out classes without objects in them
        if self.hide_empty_classes:
            model = self.sourceModel()
            index = model.index(row, 1, parent)
            data = model.data(index)

            if not self.show_groups and not parent.data():
                if data == '':
                    return False

            if parent.data():
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
