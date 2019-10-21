#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module that contains the main UI window, all of its setup and all of its actions

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging
from collections import deque

# PySide2 imports
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QIcon, QKeySequence, QPalette
from PySide2.QtWidgets import (QUndoStack, QApplication, QAbstractItemView, QFrame, QDockWidget,
                               QTreeView, QLineEdit, QPushButton, QWidget, QTextEdit, QMenu,
                               QPlainTextEdit, QUndoView, QLabel, QProgressBar, QSystemTrayIcon,
                               QAction, QActionGroup, QCheckBox, QHeaderView, QVBoxLayout,
                               QHBoxLayout, QDesktopWidget)

# Package imports
from ..models import classtable
from ..models import reftree
from .. import config
from .prefs import PrefsDialog
from .search import SearchReplaceDialog

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
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(100)

        # Object navigation history
        self.obj_history = deque([], config.MAX_OBJ_HISTORY)

        app = QApplication.instance()
        base_font = QFont()
        base_font.fromString(self.prefs['base_font'])
        app.setFont(base_font)

        # Object class table widget
        # classTable = QTableView(self)
        classTable = classtable.TableView(self)
        classTable.setObjectName("classTable")
        classTable.setAlternatingRowColors(True)
        classTable.setFrameShape(QFrame.StyledPanel)
        classTable_font = QFont()
        classTable_font.fromString(self.prefs['class_table_font'])
        classTable.setFont(classTable_font)
        fm = classTable.fontMetrics()
        classTable.setWordWrap(True)
        classTable.setEditTriggers(QAbstractItemView.EditKeyPressed |
                                   QAbstractItemView.DoubleClicked |
                                   QAbstractItemView.AnyKeyPressed |
                                   QAbstractItemView.SelectedClicked)
        # classTable.horizontalHeader().setMovable(True)
        # classTable.verticalHeader().setMovable(False)
        classTable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        classTable.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        classTable.horizontalHeader().setDefaultSectionSize(self.prefs['default_column_width'])
        classTable.verticalHeader().setDefaultSectionSize(fm.height() + 0)
        classTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        classTable.setContextMenuPolicy(Qt.CustomContextMenu)
        classTable.customContextMenuRequested.connect(self.custom_table_context_menu)

        # Create table model and proxy layers for transposing and filtering
        self.classTableModel = classtable.IDFObjectTableModel(classTable)
        self.transposeableModel = classtable.TransposeProxyModel(self.classTableModel)
        self.transposeableModel.setSourceModel(self.classTableModel)
        self.sortableModel = classtable.SortFilterProxyModel(self.transposeableModel)
        self.sortableModel.setSourceModel(self.transposeableModel)

        # Assign model to table (enable sorting FIRST)
        # table.setSortingEnabled(True) # Disable for now, CRUD actions won't work!
        classTable.setModel(self.sortableModel)

        # Connect some signals
        selection_model = classTable.selectionModel()
        selection_model.selectionChanged.connect(self.table_selection_changed)

        # These are currently broken
        # classTable.horizontalHeader().sectionMoved.connect(self.moveObject)
        # classTable.verticalHeader().sectionMoved.connect(self.moveObject)

        # Object class tree widget
        classTreeDockWidget = QDockWidget("Object Classes and Counts", self)
        classTreeDockWidget.setObjectName("classTreeDockWidget")
        classTreeDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)

        classTree = QTreeView(classTreeDockWidget)
        classTree.setUniformRowHeights(True)
        classTree.setAllColumnsShowFocus(True)
        classTree.setRootIsDecorated(False)
        classTree.setExpandsOnDoubleClick(True)
        classTree.setIndentation(15)
        classTree.setAnimated(True)
        classTree_font = QFont()
        classTree_font.fromString(self.prefs['class_tree_font'])
        classTree.setFont(classTree_font)
        classTree.setAlternatingRowColors(True)
        classTree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        palette = classTree.palette()
        palette.setColor(QPalette.Highlight, Qt.darkCyan)
        classTree.setPalette(palette)

        class_tree_window = QWidget(classTreeDockWidget)
        class_tree_dock_layout_v = QVBoxLayout()
        class_tree_dock_layout_h = QHBoxLayout()
        class_tree_dock_layout_v.setContentsMargins(0, 8, 0, 0)
        class_tree_dock_layout_h.setContentsMargins(0, 0, 0, 0)

        class_tree_filter_edit = QLineEdit(classTreeDockWidget)
        class_tree_filter_edit.setPlaceholderText("Filter Classes")
        class_tree_filter_edit.textChanged.connect(self.treeFilterRegExpChanged)

        class_tree_filter_cancel = QPushButton("Clear", classTreeDockWidget)
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
        commentDockWidget = QDockWidget("Comments", self)
        commentDockWidget.setObjectName("commentDockWidget")
        commentDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        commentView = UndoRedoTextEdit(commentDockWidget, self)
        commentView.setLineWrapMode(QTextEdit.FixedColumnWidth)
        commentView.setLineWrapColumnOrWidth(499)
        commentView.setFrameShape(QFrame.StyledPanel)
        commentView_font = QFont()
        commentView_font.fromString(self.prefs['comments_font'])
        commentView.setFont(commentView_font)
        commentDockWidget.setWidget(commentView)

        # Info and help widget
        infoDockWidget = QDockWidget("Info", self)
        infoDockWidget.setObjectName("infoDockWidget")
        infoDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        infoView = QTextEdit(infoDockWidget)
        infoView.setFrameShape(QFrame.StyledPanel)
        infoView.setReadOnly(True)
        infoDockWidget.setWidget(infoView)

        # Node list and jump menu widget
        refDockWidget = QDockWidget("Field References", self)
        refDockWidget.setObjectName("refDockWidget")
        refDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        ref_model = reftree.ReferenceTreeModel(None, refDockWidget)
        refView = QTreeView(refDockWidget)
        refView.setModel(ref_model)
        refView.setUniformRowHeights(True)
        refView.setRootIsDecorated(False)
        refView.setIndentation(15)
        refView.setColumnWidth(0, 160)
        refView.setFrameShape(QFrame.StyledPanel)
        refDockWidget.setWidget(refView)
        refView.doubleClicked.connect(self.ref_tree_double_clicked)

        # Logging and debugging widget
        logDockWidget = QDockWidget("Log Viewer", self)
        logDockWidget.setObjectName("logDockWidget")
        logDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        logView = QPlainTextEdit(logDockWidget)
        logView.setLineWrapMode(QPlainTextEdit.NoWrap)
        logView.setReadOnly(True)
        logView_font = QFont()
        logView_font.fromString(self.prefs['base_font'])
        logView.setFont(logView_font)
        logView.ensureCursorVisible()
        logDockWidget.setWidget(logView)

        # Undo view widget
        undoDockWidget = QDockWidget("Undo History", self)
        undoDockWidget.setObjectName("undoDockWidget")
        undoDockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        undoView = QUndoView(self.undo_stack)
        undoDockWidget.setWidget(undoView)

        # Define corner docking behaviour
        self.setDockNestingEnabled(True)
        self.setCorner(Qt.TopLeftCorner,
                       Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner,
                       Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner,
                       Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner,
                       Qt.RightDockWidgetArea)

        # Assign main widget and dock widgets to QMainWindow
        self.setCentralWidget(classTable)
        self.addDockWidget(Qt.LeftDockWidgetArea, classTreeDockWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, commentDockWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, infoDockWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, refDockWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, logDockWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, undoDockWidget)

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
        self.setWindowIcon(QIcon(':/images/logo.png'))

        # Status bar setup
        self.statusBar().showMessage('Status: Ready')
        self.unitsLabel = QLabel()
        self.unitsLabel.setAlignment(Qt.AlignCenter)
        self.unitsLabel.setMinimumSize(self.unitsLabel.sizeHint())
        self.unitsLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.unitsLabel)
        self.pathLabel = QLabel()
        self.pathLabel.setAlignment(Qt.AlignCenter)
        self.pathLabel.setMinimumSize(self.pathLabel.sizeHint())
        self.pathLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.pathLabel)
        self.versionLabel = QLabel()
        self.versionLabel.setAlignment(Qt.AlignCenter)
        self.versionLabel.setMinimumSize(self.versionLabel.sizeHint())
        self.versionLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.statusBar().addPermanentWidget(self.versionLabel)
        self.progressBarIDF = QProgressBar()
        self.progressBarIDF.setAlignment(Qt.AlignCenter)
        self.progressBarIDF.setMaximumWidth(200)
        self.statusBar().addPermanentWidget(self.progressBarIDF)

        self.clipboard = QApplication.instance().clipboard()
        self.obj_clipboard = []

        self.setStyleSheet("""
            QToolTip {
               background-color: gray;
               color: white;
               border: black solid 1px
            } 
            # QMenu {
            #     background-color: rgbf(0.949020, 0.945098, 0.941176);
            #     color: rgb(255,255,255);
            # }
            # QMenu::item::selected {
            #     background-color: rgbf(0.949020, 0.945098, 0.941176);
            # }
            """)

    def create_tray_menu(self):
        """Creates an icon and menu for the system tray
        """

        # Menu for the system tray
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.exitAct)

        # System tray itself
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(':/images/logo.png'))
        self.trayIcon.setToolTip('IDF+')
        self.trayIcon.show()

    def create_actions(self):
        """Creates appropriate actions for use in menus and toolbars.
        """

        self.newAct = QAction(QIcon(':/images/new1.png'), "&New", self,
                                    shortcut=QKeySequence.New,
                                    statusTip="Create a new file",
                                    iconVisibleInMenu=True,
                                    triggered=self.new_file)

        self.openAct = QAction(QIcon(':/images/open.png'), "&Open...", self,
                                     shortcut=QKeySequence.Open,
                                     statusTip="Open an existing file",
                                     iconVisibleInMenu=True,
                                     triggered=self.open_file)

        self.saveAct = QAction(QIcon(':/images/save.png'), "&Save", self,
                                     shortcut=QKeySequence.Save,
                                     statusTip="Save the document to disk",
                                     iconVisibleInMenu=True,
                                     triggered=self.save)

        self.saveFormatAct = QAction(QIcon(':/images/save.png'), "&Format && Save",
                                     self, shortcut=QKeySequence('Ctrl+Shift+F'),
                                     statusTip="Format File and Save to disk",
                                     iconVisibleInMenu=True,
                                     triggered=self.format_save)

        self.saveAsAct = QAction(QIcon(':/images/saveas.png'), "Save &As...", self,
                                       shortcut=QKeySequence.SaveAs,
                                       statusTip="Save the document under a new name",
                                       iconVisibleInMenu=True,
                                       triggered=self.save_as)

        self.exitAct = QAction(QIcon(':/images/quit.png'), "E&xit", self,
                                     shortcut=QKeySequence('Ctrl+Q'),
                                     iconVisibleInMenu=True,
                                     statusTip="Exit the application",
                                     triggered=self.closeAllWindows)

        self.cutObjAct = QAction(QIcon(':/images/cut.png'), "Cu&t Object", self,
                                       shortcut=QKeySequence.Cut,
                                       statusTip="Cut current selection's contents to clipboard",
                                       iconVisibleInMenu=True,
                                       triggered=self.cutObject,
                                       iconText='Cut Obj')

        self.copyAct = QAction(QIcon(':/images/copy.png'),
                                     "&Copy Selected Values", self,
                                     statusTip="Copy current selection's contents to clipboard",
                                     iconVisibleInMenu=True,
                                     triggered=self.copySelected)

        self.pasteAct = QAction(QIcon(':/images/paste.png'),
                                      "&Paste Selected Values", self,
                                      statusTip="Paste clipboard into current selection",
                                      iconVisibleInMenu=True,
                                      triggered=self.pasteSelected)

        self.pasteExtAct = QAction(QIcon(':/images/paste.png'),
                                      "&Paste from External", self,
                                      shortcut=QKeySequence('Ctrl+Shift+v'),
                                      statusTip="Paste from external program",
                                      iconVisibleInMenu=True,
                                      triggered=self.paste_from_external)

        self.transposeAct = QAction("Transpose", self,
                                          shortcut=QKeySequence('Ctrl+t'),
                                          statusTip="Transpose rows and columns in object display",
                                          triggered=self.transpose_table)

        self.newObjAct = QAction(QIcon(':/images/new2.png'), "New Object", self,
                                       shortcut=QKeySequence('Ctrl+Shift+n'),
                                       statusTip="Create new object in current class",
                                       iconVisibleInMenu=True,
                                       triggered=self.newObject,
                                       iconText='New Obj')

        self.copyObjAct = QAction(QIcon(':/images/copy.png'), "Copy Object", self,
                                        shortcut=QKeySequence.Copy,
                                        statusTip="Copy the current Object(s)",
                                        iconVisibleInMenu=True,
                                        triggered=self.copyObject,
                                        iconText='Copy Obj')

        self.pasteObjAct = QAction(QIcon(':/images/paste.png'), "Paste Object", self,
                                         shortcut=QKeySequence.Paste,
                                         statusTip="Paste the currently copies Object(s)",
                                         iconVisibleInMenu=True,
                                         triggered=self.pasteObject,
                                         iconText='Paste Obj')

        self.dupObjAct = QAction(QIcon(':/images/copy.png'), "Duplicate Object", self,
                                       shortcut=QKeySequence('Shift+Ctrl+d'),
                                       statusTip="Duplicate the current Object(s)",
                                       iconVisibleInMenu=True,
                                       triggered=self.duplicateObject,
                                       iconText='Dup Obj')

        self.delObjAct = QAction(QIcon(':/images/delete.png'), "Delete Object", self,
                                       shortcut=QKeySequence.Delete,
                                       statusTip="Delete the current Object(s)",
                                       iconVisibleInMenu=True,
                                       triggered=self.deleteObject,
                                       iconText='Del Obj')

        self.undoAct = QAction(QIcon(':/images/undo.png'), "&Undo", self,
                                     shortcut=QKeySequence.Undo,
                                     statusTip="Undo previous action",
                                     iconVisibleInMenu=True,
                                     triggered=self.undo_stack.undo)

        self.redoAct = QAction(QIcon(':/images/redo.png'), "&Redo", self,
                                     shortcut=QKeySequence.Redo,
                                     statusTip="Redo previous action",
                                     iconVisibleInMenu=True,
                                     triggered=self.undo_stack.redo)

        self.groupAct = QAction("Hide Groups in Class Tree", self,
                                      shortcut=QKeySequence('Ctrl+g'),
                                      triggered=self.toggle_groups,
                                      checkable=True)

        # self.navForwardAct = QAction("Forward", self,
        #         shortcut=QKeySequence('Ctrl+Plus'),
        #         statusTip="Go forward to the next object",
        #         triggered=self.navForward)
        #
        # self.navBackAct = QAction("Back", self,
        #         shortcut=QKeySequence('Ctrl+Minus'),
        #         statusTip="Go back to the previous object",
        #         triggered=self.navBack)

        self.showInFolderAct = QAction(QIcon(':/images/new.png'), "&Show in folder",
                                             self, shortcut=QKeySequence('Ctrl+Shift+t'),
                                             statusTip="Open location of current file",
                                             iconVisibleInMenu=True)
        self.showInFolderAct.triggered.connect(lambda: self.show_in_folder())

        self.epDocGettingStartedAction = QAction("EnergyPlus Getting Started", self,
                                                       triggered=self.energy_plus_docs)

        self.epDocIORefAction = QAction("EnergyPlus I/O Reference", self,
                                              triggered=self.energy_plus_docs)

        self.epDocOutputDetailsAction = QAction("EnergyPlus Output Details and Examples",
                                                      self, triggered=self.energy_plus_docs)

        self.epDocEngineeringRefAction = QAction("EnergyPlus Engineering Reference", self,
                                                       triggered=self.energy_plus_docs)

        self.epDocAuxiliaryProgsAction = QAction("EnergyPlus Auxiliary Programs", self,
                                                       triggered=self.energy_plus_docs)

        self.epDocEMSGuideAction = QAction("EnergyPlus EMS Application Guide", self,
                                                 triggered=self.energy_plus_docs)

        self.epDocComplianceAction = QAction("Using EnergyPlus for Compliance", self,
                                                   triggered=self.energy_plus_docs)

        self.epDocInterfaceAction = QAction("External Interface Application Guide", self,
                                                  triggered=self.energy_plus_docs)

        self.epDocTipsTricksAction = QAction("Tips and Tricks Using EnergyPlus", self,
                                                   triggered=self.energy_plus_docs)

        self.epDocPlantGuideAction = QAction("EnergyPlus Plant Application Guide", self,
                                                   triggered=self.energy_plus_docs)

        self.epDocAcknowledgmentsAction = QAction("EnergyPlus Acknowledgments", self,
                                                        triggered=self.energy_plus_docs)

        self.openInEditorAct = QAction(QIcon(':/images/new.png'),
                                             "&Open in text editor", self,
                                             shortcut=QKeySequence('Ctrl+e'),
                                             statusTip="Open current file in default editor",
                                             iconVisibleInMenu=True,
                                             triggered=self.open_in_text_editor)

        self.helpAct = QAction("&EnergyPlus Help (Online)", self,
                                     statusTip="Show the EnergyPlus' help",
                                     triggered=self.energyplus_help)

        self.aboutAct = QAction("&About IDF+", self,
                                      statusTip="Show the application's About box",
                                      triggered=self.about)

        self.clearRecentAct = QAction("Clear Recent", self,
                                            statusTip="Clear recent files",
                                            triggered=self.clear_recent)

        self.minimizeAction = QAction("Mi&nimize", self,
                                            triggered=self.hide)

        self.maximizeAction = QAction("Ma&ximize", self,
                                            triggered=self.showMaximized)

        self.restoreAction = QAction("&Restore", self,
                                           triggered=self.showNormal)

        self.showPrefsAction = QAction("&Preferences", self,
                                             triggered=self.show_prefs_dialog)

        self.showSearchAction = QAction("&Search && Replace", self,
                                              shortcut=QKeySequence('Ctrl+f'),
                                              triggered=self.show_search_dialog)

        self.findThisAct = QAction("Find This", self,
                                         triggered=self.find_this)

        self.jumpFilterGeometry = QAction("Include Geometry", self,
                                                triggered=self.jump_to_filter_geometry,
                                                checkable=True)

        self.setIPUnitsAction = QAction("&IP Units", self,
                                              triggered=self.toggle_units,
                                              checkable=True)

        self.setSIUnitsAction = QAction("&SI Units", self,
                                              triggered=self.toggle_units,
                                              checkable=True)

        self.classWithObjsAction = QAction("Show Only Classes With Objects", self,
                                                 shortcut=QKeySequence('Ctrl+l'),
                                                 statusTip="Show Only Classes With Objects",
                                                 triggered=self.toggle_full_tree,
                                                 checkable=True)

        self.fillRightAction = QAction("Fill right", self,
                                             shortcut=QKeySequence('Ctrl+d'),
                                             statusTip="Fill right",
                                             triggered=self.fill_right)

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
                                self.saveAsAct, self.saveFormatAct, None, self.exitAct)
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
        self.editMenu.addAction(self.pasteExtAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.delObjAct)
        self.editMenu.addSeparator().setText('Values')
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.fillRightAction)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.showSearchAction)

        # Tools Menu
        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.showInFolderAct)
        self.toolsMenu.addAction(self.openInEditorAct)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.showPrefsAction)

        # View Menu
        self.viewMenu = self.menuBar().addMenu("&View")
        action_group = QActionGroup(self)
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
        self.viewMenu.addAction(self.groupAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.transposeAct)

        # Jump Menu
        self.jumpToMenu = self.menuBar().addMenu("&Jump")
        self.update_jump_menu()
        self.jumpToMenu.aboutToShow.connect(self.update_jump_menu)
        self.jumpFilterGeometry.setEnabled(False)

        # Help Menu
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.helpAct)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.epDocGettingStartedAction)
        self.helpMenu.addAction(self.epDocIORefAction)
        self.helpMenu.addAction(self.epDocOutputDetailsAction)
        self.helpMenu.addAction(self.epDocEngineeringRefAction)
        self.helpMenu.addAction(self.epDocAuxiliaryProgsAction)
        self.helpMenu.addAction(self.epDocEMSGuideAction)
        self.helpMenu.addAction(self.epDocComplianceAction)
        self.helpMenu.addAction(self.epDocInterfaceAction)
        self.helpMenu.addAction(self.epDocTipsTricksAction)
        self.helpMenu.addAction(self.epDocPlantGuideAction)
        self.helpMenu.addAction(self.epDocAcknowledgmentsAction)

    def create_tool_bars(self):
        """Creates the necessary toolbars.
        """

        # File Toolbar
        self.fileToolBar = self.addToolBar("File Toolbar")
        self.fileToolBar.setObjectName('fileToolbar')
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

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
        self.editToolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Object history navigation toolbar
        # self.navToolBar = self.addToolBar("Navigation Toolbar")
        # self.navToolBar.setObjectName('viewToolBar')
        # self.navToolBar.addAction(self.navForwardAct)
        # self.navToolBar.addAction(self.navBackAct)
        # self.navToolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Object filter toolbar
        self.filterToolBar = self.addToolBar("Filter Toolbar")
        self.filterToolBar.setObjectName('filterToolBar')
        self.filterBox = QLineEdit()
        self.filterBox.setPlaceholderText("Filter Objects")
        self.filterBox.setMaximumWidth(160)
        self.filterBox.setFixedWidth(160)
        # filterLabel = QLabel("Filter Obj:", self)
        # filterLabel.setBuddy(self.filterBox)
        # self.filterToolBar.addWidget(filterLabel)
        self.filterBox.textChanged.connect(self.tableFilterRegExpChanged)
        self.filterBox.textChanged.connect(self.treeFilterRegExpChanged)
        clearFilterButton = QPushButton('Clear')
        clearFilterButton.setMaximumWidth(45)
        clearFilterButton.clicked.connect(self.clearFilterClicked)
        self.filterToolBar.addWidget(self.filterBox)
        self.filterToolBar.addWidget(clearFilterButton)
        self.caseSensitivity = QCheckBox('Case Sensitive')
        self.caseSensitivity.stateChanged.connect(self.caseSensitivityChanged)
        self.filterToolBar.addWidget(self.caseSensitivity)
        self.filterToolBar.addSeparator()
        self.filterToolBar.addAction(self.transposeAct)

    def create_shortcuts(self):
        """Creates keyboard shortcuts.
        """

        # QShortcut(QKeySequence('Ctrl+l'), self).activated.connect(self.toggle_full_tree)
        # QShortcut(QKeySequence('Ctrl+d'), self).activated.connect(self.fill_right)
        # QShortcut(QKeySequence('Ctrl+d'), self).activated.connect(self.fill_right)

