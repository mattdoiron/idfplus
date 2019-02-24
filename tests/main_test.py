#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
from pytestqt import qtbot

# PySide2 imports
from PySide2.QtWidgets import QTextEdit, QTreeView, QPlainTextEdit, QUndoView, QLineEdit

# Package imports
from idfplus.main import IDFPlus
from idfplus.models.classtable import TableView
from idfplus.widgets.main import UndoRedoTextEdit


def test_idfplus(qtbot):
    """Test for presence and type of main GUI components.
    """

    main_window = IDFPlus()
    qtbot.addWidget(main_window)

    assert isinstance(main_window.classTable, TableView)
    assert isinstance(main_window.commentView, UndoRedoTextEdit)
    assert isinstance(main_window.infoView, QTextEdit)
    assert isinstance(main_window.classTree, QTreeView)
    assert isinstance(main_window.logView, QPlainTextEdit)
    assert isinstance(main_window.undoView, QUndoView)
    assert isinstance(main_window.refView, QTreeView)
    assert isinstance(main_window.filterTreeBox, QLineEdit)
