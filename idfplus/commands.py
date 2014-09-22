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
# import sys
# import transaction

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
        self.indexes = main_window.classTable.selectedIndexes()
        self.index_list = [(index.row(), index.column()) for index in self.selectedIndexes]
        self.main_window = main_window
        obj_class_index = main_window.classTree.selectedIndexes()[0]
        self.obj_class_index = QtCore.QPersistentModelIndex(obj_class_index)
        self.obj_class = main_window.current_obj_class
        self.obj_orientation = main_window.obj_orientation
        self.tx_id = None
        self.mime_data = None
        self.new_objects = None
        self.old_objects = None
        self.copied_objects = None
        self.from_clipboard = kwargs.get('from_clipboard', False)
        self.from_selection = kwargs.get('from_selection', False)
        self.value = kwargs.get('value', None)
        self.old_value = None
        self.model = self.main_window.classTable.model().sourceModel()

    def update_model(self):

        # Make sure the table view is updated so we grab the right model
        if self.main_window.current_obj_class != self.obj_class:
            self.main_window.load_table_view(self.obj_class)
            self.main_window.classTree.setCurrentIndex(self.obj_class_index)

            # Get the new table's model
            self.model = self.main_window.classTable.model().sourceModel()

            # Recreate the index for the new model
            self.indexes = []
            for i in self.index_list:
                self.indexes.append(self.model.index(i[0], i[1], QtCore.QModelIndex()))


class NewObjectCmd(ObjectCmd):
    """Class that handles creating new objects, and undo of that creation."""

    def undo(self, *args, **kwargs):
        self.update_model()

        # Define the offset from the index to delete
        if self.main_window.obj_orientation == QtCore.Qt.Vertical:
            row_offset = 0
            col_offset = 1
        else:
            row_offset = 1
            col_offset = 0

        # Recreate index for new model, but with an offset, or use the last row
        if self.index_to_delete.row() == -1:
            index = self.index_to_delete
        else:
            index = self.model.createIndex(self.index_list[-1][0] + row_offset,
                                           self.index_list[-1][1] + col_offset)

        # Find the top and bottom corners of the selection in the new model
        top_left = self.model.createIndex(self.index_list[0][0],
                                          self.index_list[0][1])
        bottom_right = self.model.createIndex(self.index_list[-1][0],
                                              self.index_list[-1][1])

        # Get the table's model and call its remove method
        self.model.removeObjects(index, self.delete_count)

        # Reselect the previously deleted range
        selection = QtGui.QItemSelection(top_left, bottom_right)
        selection_model = self.main_window.classTable.selectionModel()
        selection_model.reset()
        selection_model.select(selection, QtGui.QItemSelectionModel.SelectCurrent)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(top_left, bottom_right)
        self.main_window.classTree.expandAll()

    def redo(self, from_clipboard=False, *args, **kwargs):
        self.update_model()

        # Set a name for the undo/redo action
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
            self.delete_count = len(new_objects or [0])

        # Define the index at which the objects will be inserted, deleted
        if not self.indexes:
            index = QtCore.QModelIndex()
        else:
            index = self.indexes[-1]
        self.index_to_delete = self.indexes[0]

        # Call the table's insert method
        self.model.insertObjects(index, self.new_objects)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(index, index)
        self.main_window.classTree.expandAll()


class PasteSelectedCmd(ObjectCmd):
    """Pastes clipboard into cells starting at selected cell."""

    def undo(self):
        self.update_model()

        # insert rest here
        index = None
        value = None

        # Replace the data
        self.model.setData(index, value)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], index)


    def redo(self, *args, **kwargs):
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Paste data')

        # Get the currently-selected indexes and proceed only if there are any
        if len(self.indexes) <= 0:
            return False

        # Find the selected cell at which to start pasting
        start_col = self.indexes[0].column()
        start_row = self.indexes[0].row()

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

                # Save the data about to be replaced for undo
                saved_value = self.model.data(index, value)
                self.old_objects = []
                self.old_objects.append((start_row + i,
                                         start_col + j,
                                         saved_value))

                # Replace the data
                self.model.setData(index, value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], index)


class DeleteObjectCmd(ObjectCmd):
    """Class that handles deleting objects, and undo of that deletion."""

    def undo(self):
        self.update_model()

        # Define the offset from the index to delete
        if self.main_window.obj_orientation == QtCore.Qt.Vertical:
            row_offset = 0
            col_offset = -1
        else:
            row_offset = -1
            col_offset = 0

        # Recreate index for new model, but with an offset, or use the last row
        index = self.model.createIndex(self.index_list[0][0] + row_offset,
                                       self.index_list[0][1] + col_offset)

        # Find the top and bottom corners of the selection in the new model
        top_left = self.model.createIndex(self.index_list[0][0],
                                          self.index_list[0][1])
        bottom_right = self.model.createIndex(self.index_list[-1][0],
                                              self.index_list[-1][1])

        # Call the table's insert method
        self.model.insertObjects(index, self.old_objects)

        # Reselect the previously deleted range
        selection = QtGui.QItemSelection(top_left, bottom_right)
        selection_model = self.main_window.classTable.selectionModel()
        selection_model.reset()
        selection_model.select(selection, QtGui.QItemSelectionModel.SelectCurrent)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(index, index)
        self.main_window.classTree.expandAll()

    def redo(self, *args, **kwargs):
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Delete object')

        # Make a copy of the object(s) about to be deleted (only once)
        if self.old_objects is None:
            self.old_objects = self.main_window.copyObject(save=False)

        # Make a set to find unique columns/rows - use to find number to be deleted
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in self.indexes])
        else:
            index_set = set([index.row() for index in self.indexes])
        self.delete_count = len(list(index_set))

        # Get the table's model and call its remove method
        self.model.removeObjects(self.indexes[0], self.delete_count)

        # Find the top and bottom corners of the selection in the new model
        top_left = self.model.createIndex(self.index_list[0][0],
                                          self.index_list[0][1])
        bottom_right = self.model.createIndex(self.index_list[-1][0],
                                              self.index_list[-1][1])

        # Clear any current selection
        selection_model = self.main_window.classTable.selectionModel()
        selection_model.reset()

        # Notify everyone that data has changed
        self.model.dataChanged.emit(top_left, bottom_right)
        self.main_window.classTree.expandAll()


class ModifyObjectCmd(ObjectCmd):
    """Class that handles modifying a single field value, and undo of that change."""

    def undo(self):
        self.update_model()

        # Call the setData method to change the values
        self.model.setData(self.indexes[0], self.old_value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], self.indexes[0])

    def redo(self, *args, **kwargs):
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Modify object')

        # Store the old value for use by undo
        self.old_value = self.model.data(self.indexes[0], QtCore.Qt.DisplayRole)

        # Call the setData method to change the values
        self.model.setData(self.indexes[0], self.value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], self.indexes[0])
