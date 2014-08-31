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
# from pint import UnitRegistry
from collections import OrderedDict
# from persistent import Persistent
# from persistent.list import PersistentList
# from persistent.dict import PersistentDict
from persistent.mapping import PersistentMapping
from odict.pyodict import _odict

# Package imports
from . import logger

# Constants
from . import idfsettings as c

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist

# Setup logging
log = logger.setup_logging(c.LOG_LEVEL, __name__)

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
        # data_dir = 'data'
        # units_file = 'units.dat'
        self._ureg = None #UnitRegistry(os.path.join(APP_ROOT, data_dir, units_file))

        # Call the parent class' init method
        super(IDDFile, self).__init__(data, **kwargs)

    def __reduce__(self):
        return super(IDDFile, self).__reduce__()

    # def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
    #     """Override the default __setitem__ to ensure that only certain
    #     object types are allowed."""
    #
    #     if not isinstance(value, IDDObject):
    #         print('value is: {}'.format(value))
    #         raise TypeError('Only items of type IDDObject can be added!')
    #
    #     super(IDDFile, self).__setitem__(key, value, dict_setitem)

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
        self.tags = dict()
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


class IDFFile(OrderedDict):
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
        self.options = list()
        self.object_lists = dict()
        self._version = None

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


class IDFObject(list):
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
        # self._incoming_links = list()
        # self._outgoing_links = list()
        self._graph = None
        self._group = kwargs.pop('group', None)
        self._obj_class = kwargs.pop('obj_class', None)
        self.comments = kwargs.pop('comments', None)

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

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

    def set_defaults(self, idd):
        """Populates the field with its defaults"""

        # print('setting defaults')
        idd_objects = idd.get(self.obj_class)
        for i, field in enumerate(idd_objects):
            default = field.tags.get('default', None)
            try:
                self[i].value = default
            except IndexError:
                if default is None:
                    self.append(default)
                else:
                    self.append(IDFField(self, value=default))


class IDFField(object):
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
        self.tags = dict()
        self.obj_class = outer._obj_class
        self._ureg = None #outer.idd._ureg
        self._outer = outer

        # self._idf_file = outer._outer
        # idd = outer.idd
        # self._units = outer.idd[self._obj_class][key].units
        # self._ip_units = outer.idd[self._obj_class][key].ip_units
        # if not self._ip_units:
        #     self._ip_units = outer.idd.conversions[self._units]

        # Call the parent class' init method
        super(IDFField, self).__init__()

    # def __repr__(self):
    #     return self.value or str()

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

#
# class PersistentDict(OrderedDict):
#     """Ordered dict that writes to a file when asked to
#     """
#
#     def __init__(self, filename, **kwargs):
#         self.flag = kwargs.get('flag', 'c')           # r=readonly, c=create, or n=new
#         self.mode = kwargs.get('mode', None)          # None or an octal triple like 0644
#         self.format = kwargs.get('format', 'pickle')  # 'csv', 'json', or 'pickle'
#         self.filename = filename
#
#         # Call the parent class' init method before self.load
#         super(PersistentDict, self).__init__()
#
#         # Call self.load
#         if self.flag != 'n' and os.access(filename, os.R_OK):
#             with open(filename, 'rb') as fileobj:
#                 self.update(pickle.load(fileobj))
#                 # return pickle.load(fileobj)
#
#     def sync(self):
#         '''Write dict to disk'''
#         if self.flag == 'r':
#             return
#         filename = self.filename
#         tempname = filename + '.tmp'
#         with open(tempname, 'wb') as fileobj:
#             try:
#                 # self.dump(fileobj)
#                 pickle.dump(self, fileobj, 2)
#             except Exception:
#                 os.remove(tempname)
#                 raise
#         shutil.move(tempname, self.filename)    # atomic commit
#         if self.mode is not None:
#             os.chmod(self.filename, self.mode)
#
#     def close(self):
#         self.sync()
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, *exc_info):
#         self.close()
#
#
# class IDDFile2(PersistentDict):
#     """Ordered dict that writes to a file when asked to
#     """
#
#     def __init__(self, filename, **kwargs):
#
#         # Various attributes of the idd file
#         self._groups = list()
#         self._conversions = list()
#         self._version_set = False
#         self._version = kwargs.get('version', None)
#         self.options = list()
#         self.tags = dict()
#         self._ureg = None
#
#         # Call the parent class' init method before self.load
#         super(IDDFile2, self).__init__(filename, **kwargs)
#
#     @property
#     def version(self):
#         """Read-only property containing idf file version."""
#         # return '8.1'
#         return self['Version'][0].value
#
#     @property
#     def groups(self):
#         """Read-only property containing list of all possible class groups"""
#         return self._groups
#
#     @property
#     def conversions(self):
#         """Read-only property containing list unit conversions"""
#         return self._conversions