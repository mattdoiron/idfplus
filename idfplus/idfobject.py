#!/usr/bin/env python

from PySide import QtGui, QtCore

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
        if not index.isValid():  # or \
#                not (0 <= index.row() < len(self.idfObjects)):
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
            data = idfObject['fields'][column]
        elif role == QtCore.Qt.EditRole:
            data = idfObject['fields'][column]
        elif role == QtCore.Qt.ToolTipRole:
            data = "tooltip test"
#            return msg
#        elif role == QtCore.Qt.DecorationRole:
#            data = QtGui.QIcon("icon.png")
        #    row = index.row()
        #    value = self.__colors[row]
        #
        #    pixmap = QtGui.QPixmap(26, 26)
        #    pixmap.fill(value)
        #
        #    icon = QtGui.QIcon(pixmap)
        #    return icon
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
                return self.field_labels[section]
            if orientation == QtCore.Qt.Vertical:
                return self.objID_lables[section]
        return None

    def rowCount(self, index):
        return len(self.idfObjects)

    def columnCount(self, index):
        return len(self.field_labels)

    def setData(self, index, value, role):
        if not index.isValid():  # or \
#                not (0 <= index.row() < len(self.idfObjects)):
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
        field_labels = []
        for tag_item in self.iddPart['field_tags']:
            for tag in tag_item:
                if tag['tag'] == '\\field':
                    field_labels.append(tag['value'])

        objID_lables = ['Obj' + str(i) for i in range(1, len(self.idfObjects) + 1)]

        self.objID_lables = objID_lables
        self.field_labels = field_labels

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

#    def save(self):
#        exception = None
#        fh = None
#        try:
#            if self.filename.isEmpty():
#                raise IOError, "no filename specified for saving"
#            fh = QFile(self.filename)
#            if not fh.open(QIODevice.WriteOnly):
#                raise IOError, unicode(fh.errorString())
#            stream = QDataStream(fh)
#            stream.writeInt32(MAGIC_NUMBER)
#            stream.writeInt16(FILE_VERSION)
#            stream.setVersion(QDataStream.Qt_4_1)
#            for idfObject in self.idfObjects:
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


class TransposeProxyModel(QtGui.QAbstractProxyModel):
    '''Translates columns to rows or vice versa'''

    def __init__(self, parent=None):
        super(TransposeProxyModel, self).__init__(parent)

    def setSourceModel(self, source):
        super(TransposeProxyModel, self).setSourceModel(source)

        # connect signals
        self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)

#        self.sourceModel().rowsInserted.connect(self._rowsInserted)
#        self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
#        self.sourceModel().dataChanged.connect(self._dataChanged)

    def mapFromSource(self, sourceIndex):
        if not sourceIndex.isValid():
            return QtCore.QModelIndex()
        return self.createIndex(sourceIndex.column(),
                                sourceIndex.row(),
                                QtCore.QModelIndex())

    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return QtCore.QModelIndex()
        return self.sourceModel().createIndex(proxyIndex.column(),
                                              proxyIndex.row(),
                                              QtCore.QModelIndex())

    def index(self, row, col, parent):
        return self.createIndex(row, col)

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent):
        if self.sourceModel():
            return self.sourceModel().columnCount(QtCore.QModelIndex())
        else:
            return 0

    def columnCount(self, parent):
        if self.sourceModel():
            return self.sourceModel().rowCount(QtCore.QModelIndex())
        else:
            return 0

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            new_orientation = QtCore.Qt.Vertical
        else:
            new_orientation = QtCore.Qt.Horizontal
        return self.sourceModel().headerData(section, new_orientation, role)
