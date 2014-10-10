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
        # self.selectedIndexes = main_window.classTable.selectedIndexes()
        self.indexes = main_window.classTable.selectedIndexes()
        # self.index_list = [(index.row(), index.column()) for index in self.selectedIndexes]
        self.main_window = main_window
        obj_class_index = main_window.classTree.selectedIndexes()[0]
        self.obj_class_index = QtCore.QPersistentModelIndex(obj_class_index)
        self.obj_class = main_window.current_obj_class
        self.obj_orientation = main_window.obj_orientation
        self.tx_id = None
        self.mime_data = None
        self.new_objects = None
        self.new_object_groups = None
        self.old_objects = None
        # self.copied_objects = None
        self.from_clipboard = kwargs.get('from_clipboard', False)
        self.from_selection = kwargs.get('from_selection', False)
        self.value = kwargs.get('value', None)
        self.old_value = None
        self.index_groups = []
        self.delete_count = 1
        self.model = self.main_window.classTable.model()
        self.selection_model = self.main_window.classTable.selectionModel()

        # Convert indexes to source indexes for storage, then convert back later
        indexes_source_partial = [self.model.mapToSource(ind)
                                  for ind in self.indexes]
        self.indexes_source = [self.model.sourceModel().mapToSource(ind)
                               for ind in indexes_source_partial]

    def update_model(self):

        # Make sure the table view is updated so we grab the right model
        if self.main_window.current_obj_class != self.obj_class:
            # self.main_window.load_table_view(self.obj_class)
            self.main_window.classTree.setCurrentIndex(self.obj_class_index)

            # Get the new table's model
            self.model = self.main_window.classTable.model()
            self.selection_model = self.main_window.classTable.selectionModel()

    def update_selection(self, single=None, offset=None):
        # self.selection_model.reset()
        # return

        # Ensure there is an offset
        if offset is None:
            offset = 0

        # Define what to select based on the single keyword
        if single is True:

            # Define the offset from the index to delete
            if self.main_window.obj_orientation == QtCore.Qt.Vertical:
                row_offset = 0
                col_offset = offset
            else:
                row_offset = offset
                col_offset = 0

            # Create a new selection index with an offset
            selection = self.model.index(self.indexes[-1].row() + row_offset,
                                         self.indexes[-1].column() + col_offset)

            # If the index is not valid, use a non-offset index
            if not selection.isValid():
                selection = self.indexes[-1]

                # If it's still not valid, don't select anything
                if not self.indexes[-1].isValid():
                    selection = None

            # print('single selection: {}, {}'.format(selection.row(), selection.column()))
        else:
            # Construct a selection from the saved indexes
            selection = QtGui.QItemSelection(self.indexes[0], self.indexes[-1])
            # print('range selection top: {}, {}'.format(self.indexes[0].row(), self.indexes[0].column()))
            # print('range selection bottom: {}, {}'.format(self.indexes[-1].row(), self.indexes[-1].column()))

        # Clear the selection model and reselect the appropriate indexes if necessary
        self.selection_model.reset()
        if selection:
            self.selection_model.select(selection,
                                        QtGui.QItemSelectionModel.SelectCurrent)

        # Hack to 'refresh' the class tree
        self.main_window.classTree.expandAll()

