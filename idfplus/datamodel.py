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
import os
import ZODB
from collections import OrderedDict
from pint import UnitRegistry
from persistent import Persistent
from persistent.list import PersistentList
from persistent.dict import PersistentDict
from persistent.mapping import PersistentMapping
from odict.pyodict import _odict, _nil
from BTrees.OOBTree import OOBTree

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

class IDDFileDoesNotExist(Exception):
    """Exception called when no IDD file is found."""
    def __init__(self, message, version):
        self.message = message
        self.version = version


class VersionAlreadySet(Exception):
    """Exception called when the IDD/IDF version is already set."""
    pass


class PODict(_odict, PersistentMapping):

    def _dict_impl(self):
        return PersistentMapping


# class PODict(_odict, OOBTree):
#
#     def _dict_impl(self):
#         return OOBTree
#
#     def _get_lh(self):
#         try:
#             return self['____lh']
#         except KeyError:
#             self['____lh'] = _nil
#         return self['____lh']
#
#     def _set_lh(self, val):
#         self['____lh'] = val
#
#     lh = property(_get_lh, _set_lh)
#
#     def _get_lt(self):
#         try:
#             return self['____lt']
#         except KeyError:
#             self['____lt'] = _nil
#         return self['____lt']
#
#     def _set_lt(self, val):
#         self['____lt'] = val
#
#     lt = property(_get_lt, _set_lt)
#
#     def __getitem__(self, key):
#         if key.startswith('____'):
#             return self._dict_impl().__getitem__(self, key)
#         return _odict.__getitem__(self, key)
#
#     def __setitem__(self, key, val=None):
#         if key.startswith('____'):
#             # private attributes, no way to set persistent attributes on
#             # OOBTree deriving class.
#             print('private attribute fail {}'.format(key))
#             self._dict_impl().__setitem__(self, key, val)
#         else:
#             # super(PODict, self).__setitem__(key, val)
#             print('key: {}, val: {}'.format(key, val))
#             _odict.__setitem__(self, key, val)
#
#     def __repr__(self):
#         if self:
#             pairs = ("(%r, %r)" % (k, v) for k, v in self.iteritems())
#             return "OOBTodict([%s])" % ", ".join(pairs)
#         else:
#             return "OOBTodict()"


# class PODict(OrderedDict):
#     """Custom OrderedDict that ensures the 'changed' flag is set for ZODB
#     persistence."""
#
#     def __init__(self):
#         self._data = OrderedDict()
#         super(PODict, self).__init__()
#
#     def __delitem__(self, key, dict_delitem=dict.__delitem__):
#         self._data.__delitem__(key, dict_delitem)
#         self._data._p_changed = True
#         self._p_changed = True
#
#     def __getitem__(self, key):
#         return self._data.__getitem__(key)
#
#     def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
#         self._data.__setitem__(key, value, dict_setitem)
#         self._data._p_changed = True
#         self._p_changed = True
#
#     # def __getattribute__(self, name):
#     #     return self._data.__getattribute__(name)
#     #
#     # def __setattr__(self, name, value):
#     #     return self._data.__setattr__(name, value)
#
#     def __contains__(self, key):
#         return self._data.__contains__(key)
#
#     def __len__(self):
#         return self._data.__len__()
#
#     def __iter__(self):
#         return self._data.__iter__()
#
#     def __delattr__(self, name):
#         return self._data.__delattr__(name)
#
#     def __repr__(self, _repr_running={}):
#         return self._data.__repr__(_repr_running)
#
#     def __format__(self, *args, **kwargs):
#         return self._data.__format__(*args, **kwargs)
#
#     def clear(self):
#         self._data.clear()
#         self._data._p_changed = True
#         self._p_changed = True
#
#     def update(self, other=None, **kwargs):
#         self._data.update(other, **kwargs)
#         self._data._p_changed = True
#         self._p_changed = True
#
#     def itervalues(self):
#         return self._data.itervalues()
#
#     def iteritems(self):
#         return self._data.iteritems()
#
#     def iterkeys(self):
#         return self._data.iterkeys()
#
#     def setdefault(self, key, default=None):
#         if not key in self._data:
#             self._data._p_changed = True
#             self._p_changed = True
#         return self._data.setdefault(key, default)
#
#     def values(self):
#         return self._data.values()
#
#     def keys(self):
#         return self._data.keys()
#
#     def items(self):
#         return self._data.items()
#
#     def get(self, key, default=None):
#         return self._data.get(key, default)
#
#     def pop(self, key, default=OrderedDict._OrderedDict__marker):
#         self._data._p_changed = True
#         self._p_changed = True
#         return self._data.pop(key, default)
#
#     def popitem(self, last=True):
#         self._data._p_changed = True
#         self._p_changed = True
#         return self._data.popitem(last)


