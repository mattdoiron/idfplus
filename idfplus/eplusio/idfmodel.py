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
import uuid
import copy
import networkx as nx
from collections import OrderedDict
from whoosh.fields import Schema, ID
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import QueryParser

# Package imports
from . import refmodel
from . import config
from .iddmodel import UNITS_REGISTRY, UNIT_TYPES, ALLOWED_OPTIONS

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist


class IDFError(Exception):
    """Base class for IDF exceptions.
    """

    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(IDFError, self).__init__(*args, **kwargs)


class IDFFile(OrderedDict):
    """Primary object representing idf file and container for idf objects.

    Contains an OrderedDict of lists of IDFObjects with the class type as a
    key. For example:
    {'ScheduleTypeLimits': [IDFObject1, IDFObject2, IDFObject3],
    'SimulationControl':  [IDFObject4]}

    :attr IDDFile idd: IDDFile object containing pre-compiled idd file
    :attr str version: EnergyPlus version number (eg. 8.1.0.008)
    :attr str eol_char: depends on file (could be \\n or \\r\\n, etc)
    :attr list options: options that may have been found in idf file
    :attr str file_path: full, absolute path to idf file
    """

    def __init__(self, *args, **kwargs):
        """Initializes a new idf, blank or opens the given file_path

        :param str file_path:
        :param \*args: arguments to pass to base dictionary type
        :param \*\*kwargs: keyword arguments to pass to base dictionary type
        """

        # Call the parent class' init method
        super(IDFFile, self).__init__(*args, **kwargs)

        # Various attributes of the idf file
        self._idd = None
        self._eol_char = '\n'
        self.file_path = None
        self.options = list()
        self._version = None
        self.si_units = True
        self._uuid = str(uuid.uuid4())
        self._references = refmodel.ReferenceModel(self)
        self._init_index()

    def _init_index(self):
        """Initializes the search index and its schema.
        """

        self.schema = Schema(uuid=ID(unique=True, stored=True),
                             obj_class=ID(stored=True),
                             value=ID(stored=True))
        self.index = RamStorage().create_index(self.schema)

    def init_blank(self):
        """Sets up a blank idf file
        """

        # Prepare the idd file
        from . import parser
        idd_parser = parser.IDDParser()
        self._idd = idd_parser.load_idd(config.DEFAULT_IDD_VERSION)
        self.update((k, list()) for k, v in self._idd.iteritems())

        # Create the only mandatory object (version)
        version_obj = IDFObject(self, 'Version')
        version_field = IDFField(version_obj, 'A1')
        version_field.value = config.DEFAULT_IDD_VERSION
        version_obj.append(version_field)
        self['Version'].append(version_obj)

    @property
    def version(self):
        """Read-only property containing idf file version
        """

        return self._version

    @property
    def idd(self):
        """Read-only property containing idd file
        """

        return self._idd

    def set_idd(self, idd):
        """Sets the IDD file and takes care of some setup operations
        :param idd:
        """

        self._idd = idd
        self._version = idd.version
        self._references.set_idd(idd)
        self._populate_obj_classes()

    def reference_tree_data(self, current_obj_class, index):
        """Constructs a list of lists of nodes for the reference tree view.

        :param index:
        :param current_obj_class:
        """

        # Retrieve the node (could be invalid so use try)
        try:
            ref_graph = self._references._ref_graph
            field = self[current_obj_class][index.row()][index.column()]
            if not field:
                data = None
            else:
                ancestors = nx.ancestors(ref_graph, field._uuid)
                descendants = nx.descendants(ref_graph, field._uuid)
                data = [[ref_graph.node[ancestor]['data'] for ancestor in ancestors],
                        [ref_graph.node[descendant]['data'] for descendant in descendants]]
        except (nx.exception.NetworkXError, IndexError):
            data = None

        return data

    def reference_count(self, field):
        """Returns a count of references for the given field.

        :param field:
        """

        # Continue only if this field references an object-list
        if not field:
            return -1
        object_list_name = field.tags.get('object-list', '')
        if not object_list_name:
            return -1
        return self._references.reference_count(field)

    def _populate_obj_classes(self):
        """Pre-allocates the keys of the IDFFile.

        This must be done early so that all objects added later are added
        in the proper order (this is an OrderedDict!).
        """

        self.update((k, list()) for k in self._idd.iterkeys())

    def search(self, search_query, whole_field=False, advanced=False):
        """Performs search for a search_query

        :param search_query:
        :param whole_field:
        :param advanced:
        :return:
        """

        if advanced:
            query = search_query
        elif whole_field:
            query = '"{}"'.format(search_query)
        else:
            query = '*"{}"*'.format(search_query)

        with self.index.searcher() as searcher:
            parser = QueryParser("value", self.schema)
            parsed_query = parser.parse(query)
            hits = searcher.search(parsed_query, limit=None, scored=False, sortedby=None)
            results = [hit.fields() for hit in hits]

        return results, parsed_query

    def idf_objects(self, obj_class):
        """Returns all the objects in the specified class.

        :param obj_class:
        """

        return self.get(obj_class, list())

    def get_objects(self, key, index, count=None):
        """Returns the specified object.

        :param count: Number of objects to return.
        :param index: Starting index.
        :param key: Class of objects to return.
        :returns list: List of IDFObjects.
        """

        if count is None:
            count = index + 1

        return self[key][index:count]

    def add_objects(self, obj_class, new_objects, position=None, update_index=True):
        """Adds the specified object(s) to the IDFFile.

        :param update_index:
        :param obj_class:
        :param position:
        :param new_objects: List of IDFObjects or single IDFObject
        :returns int: Number of objects added
        """

        # We accept lists or single objects, but must use lists later on
        if isinstance(new_objects, IDFObject):
            new_objects = [new_objects]

        # Fail if object class is not valid
        if not self.idd.valid_class(obj_class):
            return 0

        # Set insert point to 'position' or end of list
        if position is None:
            position = len(self[obj_class])

        # If there are no objects to add, make a new blank one
        if not new_objects or (len(new_objects) == 1 and new_objects[0] is None):
            obj = IDFObject(self, obj_class)
            obj.set_defaults(self.idd)
            new_objects = [obj]

        # Insert the new object(s)
        self[obj_class][position:position] = new_objects
        idd_obj = self.idd.idd_object(obj_class)

        if update_index is True:
            # Update the index
            self._index_objects(new_objects)

        # Update references
        self._references.insert_references(new_objects)

        return len(new_objects)

    def _index_objects(self, new_objects):
        """

        :param new_objects:
        :return:
        """

        with self.index.writer() as writer:
            for obj in new_objects:
                for field in obj:
                    if not field:
                        continue
                    writer.add_document(uuid=unicode(field.uuid),
                                        obj_class=unicode(field.obj_class),
                                        value=unicode(field.value.lower()),
                                        _stored_value=unicode(field.value))

    def _deindex_objects(self, objects_to_delete):
        """

        :param objects_to_delete:
        :return:
        """

        with self.index.writer() as writer:
            for obj in objects_to_delete:
                for field in obj:
                    if not field:
                        continue
                    writer.delete_by_term('uuid', unicode(field.uuid))

    def _upsert_field_index(self, fields):
        """

        :param field:
        :return:
        """

        with self.index.writer() as writer:
            for field in fields:
                if not field:
                    continue
                writer.update_document(uuid=unicode(field.uuid),
                                       obj_class=unicode(field.obj_class),
                                       value=unicode(field.value.lower()),
                                       _stored_value=unicode(field.value))

    def field(self, obj_class, index_obj, index_field):
        """Returns the specified field. Convenience function.

        :param index_field:
        :type index_field: int
        :param index_obj:
        :type index_obj: int
        :param obj_class:
        :type obj_class: str
        :return: IDFField object
        """

        try:
            field = self[obj_class][index_obj][index_field]
        except (IndexError, TypeError):
            field = None

        if not field:
            message = 'Field does not exist. ({}:{}:{})'.format(obj_class, index_obj, index_field)
            raise IDFError(message)
        else:
            return field

    def allocate_fields(self, obj_class, index_obj, index_field):
        """Checks for max allowable fields and allocates more if necessary.

        :param index_field:
        :type index_field: int
        :param index_obj:
        :type index_obj: int
        :param obj_class:
        :type obj_class: str
        """

        idd_object = self._idd.idd_object(obj_class)
        max_field_count = len(idd_object)
        idf_object = self[obj_class][index_obj]
        current_field_count = len(idf_object)

        # If within limits allowed, allocate additional field 'slots'
        if index_field < max_field_count:
            extra_field_count = index_field - current_field_count + 1
            extra_fields = extra_field_count * [None]
            idf_object.extend(extra_fields)

            # Create a new field object, give it a value and save it
            field = IDFField(idf_object, idd_object.key(index_field))
            self[obj_class][index_obj][index_field] = field

    def remove_objects(self, obj_class, first_row, last_row):
        """Deletes specified object.

        :param first_row:
        :param last_row:
        :param obj_class:
        """

        # Remove the fields from graph also
        objects_to_delete = self[obj_class][first_row:last_row]
        obj_class = objects_to_delete[0].obj_class
        # log.debug('nodes before delete: {}'.format(ref_graph.number_of_nodes()))

        # Delete objects and update reference list
        self._deindex_objects(objects_to_delete)
        self._references.remove_references(objects_to_delete)
        del self[obj_class][first_row:last_row]

    def units(self, field):
        """Returns the given field's current display units.

        :param field:
        """

        if field is None:
            return None

        # Look-up the default units
        if isinstance(field, IDFField):
            idd_field = self.idd.field(field.obj_class, field.index)
        else:
            idd_field = field
        units = idd_field.tags.get('units')

        # Check for special cases where units are based on another field
        if units:
            if units.startswith('BasedOnField'):
                based_on_field_key = units.split()[-1]
                based_on_field = self.idd.field(field.obj_class, based_on_field_key)

                # Use these results to find the actual units to use
                actual_units = UNIT_TYPES.get(based_on_field.value)

                if actual_units:
                    units = actual_units

        # If SI units are requested, return now (SI is always the default)
        if self.si_units is True:
            return units
        else:
            # Otherwise check for special ip-units exceptions
            ip_units = idd_field.tags.get('ip-units')
            if ip_units:
                return ip_units
            else:
                unit_dict = UNITS_REGISTRY.get(units)
                if unit_dict:
                    return unit_dict.keys()[0]
                else:
                    return units

    def _unit_conversion(self, field):
        """Gets the appropriate unit conversion value(s)

        :param field:
        """

        # Get the idd field corresponding to this idf field
        idd_object = self.idd.idd_object(field.obj_class)
        idd_field = idd_object[field.key]

        # Look-up the default units and any ip-unit exceptions
        units = idd_field.tags.get('units')
        ip_units = idd_field.tags.get('ip-units')

        if units:
            # Check for the special case of units based on another field
            if units.startswith('BasedOnField'):
                based_on_field_key = units.split()[-1]
                based_on_field = idd_object[based_on_field_key]

                # Use these results to find the actual units to use
                actual_units = UNIT_TYPES.get(based_on_field.value)

                if actual_units:
                    units = actual_units

            # Lookup the dict of unit conversions for this SI unit.
            conversion = UNITS_REGISTRY.get(units)
            if conversion:
                # Lookup the desired ip_units in the dict if specified, otherwise get the
                # 'first' (only) one in the dict.
                return conversion.get(ip_units, conversion.get(conversion.keys()[0]))

        return None

    def to_si(self, field, override_value=None):
        """Accepts field, and returns the value in SI units.

        :param override_value: Convert this value instead of the field's current value
        :param field: IDFField object containing the value to be converted
        """

        if not field:
            return

        # Get the unit conversion
        conversion = self._unit_conversion(field)
        value = override_value or field.value
        if not conversion:
            return override_value or field.value

        try:
            # Convert units and force it back to a string
            data = str(float(value) / conversion)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conversion[0]
            adder = conversion[1]
            data = str((float(value) - adder) / multiplier)

        return data

    def to_ip(self, field):
        """Accepts a field, and returns the value in IP units.

        :param field: IDFField object containing the value to be converted
        """

        if not field:
            return

        # Get the unit conversion
        conversion = self._unit_conversion(field)
        if not conversion:
            return field.value

        try:
            # Convert units and force it back to a string
            data = str(float(field.value) * conversion)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conversion[0]
            adder = conversion[1]
            data = str(float(field.value) * multiplier + adder)
        except ValueError:
            data = field.value

        return data

    def set_options(self, options):
        """Sets the specified options in this idf's options field

        :param options: Dictionary of options to set
        :type options: dict
        """

        for option, value in options.iteritems():

            if value in ALLOWED_OPTIONS[option] or value == '':
                # Remove all options of this type
                for opt in ALLOWED_OPTIONS[option]:
                    try:
                        self.options.pop(self.options.index(opt))
                    except (TypeError, ValueError):
                        continue

                # Replace with only the one we want (or not if the value is empty)
                if value:
                    self.options.append(value)

            else:
                raise ValueError('Invalid option for {}!'.format(option))

    def iter_ordered(self):

        # TODO save order of object as they are being parsed then create a list of objects
        # according to the sorted list of the objects. Then yield the items here in order.
        # for obj_class in self._idd.iterkeys():
        #     yield obj_class, self.idf_objects(obj_class)
        pass

    def field_by_uuid(self, field_uuid):

        # print(field_uuid)
        field = self._references._ref_graph.node[field_uuid]['data']
        # print(field)
        return field


