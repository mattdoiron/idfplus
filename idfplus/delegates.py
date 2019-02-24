#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module to manage delegates for Qt table views

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging

# PySide2 imports
# from PySide2 import QtGui
# from PySide2 import QtCore
from PySide2.QtCore import Qt, QSize, QSortFilterProxyModel
from PySide2.QtGui import (QFontMetrics, QTextOption, QTextCursor, QFont, QStandardItem,
                           QStandardItemModel, QValidator)
from PySide2.QtWidgets import (QStyledItemDelegate, QFrame, QAbstractItemView, QTableView,
                               QComboBox, QCompleter, QPlainTextEdit, QAbstractItemDelegate)

# Package imports
from . import commands

# Setup logging
log = logging.getLogger(__name__)


class GenericDelegate(QStyledItemDelegate):
    """Template delegate for the table view.
    """

    def __init__(self, main_window, idd_objects, obj_orientation):
        super(GenericDelegate, self).__init__(main_window)
        self.delegates = dict()
        self.main_window = main_window
        self.obj_orientation = obj_orientation
        self.assignDelegates(idd_objects)
        self.prefs = main_window.prefs

    def insertDelegate(self, index, delegate):
        """

        :param index:
        :param delegate:
        """

        delegate.setParent(self)
        self.delegates[index] = delegate

    def removeDelegate(self, index):
        """

        :param index:
        """

        if index in self.delegates:
            del self.delegates[index]

    def getRowOrCol(self, index):
        """

        :param index:
        :return: :rtype:
        """

        if self.obj_orientation == Qt.Horizontal:
            return index.column()
        if self.obj_orientation == Qt.Vertical:
            return index.row()

    def sizeHint(self, option, index):
        """

        :param option:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.sizeHint(option, index)
        else:
            return super(GenericDelegate, self).sizeHint(option, index)

    def paint(self, painter, option, index):
        """

        :param painter:
        :param option:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            super(GenericDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """

        :param parent:
        :param option:
        :param index:
        :return: :rtype:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return super(GenericDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            super(GenericDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """

        :param editor:
        :param model:
        :param index:
        """

        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            super(GenericDelegate, self).setModelData(editor, model, index)

    def assignDelegates(self, idd_obj):
        """Cycle through table and assign delegates as needed depending on tags

        :param idd_obj:
        """

        # List of tags that would go in a combobox
        combo_fields = ['minimum', 'minimum>', 'maximum', 'maximum<', 'default',
                        'key', 'object-list']

        # Cycle through field tags
        for i, field_key in enumerate(idd_obj.ordered_fields()):

            # Create a list of tags which would go in a combo box
            field = idd_obj[field_key]
            matches = set(combo_fields).intersection(set(field.tags))

            # If there are choices then use the choiceDelegate, otherwise check type
            if len(matches) > 0:
                self.insertDelegate(i, ChoiceDelegate(self.main_window, field))
            else:
                self.insertDelegate(i, AlphaNumericDelegate(self.main_window))


class CustomStyledItemDelegate(QStyledItemDelegate):

    def __init__(self, main_window, parent=None):
        super(CustomStyledItemDelegate, self).__init__(parent)
        self.padding = 2
        self.prefs = main_window.prefs

    def sizeHint(self, option, index):

        if not index.isValid():
            return QSize(self.prefs['default_column_width'], 14)

        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, 0)
        text = index.data(Qt.DisplayRole)

        fm = QFontMetrics(option.font)
        b_rect = fm.boundingRect(rect,
                                 Qt.AlignLeft |
                                 Qt.AlignVCenter |
                                 Qt.TextWrapAnywhere,
                                 text)

        return QSize(int(self.prefs['default_column_width']),
                            b_rect.height())

    def paint(self, painter, option, index):

        if not index.isValid():
            return

        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, 0)
        text = index.data(Qt.DisplayRole)

        painter.save()
        opt = QTextOption()
        opt.setWrapMode(QTextOption.WrapAnywhere)
        opt.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        painter.drawText(rect, text, opt)
        painter.restore()


class AlphaNumericDelegate(CustomStyledItemDelegate):
    """

    :param main_window:
    :type main_window:
    """

    def __init__(self, main_window, parent=None):
        super(AlphaNumericDelegate, self).__init__(main_window, parent)
        self.main_window = main_window
        self.prefs = main_window.prefs

    def createEditor(self, parent, option, index):
        text_edit = ExtendedPlainTextEditor(parent)
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setFrameStyle(QFrame.NoFrame)
        text_edit.setWordWrapMode(QTextOption.WrapAnywhere)
        text_edit_font = QFont()
        text_edit_font.fromString(self.prefs['class_table_font'])
        text_edit.setFont(text_edit_font)
        text_edit.setStyleSheet("""QPlainTextEdit { margin-left:0;
            margin-top:0; margin-bottom:0; margin-right:0;
            padding-left:-2; padding-top:0; padding-bottom:0;
            padding-right:-2; vertical-align: middle;}""")
        return text_edit

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        # Block signals, then update value
        value = index.data(Qt.EditRole)
        editor.blockSignals(True)
        editor.setPlainText(value)
        editor.moveCursor(QTextCursor.Start, QTextCursor.MoveAnchor)
        editor.moveCursor(QTextCursor.End, QTextCursor.KeepAnchor)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        """Create undo command and push it to the undo stack

        :param editor:
        :param model:
        :param index:
        :return: :rtype:
        """

        value = editor.toPlainText()
        if index.data(Qt.EditRole) == value:
            return
        cmd = commands.ModifyObjectCmd(self.main_window, value=value)
        self.main_window.undo_stack.push(cmd)


class ChoiceDelegate(CustomStyledItemDelegate):
    """

    :param field:
    :type field:
    :param main_window:
    :type main_window:
    """

    def __init__(self, main_window, field, parent=None):
        super(ChoiceDelegate, self).__init__(main_window, parent)
        self.field = field
        self.model = None
        self.main_window = main_window
        self.prefs = main_window.prefs
        self.combo_fields = ['minimum>', 'minimum', 'maximum<', 'maximum', 'default',
                             'key', 'object-list']

    def createEditor(self, parent, option, index):
        """Creates a custom editor based on an extended QCombobox

        :param parent:
        :param option:
        :param index:
        """

        # If there isn't already a model, populate it
        if not self.model:
            self.model = QStandardItemModel()
            for tag, value in self.field.tags.iteritems():
                if tag in self.combo_fields:
                    if tag == 'default':
                        self.model.insertRow(0, [QStandardItem(value),
                                                 QStandardItem(tag)])
                    elif tag == 'object-list':
                        # Get list of all classes that are part of the object-list
                        class_list = []
                        if isinstance(value, set) or isinstance(value, list):
                            for val in value:
                                class_list.extend(self.main_window.idd.object_lists[val])
                        else:
                            class_list.extend(self.main_window.idd.object_lists[value])

                        # Cycle through all classes in the list
                        for cls in class_list:

                            # Get the objects for the current class
                            idf_objects = self.main_window.idf.get(cls)

                            # Cycle through all idf objects in the class
                            for obj in idf_objects:
                                self.model.appendRow([QStandardItem(obj[0].value),
                                                      QStandardItem(cls)])
                    elif tag == 'node':
                        # Retrieve a list of all nodes?
                        pass
                    elif tag == 'external-list':
                        # Retrieve list from external file
                        pass
                    else:
                        # Need to check if it's a list...is there a better way?
                        # Could make them all lists...would be annoying.
                        if isinstance(value, list):
                            for val in value:
                                self.model.appendRow([QStandardItem(val),
                                                      QStandardItem(tag)])
                        else:
                            self.model.appendRow([QStandardItem(value),
                                                  QStandardItem(tag)])

        if self.model.rowCount() > 0:
            # Check for and remove the 'current' item so it can be replace (at the top)
            myitem = self.model.findItems('current', column=1)
            if len(myitem) > 0:
                self.model.removeRow(myitem[0].row())

            # Make a special item for the 'current' item
            value = index.data(Qt.EditRole)
            current_item = QStandardItem('current')
            value_item = QStandardItem(value)
            self.model.insertRow(0, [value_item, current_item])

        # Table AND combo get same model (table first!)
        if 'object-list' in self.field.tags.keys():
            auto_complete = True
        else:
            auto_complete = False
        font = QFont()
        font.fromString(self.prefs['class_table_font'])
        self.comboBox = ExtendedComboBox(parent, auto_complete)
        self.tableView = QTableView(self.comboBox)
        self.tableView.setModel(self.model)
        self.comboBox.setModel(self.model)
        self.comboBox.setView(self.tableView)
        self.comboBox.setFont(font)
        self.comboBox.lineEdit().selectAll()  # TODO should depend on trigger!
        self.comboBox.lineEdit().setFont(font)

        # Set properties of tableView and the combobox
        self.tableView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.horizontalHeader().setVisible(False)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setFont(font)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        header_width = self.tableView.horizontalHeader().length()
        col_width = self.tableView.columnWidth(0)
        scroll_width = self.tableView.verticalScrollBar().width()
        self.tableView.setMinimumWidth(header_width + scroll_width)
        self.comboBox.set_popup_width(col_width + scroll_width)

        return self.comboBox

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """

        value = index.data(Qt.EditRole)
        combo_index = editor.findText(value)
        if combo_index >= 0:
            editor.blockSignals(True)
            editor.setCurrentIndex(combo_index)
            editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        """Create undo command and push it to the undo stack

        :param editor:
        :param model:
        :param index:
        :return: :rtype:
        """

        if index.data(Qt.EditRole) == editor.currentText():
            return
        cmd = commands.ModifyObjectCmd(self.main_window,
                                       value=editor.currentText())
        self.main_window.undo_stack.push(cmd)


class CustomValidator(QValidator):
    """Customized validator for preventing certain inputs
    """

    def validate(self, input_str, pos):
        """

        :param input_str:
        :param pos:
        :return: :rtype:
        """

        # Blanks are ok
        if not input_str:
            return QValidator.Intermediate

        # Reject invalid characters
        matches = set(input_str).intersection({';', ',', '#', '!'})
        if len(matches) > 0:
            return QValidator.Invalid

        # Accept everything else
        return QValidator.Acceptable


class ExtendedComboBox(QComboBox):
    """Customized QComboBox which adds a filtered, popup auto-completer
    """

    def __init__(self, parent, auto_complete):
        super(ExtendedComboBox, self).__init__(parent)

        # Set some properties
        # self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.setStyleSheet("QComboBox { border:0px; } "
                           "QComboBox QAbstractItemView { margin:0px; padding:0px; border:0px; }")
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setValidator(CustomValidator(self))
        self.setMaxVisibleItems(15)
        self.auto_complete = auto_complete

        if auto_complete is True:
            # Add a filter model to filter matching items
            self.filter_model = QSortFilterProxyModel(self)
            self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.filter_model.setSourceModel(self.model())

            # Create and add a completer, which uses the filter model. Always show
            # all (filtered) completions
            self.completer = QCompleter(self)
            self.completer.setModel(self.filter_model)
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.completer.setMaxVisibleItems(15)
            self.setCompleter(self.completer)

            # Connect signals
            self.lineEdit().textEdited[str].connect(self.filter_model.setFilterFixedString)
            # self.completer.activated.connect(self.on_completer_activated)
        else:
            self.setCompleter(None)

    def set_popup_width(self, width):
        """

        :param width:
        """

        if self.auto_complete:
            self.completer.popup().setMinimumWidth(width)

    # def on_completer_activated(self, text):
    #     """On selection of an item from the completer, select the corresponding
    #     item from combobox"""
    #     if text:
    #         index = self.findText(text)
    #         self.setCurrentIndex(index)
    #         self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        """On model change, update the models of the filter and completer as well

        :param model:
        """

        super(ExtendedComboBox, self).setModel(model)
        if self.auto_complete:
            self.filter_model.setSourceModel(model)
            self.completer.setModel(self.filter_model)

    def setModelColumn(self, column):
        """On model column change, update the model column of the filter and completer

        :param column:
        """

        if self.auto_complete:
            self.completer.setCompletionColumn(column)
            self.filter_model.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)


class ExtendedPlainTextEditor(QPlainTextEdit):

    def __init__(self, parent, **kwargs):
        """Subclassed QPlainTextEdit to override keypress events.

        :type parent: GenericDelegate
        """

        super(ExtendedPlainTextEditor, self).__init__(parent, kwargs)
        self.editor = parent.parent()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Comma, Qt.Key_Exclam,
                           Qt.Key_NumberSign, Qt.Key_Semicolon]:
            event.accept()
            return
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            event.accept()
            self.editor.commitData(self)
            self.editor.closeEditor(self, QAbstractItemDelegate.NoHint)
            return
        else:
            return super(ExtendedPlainTextEditor, self).keyPressEvent(event)
