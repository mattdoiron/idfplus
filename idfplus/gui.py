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
from collections import deque

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import tablemodel
from . import idfsettings as c
from . import logger
from . import treemodel

# Global variables
log = logger.setup_logging(c.LOG_LEVEL, __name__)


class UI_MainWindow(object):
    """Container class to hold all UI-related creation methods. Must be sublcassed."""

    def create_ui(self):
        """Setup main UI elements, dock widgets, UI-related elements, etc. """

        log.debug('Loading UI')

        # Undo Stack
        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(100)

        # Object navigation history
        self.obj_history = deque([], c.MAX_OBJ_HISTORY)

        # Object class table widget
        classTable = tablemodel.TableView(self)
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont("Arial", 9)
        classTable.setFont(font)
        fm = classTable.fontMetrics()
        classTable.setWordWrap(True)
        classTable.setEditTriggers(QtGui.QAbstractItemView.EditKeyPressed |
                                   QtGui.QAbstractItemView.DoubleClicked |
                                   QtGui.QAbstractItemView.AnyKeyPressed |
                                   QtGui.QAbstractItemView.SelectedClicked)
        # classTable.horizontalHeader().setMovable(True)
        # classTable.verticalHeader().setMovable(False)
        # classTable.horizontalHeader().setContentsMargins(0, 0, 0, 0)
        # classTable.verticalHeader().setContentsMargins(0, 0, 0, 0)
        classTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        classTable.horizontalHeader().setDefaultSectionSize(c.DEFAULT_COLUMN_WIDTH)
        classTable.verticalHeader().setDefaultSectionSize(fm.height() + 5)
        # classTable.setStyleSheet("QTableView {padding: 0px; border: 0px;} ")

        # classTable.clicked.connect(self.table_clicked)
        # classTable.selectionModel().currentChanged.connect(self.table_clicked)
        classTable.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)

        # These are currently broken
        # classTable.horizontalHeader().sectionMoved.connect(self.moveObject)
        # classTable.verticalHeader().sectionMoved.connect(self.moveObject)

        # Object class tree widget
        classTreeDockWidget = QtGui.QDockWidget("Object Classes and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)

        classTree = QtGui.QTreeView(classTreeDockWidget)
        classTree.setUniformRowHeights(True)
        classTree.setExpandsOnDoubleClick(False)
        classTree.setFont(font)
        classTree.setAlternatingRowColors(True)
        classTree.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        palette = classTree.palette()
        palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.darkCyan)
        classTree.setPalette(palette)

        class_tree_window = QtGui.QWidget(classTreeDockWidget)
        class_tree_dock_layout_v = QtGui.QVBoxLayout()
        class_tree_dock_layout_h = QtGui.QHBoxLayout()
        class_tree_dock_layout_v.setContentsMargins(0, 8, 0, 0)
        class_tree_dock_layout_h.setContentsMargins(0, 0, 0, 0)

        class_tree_filter_edit = QtGui.QLineEdit(classTreeDockWidget)
        class_tree_filter_edit.setPlaceholderText("Filter Classes")
        class_tree_filter_edit.textChanged.connect(self.treeFilterRegExpChanged)

        class_tree_filter_cancel = QtGui.QPushButton("Clear", classTreeDockWidget)
        class_tree_filter_cancel.setMaximumWidth(45)
        class_tree_filter_cancel.clicked.connect(self.clearTreeFilterClicked)

        class_tree_dock_layout_h.addWidget(class_tree_filter_edit)
        class_tree_dock_layout_h.addWidget(class_tree_filter_cancel)
        class_tree_dock_layout_v.addLayout(class_tree_dock_layout_h)
        class_tree_dock_layout_v.addWidget(classTree)
        class_tree_window.setLayout(class_tree_dock_layout_v)

        classTreeDockWidget.setWidget(class_tree_window)
        classTreeDockWidget.setContentsMargins(0,0,0,0)
        # classTree.clicked.connect(self.classSelected)

        # Comments widget
        commentDockWidget = QtGui.QDockWidget("Comments", self)
        commentDockWidget.setObjectName("commentDockWidget")
        commentDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        commentView = QtGui.QTextEdit(commentDockWidget)
        commentView.setFrameShape(QtGui.QFrame.StyledPanel)
        commentView.setFontFamily('Courier')
        commentView.setFontPointSize(10)
        # comment_font = commentView.font()
        # comment_font.setFamily("Courier")
        # comment_font.setFixedPitch(True)
        # comment_font.setPointSize(5)
        # commentView.setFont(comment_font)
        commentView.setReadOnly(True) # Just for now!
        commentDockWidget.setWidget(commentView)

        # Info and help widget
        infoDockWidget = QtGui.QDockWidget("Info", self)
        infoDockWidget.setObjectName("infoDockWidget")
        infoDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        infoView = QtGui.QTextEdit(infoDockWidget)
        infoView.setFrameShape(QtGui.QFrame.StyledPanel)
        infoView.setReadOnly(True)
        infoDockWidget.setWidget(infoView)

        # Node list and jump menu widget
        refDockWidget = QtGui.QDockWidget("Field References", self)
        refDockWidget.setObjectName("refDockWidget")
        refDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        ref_model = treemodel.ReferenceTreeModel(None, ("", ""), refDockWidget)
        refView = QtGui.QTreeView(refDockWidget)
        refView.setModel(ref_model)
        refView.setUniformRowHeights(True)
        refView.setRootIsDecorated(False)
        refView.setIndentation(15)
        refView.setColumnWidth(0, 160)
        # refView.resizeColumnToContents(0)
        # refView.setHeaderHidden(True)
        refView.setFrameShape(QtGui.QFrame.StyledPanel)
        refDockWidget.setWidget(refView)
        refView.doubleClicked.connect(self.ref_tree_double_clicked)

        # Logging and debugging widget
        logDockWidget = QtGui.QDockWidget("Log Viewer", self)
        logDockWidget.setObjectName("logDockWidget")
        logDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        logView = QtGui.QPlainTextEdit(logDockWidget)
        logView.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        logView.setReadOnly(True)
        logView.setFont(font)
        logView.ensureCursorVisible()
        logDockWidget.setWidget(logView)

        # Undo view widget
        undoDockWidget = QtGui.QDockWidget("Undo History", self)
        undoDockWidget.setObjectName("undoDockWidget")
        undoDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        undoView = QtGui.QUndoView(self.undo_stack)
        undoDockWidget.setWidget(undoView)

        # Define corner docking behaviour
        self.setDockNestingEnabled(True)
        self.setCorner(QtCore.Qt.TopLeftCorner,
                       QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner,
                       QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner,
                       QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner,
                       QtCore.Qt.RightDockWidgetArea)

        # Assign main widget and dock widgets to QMainWindow
        self.setCentralWidget(classTable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, classTreeDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, commentDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, infoDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, refDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, logDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, undoDockWidget)

        # Store widgets for access by other objects
        self.classTable = classTable
        self.commentView = commentView
        self.infoView = infoView
        self.classTree = classTree
        self.logView = logView
        self.undoView = undoView
        self.refView = refView
        self.filterTreeBox = class_tree_filter_edit

        # Store docks for access by other objects
        self.commentDockWidget = commentDockWidget
        self.infoDockWidget = infoDockWidget
        self.classTreeDockWidget = classTreeDockWidget
        self.logDockWidget = logDockWidget
        self.undoDockWidget = undoDockWidget
        self.refDockWidget = refDockWidget

        # Perform other UI-related initialization tasks
        self.center()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowTitle('IDFPlus Editor')
        self.setWindowIcon(QtGui.QIcon(':/images/eplus_sm.png'))

        # Status bar setup
        self.statusBar().showMessage('Status: Ready')
        self.statusBar().setSizeGripEnabled(True)
        self.versionLabel = QtGui.QLabel()
        self.versionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.versionLabel.setMinimumSize(self.versionLabel.sizeHint())
        self.versionLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.versionLabel)

        self.clipboard = QtGui.QApplication.instance().clipboard()
        self.obj_clipboard = []

    def create_tray_menu(self):
        """Creates an icon and menu for the system tray"""

        # Menu for the system tray
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.exitAct)

        # System tray itself
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QtGui.QIcon(':/images/eplus_sm.png'))
        self.trayIcon.setToolTip('IDFPlus')
        self.trayIcon.show()

    def create_actions(self):
        """Creates appropriate actions for use in menus and toolbars."""

        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new1.png'),
                "&New", self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file",
                triggered=self.new_file)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file",
                triggered=self.open_file)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk",
                triggered=self.save)

        self.saveAsAct = QtGui.QAction(QtGui.QIcon(':/images/saveas.png'),
                "Save &As...", self, shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.save_as)

        self.exitAct = QtGui.QAction(QtGui.QIcon(':/images/quit.png'),
                "E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'),
                "Cu&t", self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.cutObject)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+c'),
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.copySelected)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+v'),
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.pasteSelected)

        self.transposeAct = QtGui.QAction("Transpose", self,
                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Transpose rows and columns in object display.",
                triggered=self.transpose_table)

        self.newObjAct = QtGui.QAction(QtGui.QIcon(':/images/new2.png'),
                "New Obj", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+n'),
                statusTip="Create a new object in the current class.",
                triggered=self.newObject)

        self.copyObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Copy Obj", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current Object(s).",
                triggered=self.copyObject)

        self.pasteObjAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "Paste Obj", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the currently copies Object(s).",
                triggered=self.pasteObject)

        self.dupObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Dup Obj", self, shortcut=QtGui.QKeySequence('Ctrl+d'),
                statusTip="Duplicate the current Object(s).",
                triggered=self.duplicateObject)

        self.delObjAct = QtGui.QAction(QtGui.QIcon(':/images/delete.png'),
                "Del Obj", self, shortcut=QtGui.QKeySequence('Del'),
                statusTip="Delete the current Object(s).",
                triggered=self.deleteObject)

        self.navForwardAct = QtGui.QAction("Forward", self,
                shortcut=QtGui.QKeySequence('Ctrl+Plus'),
                statusTip="Go forward to the next object.",
                triggered=self.navForward)

        self.navBackAct = QtGui.QAction("Back", self,
                shortcut=QtGui.QKeySequence('Ctrl+Minus'),
                statusTip="Go back to the previous object.",
                triggered=self.navBack)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.maximizeAction = QtGui.QAction("Ma&ximize", self,
                triggered=self.showMaximized)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.undoAct = self.undo_stack.createUndoAction(self.undo_stack)
        self.undoAct.setShortcut(QtGui.QKeySequence.Undo)
        self.undoAct.setIcon(QtGui.QIcon(':/images/undo.png'))

        self.redoAct = self.undo_stack.createRedoAction(self.undo_stack)
        self.redoAct.setShortcut(QtGui.QKeySequence.Redo)
        self.redoAct.setIcon(QtGui.QIcon(':/images/redo.png'))

        self.transposeAct.setEnabled(False)

    def create_menus(self):
        """Create all required items for menus."""

        # File Menu
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (self.newAct, self.openAct, self.saveAct,
                                self.saveAsAct, None, self.exitAct)
        self.update_file_menu()
        self.fileMenu.aboutToShow.connect(self.update_file_menu)

        # Edit Menu
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.newObjAct)
        self.editMenu.addAction(self.dupObjAct)
        self.editMenu.addAction(self.delObjAct)
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.copyObjAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addAction(self.pasteObjAct)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.classTreeDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.infoView.parent().toggleViewAction())
        self.viewMenu.addAction(self.commentView.parent().toggleViewAction())
        self.viewMenu.addAction(self.logView.parent().toggleViewAction())
        self.viewMenu.addAction(self.undoView.parent().toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fileToolBar.toggleViewAction())
        self.viewMenu.addAction(self.editToolBar.toggleViewAction())
        self.viewMenu.addAction(self.navToolBar.toggleViewAction())
        self.viewMenu.addAction(self.filterToolBar.toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def create_tool_bars(self):
        """Creates the necessary toolbars."""

        # File Toolbar
        self.fileToolBar = self.addToolBar("File Toolbar")
        self.fileToolBar.setObjectName('fileToolbar')
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Edit Toolbar
        self.editToolBar = self.addToolBar("Edit Toolbar")
        self.editToolBar.setObjectName('editToolbar')
        self.editToolBar.addAction(self.undoAct)
        self.editToolBar.addAction(self.redoAct)
        self.editToolBar.addAction(self.newObjAct)
        self.editToolBar.addAction(self.dupObjAct)
        self.editToolBar.addAction(self.delObjAct)
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyObjAct)
        self.editToolBar.addAction(self.pasteObjAct)
        self.editToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Object history navigation toolbar
        self.navToolBar = self.addToolBar("Navigation Toolbar")
        self.navToolBar.setObjectName('viewToolBar')
        self.navToolBar.addAction(self.navForwardAct)
        self.navToolBar.addAction(self.navBackAct)
        self.navToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Object filter toolbar
        self.filterToolBar = self.addToolBar("Filter Toolbar")
        self.filterToolBar.setObjectName('filterToolBar')
        self.filterBox = QtGui.QLineEdit()
        self.filterBox.setPlaceholderText("Filter Objects")
        self.filterBox.setMaximumWidth(160)
        self.filterBox.setFixedWidth(160)
        # filterLabel = QtGui.QLabel("Filter Obj:", self)
        # filterLabel.setBuddy(self.filterBox)
        # self.filterToolBar.addWidget(filterLabel)
        self.filterBox.textChanged.connect(self.tableFilterRegExpChanged)
        self.filterBox.textChanged.connect(self.treeFilterRegExpChanged)
        clearFilterButton = QtGui.QPushButton('Clear')
        clearFilterButton.setMaximumWidth(45)
        clearFilterButton.clicked.connect(self.clearFilterClicked)
        self.filterToolBar.addWidget(self.filterBox)
        self.filterToolBar.addWidget(clearFilterButton)
        self.caseSensitivity = QtGui.QCheckBox('Case Sensitive')
        self.caseSensitivity.stateChanged.connect(self.caseSensitivityChanged)
        self.filterToolBar.addWidget(self.caseSensitivity)
        self.filterToolBar.addSeparator()
        self.filterToolBar.addAction(self.transposeAct)

    def create_shortcuts(self):
        """Creates keyboard shortcuts."""
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'),self).activated.connect(self.toggle_full_tree)

