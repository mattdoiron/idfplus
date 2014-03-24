#!/usr/bin/env python

from PySide import QtGui, QtCore


class GenericDelegate(QtGui.QItemDelegate):
    '''Template delegate for the table view.'''

    def __init__(self, idd_obj, obj_orientation, parent=None):
        super(GenericDelegate, self).__init__(parent)
        self.delegates = {}
        self.obj_orientation = obj_orientation
        self.assignDelegates(idd_obj)

    def insertDelegate(self, index, delegate):
        delegate.setParent(self)
        self.delegates[index] = delegate

    def removeDelegate(self, index):
        if index in self.delegates:
            del self.delegates[index]

    def getRowOrCol(self, index):
        if self.obj_orientation == QtCore.Qt.Horizontal:
            return index.column()
        if self.obj_orientation == QtCore.Qt.Vertical:
            return index.row()

    def paint(self, painter, option, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            QtGui.QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QtGui.QItemDelegate.createEditor(self, parent,
                                                    option, index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QtGui.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(self.getRowOrCol(index))
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            QtGui.QItemDelegate.setModelData(self, editor, model, index)

#    def paint(self, painter, option, index):
#        if index.column() == DESCRIPTION:
#            text = index.model().data(index).toString()
#            palette = QApplication.palette()
#            document = QTextDocument()
#            document.setDefaultFont(option.font)
#            if option.state & QStyle.State_Selected:
#                document.setHtml(QString("<font color=%1>%2</font>") \
#                        .arg(palette.highlightedText().color().name()) \
#                        .arg(text))
#            else:
#                document.setHtml(text)
#            color = palette.highlight().color() \
#                if option.state & QStyle.State_Selected \
#                else QColor(index.model().data(index,
#                            Qt.BackgroundColorRole))
#            painter.save()
#            painter.fillRect(option.rect, color)
#            painter.translate(option.rect.x(), option.rect.y())
#            document.drawContents(painter)
#            painter.restore()
#        else:
#            QItemDelegate.paint(self, painter, option, index)

#    def sizeHint(self, option, index):
#        fm = option.fontMetrics
#        if index.column() == TEU:
#            return QSize(fm.width("9,999,999"), fm.height())
#        if index.column() == DESCRIPTION:
#            text = index.model().data(index).toString()
#            document = QTextDocument()
#            document.setDefaultFont(option.font)
#            document.setHtml(text)
#            return QSize(document.idealWidth() + 5, fm.height())
#        return QItemDelegate.sizeHint(self, option, index)

#    def commitAndCloseEditor(self):
#        editor = self.sender()
#        if isinstance(editor, (QTextEdit, QLineEdit)):
#            self.emit(SIGNAL("commitData(QWidget*)"), editor)
#            self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def assignDelegates(self, idd_obj):
        # cycle through table and assign delegates as needed
        # This will depend on the type of idd object!

        # Other fields to be passed to the delegate include:
        #       field, note, units, ip-units, required-field, key(s)

        # List of tags that would go in a combobox
        comboFields = ['\\minimum',
                       '\\minimum>',
                       '\\maximum',
                       '\\maximum<',
                       '\\default',
                       '\\autosizeable',
                       '\\autocalculatable',
                       '\\key']

        # Cycle through field tags (first one is object tags so ignore)
        for i, tags in enumerate(idd_obj['field_tags'][1:]):

            tag_list = []
            tag_count = 0
            field_type = ''

            # Create a list of tags which would go in a combo box
            # There is a better way to do this - idd objects should be
            # actual python objects/dictionaries!
            for tag in tags:
                if tag['tag'] in comboFields:
                    tag_list.append(tag['tag'])
                    tag_count += 1
                if tag['tag'] == '\\type':
                    field_type = tag['value']

            # If there are choices then use the choiceDelegate
            if tag_count > 0:
                self.insertDelegate(i, ChoiceDelegate(tags))
            else:
                # Otherwise check the type field
                if field_type == 'integer':
                    self.insertDelegate(i, IntegerDelegate(tags))
                elif field_type == 'real':
                    self.insertDelegate(i, RealDelegate(tags))
                elif field_type == 'alpha':
                    self.insertDelegate(i, AlphaDelegate(tags))
                else:
                    # The type filed is not always present so check fieldname
                    fieldName = idd_obj['fields'][i - 1]
                    if fieldName.startswith('A'):
                        self.insertDelegate(i, AlphaDelegate(tags))
                    elif fieldName.startswith('N'):
                        self.insertDelegate(i, RealDelegate(tags))
                    else:
                        self.insertDelegate(i, AlphaDelegate(tags))


class IntegerDelegate(QtGui.QItemDelegate):

    def __init__(self, idd_obj, minimum=0, maximum=100, parent=None):
        super(IntegerDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.idd_obj = idd_obj
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        spinbox = QtGui.QSpinBox(parent)
        spinbox.setRange(self.minimum, self.maximum)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        return spinbox

    def setEditorData(self, editor, index):
        value = int(index.data(QtCore.Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        model.setData(index, editor.value(), QtCore.Qt.EditRole)


class RealDelegate(QtGui.QItemDelegate):

    def __init__(self, idd_obj, minimum=0, maximum=100, default=0, decimals=10, parent=None):
        super(RealDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals
        self.default = default
        self.idd_obj = idd_obj
        # use idd object to define min, max, etc

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        validator = QtGui.QDoubleValidator(self)
        validator.setRange(self.minimum, self.maximum, self.decimals)
        validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
        lineedit.setValidator(validator)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), QtCore.Qt.EditRole)


class AlphaDelegate(QtGui.QItemDelegate):

    def __init__(self, idd_obj, parent=None):
        super(AlphaDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        lineedit = QtGui.QLineEdit(parent)
        lineedit.setFrame(False)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), QtCore.Qt.EditRole)


class ChoiceDelegate(QtGui.QItemDelegate):

    def __init__(self, field, parent=None):
        super(ChoiceDelegate, self).__init__(parent)
#        self.model = model
        self.field = field
        self.comboFields = ['\\minimum',
                            '\\minimum>',
                            '\\maximum',
                            '\\maximum<',
                            '\\default',
                            '\\autosizeable',
                            '\\autocalculatable',
                            '\\key']

    def imActivated(self, index):
#        self.combo.showPopup()
#        print 'i was activated'
        pass

    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        combo.setFrame(False)
        combo.setEditable(True)
#        self.combo = combo
        combo.editTextChanged.connect(self.imActivated)
#        combo.setMinimumContentsLength(30)
#        combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        model = QtGui.QStandardItemModel()
        tag_list = []

        for tag in self.field:
            if tag['tag'] in self.comboFields:
                value_item = QtGui.QStandardItem(tag['value'])
                tag_item = QtGui.QStandardItem(tag['tag'].strip('\\'))
                if tag['tag'] == '\\default':
                    model.insertRow(0, [value_item, tag_item])
                else:
                    model.appendRow([value_item, tag_item])
                tag_list.append(tag['tag'])

#        print 'found tags: {}'.format(tag_list)
        myitem = model.findItems('current', column=1)
        if len(myitem) > 0:
            model.removeRow(myitem[0].row())

        value = index.data(QtCore.Qt.DisplayRole)
        current_item = QtGui.QStandardItem('current')
        value_item = QtGui.QStandardItem(value)
        model.insertRow(0, [value_item, current_item])

        tableView = QtGui.QTableView(parent)
        tableView.setModel(model)
        tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        tableView.setAutoScroll(False)
        tableView.resizeColumnsToContents()
        tableView.resizeRowsToContents()
#        tableView.setContentsMargins(0,0,0,0)
#        tableView.setSortingEnabled(True)
        tableView.verticalHeader().setVisible(False)
        tableView.horizontalHeader().setVisible(False)
        tableView.setMinimumWidth(tableView.horizontalHeader().length())
        tableView.setFrameShape(QtGui.QFrame.NoFrame)
#        tableView.setFrame(False)

        # Table AND combo get same model (table first!)
        combo.setModel(model)
        combo.setView(tableView)
#        combo.setContentsMargins(0,0,0,0)
#        combo.showPopup()
        return combo

    def setEditorData(self, editor, index):
#        editor.showPopup()
        value = index.data(QtCore.Qt.DisplayRole)
        comboIndex = editor.findText(value)
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), QtCore.Qt.EditRole)


#class DateDelegate(QtGui.QItemDelegate):
#
#    def __init__(self, minimum=QtCore.QDate(),
#                 maximum=QtCore.QDate.currentDate(),
#                 format="yyyy-MM-dd", parent=None):
#        super(DateDelegate, self).__init__(parent)
#        self.minimum = minimum
#        self.maximum = maximum
#        self.format = format
#
#    def createEditor(self, parent, option, index):
#        dateedit = QtGui.QDateEdit(parent)
#        dateedit.setDateRange(self.minimum, self.maximum)
#        dateedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#        dateedit.setDisplayFormat(self.format)
#        dateedit.setCalendarPopup(True)
#        return dateedit
#
#    def setEditorData(self, editor, index):
#        value = index.model().data(index, QtCore.Qt.DisplayRole).toDate()
#        editor.setDate(value)
#
#    def setModelData(self, editor, model, index):
#        model.setData(index, editor.date(), QtCore.Qt.EditRole)


#class TimeDelegate(QTGui.QItemDelegate):
#
#  def getEditWidget(self):
#    e = QtGui.QLineEdit()
#    rx = QtCore.QRegExp('[0-9]{2}:[0-6]{2}')
#    e.setValidator(QtGui.QRegExpValidator(rx,e))
#    return e
