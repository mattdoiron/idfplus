# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 17:19:47 2014

from http://www.petfactory.se/pyside-custom-data-model/
"""

from PySide import QtCore, QtGui

class PaletteListModel(QtCore.QAbstractListModel):

    def __init__(self, colors = [], parent = None):

        QtCore.QAbstractListModel.__init__(self, parent)
        self.__colors = colors



    # every model in Qt needs to implement 2 functions, data and rowCount

    def headerData(self, section, orientation, role):

        if role == QtCore.Qt.DisplayRole:

            if orientation == QtCore.Qt.Horizontal:
                return 'Palette'
            else:
                return 'Color {0}'.format(section)



    # Tells the view how many items the model contains,
    # so that it can ask for the data within the rowcount range
    # the parent parameter is used when we have hierarchal data,
    # ie a tree view
    def rowCount(self, parent):

        #return 5
        return len(self.__colors)

    # The view will call data on every row it got from the rowCount method
    # the data method recieves a QModelIndexClass and a role
    # the QModelIndexClass stores info about the item and has methods like:
    # index.row(), index.column(), index.parent() etc ...

    def data(self, index, role):

        # this make sure that the text does not dissapear when the item is
        # double clicked, when we edit it.
        if role == QtCore.Qt.EditRole:

            return self.__colors[index.row()].name()

        if role == QtCore.Qt.ToolTipRole:

            return 'Hexcode: {0}'.format(self.__colors[index.row()].name())


        if role == QtCore.Qt.DecorationRole:

            row = index.row()
            value = self.__colors[row]

            pixmap = QtGui.QPixmap(26, 26)
            pixmap.fill(value)

            icon = QtGui.QIcon(pixmap)
            return icon



        if role == QtCore.Qt.DisplayRole:

            #return 'Hardcoded!'

            row = index.row()
            value = self.__colors[row]

            return value.name()

    def flags(self, index):

        # we need to return all the flags if we only return ItemIsEditable,
        # the items will be greyed out
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def setData(self, index, value, role = QtCore.Qt.EditRole):

        # check if the role is edit role
        if role == QtCore.Qt.EditRole:

            row = index.row()

            # try to create a QColor from the value
            color = QtGui.QColor(value)

            # if the color is a valid one set the new color and return true
            if color.isValid():
                self.__colors[row] = color
                # to notiy all views that the data has changed we emit a dataChanged signal
                # if we do not do this the view will only update when it gest focus
                self.dataChanged.emit(index, index)
                return True

        # we did not supply a valid color return false
        return False




red = QtGui.QColor(255,0,0)
green = QtGui.QColor(0,255,0)
blue = QtGui.QColor(0,0,255)

model = PaletteListModel([red, green, blue])

listView = QtGui.QListView()
listView.show()
listView.setModel(model)

treeView = QtGui.QTreeView()
treeView.show()
treeView.setModel(model)