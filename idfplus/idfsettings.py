# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 22:05:59 2014

@author: matt
"""

from PySide import QtGui
from PySide import QtCore


class Settings(object):
    '''Object to handle setting and getting settings or info about them.'''

    def __init__(self, parent):
        '''Create the settings object and set some of its own settings.'''
        self.parent = parent
        self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
                                         QtCore.QSettings.UserScope,
                                         "IDF Plus Inc.",
                                         "IDFPlus Editor",
                                         parent)

    def readSettings(self):
        '''Reads application settings and restores them.'''

        print("Reading settings from: {}".format(self.getPath()))
#        print("file: {}".format(self.getFileName()))
#        print("directory: {}".format(self.getDirName()))
        settings = self.settings
        parent = self.parent

        settings.beginGroup("MainWindow")
        size = settings.value("size", QtCore.QSize(600, 500))
        position = settings.value("pos", QtCore.QPoint(200, 200))
        state = settings.value("state", QtCore.QByteArray())
#        geometry = settings.value("geometry", QtCore.QByteArray())
        style = settings.value("style", 'Cleanlooks')
        settings.endGroup()

        settings.beginGroup("Files")
        parent.recentFiles = list(settings.value("recent_files", ['']))
        settings.endGroup()

        parent.resize(size)
        parent.move(position)
        parent.restoreState(state)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(style))
#        parent.restoreGeometry(geometry)
#        parent.restoreDockWidget(parent.classTree.parent())
#        parent.restoreDockWidget(parent.infoView.parent())
#        parent.restoreDockWidget(parent.commentView.parent())

    def writeSettings(self):
        '''Writes application settings to save them.'''

        print("Writing settings")
        parent = self.parent
        settings = self.settings

#        filename = self.filename  # or '' or None
        recentFiles = parent.recentFiles or ['']

        settings.beginGroup("Files")
#        settings.setValue("LastFile", filename)
        settings.setValue("recent_files", recentFiles)
        settings.endGroup()

        settings.beginGroup("MainWindow")
        settings.setValue("size", parent.size())
        settings.setValue("pos", parent.pos())
        settings.setValue("state", parent.saveState())
#        settings.setValue("geometry", parent.saveGeometry())
        settings.endGroup()

    def showSettingsDialog(self):
        '''Handles showing the settings dialog and setting its values.'''
        pass

    def getPath(self):
        return self.settings.fileName()

    def getFileName(self):
        import os
        return os.path.basename(self.settings.fileName())

    def getDirName(self):
        import os
        return os.path.dirname(self.settings.fileName())
