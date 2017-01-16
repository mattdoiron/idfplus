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
import sqlite3
from collections import OrderedDict

# Package imports
from . import config
from .iddmodel import UNITS_REGISTRY, UNIT_TYPES, ALLOWED_OPTIONS, IDDObject

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
        self._init_db()
        self.field_registry = dict()

    def _init_db(self):

        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()

        # Create table with uuid as primary key and case-insensitive value
        cursor.execute("CREATE TABLE idf_objects"
                       "(uuid TEXT PRIMARY KEY,"
                       "obj_class TEXT,"
                       "ref_type TEXT,"
                       "value TEXT COLLATE NOCASE)")
        self.db.commit()

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
        version_field = IDFField(version_obj, config.DEFAULT_IDD_VERSION, key='A1')
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

        if not idd:
            raise

        self._idd = idd
        self._version = idd.version
        self._populate_obj_classes()

    def reference_tree_data(self, obj_class, index):
        """Constructs a list of lists of nodes for the reference tree view.

        :param index:
        :param obj_class:
        """

        if not index:
            return None

        # Retrieve the node (could be invalid so use try)
        try:
            field = self[obj_class][index.row()][index.column()]
            if not field:
                data = None
            else:
                try:
                    data = self.references(field)
                except KeyError:
                    data = None
        except IndexError:
            data = None

        return data

    def reference_count(self, field):
        """Returns a count of references for the given field.

        :param field:
        """

        # Continue only if a valid field is present and the right type
        if not field:
            return -1
        if field.ref_type not in ['object-list', 'reference']:
            return -1

        return len(self.references(field))

    def references(self, field, ignore_geometry=False):
        """Performs search for all references

        :return:
        """

        if not field.value:
            return None

        if field.ref_type == 'object-list':
            refs = self._query_refs(field, 'reference', ignore_geometry=ignore_geometry)
        elif field.ref_type == 'reference':
            refs = self._query_refs(field, 'object-list', ignore_geometry=ignore_geometry)
        else:
            refs = self._query_refs(field, 'node', ignore_geometry=ignore_geometry)

        return refs

    def _query_refs(self, field, ref_type, ignore_geometry):
        """Performs search for incoming or outgoing references

        :return:
        """

        query = "value='{}' AND ref_type='{}'".format(field.value, ref_type)
        query += " AND NOT obj_class ='{}'".format(field.obj_class.lower())

        if ignore_geometry:
            query += " AND NOT obj_class='buildingsurface:detailed'"
            query += " AND NOT obj_class='fenestrationsurface:detailed'"

        query_records = "SELECT * from idf_objects WHERE {}".format(query)

        try:
            records = self.db.execute(query_records).fetchall()
        except sqlite3.OperationalError as e:
            records = []
            print("Invalid SQLite query! ('{}')".format(query_records))

        results = [self.field_by_uuid(row['uuid']) for row in records]

        return results

    def _populate_obj_classes(self):
        """Pre-allocates the keys of the IDFFile.

        This must be done early so that all objects added later are added
        in the proper order (this is an OrderedDict!).
        """

        self.update((k, list()) for k in self._idd.iterkeys())

    def search(self, search_query, whole_field=False, advanced=False, ignore_geometry=False):
        """Performs search for a search_query

        :param search_query:
        :param whole_field:
        :param advanced:
        :return:
        """

        if advanced:
            query = search_query
        elif whole_field:
            query = "value='{}'".format(search_query)
        else:
            query = "value LIKE '%{}%'".format(search_query)

        if ignore_geometry and not advanced:
            query += " AND NOT obj_class='buildingsurface:detailed'"
            query += " AND NOT obj_class='fenestrationsurface:detailed'"

        query_records = "SELECT * from idf_objects WHERE {}".format(query)
        print(query_records)

        try:
            records = self.db.execute(query_records).fetchall()
            result_query = query_records
        except sqlite3.OperationalError as e:
            records = []
            result_query = "Invalid SQLite query! ('{}')".format(query_records)

        return records, result_query

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

    def add_objects(self, obj_class, new_objects, position=None, update=True):
        """Adds the specified object(s) to the IDFFile.

        :param update:
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

        # Conditionally update the index
        if update is True:
            self._index_objects(new_objects)

        # Update field registry (map of uuid's to python field objects)
        for obj in new_objects:
            for field in obj:
                if field:
                    self.field_registry[field.uuid] = field

        return len(new_objects)

    def _index_objects(self, new_objects):
        """

        :param new_objects:
        :return:
        """

        for obj in new_objects:
            self._upsert_field_index(obj, commit=False)
        self.db.commit()

    def _deindex_objects(self, objects_to_delete):
        """

        :param objects_to_delete:
        :return:
        """

        # Create IDFField objects for all fields and add them to the IDFObject
        field_objects = list()
        append_new_field = field_objects.append
        for obj in objects_to_delete:
            for field in obj:
                append_new_field((field.uuid,))

        delete_operation = "DELETE FROM idf_objects WHERE uuid=(?)"
        self.db.executemany(delete_operation, field_objects)
        self.db.commit()

    def _upsert_field_index(self, fields, commit=True):
        """

        :param fields:
        :return:
        """

        if not fields:
            return

        field_objects = list()
        append_new_field = field_objects.append
        for field in fields:
            if field:
                append_new_field((field.uuid, field.obj_class, field.ref_type, field.value))

        upsert_operation = "INSERT OR REPLACE INTO idf_objects VALUES (?, ?, ?, ?)"
        self.db.executemany(upsert_operation, field_objects)

        if commit:
            self.db.commit()

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
            field = IDFField(idf_object, key=idd_object.key(index_field))
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

        # Deindex and delete objects
        self._deindex_objects(objects_to_delete)
        del self[obj_class][first_row:last_row]

    def units(self, field):
        """Returns the given field's current display units.

        :param eplusio.idfmodel.IDFField field:
        """

        if field is None:
            return None

        # Look-up the default units
        units = field.tags.get('units')

        # Check for special cases where units are based on another field
        if units:
            if units.startswith('BasedOnField'):
                units = self._based_on_units(units, field)

        # If SI units are requested, return now (SI is always the default)
        if self.si_units is True:
            return units
        else:
            # Otherwise check for special ip-units exceptions
            ip_units = field.tags.get('ip-units')
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
                units = self._based_on_units(units, field)

            # Lookup the dict of unit conversions for this SI unit.
            conversion = UNITS_REGISTRY.get(units)
            if conversion:
                # Lookup the desired ip_units in the dict if specified, otherwise get the
                # 'first' (only) one in the dict.
                return conversion.get(ip_units, conversion.get(conversion.keys()[0]))

        return None

    def _based_on_units(self, units, field):
        """Returns units if field's units are based on the content of another field.

        :param units:
        :param field:
        :return:
        """

        based_on_field_key = units.split()[-1]
        based_on_field_idd = self.idd.field(field.obj_class, based_on_field_key)
        index = based_on_field_idd.index
        try:
            based_on_field = field._outer[index]
            actual_units = UNIT_TYPES.get(based_on_field.value)
        except (IndexError, KeyError):
            actual_units = ''

        return actual_units

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
        # This will allow getting rid of the OrderedDict class which is slow!
        pass

    def field_by_uuid(self, field_uuid):

        return self.field_registry.get(field_uuid, None)


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

    # Using slots simplifies the internal structure of the object and makes
    # it more memory efficiency
    __slots__ = ['comments', 'comments_special', '_outer', 'obj_class',
                 '_group', '_uuid', 'obj_class', 'group', 'uuid']

    def __init__(self, outer, obj_class, **kwargs):
        """Use kwargs to pre-populate some values, then remove them from kwargs

        Also sets the idd file for use by this object.

        :param IDFFile outer:
        :param str obj_class: Class type of this idf object
        :param \*\*kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self.comments = list()
        self.comments_special = list()
        self.obj_class = obj_class
        self._outer = outer
        self._uuid = None

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

    def __str__(self):
        """String representation of the object.
        """

        field_str = self.obj_class + ','
        for field in self:
            field_str += str(field or '') + ','
        field_str = field_str[:-1]
        field_str += ';'
        return field_str

    @property
    def uuid(self):
        """Read-only property containing uuid

        :rtype: str
        """

        if not self._uuid:
            self._uuid = str(uuid.uuid4())
        return self._uuid

    def duplicate(self):
        """Create a new IDFField object and copy this one's references and value.

        :return:
        """

        def new_field(field):
            if field:
                new = IDFField(self, field._value, key=field._key,
                               tags=field._tags, index=field._index)
            else:
                new = None
            return new

        # Create a new object
        result = IDFObject(self._outer, self.obj_class)

        # Populate the new object with deep copies of all this object's fields
        result[:] = [new_field(_field) for _field in self]

        return result

    def set_defaults(self, idd):
        """Populates the object's fields with their defaults

        :param idd: IDDObject to use for sourcing defaults
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
                    self.append(IDFField(self, default, key=idd_field.key))

    __repr__ = __str__


class IDFField(object):
    """Basic component of the idf object classes.

    Contains a key and value. Values must always be in metric units.
    Simply a regular dict containing keys which are the names of various
    field tags such as: required, field, type, minimum, etc.
    """

    # TODO This class is actually the same as IDDField. Merge them?
    # Create a base class with common attributes and subclass it to add any
    # differences. When creating a new field, simply copy the IDDField and add
    # the appropriate attributes like value? Need to reset uuid on copy operations.

    # Using slots simplifies the internal structure of the object and makes
    # it more memory efficiency
    __slots__ = ['key', 'tags', 'value', 'idd_object', 'ref_type', 'ureg',
                 'outer', 'uuid', '_key', '_tags', '_value', '_idd_object',
                 '_ref_type', '_outer', '_uuid', 'index', '_index']

    def __init__(self, outer, value=None, **kwargs):
        """Initializes a new idf field

        :param value:
        :param IDFObject outer:
        """

        self._key = kwargs.pop('key', None)
        self._tags = kwargs.pop('tags', None)
        self._index = kwargs.pop('index', None)
        self._value = value
        self._idd_object = None
        self._ref_type = None
        self._outer = outer
        self._uuid = None

        # Call the parent class' init method
        super(IDFField, self).__init__()

    def __str__(self):
        """String representation of the field.
        """

        return str(self._value)

    @property
    def key(self):
        """Returns the field's key

        :rtype: str
        """

        if not self._key:
            self._key = self.idd_object.key(self.index)
        return self._key

    @property
    def value(self):
        """Returns value of field

        :rtype: str
        """

        return self._value

    @value.setter
    def value(self, new_value):
        """Sets value of field and makes sure that index is also updated

        :param new_value:
        """

        # Update the value and then the IDFFile's index
        self._value = new_value
        self._outer._outer._upsert_field_index([self])

    @property
    def tags(self):
        """Returns this field's tags

        :rtype: dict
        """

        if not self._tags:
            self._tags = self.idd_object[self.key].tags
        return self._tags

    @property
    def name(self):
        """Return this field's name (the 'field' tag)

        :rtype: str
        :return: The name of the field from the idd file
        """

        return self.tags.get('field', str())

    @property
    def obj_class(self):
        """Returns this field's outer object's (IDFObject) class

        :rtype: str
        :return: The name of the class from the outer object
        """

        return self._outer.obj_class

    @property
    def index(self):
        """Read-only property that returns the index of this field

        :rtype: int
        :return: The index of this field in its outer class
        """

        if not self._index:
            self._index = self._outer.index(self)
        return self._index

    @property
    def field_id(self):
        """Read-only property that returns the id of this field

        :rtype: tuple
        """

        try:
            my_id = (self.obj_class,
                     self._outer._outer[self.obj_class].index(self._outer),
                     self.index)
        except KeyError:
            my_id = None
        return my_id

    @property
    def ref_type(self):
        """Read-only property containing reference type

        :rtype: str
        """

        if not self._ref_type:
            ref_type_set = set(self.tags.keys()) & {'reference', 'object-list'}
            type_tag = self.tags.get('type', None)

            if type_tag == 'node':
                self._ref_type = 'node'
            else:
                self._ref_type = unicode(list(ref_type_set)[0]) if ref_type_set else None
        return self._ref_type

    @property
    def idd_object(self):
        """Read-only property containing the object's IDD Class Object

        :rtype: IDDObject
        """

        if not self._idd_object:
            self._idd_object = self._outer._outer._idd.get(self.obj_class)
        return self._idd_object

    @property
    def uuid(self):
        """Read-only property containing uuid

        :rtype: str
        """

        if not self._uuid:
            self._uuid = str(uuid.uuid4())
        return self._uuid

    def has_tags(self, tags_to_check):
        """Returns a list of tags which are contained in both this field and tags_to_check

        :rtype: str
        :param tags_to_check:
        """

        return list(set(self.tags) & set(tags_to_check))
