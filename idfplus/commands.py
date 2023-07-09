#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module to manage QtCommands

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging
from itertools import chain

# PySide6 imports
from PySide6.QtCore import (Qt, QPersistentModelIndex, QItemSelection, QItemSelectionRange,
                            QItemSelectionModel)
from PySide6.QtGui import QUndoCommand

# Setup logging
log = logging.getLogger(__name__)


class ObjectCmd(QUndoCommand):
    """Base class to be inherited by all classes needing QUndoCommand features
    """

    def __init__(self, main_window, *args, **kwargs):
        self.from_clipboard = kwargs.pop('from_clipboard', False)
        self.from_selection = kwargs.pop('from_selection', False)
        self.value = kwargs.pop('value', None)
        super(ObjectCmd, self).__init__(*args, **kwargs)

        # TODO many of these are not needed for all subclasses. Break them out into
        # separate init methods in each subclass
        self.indexes_in = main_window.classTable.selectedIndexes()
        # self.indexes = [QPersistentModelIndex(i) for i in self.indexes_in]
        self.indexes = self.indexes_in
        self.main_window = main_window
        obj_class_index = main_window.classTree.selectedIndexes()[0]
        self.obj_class_index = QPersistentModelIndex(obj_class_index)
        self.obj_class = main_window.current_obj_class
        self.obj_orientation = main_window.obj_orientation
        self.mime_data = None
        self.new_objects = None
        self.new_object_groups = None
        self.old_objects = None
        self.old_value = None
        self.index_groups = []
        self.delete_count = 1
        self.model = self.main_window.classTable.model()
        self.selection_model = self.main_window.classTable.selectionModel()

        # Convert indexes to source indexes for storage, then convert back later
        indexes_source_partial = [self.model.mapToSource(ind)
                                  for ind in self.indexes_in]
        self.indexes_source = [self.model.sourceModel().mapToSource(ind)
                               for ind in indexes_source_partial]

        # Convert selection to source indexes for storage, then convert back later
        self.selection_saved = []
        for sel in self.selection_model.selection():
            self.selection_saved.append((sel.topLeft(), sel.bottomRight()))

    def update_model(self):
        """Ensures that the model is up-to-date and changes it if not.
        """

        # Make sure the table view is updated so we grab the right model
        if self.main_window.current_obj_class != self.obj_class:
            self.main_window.classTree.setCurrentIndex(self.obj_class_index)

        # Get the new table's model (even if there is no need to change obj_class!)
        # Sometimes the model changes for other reasons (transposed or now).
        self.model = self.main_window.classTable.model()
        self.selection_model = self.main_window.classTable.selectionModel()

    def update_selection(self, highlight_size=None, offset=None):
        """Ensures that the selection is up-to-date and changes it if not.

        :param highlight_size:
        :param offset:
        """

        # Use stored selection to reconstruct indexes for the current model.
        selection = QItemSelection()
        for sel in self.selection_saved:
            if self.obj_orientation == self.main_window.obj_orientation:
                top_left = self.model.index(sel[0].row(), sel[0].column())
                bottom_right = self.model.index(sel[1].row(), sel[1].column())
            else:
                top_left = self.model.index(sel[0].column(), sel[0].row())
                bottom_right = self.model.index(sel[1].column(), sel[1].row())

            sel_range = QItemSelectionRange(top_left, bottom_right)
            selection.append(sel_range)

        if not selection:
            col_count = self.model.columnCount(self.model.index(0, 0))
            row_count = self.model.rowCount(self.model.index(0, 0))
            # print(row_count, col_count)
            if self.obj_orientation == self.main_window.obj_orientation:
                top_left = self.model.index(0, col_count-1)
                bottom_right = self.model.index(row_count-1, col_count-1)
                # print('using 1')
            else:
                top_left = self.model.index(0, row_count-1)
                bottom_right = self.model.index(row_count-1, col_count-1)
                # print('using 2')
            # print('1 br: {},{}'.format(bottom_right.row(), bottom_right.column()))
            sel_range = QItemSelectionRange(top_left, bottom_right)
            selection.append(sel_range)

        last_sel = selection[-1]
        selection_new = QItemSelection()

        if not self.selection_saved:
            self.selection_saved.append((last_sel.topLeft(), last_sel.bottomRight()))

        # Define the offset and range
        if self.main_window.obj_orientation == Qt.Vertical:
            row_offset = 0
            col_offset = 0 if not offset else selection[-1].width()
            range_size = selection[-1].width()
        else:
            row_offset = 0 if not offset else selection[-1].height()
            col_offset = 0
            range_size = selection[-1].height()

        if highlight_size is None:
            highlight_size = range_size

        # Construct the selection range indexes for the current model
        if self.main_window.obj_orientation == Qt.Vertical:
            top_left = self.model.index(last_sel.top() + row_offset,
                                        last_sel.left() + col_offset)
            bottom_right = self.model.index(last_sel.bottom() + row_offset,
                                            last_sel.left() + highlight_size - 1
                                            + col_offset)
        else:
            top_left = self.model.index(last_sel.top() + row_offset,
                                        last_sel.left() + col_offset)
            bottom_right = self.model.index(last_sel.top() + highlight_size - 1
                                            + row_offset,
                                            last_sel.right() + col_offset)

        # Check for a selection range that extends beyond the size of the current model
        if not bottom_right.isValid():
            sel = self.selection_saved[-1]
            if self.obj_orientation == Qt.Vertical and \
               self.obj_orientation == self.main_window.obj_orientation:
                count = self.model.columnCount(top_left)
                bottom_right = self.model.index(sel[1].row() + row_offset,
                                                count - 1 + col_offset)
                # print('1 br: {},{}'.format(bottom_right.row(), bottom_right.column()))
            elif self.obj_orientation == Qt.Vertical and \
                 self.obj_orientation != self.main_window.obj_orientation:
                count = self.model.rowCount(top_left)
                bottom_right = self.model.index(count - 1 + row_offset,
                                                sel[1].row() + col_offset)
                # print('2 br: {},{}'.format(bottom_right.row(), bottom_right.column()))
            elif self.obj_orientation == Qt.Horizontal and \
                 self.obj_orientation == self.main_window.obj_orientation:
                count = self.model.rowCount(top_left)
                bottom_right = self.model.index(count - 1 + row_offset,
                                                sel[1].column() + col_offset)
                # print('3 br: {},{}'.format(bottom_right.row(), bottom_right.column()))
            elif self.obj_orientation == Qt.Horizontal and \
                 self.obj_orientation != self.main_window.obj_orientation:
                count = self.model.columnCount(top_left)
                bottom_right = self.model.index(sel[1].column() + row_offset,
                                                count - 1 + col_offset)
                # print('4 br: {},{}'.format(bottom_right.row(), bottom_right.column()))

        # Create the selection range and append it to the new selection
        sel_range = QItemSelectionRange(top_left, bottom_right)
        selection_new.append(sel_range)

        # Clear the selection model and reselect the appropriate indexes if necessary
        self.selection_model.reset()
        self.selection_model.select(selection_new,
                                    QItemSelectionModel.SelectCurrent)
        self.main_window.classTable.setFocus()

        # Hack to 'refresh' the class tree
        self.main_window.classTree.expandAll()