class IDDFile(PODict):
    """Primary object representing idd file and container for idd objects.

    Is an OrderedDict of IDDObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': IDDObject,
         'SimulationControl':  IDDObject}

    :attr str version: IDD file version
    :attr list groups: List of groups to which classes can belong
    """

    def __init__(self, version=None, data=(), **kwargs):
        """Initializes the idd file

        :param str version: IDD file version
        :param list groups: list of groups from the idd file
        :param list conversions: list of unit conversions from the idd file
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Various attributes of the idd file
        self._groups = list()
        self._conversions = list()
        self._version_set = False
        # self._data = OrderedDict()
        self._version = version
        self.options = list()
        self.tags = dict()
        # compiled_idd_file_name = 'EnergyPlus_IDD_v{}.dat'
        data_dir = 'data'
        units_file = 'units.dat'
        self._ureg = None #UnitRegistry(os.path.join(APP_ROOT, data_dir, units_file))

        # # Continue only if a version is specified, else a blank IDD file
        # if version:
        #
        #     # Create the full path to the idd file
        #     idd_file_path = os.path.join(APP_ROOT, data_dir,
        #                                  compiled_idd_file_name.format(version))
        #     print(idd_file_path)
        #     # Check if the file name is a file and then open the idd file
        #     if os.path.isfile(idd_file_path):
        #         storage = ZODB.FileStorage.FileStorage(idd_file_path)
        #         db = ZODB.DB(storage)
        #         connection = db.open()
        #
        #         with db.open() as connection:
        #             root = connection.root
        #
        #             try:
        #                 test = root.idd.version
        #                 return root.idd
        #             except AttributeError:
        #                 raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_file_path))

                # f = shelve.open(idd_file_path)

                # if f.get('idd', None):
                #     return f
                # else:
                #     raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_file_path))
            #     # Set some more attributes with using the idd file
            #     self._groups = f['groups']
            #     self._conversions = f.get('conversions', None)
            #     #self._class_tree = f['class_tree']  # To be implemented
            #     self._OrderedDict__update(f['idd'])
            #
            #     f.close()
            # else:
            #     raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_file_path))

        # Call the parent class' init method
        super(IDDFile, self).__init__(data, **kwargs)

    # def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
    #     """Override the default __setitem__ to ensure that only certain
    #     object types are allowed."""
    #
    #     if not isinstance(value, IDDObject):
    #         print('value is: {}'.format(value))
    #         raise TypeError('Only items of type IDDObject can be added!')
    #
    #     super(IDDFile, self).__setitem__(key, value, dict_setitem)

    # def _set_version(self, version):
    #     """Method used to set the version of the IDD file. Can only
    #     :param str version:
    #     be set once for safety and sanity."""
    #     if self._version_set is True:
    #         raise VersionAlreadySet('Version can be set only once.')
    #     else:
    #         self._version = version
    #         self._version_set = True

    @property
    def version(self):
        """Read-only property containing idf file version."""
        return self._version

    @property
    def groups(self):
        """Read-only property containing list of all possible class groups"""
        return self._groups

    @property
    def conversions(self):
        """Read-only property containing list unit conversions"""
        return self._conversions


