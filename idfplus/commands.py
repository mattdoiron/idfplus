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
        self.indexes = main_window.classTable.selectedIndexes()
        self.main_window = main_window
        self.obj_class = main_window.current_obj_class
        self.obj_orientation = main_window.obj_orientation
        self.tx_id = None
        self.mime_data = None
        self.copied_objects = None
        self.from_clipboard = kwargs.get('from_clipboard', False)
        self.from_selection = kwargs.get('from_selection', False)
        self.value = kwargs.get('value', None)

    def undo(self, *args, **kwargs):
        # Call the undo function
        self.main_window.db.db.undo(self.tx_id)
        transaction.commit()

        # Let the table model know that something has changed. For now, the whole
        # table must be reloaded because undo could do any number of things, all which
        # need different update operations (like insert rows, remove columns, etc).
        self.main_window.load_table_view(self.obj_class)

    def redo(self, *args, **kwargs):
        # At this point there was a transaction completed. Save it's id for later undos
        no_initial = lambda tx: True if tx['description'] not in ['initial database creation','Load file'] else False
        undo_log = self.main_window.db.db.undoLog(0, sys.maxint, no_initial)
        self.tx_id = undo_log[0]['id']


class NewObjectCmd(ObjectCmd):

    def redo(self, from_clipboard=False, *args, **kwargs):
        self.setText('Create object')

        # Define which (if any) new objects to insert
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

        # Define the index at which the objects will be inserted
        if len(self.indexes) <= 0:
            index = QtCore.QModelIndex()
        else:
            index = self.indexes[0]

        # Get the table's model and call its insert method
        model = self.main_window.classTable.model().sourceModel()
        model.insertObjects(index, new_objects)

        # Now commit the transaction
        # transaction.commit()

        super(NewObjectCmd, self).redo(*args, **kwargs)


class PasteSelectedCmd(ObjectCmd):

    def redo(self, *args, **kwargs):
        """Pastes clipboard into cells starting at selected cell."""
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
        model = self.main_window.classTable.model().sourceModel()
        rows = raw_text.split('\n')
        for i, row in enumerate(rows[:-1]):
            values = row.split('\t')
            for j, value in enumerate(values):

                # Save value and rows to data model
                index = model.index(start_row + i,
                                    start_col + j,
                                    QtCore.QModelIndex())
                model.setData(index, value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        model.dataChanged.emit(self.indexes[0], index)

        # Now commit the transaction
        # transaction.commit()

        super(PasteSelectedCmd, self).redo(*args, **kwargs)

class DeleteObjectCmd(ObjectCmd):

    def redo(self, *args, **kwargs):
        self.setText('Delete object')

        # Get the currently-selected indexes and proceed only if there are any
        if len(self.indexes) <= 0:
            return False

        # Make a set to find unique columns/rows
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in self.indexes])
        else:
            index_set = set([index.row() for index in self.indexes])
        count = len(list(index_set))

        # Get the table's model and call its remove method
        model = self.main_window.classTable.model().sourceModel()
        model.removeObjects(self.indexes[0], count)

        # Now commit the transaction
        # transaction.commit()

        super(DeleteObjectCmd, self).redo(*args, **kwargs)


class ModifyObjectCmd(ObjectCmd):

    def undo(self):
        # Get the table's model and call it's setData method
        model = self.main_window.classTable.model().sourceModel()
        model.setData(self.indexes[0], self.old_value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        model.dataChanged.emit(self.indexes[0], self.indexes[0])

    def redo(self, *args, **kwargs):
        self.setText('Modify object')

        # Get the table's model and call it's setData method
        model = self.main_window.classTable.model().sourceModel()
        self.old_value = model.data(self.indexes[0], QtCore.Qt.DisplayRole)
        model.setData(self.indexes[0], self.value, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        model.dataChanged.emit(self.indexes[0], self.indexes[0])

        # Now commit the transaction
        # transaction.commit()

        # super(ModifyObjectCmd, self).redo(*args, **kwargs)