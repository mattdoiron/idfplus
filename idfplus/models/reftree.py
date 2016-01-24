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
            if data in ['Class', 'Field', 'Outgoing:', 'Incoming:', '']:
                return data
            if column == 1:
                return self.itemData[column].obj_class
            else:
                return self.itemData[column].value
        except IndexError:
            return None


class ReferenceTreeModel(CustomTreeModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def __init__(self, data, root, parent=None):
        super(ReferenceTreeModel, self).__init__(parent)
        self.rootItem = RefTreeItem(root)
        self.setupModelData(data, self.rootItem)

    def setupModelData(self, data, parent):
        if data:
            if data[0]:
                ancestor_root = RefTreeItem(('Incoming:',''), parent)
                parent.appendChild(ancestor_root)
                for item in data[0]:
                    tree_data = (item._outer[0], item)
                    ancestor_root.appendChild(RefTreeItem(tree_data, ancestor_root))
            if data[1]:
                descendant_root = RefTreeItem(('Outgoing:',''), parent)
                parent.appendChild(descendant_root)
                for item in data[1]:
                    # tree_data = (str(item._outer[0].value), item.obj_class)
                    tree_data = (item._outer[0], item)
                    descendant_root.appendChild(RefTreeItem(tree_data, descendant_root))

    def get_field(self, index):
        if index.isValid():
            return index.internalPointer().item()[1]
        else:
            return None
