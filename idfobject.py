#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

#import platform
from PySide import QtGui, QtCore
#import richtextlineedit


#NAME, OWNER, COUNTRY, DESCRIPTION, TEU = range(5)
#
#MAGIC_NUMBER = 0x570C4
#FILE_VERSION = 1


#class IDFObject(object):
#
#    def __init__(self, name, owner, country, teu=0, description=""):
#        self.name = QString(name)
#        self.owner = QString(owner)
#        self.country = QString(country)
#        self.teu = teu
#        self.description = QString(description)
#
#    def __cmp__(self, other):
#        return QString.localeAwareCompare(self.name.toLower(),
#                                          other.name.toLower())


#class IDFObjectContainer(object):
#
#    def __init__(self, filename=QString()):
#        self.filename = QString(filename)
#        self.dirty = False
#        self.idfObjects = {}
#        self.owners = set()
#        self.countries = set()
#
#    def idfObject(self, identity):
#        return self.idfObjects.get(identity)
#
#    def addIDFObject(self, idfObject):
#        self.idfObjects[id(idfObject)] = idfObject
#        self.owners.add(unicode(idfObject.owner))
#        self.countries.add(unicode(idfObject.country))
#        self.dirty = True
#
#    def removeIDFObject(self, idfObject):
#        del self.idfObjects[id(idfObject)]
#        del idfObject
#        self.dirty = True
#
#    def __len__(self):
#        return len(self.idfObjects)
#
#    def __iter__(self):
#        for idfObject in self.idfObjects.values():
#            yield idfObject
#
#    def inOrder(self):
#        return sorted(self.idfObjects.values())
#
#    def load(self):
#        exception = None
#        fh = None
#        try:
#            if self.filename.isEmpty():
#                raise IOError, "no filename specified for loading"
#            fh = QFile(self.filename)
#            if not fh.open(QIODevice.ReadOnly):
#                raise IOError, unicode(fh.errorString())
#            stream = QDataStream(fh)
#            magic = stream.readInt32()
#            if magic != MAGIC_NUMBER:
#                raise IOError, "unrecognized file type"
#            fileVersion = stream.readInt16()
#            if fileVersion != FILE_VERSION:
#                raise IOError, "unrecognized file type version"
#            self.idfObjects = {}
#            while not stream.atEnd():
#                name = QString()
#                owner = QString()
#                country = QString()
#                description = QString()
#                stream >> name >> owner >> country >> description
#                teu = stream.readInt32()
#                idfObject = IDFObject(name, owner, country, teu, description)
#                self.idfObjects[id(idfObject)] = idfObject
#                self.owners.add(unicode(owner))
#                self.countries.add(unicode(country))
#            self.dirty = False
#        except IOError, e:
#            exception = e
#        finally:
#            if fh is not None:
#                fh.close()
#            if exception is not None:
#                raise exception
#
#    def save(self):
#        exception = None
#        fh = None
#        try:
#            if self.filename.isEmpty():
#                raise IOError, "No filename specified for saving!"
#            fh = QFile(self.filename)
#            if not fh.open(QIODevice.WriteOnly):
#                raise IOError, unicode(fh.errorString())
#            stream = QDataStream(fh)
#            stream.writeInt32(MAGIC_NUMBER)
#            stream.writeInt16(FILE_VERSION)
#            stream.setVersion(QDataStream.Qt_4_1)
#            for idfObject in self.idfObjects.values():
#                stream << idfObject.name << idfObject.owner << idfObject.country \
#                       << idfObject.description
#                stream.writeInt32(idfObject.teu)
#            self.dirty = False
#        except IOError, e:
#            exception = e
#        finally:
#            if fh is not None:
#                fh.close()
#            if exception is not None:
#                raise exception


class IDFObjectTableModel(QtCore.QAbstractTableModel):

    def __init__(self, idfObjects, iddPart):
        super(IDFObjectTableModel, self).__init__()
        self.idfObjects = idfObjects
        self.iddPart = iddPart
#        self.filename = filename
        self.dirty = False

#    def sortByName(self):
#        self.idfObjects = sorted(self.idfObjects)
#        self.reset()

#    def sortByTEU(self):
#        idfObjects = [(idfObject.teu, idfObject) for idfObject in self.idfObjects]
#        idfObjects.sort()
#        self.idfObjects = [idfObject for teu, idfObject in idfObjects]
#        self.reset()

