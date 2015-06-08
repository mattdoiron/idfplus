#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
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

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
from collections import OrderedDict
# from persistent import Persistent
# from persistent.list import PersistentList
# from persistent.dict import PersistentDict
from persistent.mapping import PersistentMapping
from odict.pyodict import _odict
import uuid
import copy
import networkx as nx

# Package imports
from . import refmodel
from . import logger

# Constants
from . import config

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist

# Setup logging
log = logger.setup_logging(config.LOG_LEVEL, __name__, config.LOG_PATH)


class IDDError(Exception):
    """Base class for IDD exceptions."""
    def __init__(self, message, version, *args, **kwargs):
        self.message = message
        self.version = version
        super(IDDError, self).__init__(*args, **kwargs)


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
        self._version = version
        self._parser_version = config.PARSER_VERSION
        self.options = list()
        self.tags = dict()
        self.object_lists = dict()
        self._ureg = config.UNITS_REGISTRY

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
    def parser_version(self):
        """Read-only property containing version of the parser used to generate file."""
        return self._parser_version

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

    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj"""

        # Prepare the info variable and add the object class
        info = '--[ Object Class ]----------------------'
        info += '\nClass: {}'.format(self._obj_class)

        # Grab the object memo, if any
        memo = self.tags.get('memo')
        if memo:
            info += '\n'
            if isinstance(memo, list):
                info += ' '.join(memo)
            else:
                info += memo

        # Grab various info from field tags
        unique = self.tags.get('unique-object')
        required = self.tags.get('required-object')
        obsolete = self.tags.get('obsolete')
        min_fields = self.tags.get('min-fields')

        # Add nicely formatted versions of the above field tags
        info += '\n'
        info += '\nUnique: {}'.format(unique or 'No')
        info += '\nRequired: {}'.format(required or 'No')
        info += '\nMinimum Fields: {}'.format(min_fields) if min_fields else ''
        info += '\nObject Obsolete: {}'.format(obsolete) if obsolete else ''

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
        self._outer = outer
        self._obj_class = outer.obj_class
        self.tags = dict()

         # Call the parent class' init method
        super(IDDField, self).__init__()

    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj"""

        # Prepare the info variable and add the field name
        info = '--[ Field ]----------------------------------'
        field = self.tags.get('field', 'Un-named')
        info += '\nField: {} ({})'.format(self.key, field)

        # Grab the field note, if any
        note = self.tags.get('note')
        if note:
            info += '\n'
            if isinstance(note, list):
                info += ' '.join(note)
            else:
                info += note

        # Grab various info from field tags
        required = self.tags.get('required')
        units = self.tags.get('units')
        ip_units = self.tags.get('ip_units')
        minimum = self.tags.get('minimum')
        minimum_gt = self.tags.get('minimum>')
        maximum = self.tags.get('maximum')
        maximum_lt = self.tags.get('maximum<')
        default = self.tags.get('default')
        deprecated = self.tags.get('deprecated')
        autosizable = self.tags.get('autosizable')
        autocalculatable = self.tags.get('autocalculatable')

        # Add nicely formatted versions of the above field tags
        info += '\n'
        info += '\nDefault: {}'.format(default or 'n/a')
        info += '\nRequired: {}'.format(required or 'No')
        if units:
            info += '\nDefault Units: {}'.format(units)
            if ip_units:
                info += ' ({})'.format(ip_units)
        info += '\nMinimum: {}'.format(minimum) if minimum else ''
        info += '\nMinimum>: {}'.format(minimum_gt) if minimum_gt else ''
        info += '\nMaximum: {}'.format(maximum) if maximum else ''
        info += '\nMaximum<: {}'.format(maximum_lt) if maximum_lt else ''
        info += '\nDeprecated: Yes' if deprecated else ''
        info += '\nAutosizable: Yes' if autosizable else ''
        info += '\nAutocalculatable: Yes' if autocalculatable else ''

        return info

    @property
    def obj_class(self):
        """
        :rtype : str
        :return : The name of the class from the outer object
        """
        return self._outer._obj_class

    @property
    def units(self):
        """Read-only property containing idd field's SI units.
        :rtype : str
        """
        return self.tags.get('units')

    @property
    def ip_units(self):
        """Read-only property containing idd field's IP units.
        :rtype : str
        """
        return self.tags.get('ip-units')