class IDFObject(list):
    """Represents objects in idf files.

    Contains a list of fields in the form: [IDFField1, IDFField2, IDFField3]

    :attr str obj_class: Class type of object
    :attr str group: Group to which this object belongs
    :attr IDFFile idd: Contains the IDD file used by this IDF object
    :attr list comments: User comments for this object
    :attr list incoming_links: List of tuples of objects that link to this
    :attr list outgoing_links: List of tuples of objects to which this links
    """

    # TODO This class is almost the same as IDDObject. It should subclass it.

    def __init__(self, outer, obj_class, **kwargs):
        """Use kwargs to pre-populate some values, then remove them from kwargs

        Also sets the idd file for use by this object.

        :param eplusio.iddmodel.IDFFile outer:
        :param str obj_class: Class type of this idf object
        :param \*\*kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self.comments = kwargs.pop('comments', [])
        self._outer = outer
        self._ref_graph = None
        self._obj_class = obj_class
        self._group = kwargs.pop('group', None)
        self._uuid = str(uuid.uuid4())

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

    def __deepcopy__(self, memo):
        """Reimplement deepcopy to avoid recursion issues with IDFFile/IDFObject
        """

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
        if result:
            for field in result:
                if field:
                    field._outer = result

        return result

    def __str__(self):
        """String representation of the object.
        """

        fields = [field.value for field in self]
        return self._obj_class + ',' + ','.join(fields) + ';'

    @property
    def obj_class(self):
        """Read-only property containing idf object's class type

        :rtype : str
        """

        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idf object's group

        :rtype : str
        """

        return self._group

    @property
    def uuid(self):
        """Read-only property containing uuid

        :return: :rtype:
        """

        return self._uuid

    def set_defaults(self, idd):
        """Populates the object's fields with their defaults

        :param idd:
        """

        idd_object = idd.idd_object(self.obj_class)
        for i, idd_field in enumerate(idd_object.itervalues()):
            default = idd_field.tags.get('default', None)
            try:
                # If there is a field present, set its value
                self[i].value = default
            except IndexError:
                # No field so append None or a blank field object
                if default is None:
                    self.append(default)
                else:
                    self.append(IDFField(self, idd_field.key, value=default))

    def set_group(self, class_group):
        """Sets this IDFObject's class group

        :param class_group:
        :return:
        """

        self._group = class_group

    def set_class(self, obj_class):
        """Sets this IDFObject's object-class

        :param obj_class:
        :return:
        """

        self._obj_class = obj_class


