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

# System imports
# import transaction
# from persistent.list import PersistentList

# PySide imports
# from PySide import QtGui
from PySide import QtCore

# # Package imports
# from .datamodel import (IDFObject, IDFField)


class JumpTreeModel(QtCore.QAbstractItemModel):
    """Qt object that handles interaction between the jump widget and the data
    displayed in the tree view.
    """

    def __init__(self, jump_tree):
        if jump_tree is None:
            self.jump_tree = []
        else:
            self.jump_tree = jump_tree
        super(JumpTreeModel, self).__init__()

    def data(self, index, role):
        """Provides various data to TreeView models. Trees iterate through
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
                data = self.jump_tree[row][column]
            except (AttributeError, IndexError):
                data = None
        return data

    # def headerData(self, section, orientation, role, old_orientation=None):
    #     if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
    #         return self.field_labels[section]
    #     return None

    def rowCount(self, index):
        return len(self.jump_tree)

    def columnCount(self, index):
        return 1