#    def sortByCountryOwner(self):
#        def compare(a, b):
#            if a.country != b.country:
#                return QString.localeAwareCompare(a.country, b.country)
#            if a.owner != b.owner:
#                return QString.localeAwareCompare(a.owner, b.owner)
#            return QString.localeAwareCompare(a.name, b.name)
#        self.idfObjects = sorted(self.idfObjects, compare)
#        self.reset()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        current_flags = QtCore.QAbstractTableModel.flags(self, index)
        return QtCore.Qt.ItemFlags(current_flags | QtCore.Qt.ItemIsEditable)

    def data(self, index, role):
        if not index.isValid() or \
                not (0 <= index.row() < len(self.idfObjects)):
#            print "data() called with invalid index"
            return None

        row = index.row()
        column = index.column()
        idfObject = self.idfObjects[row]

#        print 'data called with role: {}'.format(role)

        if column >= len(idfObject['fields']):
            return None

        data = None
        if role == QtCore.Qt.DisplayRole:
#            print 'data called with index ({},{})'.format(row, column)
            data = idfObject['fields'][column]
        elif role == QtCore.Qt.EditRole:
            data = idfObject['fields'][column]
        elif role == QtCore.Qt.ToolTipRole:
            data = "tooltip test"
#            return msg
        elif role == QtCore.Qt.DecorationRole:
            data = QtGui.QIcon("icon.png")
        # elif role == Qt.TextAlignmentRole:
        #     if column == TEU:
        #         return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))
        #     return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
        # elif role == Qt.TextColorRole and column == TEU:
        #     if idfObject.teu < 80000:
        #         return QVariant(QColor(Qt.black))
        #     elif idfObject.teu < 100000:
        #         return QVariant(QColor(Qt.darkBlue))
        #     elif idfObject.teu < 120000:
        #         return QVariant(QColor(Qt.blue))
        #     else:
        #         return QVariant(QColor(Qt.red))
        # elif role == Qt.BackgroundColorRole:
        #     if idfObject.country in (u"Bahamas", u"Cyprus", u"Denmark",
        #             u"France", u"Germany", u"Greece"):
        #         return QVariant(QColor(250, 230, 250))
        #     elif idfObject.country in (u"Hong Kong", u"Japan", u"Taiwan"):
        #         return QVariant(QColor(250, 250, 230))
        #     elif idfObject.country in (u"Marshall Islands",):
        #         return QVariant(QColor(230, 250, 250))
        #     else:
        #         return QVariant(QColor(210, 230, 230))
        return data

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.hlabels[section]
            if orientation == QtCore.Qt.Vertical:
                return self.vlabels[section]
        return None

    def rowCount(self, index):
        return len(self.idfObjects)

    def columnCount(self, index):
        return len(self.hlabels)

    def setData(self, index, value, role):
#        print "set data called"
        if not index.isValid() or \
                not (0 <= index.row() < len(self.idfObjects)):
#            print "data() called with invalid index"
            return False

        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            idfObject = self.idfObjects[row]

            idfObject['fields'][column] = value
            self.dirty = True
            self.dataChanged.emit(index, index)
#            print "data changed"
            return True
        return False

#    def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
#        self.beginInsertRows(QtCore.QModelIndex(), position,
#                             position + rows - 1)
#        for row in range(rows):
#            self.idfObjects.insert(position + row, [])
##                                   IDFObject(" Unknown",
##                                             " Unknown",
##                                             " Unknown"))
#        self.endInsertRows()
#        self.dirty = True
#        return True
#
#    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
#        self.beginRemoveRows(QtCore.QModelIndex(), position,
#                             position + rows - 1)
#        self.idfObjects = self.idfObjects[:position] + \
#                     self.idfObjects[position + rows:]
#        self.endRemoveRows()
#        self.dirty = True
#        return True

    def load(self):
