#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Classes that manage the reference tree

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# Package imports
from .basetree import BaseTreeItem
from .basetree import CustomTreeModel


class RefTreeItem(BaseTreeItem):
    """Low level item for a custom reference tree view
    """

    def data(self, column):
        """Returns data for specified column in specialized reference tree

        :type column: int
        :return:
        """

        data = self.itemData[column]
        try:
            if data in ['Object', 'Class', '']:
                return data
            if column == 1:
                return self.itemData[column].obj_class_display
            else:
                return self.itemData[1]._outer[0].value or self.itemData[1].value
        except IndexError:
            return None


class ReferenceTreeModel(CustomTreeModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def __init__(self, data, parent=None):
        super(ReferenceTreeModel, self).__init__(parent)
        self.rootItem = RefTreeItem(("Object", "Class"))
        self.setupModelData(data, self.rootItem)

    def setupModelData(self, data, parent):
        if data:
            for item in data:
                tree_item = RefTreeItem((item.uuid, item))
                parent.appendChild(tree_item)

    @staticmethod
    def field_uuid(index):
        if index.isValid():
            return index.internalPointer().item()[0]
        else:
            return None