class IDFFile(OrderedDict):
    """Primary object representing idf file and container for idf objects.

    Contains an OrderedDict of lists of IDFObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': [IDFObject1, IDFObject2, IDFObject3],
         'SimulationControl':  [IDFObject4]}

    :attr IDDFile idd: IDDFile object containing precompiled idd file
    :attr str version: EnergyPlus version number (eg. 8.1.0.008)
    :attr str eol_char: depends on file (could be \n or \r\n, etc)
    :attr list options: options that may have been found in idf file
    :attr str file_path: full, absolute path to idf file
    """

    def __init__(self, *args, **kwargs):
        """Initializes a new idf, blank or opens the given file_path

        :param str file_path:
        :param *args: arguments to pass to base dictionary type
        :param **kwargs: keyword arguments to pass to base dictionary type
        """

        # Call the parent class' init method
        super(IDFFile, self).__init__(*args, **kwargs)

        # Various attributes of the idf file
        # self._version_set = False
        self._idd = None
        self._eol_char = '\n'
        self.file_path = None
        self.options = list()
        self._version = None
        self.si_units = True
        self._uuid = str(uuid.uuid4())
        # self.ref_lists = dict()
        self._references = refmodel.ReferenceModel()

    def init_blank(self):
        """Sets up a blank idf file"""

        # Prepare the idd file
        from . import parser
        idd_parser = parser.IDDParser()
        self._idd = idd_parser.load_idd(config.DEFAULT_IDD_VERSION)
        self.update((k, list()) for k, v in self._idd.iteritems())

        # Create the only mandatory object (version)
        version_obj = IDFObject(self)
        version_field = IDFField(version_obj)
        version_field.value = config.DEFAULT_IDD_VERSION
        version_obj.append(version_field)
        self['Version'].append(version_obj)

        # Setup graph
        import networkx as nx
        self._ref_graph = nx.DiGraph()

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

    def reference_tree_data(self, current_obj_class, index):
        # Retrieve the node (could be invalid so use try)
        try:
            ref_graph = self._references._ref_graph
            field = self[current_obj_class][index.row()][index.column()]
            ancestors = nx.ancestors(ref_graph, field._uuid)
            descendants = nx.descendants(ref_graph, field._uuid)
            data = [[ref_graph.node[ancestor]['data'] for ancestor in ancestors],
                    [ref_graph.node[descendant]['data'] for descendant in descendants]]
        except (nx.exception.NetworkXError, IndexError) as e:
            data = None

        return data

    def reference_count(self, field):
        # Continue only if this field references an object-list
        object_list_name = field.tags.get('object-list', '')
        if not object_list_name:
            return -1

        # Ensure we have a list to simplify later operations
        if not isinstance(object_list_name, list):
            object_list_name = [field.tags['object-list']]

        # Cycle through all class names in the object lists and count references
        ref_node_count = 0
        for cls_list in object_list_name:
            if self._references._ref_lists[cls_list].get(field.value, None):
                ref_node_count += 1

        return ref_node_count

    def populate_ref_list(self, idf):
        self._references.populate_ref_list(idf)

    def populate_obj_classes(self, idd):
        self.update((k, list()) for k, v in idd.iteritems())

    def find(self, contains=None):
        """Searches within the file for objects having 'contains'
        :param str contains:  (Default value = None)
        """
        pass

    def get_object(self, key, index):
        """Returns the specified object."""
        return self[key][index]

    def add_object(self, idf_object):
        """Adds the specified object to the specified class."""
        obj_class = idf_object.obj_class
        try:
            self[obj_class].append(idf_object)
        except (AttributeError, KeyError) as e:
            self[obj_class] = [idf_object]
        # self._references.add_reference(field, cls_list, object_list_name)
        # self._add_reference(field, cls_list, object_list_name)

    def update_object(self, obj_class, index, new_values):
        """Updates the specified object."""
        self[obj_class][index].update(new_values)
        self._update_reference()

    def delete_object(self, obj_class, index):
        """Deletes specified object."""
        del self[obj_class][index]
        self._delete_reference()

    def get_class(self, key):
        """Returns a list of classes for the specified class."""
        return self[key]

    def _get_reference(self):
        """Returns the node for the specified reference."""
        return self._references.reference()

    def _update_reference(self):
        """Updates the specified reference."""
        return self._references.update_reference()

    def _delete_reference(self):
        """Deletes the specified reference."""
        return self._references.delete_reference()


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
        self._ref_graph = None
        self._group = kwargs.pop('group', None)
        self._obj_class = kwargs.pop('obj_class', None)
        self.comments = kwargs.pop('comments', [])
        self._outer = idf
        self._uuid = str(uuid.uuid4())

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

    def __deepcopy__(self, memo):
        """Reimplement deepcopy to avoid recursion issues with IDFFile/IDFObject"""

        # Create a new object, same class as this one, without triggering init
        cls = self.__class__
        result = cls.__new__(cls)

        # Populate the new object with deep copies of all this object's fields
        result[:] = [copy.deepcopy(field) for field in self]

        # Copy all this objects attributes except IDFFile (leave as a reference)
        for key, val in self.__dict__.items():
            if isinstance(val, IDFFile):
                setattr(result, key, val)
            elif key == '_uuid':
                setattr(result, key, str(uuid.uuid4()))
            else:
                setattr(result, key, copy.copy(val))

        # The copied objects will use references to the old object, update them
        for field in result:
            field._outer = result

        return result

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
                # If there is a field present, set its value
                self[i].value = default
            except IndexError:
                # No field so append None or a blank field object
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
        self._ureg = None #outer.idd._ureg
        self._outer = outer
        self._uuid = str(uuid.uuid4())

        # self._idf_file = outer._outer
        # idd = outer.idd
        # self._units = outer.idd[self._obj_class][key].units
        # self._ip_units = outer.idd[self._obj_class][key].ip_units
        # if not self._ip_units:
        #     self._ip_units = outer.idd.conversions[self._units]

        # Call the parent class' init method
        super(IDFField, self).__init__()

    def __deepcopy__(self, memo):
        """Reimplement deepcopy to avoid recursion issues with IDFFile/IDFObject"""

        # Create a new object, same class as this one, without triggering init
        cls = self.__class__
        result = cls.__new__(cls)

        # Copy all this objects attributes except IDFObject (leave as a reference)
        for key, val in self.__dict__.items():
            if isinstance(val, IDFObject):
                setattr(result, key, val)
            elif key == '_uuid':
                setattr(result, key, str(uuid.uuid4()))
            else:
                setattr(result, key, copy.copy(val))

        return result

    @property
    def name(self):
        """
        :rtype : str
        :return : The name of the field from the idd file
        """
        if 'field' in self.tags:
            return self.tags['field']
        else:
            return str()

    @property
    def obj_class(self):
        """
        :rtype : str
        :return : The name of the class from the outer object
        """
        return self._outer._obj_class

    @property
    def position(self):
        """
        :rtype : int
        :return : The index of this field in its outer class
        """
        return self._outer.index(self.value)

    @property
    def field_id(self):
        try:
            my_id = (self._outer._obj_class,
                     self._outer._outer[self._outer._obj_class].index(self._outer),
                     self._outer.index(self))
        except KeyError as e:
            my_id = None
        return my_id

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