class IDFField(object):
    """Basic component of the idf object classes.

    Contains a key and value. Values must always be in metric units.
    Simply a regular dict containing keys which are the names of various
    field tags such as: required, field, type, minimum, etc.
    """

    # TODO This class is actually the same as IDDField. Merge them?

    def __init__(self, outer, key, *args, **kwargs):
        """Initializes a new idf field

        :param str key:
        :param value:
        :param IDFObject outer:
        """

        self.key = key
        self.tags = dict()
        self._value = kwargs.pop('value', None)
        self._ureg = None
        self._outer = outer
        self._uuid = str(uuid.uuid4())

        # Call the parent class' init method
        super(IDFField, self).__init__()

    def __deepcopy__(self, memo):
        """Reimplement deepcopy to avoid recursion issues with IDFFile/IDFObject
        """

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
    def value(self):
        """Returns value of field
        """

        return self._value

    @value.setter
    def value(self, new_value):
        """Sets value of field

        :param new_value:
        """

        # Update the value and then the IDFFile's index
        self._value = new_value
        self._outer._outer._upsert_field_index([self])

    @property
    def name(self):
        """Return this field's name (the 'field' tag)

        :rtype: str
        :return: The name of the field from the idd file
        """

        if 'field' in self.tags:
            return self.tags['field']
        else:
            return str()

    @property
    def obj_class(self):
        """Returns this field's outer object's (IDFObject) class

        :rtype: str
        :return: The name of the class from the outer object
        """

        return self._outer._obj_class

    @property
    def index(self):
        """Read-only property that returns the index of this field

        :rtype: int
        :return: The index of this field in its outer class
        """

        return self._outer.index(self)

    @property
    def field_id(self):
        """Read-only property that returns the id of this field
        """

        try:
            my_id = (self._outer._obj_class,
                     self._outer._outer[self._outer._obj_class].index(self._outer),
                     self._outer.index(self))
        except KeyError:
            my_id = None
        return my_id

    @property
    def uuid(self):
        """Read-only property containing uuid

        :return: :rtype:
        """

        return self._uuid