class NewObjectCmd(ObjectCmd):
    """Class that handles creating new objects and undoing that creation.
    """

    def undo(self):
        """Undo action for inserting new objects."""

        # Ensure that we have the right model available
        self.update_model()

        # Define the range to delete in the form [[<flattened list here>]]
        flat_groups = [list(set(chain.from_iterable(self.new_object_groups)))]
        delete_range = [flat_groups[0][-self.delete_count:]]

        # Get the table's model and call its remove method
        self.model.removeObjects(delete_range, offset=1, delete_count=self.delete_count)

        # Update the selection
        self.update_selection()

    def redo(self):
        """Redo action for inserting new objects.
        """

        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Create object')

        # Define which (if any) new objects to insert
        if self.new_objects is None:

            # Objects come from the clipboard
            if self.from_clipboard is True:
                self.new_objects = self.main_window.obj_clipboard[1]
                if self.indexes_source:
                    self.new_object_groups = [[self.indexes_source[-1].row()]]
                else:
                    self.new_object_groups = []

                # Flatten the provided object list (no need for groups here)
                flat_objs = [list(chain.from_iterable(self.new_objects))]
                self.new_objects = flat_objs
                self.delete_count = len(flat_objs[0])

            # Objects come from the current selection
            elif self.from_selection is True:
                if not self.main_window.copyObject():
                    return False
                self.new_objects = self.main_window.obj_clipboard[1]
                self.new_object_groups = self.main_window.obj_clipboard[0]
                self.delete_count = sum([len(i) for i in self.new_object_groups])

                # Flatten the provided groups (no need for groups here)
                flat_groups = [list(set(chain.from_iterable(self.new_object_groups)))]
                flat_objs = [list(chain.from_iterable(self.new_objects))]
                self.new_object_groups = flat_groups
                self.new_objects = flat_objs

            # Blank object to be inserted
            else:
                if self.indexes_source:
                    self.new_object_groups = [[self.indexes_source[-1].row()]]
                else:
                    self.new_object_groups = []
                self.delete_count = 1
                # single = True

        # Call the table's insert method
        self.model.insertObjects(self.new_object_groups, self.new_objects, offset=1)

        # Update the selection
        self.update_selection(highlight_size=self.delete_count, offset=True)
        self.main_window.set_dirty(True)