#    def createAction(self, text, slot=None, shortcut=None, icon=None,
#                     tip=None, checkable=False, signal="triggered()"):
#        action = QAction(text, self)
#        if icon is not None:
#            action.setIcon(QIcon(":/%s.png" % icon))
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
        menu = QMenu(self)
        menu.addAction(self.undoAct)
        menu.addAction(self.redoAct)
        menu.addSeparator()
        menu.addAction(self.copyObjAct)
        menu.addAction(self.dupObjAct)
        menu.addAction(self.delObjAct)
        menu.addAction(self.newObjAct)
        menu.addAction(self.cutObjAct)
        menu.addSeparator()
        menu.addMenu(self.jumpToMenu)
        menu.addSeparator()
        menu.addAction(self.findThisAct)
        menu.popup(self.classTable.viewport().mapToGlobal(position))
        self.mouse_position = position

    def reset_progress_bar(self):
        self.progressBarIDF.hide()

    def center(self):
        """Called to center the window on the screen on startup.
        """

        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def show_prefs_dialog(self):
        """Handles showing the settings dialog and setting its values.
        """

        dlg = PrefsDialog(self, self.prefs)
        if dlg.exec_():
            # Refresh the table view to take into account any new prefs
            self.load_table_view(self.current_obj_class)

            # Clear the idd cache if requested
            if self.prefs.get('clear_idd_cache', False) == True:
                self.clear_idd_cache()

            # Update preferences if various flags apply
            if not self.idf:
                return
            options_dict = dict()
            if self.prefs.get('apply_default_save_behaviour', False) == True:
                options_dict.update({'sort_order': self.prefs.get('sort_order'),
                                     'special_formatting': self.prefs.get('special_formatting')})
            # if self.prefs.get('apply_default_units_behaviour', False) == True:
            #     options_dict.update({'save_units': self.prefs.get('save_units')})
            # if self.prefs.get('apply_default_hidden_class_behaviour', False) == True:
            #     options_dict.update({'save_hidden_classes': self.prefs.get('save_hidden_classes')})
            if options_dict:
                self.idf.set_options(options_dict)
                self.set_dirty(True)

    def show_search_dialog(self):
        """Opens the search dialog.
        """

        SearchReplaceDialog(self).show()

    def find_this(self):
        """Searches for fields with similar content.
        """

        index = self.classTable.indexAt(self.mouse_position)
        text = self.classTable.model().data(index, Qt.EditRole)
        if text:
            SearchReplaceDialog(self, initial_query=text).show()


class UndoRedoTextEdit(QTextEdit):

    def __init__(self, parent, main_window):
        super(UndoRedoTextEdit, self).__init__(parent)
        self.main_window = main_window
        self.init_text = ""
        self.init_cursor = 0
        self.first_key_press = True

    def keyPressEvent(self, event):
        if self.first_key_press:
            self.init_cursor = self.textCursor().position()
            self.first_key_press = False
        QTextEdit.keyPressEvent(self, event)

    def focusInEvent(self, event):
        self.init_text = self.toPlainText()
        QTextEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        if self.toPlainText() != self.init_text:
            self.main_window.editComments(self.init_text, self.init_cursor)
        self.first_key_press = True
        QTextEdit.focusOutEvent(self, event)
