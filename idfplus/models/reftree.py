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
