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
    #TODO: Move this an all commands to a module

    def __init__(self, parent, **kwargs):
        super(ObjectCmd, self).__init__(**kwargs)
        self.index = kwargs.get('index', False)
        self.indexes = parent.classTable.selectedIndexes()
        self.parent = parent
        self.obj_orientation = self.parent.obj_orientation
        self.tx_id = None
        self.mime_data = None
        self.copied_objects = None
        self.from_clipboard = kwargs.get('from_clipboard', False)
        self.from_selection = kwargs.get('from_selection', False)
        self.value = kwargs.get('value', False)

    def undo(self, *args, **kwargs):
        # Call the undo function
        self.parent.db.db.undo(self.tx_id)
        transaction.commit()

        # Let the table model know that something has changed. For now, the whole
        # table must be reloaded because undo could do any number of things, all which
        # need different update operations (like insert rows, remove columns, etc).
        self.parent.load_table_view(self.parent.current_obj_class)

    def redo(self, *args, **kwargs):
        # At this point there was a transaction completed. Save it's id for later undos
        no_initial = lambda tx: True if tx['description'] not in ['initial database creation','Load file'] else False
        undo_log = self.parent.db.db.undoLog(0, sys.maxint, no_initial)
        self.tx_id = undo_log[0]['id']


class NewObjectCmd(ObjectCmd):
    #TODO: Change from insertColumns/Rows to insertObject in IDFFile class?

    def redo(self, from_clipboard=False, *args, **kwargs):
        self.setText('Create object')

        # Define which (if any) new objects to insert
        new_objects = None
        if self.from_clipboard is True:
            if not self.copied_objects:
                self.copied_objects = self.parent.obj_clipboard
            new_objects = self.copied_objects
        elif self.from_selection is True:
            if not self.copied_objects:
                if not self.parent.copyObject():
                    return False
                self.copied_objects = self.parent.obj_clipboard
            new_objects = self.copied_objects


        # Detect orientation, then make a set to find unique columns/rows
        #TODO: Shouldn't need to detect orientation this way. Proxy model should do that.
        if self.obj_orientation == QtCore.Qt.Vertical:
            index_set = set([index.column() for index in self.indexes])
            index_list = list(index_set)
            model = self.parent.classTable.model().sourceModel()

            # Define the position into which the objects will be inserted
            if len(self.indexes) <= 0:
                # No selection, so add to end of object list
                position = model.columnCount(QtCore.QModelIndex())
            else:
                # Selection made so insert at end of selection
                position = index_list[-1] + 1

            # Call the model's insertColumns method
            model.insertColumns(position, new_objects)
        else:
            index_set = set([index.row() for index in self.indexes])
            index_list = list(index_set)
            model = self.parent.classTable.model()

            # Define the position into which the objects will be inserted
            if len(self.indexes) <= 0:
                position = model.rowCount(QtCore.QModelIndex())
            else:
                position = index_list[-1] + 1

            # Call the model's insertColumns method
            model.insertRows(position, new_objects)

        # Now commit the transaction
        transaction.commit()

        super(NewObjectCmd, self).redo(*args, **kwargs)


class PasteSelectedCmd(ObjectCmd):
    #FIXME this one is broken...pastes wrong
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
            self.mime_data = self.parent.clipboard.mimeData()
        if self.mime_data.hasText():
            raw_text = self.mime_data.text()
        else:
            return False

        # Iterate through text, splitting into rows
        table_model = self.parent.classTable.model()
        rows = raw_text.split('\n')
        for i, row in enumerate(rows[:-1]):
            cols = row.split('\t')
            for j, col in enumerate(cols):

                # Save cols and rows to data model
                index = table_model.index(start_row + i,
                                          start_col + j,
                                          QtCore.QModelIndex())
                table_model.setData(index, col, QtCore.Qt.EditRole)

        # Notify everyone that data has changed
        table_model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

        # Now commit the transaction
        transaction.commit()

        super(PasteSelectedCmd, self).redo(*args, **kwargs)

class DeleteObjectCmd(ObjectCmd):
    #TODO change from removeColumns/Rows to removeObject in IDFFile class?

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

        if self.obj_orientation == QtCore.Qt.Vertical:
            model = self.parent.classTable.model().sourceModel()
            position = self.indexes[0].column()
            model.removeColumns(position, count)
        else:
            model = self.parent.classTable.model()
            position = self.indexes[0].row()
            model.removeRows(position, count)

        # Now commit the transaction
        transaction.commit()

        super(DeleteObjectCmd, self).redo(*args, **kwargs)


class ModifyObjectCmd(ObjectCmd):

    def redo(self, *args, **kwargs):
        self.setText('Modify object')

        if self.obj_orientation == QtCore.Qt.Vertical:
            model = self.parent.classTable.model().sourceModel()
        else:
            model = self.parent.classTable.model()

        model.setData(self.index, self.value, QtCore.Qt.EditRole)

        # Now commit the transaction
        self.parent.dataChanged.emit(self.index, self.index)
        transaction.commit()

        super(ModifyObjectCmd, self).redo(*args, **kwargs)