class IDDObject(list):
    """Represents objects in idd files.

    Contains a list of fields in the form:
        [IDDField1, IDDField2, IDDField3}
    """

    def __init__(self, outer, data=(), **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param str obj_class: Class type of this idf object
        :param str group: group that this idd object belongs to
        :param IDDFile outer: the outer object for this object (type IDDFile)
        :param args: arguments to pass to dictionary
        :param kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self._obj_class = kwargs.pop('obj_class', None)
        self._group = kwargs.pop('group', None)
        # self._outer = outer
        # self._idd = outer
        self.tags = dict()  # TODO populate this during parsing (only fields done now)
        self.comments = kwargs.pop('comments', None)
        self.comments_special = kwargs.pop('comments_special', None)

        # Call the parent class' init method
        super(IDDObject, self).__init__(data, **kwargs)

    # def __setitem__(self, key, value):
    #     """Override the default __setitem__ to ensure that only certain
    #     object types are allowed."""
    #
    #     if not isinstance(value, IDDField):
    #         raise TypeError('Only items of type IDDField can be added!')
    #
    #     super(IDDObject, self).__setitem__(key, value)

    @property
    def obj_class(self):
        """Read-only property containing idd object's class type
        :returns str: Returns the obj_class string
        """
        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idd object's group.
        :rtype : str
        """
        return self._group

    @property
    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj"""

        memo = self.tags.get('memo')
        if type(memo) is list:
            info = ' '.join(self.tags.get('memo', ''))
        else:
            info = memo

        unique = 'Yes' if 'unique-object' in self.tags else 'No'
        required = 'Yes' if 'required-object' in self.tags else 'No'
        obsolete = 'Yes' if 'obsolete' in self.tags else 'No'
        min_fields = self.tags.get('min-fields', '0')

        info += '\n\nUnique: {}'.format(unique)
        info += '\nRequired: {}'.format(required)
        info += '' if int(min_fields) <= 0 else '\nMinimum Fields: {}'.format(min_fields)
        info += '' if obsolete == 'No' else '\nObject Obsolete: {}'.format(obsolete)

        return info


class IDDField(object):
    """Basic component of the idd object classes.

    A regular object containing parameters such as key, value, tags.
    Examples of tags from are:
        required, field, type, minimum, etc.
    """

    #TODO Values should be Quantities from the pint python library.
    #TODO merge this class with IDFField?

    def __init__(self, outer, **kwargs):

        self.value = kwargs.pop('value', None)
        self.key = kwargs.pop('key', None)
        # self._idd = outer._idd
        # self._outer = outer
        self.obj_class = outer.obj_class
        self.tags = dict()

        # if iterable:
        #     iterable.setdefault(key, key)
        #     iterable.setdefault(value, value)

         # Call the parent class' init method
        super(IDDField, self).__init__()

    # @property
    # def units(self):
    #     """Read-only property containing idd field's SI units.
    #     :rtype : str
    #     """
    #     return self._value # .units
    #
    # @property
    # def ip_units(self):
    #     """Read-only property containing idd field's IP units.
    #     :rtype : str
    #     """
    #     return self._value # _ip_units


class IDFFile(PODict):
    """Primary object representing idf file and container for idf objects.

    Contains an OrderedDict of lists of IDFObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': [IDFObject1, IDFObject2, IDFObject3],
         'SimulationControl':  [IDFObject4]}

    :attr IDDFile idd: IDDFile object containing precompiled idd file
    :attr str version: EnergyPlus vesion number (eg. 8.1.0.008)
    :attr str eol_char: depends on file (could be \n or \r\n, etc)
    :attr list options: options that may have been found in idf file
    :attr str file_path: full, absolute path to idf file
    """

    def __init__(self, data=(), **kwargs):
        """Initializes a new idf, blank or opens the given file_path

        :param str file_path:
        :param *args: arguments to pass to base dictionary type
        :param **kwargs: keyword arguments to pass to base dictionary type
        """

        # Various attributes of the idf file
        self._version_set = False
        self._idd = None
        self._eol_char = None
        self.file_path = None
        self.options = PersistentList()
        self._version = None

        # # Load the idf file if specified, otherwise prepare a blank one
        # if file_path:
        #     from . import idfparse
        #     print("IDFFile file_path: {}".format(file_path))
        #     self.file_path = file_path
        #     parser = idfparse.IDFParser(self)
        #     for progress in parser.parse_idf():
        #         # print(progress)
        #         yield progress
        # else:
        #     default = '8.1'  # retrieve this from settings eventually
        #     self._version = kwargs.pop('version', default)
        #     self._idd = IDDFile(self._version)
        # yield self

        # Call the parent class' init method
        super(IDFFile, self).__init__(data, **kwargs)

    # def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
    #     """Override the default __setitem__ to ensure that only certain
    #     object types are allowed."""
    #
    #     if not isinstance(value, list):
    #         raise TypeError('Only lists of IDFObjects can be added!')
    #
    #     for val in value:
    #         if not isinstance(val, IDFObject):
    #             raise TypeError('Only items of type IDFObject can be added!')
    #
    #     super(IDFFile, self).__setitem__(key, value, dict_setitem)

    # def __getitem__(self, key):
    #     """"""
    #     # print(key)
    #     # print(type(self))
    #     # print(type(self._classes))
    #     # print(self._classes.items())
    #     # print(self.file_path)
    #     # print(self._classes)
    #     if key in self._classes:
    #         return self._classes[key]
    #     else:
    #         return None

    # def load_idd(self):
    #     """Loads an idd file into the object instance variable.
    #     Also sets some attributes of the file.
    #     :rtype : bool
    #     :param version:
    #     :return: :raise IDDFileDoesNotExist:
    #     """
    #
    #     idd_file_name = 'EnergyPlus_IDD_v{}.dat'.format(self.version)
    #     data_dir = 'data'
    #
    #     # Create the full path to the idd file
    #     idd_file_path = os.path.join(APP_ROOT, data_dir, idd_file_name)
    #     print('checking for idd version: {}'.format(self.version))
    #     print(idd_file_path)
    #
    #     # Check if the file name is a file and then open the idd file
    #     if os.path.isfile(idd_file_path):
    #         print('idd found, loading...')
    #         # storage = ZODB.FileStorage.FileStorage(idd_file_path)
    #         db = ZODB.DB(idd_file_path)
    #         connection = db.open()
    #         root = connection.root
    #
    #         try:
    #             print('testing if loaded idd file has a version attribute')
    #             test = root.idd.version
    #             idd = root.idd
    #             self._idd = idd
    #             # db.close()
    #             return True
    #         except AttributeError:
    #             print('no version attribute found!')
    #             raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_file_path))
    #     else:
    #         print('idd not found')
    #         raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_file_path))

    # def load_idf(self, file_path):
    #     """Parses and loads an idf file into the object instance variable.
    #     Also sets some attributes of the file.
    #     :param file_path:
    #     """
    #     from . import idfparse
    #     print("IDFFile file_path: {}".format(file_path))
    #     self.file_path = file_path
    #     parser = idfparse.IDFParser(self)
    #     for progress in parser.parse_idf():
    #         # print(progress)
    #         yield progress

    # def _set_version(self, version):
    #     """Method used to set the version of the IDF file. Can only
    #     be set once for safety and sanity."""
    #     if self._version_set is True:
    #         raise VersionAlreadySet('Version can be set only once.')
    #     else:
    #         self._version = version
    #         self._version_set = True

    @property
    def version(self):
        """Read-only property containing idf file version"""
        return self._version

    @property
    def idd(self):
        """Read-only property containing idd file"""
        return self._idd

    def find(self, contains=None):
        """Searches within the file for objects having 'contains'
        :param str contains:  (Default value = None)
        """
        pass

    def save(self, file_path):
        """Handles writing of the idf file back to disk.
        :param str file_path: The absolute file path to the corresponding idf
        """
#        exception = None
#        fh = None
#        try:
#            if file_path.isEmpty():
#                raise IOError, "no filename specified for saving"
#            fh = QtCore.QFile(self.file_path)
#            if not fh.open(QtCore.QIODevice.WriteOnly):
#                raise IOError, unicode(fh.errorString())
#            stream = QtCore.QDataStream(fh)
#            stream.writeInt32(MAGIC_NUMBER)
#            stream.writeInt16(FILE_VERSION)
#            stream.setVersion(QtCore.QDataStream.Qt_4_1)
#            for idfObject in self.idfObjects:
#                stream << idfObject.name << idfObject.owner \
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
        pass


class IDFObject(PersistentList):
    """Represents objects in idf files.

    Contains a list of fields in the form:
        [IDFField1, IDFField2, IDFField3]

    :attr str obj_class: Class type of object
    :attr str group: Group to which this object belongs
    :attr IDFFile idd: Contains the IDD file used by this IDF object
    :attr list comments: User comments for this object
    :attr list incoming_links: List of tuples of objects that link to this
    :attr list outgoing_links: List of tuples of objects to which this links
    """

    #TODO This class is almost the same as IDDObject. It should subclass it.

    def __init__(self, idf, data=(), **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param str group:
        :param str outer:
        :param str args:
        :param IDDFile idd: idd file used by this idf file
        :param str obj_class: Class type of this idf object
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        # self._idf = idf
        # self._idd = idf.idd
        self._incoming_links = PersistentList()
        self._outgoing_links = PersistentList()
        self._group = kwargs.pop('group', None)
        self._obj_class = kwargs.pop('obj_class', None)
        self.comments = kwargs.pop('comments', None)

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

    # def __repr__(self):
    #     """Returns a string representation of the object in idf format"""
    #     values = [str(val) for val in self.value()]
    #     str_list = ','.join(values)
    #     return self._obj_class + ',' + str_list + ';'

    # @property
    # def idd(self):
    #     """Read-only property containing idd file
    #     :rtype : IDDFile"""
    #     return self._idd

    @property
    def obj_class(self):
        """Read-only property containing idf object's class type
        :rtype : str"""
        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idf object's group
        :rtype : str"""
        return self._group

    @property
    def incoming_links(self):
        """Read-only property containing incoming links
        :rtype : list"""
        return self._incoming_links

    @property
    def outgoing_links(self):
        """Read-only property containing outgoing links
        :rtype : list
        """
        return self._outgoing_links

    # @property
    # def idf_file(self):
    #     """Read-only property containing the outer class of this obj
    #     :rtype : IDFFile"""
    #     return self._idf_file

#    def value(self, field):
#        """Returns the value of the specified field.
#
#        :param field: Field id or key to be retrieved
#        :raises TypeError: If field is not a string or an int
#        """
#
#        # Check for proper types and return the value
#        if isinstance(field, int):
#            return self[self.keys()[field]]
#        elif isinstance(field, str):
#            return self[field]
#        else:
#            raise TypeError('Invalid key type - must be string or int')

    def add_link(self, obj, field_id, incoming=False, outgoing=False):
        """Ads a link to and/or from this object.

        :param IDFObject obj: Another object of type IDFObject
        :param str field_id: A field id like 'A1' or 'N1'
        :param bool incoming:  (Default value = False)
        :param bool outgoing:  (Default value = False)
        :raises ValueError: If neither incoming nor outgoing is True
        :raises TypeError: If either field_id or obj are not a valid types
        """

        # Checks for valid inputs
        if not incoming and not outgoing:
            raise ValueError('Must specify either incoming or outgoing.')
        if not isinstance(obj, IDFObject) or not isinstance(field_id, str):
            raise TypeError('Invalid object or field_id type.')

        # Adds the specified objects to the list(s) of links
        link = (obj, field_id)
        if incoming and link not in self._incoming_links:
            self._incoming_links.append((obj, field_id))
        if outgoing and link not in self._outgoing_links:
            self._outgoing_links.append((obj, field_id))
        return True

    def remove_link(self, obj, field_id, incoming=False, outgoing=False):
        """Removes a link to and/or from this object.

        :param IDFObject obj: Another object of type IDFObject
        :param str field_id: A field id like 'A1' or 'N1'
        :param bool incoming:  (Default value = False)
        :param bool outgoing:  (Default value = False)
        :raises ValueError: If neither incoming nor outgoing is True
        :raises TypeError: If either field_id or obj are not a valid types
        """

        # Checks for valid inputs
        if not incoming and not outgoing:
            raise ValueError('Must specify either incoming or outgoing.')
        if not isinstance(obj, IDFObject) or not isinstance(field_id, str):
            raise TypeError('Invalid object or field_id type.')

        # Removes the specified objects to the list(s) of links
        link = (obj, field_id)
        if incoming and link in self._incoming_links:
            self._incoming_links.remove(link)
        if outgoing and link in self._outgoing_links:
            self._outgoing_links.remove(link)
        return True

    def set_defaults(self, idd):
        """Populates the field with its defaults"""

        # print('setting defaults')
        idd_objects = idd.get(self.obj_class)
        for i, field in enumerate(idd_objects):
            default = field.tags.get('default', '')
            try:
                self[i].value = default
            except IndexError:
                self.append(IDFField(self, value=default))
            # print('default set: {}'.format(self[i]))


class IDFField(Persistent):
    """Basic component of the idf object classes.

    Simply a regular dict containing keys which are the names of various
    field tags from the following list:
        required, field, type, minimum, etc.
    """

    # TODO This class is actually the same as IDDField. Merge them?

    def __init__(self, outer, *args, **kwargs):
        """Initializes a new idf field
        :param str key:
        :param value:
        :param IDFObject outer:
        """
        self.key = kwargs.pop('key', None)
        self.value = kwargs.pop('value', None)
        self.tags = PersistentDict()
        self.obj_class = outer.obj_class
        self._ureg = None #outer.idd._ureg

        # self._idf_file = outer._outer
        # idd = outer.idd
        # self._units = outer.idd[self._obj_class][key].units
        # self._ip_units = outer.idd[self._obj_class][key].ip_units
        # if not self._ip_units:
        #     self._ip_units = outer.idd.conversions[self._units]

        # Call the parent class' init method
        super(IDFField, self).__init__()

    def __repr__(self):
        return self.value or ''

    @property
    def field(self):
        """
        :rtype : str
        :return : The name of the field from the idd file
        """
        if 'field' in self.tags:
            return self.tags['field']
        else:
            return str()

    # def __repr__(self):
    #     return self._idf_file.obj_class + ':' + self._key

    # def value(self, ip=False):
    #     """Returns the value of the field, optionally converted to IP units.
    #     :param bool ip:
    #     :returns: converted value
    #     """
    #     if ip:
    #         quantity = self._value * self._ureg(self._units)
    #         ip_quantity = quantity.to(self._ip_units)
    #         return ip_quantity.magnitude
    #     else:
    #         return self._value
