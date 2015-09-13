#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
"""

# System imports
import logging
from collections import deque

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Package imports
from . import tablemodel
from . import treemodel
from . import config

# Setup logging
log = logging.getLogger(__name__)


class UIMainWindow(object):
    """Container class to hold all UI-related creation methods. Must be sublcassed.
    """

    def create_ui(self):
        """Setup main UI elements, dock widgets, UI-related elements, etc.
        """

        log.debug('Loading UI')

        # Undo Stack
        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(100)

        # Object navigation history
        self.obj_history = deque([], config.MAX_OBJ_HISTORY)

        # Object class table widget
        # classTable = QtGui.QTableView(self)
        classTable = tablemodel.TableView(self)
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QtGui.QFrame.StyledPanel)
        font = QtGui.QFont(self.prefs['base_font'],
                           self.prefs['base_font_size'])
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
        classTable.horizontalHeader().setDefaultSectionSize(self.prefs['default_column_width'])
        classTable.verticalHeader().setDefaultSectionSize(fm.height() + 5)
        # classTable.setStyleSheet("QTableView {padding: 0px; border: 0px;} ")
        # classTable.clicked.connect(self.table_clicked)
        # classTable.selectionModel().currentChanged.connect(self.table_clicked)
        classTable.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
        classTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        classTable.customContextMenuRequested.connect(self.custom_table_context_menu)

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
        tree_font = QtGui.QFont(self.prefs['class_tree_font'],
                                self.prefs['class_tree_font_size'])
        classTree.setFont(tree_font)
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

        # Comments widget
        commentDockWidget = QtGui.QDockWidget("Comments", self)
        commentDockWidget.setObjectName("commentDockWidget")
        commentDockWidget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        commentView = QtGui.QPlainTextEdit(commentDockWidget)
        commentView.setFrameShape(QtGui.QFrame.StyledPanel)
        comment_font = QtGui.QFont(self.prefs['comments_font'],
                                   self.prefs['comments_font_size'])
        commentView.setFont(comment_font)
        commentDockWidget.setWidget(commentView)
        commentView.textChanged.connect(self.comment_view_changed)

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
        self.unitsLabel = QtGui.QLabel()
        self.unitsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.unitsLabel.setMinimumSize(self.unitsLabel.sizeHint())
        self.unitsLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.unitsLabel)
        self.versionLabel = QtGui.QLabel()
        self.versionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.versionLabel.setMinimumSize(self.versionLabel.sizeHint())
        self.versionLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.versionLabel)

        self.clipboard = QtGui.QApplication.instance().clipboard()
        self.obj_clipboard = []

        self.setStyleSheet("""QToolTip {
                           background-color: gray;
                           color: white;
                           border: black solid 1px
                           } """)

    def create_tray_menu(self):
        """Creates an icon and menu for the system tray
        """

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
        """Creates appropriate actions for use in menus and toolbars.
        """

        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new1.png'),
                "&New", self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", iconVisibleInMenu=True,
                triggered=self.new_file)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", iconVisibleInMenu=True,
                triggered=self.open_file)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", iconVisibleInMenu=True,
                triggered=self.save)

        self.saveAsAct = QtGui.QAction(QtGui.QIcon(':/images/saveas.png'),
                "Save &As...", self, shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name", iconVisibleInMenu=True,
                triggered=self.save_as)

        self.exitAct = QtGui.QAction(QtGui.QIcon(':/images/quit.png'),
                "E&xit", self, shortcut="Ctrl+Q", iconVisibleInMenu=True,
                statusTip="Exit the application", triggered=self.close)

        self.cutObjAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'),
                "Cu&t Object", self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                iconVisibleInMenu=True, triggered=self.cutObject, iconText='Cut Obj')

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy Values", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+c'),
                statusTip="Copy the current selection's contents to the clipboard",
                iconVisibleInMenu=True, triggered=self.copySelected)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste Values", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+v'),
                statusTip="Paste the clipboard's contents into the current selection",
                iconVisibleInMenu=True, triggered=self.pasteSelected)

        self.transposeAct = QtGui.QAction("Transpose", self,
                shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Transpose rows and columns in object display",
                triggered=self.transpose_table)

        self.newObjAct = QtGui.QAction(QtGui.QIcon(':/images/new2.png'),
                "New Object", self, shortcut=QtGui.QKeySequence('Ctrl+Shift+n'),
                statusTip="Create a new object in the current class",
                iconVisibleInMenu=True, triggered=self.newObject, iconText='New Obj')

        self.copyObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Copy Object", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current Object(s)", iconVisibleInMenu=True,
                triggered=self.copyObject, iconText='Copy Obj')

        self.pasteObjAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "Paste Object", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the currently copies Object(s)", iconVisibleInMenu=True,
                triggered=self.pasteObject, iconText='Paste Obj')

        self.dupObjAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "Duplicate Object", self, shortcut=QtGui.QKeySequence('Ctrl+d'),
                statusTip="Duplicate the current Object(s)", iconVisibleInMenu=True,
                triggered=self.duplicateObject, iconText='Dup Obj')

        self.delObjAct = QtGui.QAction(QtGui.QIcon(':/images/delete.png'),
                "Delete Object", self, shortcut=QtGui.QKeySequence('Del'),
                statusTip="Delete the current Object(s)", iconVisibleInMenu=True,
                triggered=self.deleteObject, iconText='Del Obj')

        self.undoAct = QtGui.QAction(QtGui.QIcon(':/images/undo.png'),
                "&Undo", self, shortcut=QtGui.QKeySequence.Undo,
                statusTip="Undo previous action", iconVisibleInMenu=True,
                triggered=self.undo_stack.undo)

        self.redoAct = QtGui.QAction(QtGui.QIcon(':/images/redo.png'),
                "&Redo", self, shortcut=QtGui.QKeySequence.Redo,
                statusTip="Redo previous action", iconVisibleInMenu=True,
                triggered=self.undo_stack.redo)

        # self.navForwardAct = QtGui.QAction("Forward", self,
        #         shortcut=QtGui.QKeySequence('Ctrl+Plus'),
        #         statusTip="Go forward to the next object",
        #         triggered=self.navForward)
        #
        # self.navBackAct = QtGui.QAction("Back", self,
        #         shortcut=QtGui.QKeySequence('Ctrl+Minus'),
        #         statusTip="Go back to the previous object",
        #         triggered=self.navBack)

        self.showInFolderAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'),
                "&Show in folder", self, shortcut=QtGui.QKeySequence('Ctrl+t'),
                statusTip="Open location of current file", iconVisibleInMenu=True,
                triggered=self.show_in_folder)

        self.openInEditorAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'),
                "&Open in text editor", self, shortcut=QtGui.QKeySequence('Ctrl+e'),
                statusTip="Open current file in default editor", iconVisibleInMenu=True,
                triggered=self.open_in_text_editor)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.clearRecentAct = QtGui.QAction("Clear Recent", self,
                statusTip="Clear recent files",
                triggered=self.clear_recent)

        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.maximizeAction = QtGui.QAction("Ma&ximize", self,
                triggered=self.showMaximized)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.showPrefsAction = QtGui.QAction("&Preferences", self,
                triggered=self.show_prefs_dialog)

        self.setIPUnitsAction = QtGui.QAction("&IP Units", self,
                triggered=self.toggle_units, checkable=True)

        self.setSIUnitsAction = QtGui.QAction("&SI Units", self,
                triggered=self.toggle_units, checkable=True)

        self.classWithObjsAction = QtGui.QAction("Show Only Classes With Objects", self,
                shortcut=QtGui.QKeySequence('Ctrl+l'),
                statusTip="Show Only Classes With Objects",
                triggered=self.toggle_full_tree)

        self.logDockWidgetAct = self.logDockWidget.toggleViewAction()
        self.transposeAct.setEnabled(False)
        self.setSIUnitsAction.setChecked(True)
        self.undoAct.setEnabled(False)
        self.redoAct.setEnabled(False)
        self.saveAct.setEnabled(False)
        self.undo_stack.canUndoChanged.connect(self.toggle_can_undo)
        self.undo_stack.canRedoChanged.connect(self.toggle_can_redo)
        self.logDockWidgetAct.toggled.connect(self.start_log_watcher)

    def toggle_can_undo(self):
        if self.undo_stack.canUndo():
            new_state = True
        else:
            new_state = False
        self.undoAct.setEnabled(new_state)
        self.set_dirty(new_state)

    def toggle_can_redo(self):
        if self.undo_stack.canRedo():
            new_state = True
        else:
            new_state = False
        self.redoAct.setEnabled(new_state)

    def create_menus(self):
        """Create all required items for menus.
        """

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
        self.editMenu.addSeparator().setText('Objects')
        self.editMenu.addAction(self.newObjAct)
        self.editMenu.addAction(self.dupObjAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.cutObjAct)
        self.editMenu.addAction(self.copyObjAct)
        self.editMenu.addAction(self.pasteObjAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.delObjAct)
        self.editMenu.addSeparator().setText('Values')
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        # Tools Menu
        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.showInFolderAct)
        self.toolsMenu.addAction(self.openInEditorAct)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.showPrefsAction)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        action_group = QtGui.QActionGroup(self)
        self.viewMenu.addAction(action_group.addAction(self.setSIUnitsAction))
        self.viewMenu.addAction(action_group.addAction(self.setIPUnitsAction))
        self.viewMenu.addSeparator().setText('Dockable Widgets')
        self.viewMenu.addAction(self.classTreeDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.infoView.parent().toggleViewAction())
        self.viewMenu.addAction(self.commentView.parent().toggleViewAction())
        self.viewMenu.addAction(self.logDockWidgetAct)
        self.viewMenu.addAction(self.undoView.parent().toggleViewAction())
        self.viewMenu.addSeparator().setText('Toolbars')
        self.viewMenu.addAction(self.fileToolBar.toggleViewAction())
        self.viewMenu.addAction(self.editToolBar.toggleViewAction())
        # self.viewMenu.addAction(self.navToolBar.toggleViewAction())
        self.viewMenu.addAction(self.filterToolBar.toggleViewAction())
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.classWithObjsAction)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def create_tool_bars(self):
        """Creates the necessary toolbars.
        """

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
        self.editToolBar.addAction(self.cutObjAct)
        self.editToolBar.addAction(self.copyObjAct)
        self.editToolBar.addAction(self.pasteObjAct)
        self.editToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Object history navigation toolbar
        # self.navToolBar = self.addToolBar("Navigation Toolbar")
        # self.navToolBar.setObjectName('viewToolBar')
        # self.navToolBar.addAction(self.navForwardAct)
        # self.navToolBar.addAction(self.navBackAct)
        # self.navToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

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
        """Creates keyboard shortcuts.
        """

        # QtGui.QShortcut(QtGui.QKeySequence('Ctrl+l'), self).activated.connect(self.toggle_full_tree)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'), self).activated.connect(self.fill_right)
        # QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'), self).activated.connect(self.fill_right)

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

    def custom_table_context_menu(self, position):

        # Create a menu and populate it with actions
        menu = QtGui.QMenu(self)
        menu.addAction(self.undoAct)
        menu.addAction(self.redoAct)
        menu.addSeparator()
        menu.addAction(self.copyObjAct)
        menu.addAction(self.dupObjAct)
        menu.addAction(self.delObjAct)
        menu.addAction(self.newObjAct)
        menu.addAction(self.cutObjAct)
        menu.popup(self.classTable.viewport().mapToGlobal(position))

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
        """Called to center the window on the screen on startup.
        """

        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def show_prefs_dialog(self):
        """Handles showing the settings dialog and setting its values.
        """

        dlg = PrefsDialog(self, self.prefs)
        if dlg.exec_():
            result = dlg.prefs
            self.load_table_view(self.current_obj_class)
        if self.prefs.get('clear_idd_cache', False) == True:
            self.clear_idd_cache()


class PrefsDialog(QtGui.QDialog):
    """Form used to view and edit global program options
    """

    def __init__(self, parent, prefs):
        super(PrefsDialog, self).__init__(parent)
        self.prefs = prefs
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        # Create the tab widget and assign its tabs
        tab_widget = QtGui.QTabWidget()
        tab_widget.addTab(AppearanceTab(self), "Appearance")
        tab_widget.addTab(LogTab(self), "Logging")
        tab_widget.addTab(AdvancedTab(self), "Advanced")

        # Create layout and assign it to self
        layout = QtGui.QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addWidget(button_box)
        self.resize(350, 350)
        self.setLayout(layout)
        self.setWindowTitle("IDF+ Options")

        # Connect gui elements to events
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        """Override default accept method to save settings
        """
        self.prefs.write_settings()
        super(PrefsDialog, self).accept()


class AppearanceTab(QtGui.QWidget):
    def __init__(self, parent):
        super(AppearanceTab, self).__init__(parent)

        self.prefs = parent.prefs

        col_width_label = QtGui.QLabel("Default Column Width:")
        self.col_width_edit = QtGui.QLineEdit(str(self.prefs['default_column_width']))
        self.col_width_edit.setMinimumWidth(40)
        validator = QtGui.QIntValidator(10, 200, self)
        self.col_width_edit.setValidator(validator)

        style_label = QtGui.QLabel("Visual Style:")
        self.style_edit = QtGui.QComboBox(self)
        self.style_edit.addItems(QtGui.QStyleFactory.keys())
        self.style_edit.setCurrentIndex(self.style_edit.findText(self.prefs['style']))

        units_header_label = QtGui.QLabel("Show Units:")
        self.header_units_check = QtGui.QCheckBox('Show Units in Header', self)
        checked_header = QtCore.Qt.Checked if self.prefs['show_units_in_headers'] == 1 else QtCore.Qt.Unchecked
        self.header_units_check.setCheckState(checked_header)
        self.cells_units_check = QtGui.QCheckBox('Show Units in Cells', self)
        checked_cells = QtCore.Qt.Checked if self.prefs['show_units_in_cells'] == 1 else QtCore.Qt.Unchecked
        self.cells_units_check.setCheckState(checked_cells)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(col_width_label)
        mainLayout.addWidget(self.col_width_edit)
        mainLayout.addWidget(style_label)
        mainLayout.addWidget(self.style_edit)
        mainLayout.addWidget(units_header_label)
        mainLayout.addWidget(self.header_units_check)
        mainLayout.addWidget(self.cells_units_check)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        self.col_width_edit.textChanged.connect(self.update)
        self.style_edit.currentIndexChanged.connect(self.update)
        self.header_units_check.stateChanged.connect(self.update)
        self.cells_units_check.stateChanged.connect(self.update)

    def update(self):
        self.prefs['default_column_width'] = self.col_width_edit.text()
        self.prefs['style'] = self.style_edit.currentText()
        self.prefs['show_units_in_headers'] = 1 if self.header_units_check.checkState() else 0
        self.prefs['show_units_in_cells'] = 1 if self.cells_units_check.checkState() else 0


class LogTab(QtGui.QWidget):
    def __init__(self, parent):
        super(LogTab, self).__init__(parent)

        self.prefs = parent.prefs

        log_label = QtGui.QLabel("Log Detail Level:")
        self.log_edit = QtGui.QComboBox(self)
        self.log_edit.addItems(['INFO', 'DEBUG', 'WARNING'])
        self.log_edit.setCurrentIndex(self.log_edit.findText(self.prefs['log_level']))

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_edit)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

        self.log_edit.currentIndexChanged.connect(self.update)

    def update(self):
        self.prefs['log_level'] = self.log_edit.currentText()


class AdvancedTab(QtGui.QWidget):
    def __init__(self, parent):
        super(AdvancedTab, self).__init__(parent)

        self.prefs = parent.prefs

        clear_idd_label = QtGui.QLabel("Clear pre-processed IDD cache:")
        self.clear_idd_button = QtGui.QPushButton("Clear IDD cache")
        self.clear_idd_button.clicked.connect(self.clear_idd_cache)

        self.checked_clear_checkbox = QtGui.QCheckBox('Cache will be cleared', self)
        self.checked_clear_checkbox.setDisabled(True)
        self.checked_clear_checkbox.setCheckState(QtCore.Qt.Unchecked)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(clear_idd_label)
        main_layout.addWidget(self.clear_idd_button)
        main_layout.addWidget(self.checked_clear_checkbox)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update(self):
        pass

    def clear_idd_cache(self):
        self.checked_clear_checkbox.setCheckState(QtCore.Qt.Checked)
        self.prefs['clear_idd_cache'] = True
