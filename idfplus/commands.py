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
import sys
import transaction

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import idfsettings as c
from . import logger

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class ObjectCmd(QtGui.QUndoCommand):
    """Base class to be inherited by all classes needing QUndoCommand features"""

    def __init__(self, main_window, **kwargs):
        super(ObjectCmd, self).__init__()
        self.selectedIndexes = main_window.classTable.selectedIndexes()
        self.indexes = None
        self.cols_rows = [(index.row(), index.column()) for index in self.selectedIndexes]
        self.main_window = main_window
        obj_class_index = main_window.classTree.selectedIndexes()[0]
        self.obj_class_index = QtCore.QPersistentModelIndex(obj_class_index)
        self.obj_class = main_window.current_obj_class
        self.obj_orientation = main_window.obj_orientation
        self.tx_id = None
        self.mime_data = None
        self.new_objects = None
        self.copied_objects = None
        self.from_clipboard = kwargs.get('from_clipboard', False)
        self.from_selection = kwargs.get('from_selection', False)
        self.value = kwargs.get('value', None)
        self.old_value = None
        self.model = None

    def set_model(self):

        # Make sure the table view is updated so we grab the right model
        if self.main_window.current_obj_class != self.obj_class:
            self.main_window.load_table_view(self.obj_class)
            self.main_window.classTree.setCurrentIndex(self.obj_class_index)

        # Get the table's model
        self.model = self.main_window.classTable.model().sourceModel()


class NewObjectCmd(ObjectCmd):

    def undo(self, *args, **kwargs):

        super(NewObjectCmd, self).set_model()

        # Make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            row_offset = 0
            col_offset = 1
        else:
            row_offset = 1
            col_offset = 0

        # Recreate the index for the possibly new model
        index = self.model.index(self.cols_rows[0][0] + row_offset,
                                 self.cols_rows[0][1] + col_offset,
                                 QtCore.QModelIndex())

        # Get the table's model and call its remove method
        self.model.removeObjects(index, 1)

    def redo(self, from_clipboard=False, *args, **kwargs):

        super(NewObjectCmd, self).set_model()

        self.setText('Create object')

        # Define which (if any) new objects to insert
        if self.new_objects is None:
            new_objects = None
            if self.from_clipboard is True:
                if not self.copied_objects:
                    self.copied_objects = self.main_window.obj_clipboard
                new_objects = self.copied_objects
            elif self.from_selection is True:
                if not self.copied_objects:
                    if not self.main_window.copyObject():
                        return False
                    self.copied_objects = self.main_window.obj_clipboard
                new_objects = self.copied_objects

            # Save the new objects for later use by undo
            self.new_objects = new_objects
            self.delete_count = len(new_objects or [])

        # Define the index at which the objects will be inserted
        if len(self.selectedIndexes) <= 0:
            index = QtCore.QModelIndex()
        else:
            # Recreate the index for the possibly new model
            index = self.model.index(self.cols_rows[0][0], self.cols_rows[0][1],
                                     QtCore.QModelIndex())
        self.index_to_delete = index

        # Call the table's insert method
        self.model.insertObjects(index, self.new_objects)


class PasteSelectedCmd(ObjectCmd):

    def redo(self, *args, **kwargs):
        """Pastes clipboard into cells starting at selected cell."""

        super(PasteSelectedCmd, self).set_model()

        self.setText('Paste data')

        # Get the currently-selected indexes and proceed only if there are any
        if len(self.selectedIndexes) <= 0:
            return False

        # Find the selected cell at which to start pasting
        start_col = self.selectedIndexes[0].column()
        start_row = self.selectedIndexes[0].row()

        # Get clipboard data if it's text, but only once (the first time)
        if not self.mime_data:
            self.mime_data = self.main_window.clipboard.mimeData()
        if self.mime_data.hasText():
            raw_text = self.mime_data.text()
        else:
            return False

        # Iterate through text, splitting into rows
        rows = raw_text.split('\n')
        for i, row in enumerate(rows[:-1]):
            values = row.split('\t')
            for j, value in enumerate(values):

                # Save value and rows to data model
                index = self.model.index(start_row + i,
                                    start_col + j,
                                    QtCore.QModelIndex())
                self.model.setData(index, value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], index)


class DeleteObjectCmd(ObjectCmd):

    def redo(self, *args, **kwargs):

        super(DeleteObjectCmd, self).set_model()

        self.setText('Delete object')

        # Get the currently-selected indexes and proceed only if there are any
        if len(self.selectedIndexes) <= 0:
            return False

        # Make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in self.selectedIndexes])
        else:
            index_set = set([index.row() for index in self.selectedIndexes])
        self.delete_count = len(list(index_set))

        # Recreate the index for the possibly new model
        index = self.model.index(self.cols_rows[0][0], self.cols_rows[0][1],
                                 QtCore.QModelIndex())

        # Get the table's model and call its remove method
        self.model.removeObjects(index, self.delete_count)


class ModifyObjectCmd(ObjectCmd):

    def undo(self):
        super(ModifyObjectCmd, self).set_model()

        # Recreate the index for the possibly new model
        index = self.model.index(self.cols_rows[0][0], self.cols_rows[0][1],
                            QtCore.QModelIndex())

        # Call the setData method to change the values
        self.model.setData(index, self.old_value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(index, index)

    def redo(self, *args, **kwargs):

        super(ModifyObjectCmd, self).set_model()

        self.setText('Modify object')

        # Recreate the index for the possibly new model
        index = self.model.index(self.cols_rows[0][0], self.cols_rows[0][1],
                                 QtCore.QModelIndex())

        # Store the old value for use by undo
        self.old_value = self.model.data(index, QtCore.Qt.DisplayRole)

        # Call the setData method to change the values
        self.model.setData(index, self.value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(index, index)