class PasteSelectedCmd(ObjectCmd):
    """Class to paste a group of values into cells and undo that paste.
    """

    def undo(self):
        """Undo action for pasting values into cells.
        """

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
            self.model.setData(index, obj[2], Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(start_index, index)

    def redo(self):
        """Redo action for pasting values into cells.
        """

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

        if not rows:
            return

        for i, row in enumerate(rows[:-1]):
            values = row.split(',')
            for j, value in enumerate(values):

                # Make an index for the data to be affected
                index = self.model.index(start_row + i, start_col + j)

                # Save the data about to be replaced (for undo) as a tuple
                self.old_objects.append((start_row + i, start_col + j,
                                         index.data(Qt.EditRole) or ''))

                # Replace the data
                self.model.setData(index, value, Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(self.indexes[0], index)
        self.main_window.set_dirty(True)


class DeleteObjectCmd(ObjectCmd):
    """Class that handles deleting objects and undo of that deletion.
    """

    def undo(self):
        """Undo action for deleting objects.
        """

        # Ensure that we have the right model available
        self.update_model()

        # Call the model's insert method with the previously-saved groups and objects
        self.model.insertObjects(self.index_groups, self.old_objects)

        # Clear any current selection and select the next item
        self.update_selection()

    def redo(self):
        """Redo action for deleting objects.
        """

        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Delete object')

        # Make a copy of the object(s) about to be deleted (only once)
        if not self.old_objects:
            (self.index_groups,
             self.old_objects) = self.model.contiguous(self.indexes_source, False,
                                                       duplicates=False)

        # Delete the objects. Note that these indexes are source indexes only
        # They must have been converted already!
        self.model.removeObjects(self.indexes_source)

        # Clear any current selection and select the next item
        self.update_selection(highlight_size=1, offset=0)
        self.main_window.set_dirty(True)


class ModifyObjectCmd(ObjectCmd):
    """Class that handles modifying a single field value and undo of that change.
    """

    def undo(self):
        """Undo action for modifying individual object values."""

        # Ensure that we have the right model available
        self.update_model()

        # Use stored source indexes to reconstruct indexes for the current model.
        # Must do this on-the-fly due to the possibility that any layer of model
        # has changed significantly.
        indexes_partial = [self.model.sourceModel().mapFromSource(ind)
                           for ind in self.indexes_source]
        indexes = [self.model.mapFromSource(ind)
                   for ind in indexes_partial]

        # Call the setData method to change the values
        self.model.setData(indexes[0], self.old_value, Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(indexes[0], indexes[0])

        # Clear any current selection and select the next item
        self.main_window.classTable.clearSelection()
        self.main_window.classTable.setCurrentIndex(indexes[0])
        self.main_window.classTable.setFocus()

    def redo(self):
        """Redo action for modifying individual object values.
        """

        # Ensure that we have the right model available
        self.update_model()

        # Set a name for the undo/redo action
        self.setText('Modify object')

        # Use stored source indexes to reconstruct indexes for the current model.
        # Must do this on-the-fly due to the possibility that any layer of model
        # has changed significantly.
        indexes_partial = [self.model.sourceModel().mapFromSource(ind)
                           for ind in self.indexes_source]
        indexes = [self.model.mapFromSource(ind)
                   for ind in indexes_partial]

        # Store the old value for use by undo (only once)
        if self.old_value is None:
            self.old_value = self.model.data(indexes[0], Qt.EditRole) or ''

        # Call the setData method to change the values
        self.model.setData(indexes[0], self.value, Qt.EditRole)

        # Notify everyone that data has changed
        self.model.dataChanged.emit(indexes[0], indexes[0])

        # Clear any current selection and select the next item
        self.main_window.classTable.clearSelection()
        self.main_window.classTable.setCurrentIndex(indexes[0])
        self.main_window.classTable.setFocus()
        self.main_window.set_dirty(True)


class EditCommentCmd(ObjectCmd):

    def __init__(self, main_window, text_editor, init_text, init_cursor, *args, **kwargs):
        super(EditCommentCmd, self).__init__(main_window, *args, **kwargs)
        self.text_editor = text_editor
        self.current_text = text_editor.toPlainText()
        self.current_cursor_pos = text_editor.textCursor().position()
        self.init_text = init_text
        self.init_cursor_pos = init_cursor

    def undo(self):
        """Undo action for editing a comment.
        """

        self.update_class_table()

        # Set the text for the editor and the underlying idf file
        self.set_comments(self.init_text)
        self.text_editor.setText(self.init_text)
        self.text_editor.init_text = self.text_editor.toPlainText()
        self.text_editor.setFocus(Qt.OtherFocusReason)
        cursor = self.text_editor.textCursor()
        cursor.setPosition(self.init_cursor_pos)
        self.text_editor.setTextCursor(cursor)
        self.text_editor.ensureCursorVisible()

    def redo(self):
        """Redo action for editing a comment.
        """

        self.setText('Edit Comments')
        self.update_class_table()
        self.main_window.set_dirty(True)

        # Set the text for the editor and the underlying idf file
        self.set_comments(self.current_text)
        self.text_editor.setText(self.current_text)
        self.text_editor.init_text = self.text_editor.toPlainText()
        self.text_editor.setFocus(Qt.OtherFocusReason)
        cursor = self.text_editor.textCursor()
        cursor.setPosition(self.current_cursor_pos)
        self.text_editor.setTextCursor(cursor)
        self.text_editor.ensureCursorVisible()

    def update_class_table(self):

        # Ensure that we have the right model available
        self.update_model()

        # Use stored source indexes to reconstruct indexes for the current model.
        # Must do this on-the-fly due to the possibility that any layer of model
        # has changed significantly.
        indexes_partial = [self.model.sourceModel().mapFromSource(ind)
                           for ind in self.indexes_source]
        indexes = [self.model.mapFromSource(ind)
                   for ind in indexes_partial]

        # Clear any current selection and select the next item
        self.main_window.classTable.clearSelection()
        self.main_window.classTable.setCurrentIndex(indexes[0])

    def set_comments(self, comments):

        sel = self.main_window.classTable.selectionModel().selection()
        if not sel:
            return
        first = sel.first().topLeft()
        if self.obj_orientation == Qt.Horizontal:
            ind = first.row()
        else:
            ind = first.column()

        comment_list = comments.splitlines(True)
        self.main_window.idf[self.obj_class][ind].comments = comment_list