#        self.idfObjects = []
        hlabels = []
        for tag_item in self.iddPart['field_tags']:
            for tag in tag_item:
                if tag['tag'] == '\\field':
                    hlabels.append(tag['value'])

        vlabels = ['Obj' + str(i) for i in range(len(self.idfObjects))]

        self.vlabels = vlabels
        self.hlabels = hlabels

        # exception = None
        # fh = None
        # try:
        #     if self.filename.isEmpty():
        #         raise IOError, "no filename specified for loading"
        #     fh = QFile(self.filename)
        #     if not fh.open(QIODevice.ReadOnly):
        #         raise IOError, unicode(fh.errorString())
        #     stream = QDataStream(fh)
        #     magic = stream.readInt32()
        #     if magic != MAGIC_NUMBER:
        #         raise IOError, "unrecognized file type"
        #     fileVersion = stream.readInt16()
        #     if fileVersion != FILE_VERSION:
        #         raise IOError, "unrecognized file type version"
        #     self.idfObjects = []
        #     while not stream.atEnd():
        #         name = QString()
        #         owner = QString()
        #         country = QString()
        #         description = QString()
        #         stream >> name >> owner >> country >> description
        #         teu = stream.readInt32()
        #         self.idfObjects.append(IDFObject(name, owner, country, teu,
        #                                description))
        #         self.owners.add(unicode(owner))
        #         self.countries.add(unicode(country))
        #     self.dirty = False
        # except IOError, e:
        #     exception = e
        # finally:
        #     if fh is not None:
        #         fh.close()
        #     if exception is not None:
        #         raise exception

    def save(self):
        exception = None
        fh = None
        try:
            if self.filename.isEmpty():
                raise IOError, "no filename specified for saving"
            fh = QFile(self.filename)
            if not fh.open(QIODevice.WriteOnly):
                raise IOError, unicode(fh.errorString())
            stream = QDataStream(fh)
            stream.writeInt32(MAGIC_NUMBER)
            stream.writeInt16(FILE_VERSION)
            stream.setVersion(QDataStream.Qt_4_1)
            for idfObject in self.idfObjects:
                stream << idfObject.name << idfObject.owner << idfObject.country \
                       << idfObject.description
                stream.writeInt32(idfObject.teu)
            self.dirty = False
        except IOError, e:
            exception = e
        finally:
            if fh is not None:
                fh.close()
            if exception is not None:
                raise exception


class IDFObjectDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(IDFObjectDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if index.column() == DESCRIPTION:
            text = index.model().data(index).toString()
            palette = QApplication.palette()
            document = QTextDocument()
            document.setDefaultFont(option.font)
            if option.state & QStyle.State_Selected:
                document.setHtml(QString("<font color=%1>%2</font>") \
                        .arg(palette.highlightedText().color().name()) \
                        .arg(text))
            else:
                document.setHtml(text)
            color = palette.highlight().color() \
                if option.state & QStyle.State_Selected \
                else QColor(index.model().data(index,
                            Qt.BackgroundColorRole))
            painter.save()
            painter.fillRect(option.rect, color)
            painter.translate(option.rect.x(), option.rect.y())
            document.drawContents(painter)
            painter.restore()
        else:
            QItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        fm = option.fontMetrics
        if index.column() == TEU:
            return QSize(fm.width("9,999,999"), fm.height())
        if index.column() == DESCRIPTION:
            text = index.model().data(index).toString()
            document = QTextDocument()
            document.setDefaultFont(option.font)
            document.setHtml(text)
            return QSize(document.idealWidth() + 5, fm.height())
        return QItemDelegate.sizeHint(self, option, index)

    def createEditor(self, parent, option, index):
        if index.column() == TEU:
            spinbox = QSpinBox(parent)
            spinbox.setRange(0, 200000)
            spinbox.setSingleStep(1000)
            spinbox.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return spinbox
        elif index.column() == OWNER:
            combobox = QComboBox(parent)
            combobox.addItems(sorted(index.model().owners))
            combobox.setEditable(True)
            return combobox
        elif index.column() == COUNTRY:
            combobox = QComboBox(parent)
            combobox.addItems(sorted(index.model().countries))
            combobox.setEditable(True)
            return combobox
        elif index.column() == NAME:
            editor = QLineEdit(parent)
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor
        elif index.column() == DESCRIPTION:
            editor = richtextlineedit.RichTextLineEdit(parent)
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor
        else:
            return QItemDelegate.createEditor(self, parent, option,
                                              index)

    def commitAndCloseEditor(self):
        editor = self.sender()
        if isinstance(editor, (QTextEdit, QLineEdit)):
            self.emit(SIGNAL("commitData(QWidget*)"), editor)
            self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole).toString()
        if index.column() == TEU:
            value = text.replace(QRegExp("[., ]"), "").toInt()[0]
            editor.setValue(value)
        elif index.column() in (OWNER, COUNTRY):
            i = editor.findText(text)
            if i == -1:
                i = 0
            editor.setCurrentIndex(i)
        elif index.column() == NAME:
            editor.setText(text)
        elif index.column() == DESCRIPTION:
            editor.setHtml(text)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == TEU:
            model.setData(index, editor.value())
        elif index.column() in (OWNER, COUNTRY):
            text = editor.currentText()
            if text.length() >= 3:
                model.setData(index, text)
        elif index.column() == NAME:
            text = editor.text()
            if text.length() >= 3:
                model.setData(index, text)
        elif index.column() == DESCRIPTION:
            model.setData(index, editor.toSimpleHtml())
        else:
            QItemDelegate.setModelData(self, editor, model, index)