#    def createAction(self, text, slot=None, shortcut=None, icon=None,
#                     tip=None, checkable=False, signal="triggered()"):
#        action = QtGui.QAction(text, self)
#        if icon is not None:
#            action.setIcon(QtGui.QIcon(":/%s.png" % icon))
#        if shortcut is not None:
#            action.setShortcut(shortcut)
#        if tip is not None:
#            action.setToolTip(tip)
#            action.setStatusTip(tip)
#        if slot is not None:
#            self.connect(action, QtCore.SIGNAL(signal), slot)
#        if checkable:
#            action.setCheckable(True)
#        return action
#

    def create_context_menu(self, pos):
        menu = QtGui.QMenu()
        openAction = menu.addAction("Test 1")
        delAction = menu.addAction("Clear")
        renaAction = menu.addAction("Test 2")
        self.classTable.setContextMenuPolicy()

    def create_progress_bar(self):

        # Setup idf progress dialog
        self.progressDialogIDF = QtGui.QProgressDialog("Loading IDF File", "", 0,
                                                       100, self)
        self.progressDialogIDF.setWindowTitle('Loading IDF File')
        self.progressDialogIDF.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDF.setMinimumDuration(500)
        self.progressDialogIDF.setCancelButton(None)

        # Setup idd progress dialog
        self.progressDialogIDD = QtGui.QProgressDialog("Loading IDD File", "", 0,
                                                       100, self)
        self.progressDialogIDD.setWindowTitle('Loading IDD File')
        self.progressDialogIDD.setWindowModality(QtCore.Qt.WindowModal)
        self.progressDialogIDD.setMinimumDuration(500)
        self.progressDialogIDD.setCancelButton(None)

    def center(self):
        """Called to center the window on the screen on startup."""
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)