class NewObjectCmd(ObjectCmd):
    """Class that handles creating new objects, and undo of that creation."""

    def undo(self, *args, **kwargs):

        # Ensure that we have the right model available
        self.update_model()

        # Define the range to delete
        delete_range = self.indexes_source[-self.delete_count:]

        # Get the table's model and call its remove method
        self.model.removeObjects(delete_range, offset=1)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(delete_range[0], delete_range[-1])

        # Clear any current selection and select the next item
        if self.delete_count > 1:
            single = False
        else:
            single = True
        self.update_selection(single=single)

    def redo(self, *args, **kwargs):

        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Create object')

        # Define which (if any) new objects to insert
        if self.new_objects is None:
            if self.from_clipboard is True:
                # print('copying from clipboard')
                self.new_objects = self.main_window.obj_clipboard[1]
                # self.new_object_groups = self.main_window.obj_clipboard[0]
                self.new_object_groups = [[self.indexes_source[-1].row()]]
                self.delete_count = sum([len(i) for i in self.new_object_groups])
            elif self.from_selection is True:
                # print('copying from selection')
                if not self.main_window.copyObject():
                    return False
                self.new_objects = self.main_window.obj_clipboard[1]
                self.new_object_groups = self.main_window.obj_clipboard[0]
                self.delete_count = sum([len(i) for i in self.new_object_groups])
                # print('objects to insert: {}'.format(self.new_objects))
                # print('groups to insert: {}'.format(self.new_object_groups))
            else:
                # print('inserting blank object')
                if self.indexes_source:
                    self.new_object_groups = [[self.indexes_source[-1].row()]]
                else:
                    self.new_object_groups = None
                self.delete_count = 1

        # print('delete_count: {}'.format(self.delete_count))
        # Call the table's insert method
        self.model.insertObjects(self.new_object_groups, self.new_objects, offset=1)

        # Notify everyone that data has changed
        if self.indexes:
            self.model.dataChanged.emit(self.indexes[0], self.indexes[-1])
        else:
            self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

        # Clear any current selection and select the next item
        if self.delete_count > 1:
            single = False
        else:
            single = True
        self.update_selection(single=single, offset=1)


class PasteSelectedCmd(ObjectCmd):
    """Pastes clipboard into cells starting at selected cell."""

    def undo(self):

        # Ensure that we have the right model available
        self.update_model()

        # Create an index to represent the start of the replacement
        start_index = self.model.index(self.old_objects[0][0],
                                       self.old_objects[0][1])

        # Cycle through all the old objects
        for obj in self.old_objects:

            # Create an index from the saved values
            index = self.model.index(obj[0], obj[1])

            # Restore the old data
            self.model.setData(index, obj[2], QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(start_index, index)


    def redo(self, *args, **kwargs):

        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Paste data')

        # Get the currently-selected indexes and proceed only if there are any
        if not self.indexes:
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
        self.old_objects = []
        rows = raw_text.split('\n')
        for i, row in enumerate(rows[:-1]):
            values = row.split('\t')
            for j, value in enumerate(values):

                # Make an index for the data to be affected
                index = self.model.index(start_row + i, start_col + j)

                # Save the data about to be replaced (for undo)
                self.old_objects.append((start_row + i,
                                         start_col + j,
                                         index.data()))

                # Replace the data
                self.model.setData(index, value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], index)


class DeleteObjectCmd(ObjectCmd):
    """Class that handles deleting objects, and undo of that deletion."""

    def undo(self):
        # Ensure that we have the right model available
        self.update_model()

        # Call the model's insert method with the previously-saved groups and objects
        self.model.insertObjects(self.index_groups, self.old_objects)

        # Clear any current selection and select the next item
        self.update_selection()

    def redo(self, *args, **kwargs):
        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Delete object')

        # Make a copy of the object(s) about to be deleted (only once)
        if not self.old_objects:
            self.index_groups, self.old_objects = self.model.get_contiguous(self.indexes_source, False)

        # Delete the objects. Note that these indexes are source indexes only
        # They must have been converted already!
        self.model.removeObjects(self.indexes_source)

        # Clear any current selection and select the next item
        self.update_selection(single=True)


class ModifyObjectCmd(ObjectCmd):
    """Class that handles modifying a single field value, and undo of that change."""

    def undo(self):
        # Ensure that we have the right model available
        self.update_model()

        # Call the setData method to change the values
        self.model.setData(self.indexes[0], self.old_value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], self.indexes[0])

        # Clear any current selection and select the next item
        self.main_window.classTable.clearSelection()
        self.main_window.classTable.setCurrentIndex(self.indexes[0])


    def redo(self, *args, **kwargs):
        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Modify object')

        # Store the old value for use by undo
        self.old_value = self.model.data(self.indexes[0], QtCore.Qt.DisplayRole)

        # Call the setData method to change the values
        self.model.setData(self.indexes[0], self.value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], self.indexes[0])

        # Clear any current selection and select the next item
        self.main_window.classTable.clearSelection()
        self.main_window.classTable.setCurrentIndex(self.indexes[0])
