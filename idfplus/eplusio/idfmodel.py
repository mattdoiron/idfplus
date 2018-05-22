#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF file, object and field models. These serve as the primary data structure for IDF files

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import uuid
import sqlite3
from collections import OrderedDict

# Package imports
from . import config
from .iddmodel import UNITS_REGISTRY, UNIT_TYPES, ALLOWED_OPTIONS, IDDObject, IDDFile

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist


class IDFError(Exception):
    """Base class for IDF exceptions.
    """

    def __init__(self, message, *args, **kwargs):
        """Init base class for IDF exceptions

        :param str message: Message to pass along with exception
        """

        self.message = message
        super(IDFError, self).__init__(*args, **kwargs)


class IDFFile(OrderedDict):
    """Primary object representing IDF file and container for IDF objects.

    This class is an :class:`collections.OrderedDict` of lists of
    :class:`IDFObject` with the class type as a key. Class keys are always lower case.
    For example:

    .. code-block:: python

        {'scheduletypelimits': [IDFObject1, IDFObject2, IDFObject3],
         'simulationcontrol':  [IDFObject4]}
    """

    def __init__(self, *args, **kwargs):
        """Initializes a new IDF, blank or opens the given file_path
        """

        # Call the parent class' init method
        super(IDFFile, self).__init__(*args, **kwargs)

        # Various attributes of the IDF file
        self._idd = None
        self._eol_char = '\n'
        self.file_path = None  #: Full absolute path to IDF file
        self.options = list()  #: List of options that may have been found in IDF file
        self._version = None
        self.si_units = True  #: Boolean representing whether SI units are to be displayed
        self._uuid = str(uuid.uuid4())
        self._init_db()
        self.field_registry = dict()  #: Dictionary containing a registry of fields

    def __getitem__(self, obj_class):
        return super(IDFFile, self).__getitem__(obj_class.lower())

    def _init_db(self):
        """Initialize the SQLite database to store field values for search
        """

        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()

        # Create table with uuid as primary key and case-insensitive value
        cursor.execute("CREATE TABLE idf_objects"
                       "(uuid TEXT PRIMARY KEY,"
                       "obj_class TEXT,"
                       "obj_class_display TEXT,"
                       "ref_type TEXT,"
                       "value TEXT COLLATE NOCASE)")
        self.db.commit()

    def init_blank(self):
        """Sets up a blank IDF file
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
        """Read-only property containing IDF file version

        :rtype: str
        """

        return self._version

    @property
    def idd(self):
        """Read-only property containing idd file

        :rtype: IDDObject
        """

        return self._idd

    def set_idd(self, idd):
        """Sets the IDD file and takes care of some setup operations

        :param IDDFile idd: IDD file to use for this IDF file
        """

        if not isinstance(idd, IDDFile):
            raise IDFError

        self._idd = idd
        self._version = idd.version
        self._populate_obj_classes()

    def reference_tree_data(self, obj_class, index):
        """Constructs a list of lists of nodes for the reference tree view.

        :param QModelIndex index: Index representing row and column location of selected field
        :param str obj_class: Object class to use when creating reference tree
        :rtype: list(IDFField) or None
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

        :param IDFField field: The field to query for references
        :rtype: int
        """

        # Continue only if a valid field is present and the right type
        if not field:
            return -1
        if field.ref_type not in ['object-list', 'reference']:
            return -1

        return len(self.references(field))

    def references(self, field, ignore_geometry=False):
        """Performs search for all references

        :param IDFField field: Field for which the references will be retrieved
        :param bool ignore_geometry: Set if returned references should exclude geometry
        :rtype: list(IDFField)
        """

        if not field.value:
            return []

        if field.ref_type == 'object-list':
            refs = self._query_refs(field, 'reference', ignore_geometry=ignore_geometry)
        elif field.ref_type == 'reference':
            refs = self._query_refs(field, 'object-list', ignore_geometry=ignore_geometry)
        else:
            refs = self._query_refs(field, 'node', ignore_geometry=ignore_geometry)

        return refs

    def _query_refs(self, field, ref_type, ignore_geometry):
        """Performs search for incoming or outgoing references

        :param IDFField field: Field for which the references will be retrieved
        :param str ref_type: Type of reference (reference or object-list)
        :param bool ignore_geometry: Set if returned references should exclude geometry
        :rtype: list(IDFField)
        """

        query = "value='{}' AND ref_type='{}'".format(field.value, ref_type)
        query += " AND NOT obj_class ='{}'".format(field.obj_class)

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
        in the proper order (this is an :class:`collections.OrderedDict`!).
        """

        self.update((k, list()) for k in self._idd.iterkeys())

    def search(self, search_query, whole_field=False, advanced=False, ignore_geometry=False):
        """Performs search for a search_query

        :param str search_query: SQL query to perform
        :param bool whole_field: Whole or partial field match
        :param bool advanced: Use advanced or simple query mode
        :param bool ignore_geometry: Set if returned references should include geometry
        :rtype: list, str
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

        try:
            records = self.db.execute(query_records).fetchall()
            result_query = query_records
        except sqlite3.OperationalError as e:
            records = []
            result_query = "Invalid SQLite query! ('{}')".format(query_records)

        return records, result_query

    def idf_objects(self, obj_class):
        """Returns all the objects in the specified class.

        :param str obj_class: Object class of IDF objects to return
        """

        return self.get(obj_class, None)

    def get(self, key, default=None):
        """Override get in order to ensure lower case obj_class names
        """

        return super(IDFFile, self).get(key.lower(), default)

    def get_objects(self, key, index, count=None):
        """Returns the specified range of objects.

        :param int count: Number of objects to return.
        :param int index: Starting index.
        :param str key: Class of objects to return.
        :rtype: list(IDFObject).
        """

        if count is None:
            count = index + 1

        return self[key][index:count]

    def add_objects(self, obj_class, new_objects, position=None, update=True):
        """Adds the specified object(s) to the IDFFile.

        :param bool update: Flag to update the field index or not
        :param str obj_class: Object class into which the objects will be added
        :param bool position: Position at which the objects will be added
        :param new_objects: :class:`IDFObject` (s) to add
        :type new_objects: list(IDFObject) or IDFObject
        :returns: Number of objects added
        :rtype: int
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
            obj.set_defaults()
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
        """Adds objects to the internal index

        :param list(IDFObject) new_objects: List of :class:`IDFObject` 's to add to
            the index
        """

        for obj in new_objects:
            self._upsert_field_index(obj, commit=False)
        self.db.commit()

    def _deindex_objects(self, objects_to_delete):
        """Remove specified objects from the internal index

        :param list(IDFObject) objects_to_delete: List of :class:`IDFObject` 's to delete
            from the index
        """

        # Create IDFField objects for all fields and add them to the IDFObject
        field_objects = list()
        append_new_field = field_objects.append
        for obj in objects_to_delete:
            for field in obj:
                if field:
                    append_new_field((field.uuid,))

        delete_operation = "DELETE FROM idf_objects WHERE uuid=(?)"
        self.db.executemany(delete_operation, field_objects)
        self.db.commit()

    def _upsert_field_index(self, fields, commit=True):
        """Upsert (update or insert) the field index

        :param list(IDFField) fields: Fields to upsert
        """

        if not fields:
            return

        field_objects = list()
        append_new_field = field_objects.append
        for field in fields:
            if field:
                append_new_field((field.uuid, field.obj_class, field.obj_class_display,
                                  field.ref_type, field.value))

        upsert_operation = "INSERT OR REPLACE INTO idf_objects VALUES (?, ?, ?, ?, ?)"
        self.db.executemany(upsert_operation, field_objects)

        if commit:
            self.db.commit()

    def field(self, obj_class, index_obj, index_field):
        """Returns the specified field. Convenience function.

        :param int index_field: Position of field in its object
        :param int index_obj: Position of object in its class
        :param str obj_class: Class of object to return
        :rtype: IDFField
        """

        try:
            field = self[obj_class][index_obj][index_field]
        except (IndexError, TypeError):
            field = None

        return field

    def allocate_fields(self, obj_class, index_obj, index_field):
        """Checks for max allowable fields and allocates more if necessary.

        :param int index_field: Position of field in its object
        :param int index_obj: Position of object in its class
        :param str obj_class: Class of object to return
        """

        idd_object = self.idd.idd_object(obj_class)
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
        """Deletes specified object(s)

        :param int first_row: Position of first row to delete
        :param int last_row: Postition of last row to delete
        :param str obj_class: Class of objects to delete
        """

        # Remove the fields from graph also
        objects_to_delete = self[obj_class][first_row:last_row]
        obj_class = objects_to_delete[0].obj_class

        # Deindex and delete objects
        self._deindex_objects(objects_to_delete)
        del self[obj_class][first_row:last_row]

    def units(self, field):
        """Returns the given field's current display units.

        :param IDFField field: Field for which the units are desired
        :rtype: str
        """

        if field is None:
            return None

        # Look-up the default units
        units = field.tags.get('units')

        # Check for special cases where units are based on another field
        if units:
            if units.startswith('BasedOnField'):
                units = self._based_on_units(units, field)

        # Check for another special case where there is no direct indicator of units
        if field.value and not units:
            if field.obj_class == 'schedule:compact' and field.index > 1:
                field_type = field.value.split(":")
                if not field_type[0].lower() in ["through", "for", "interpolate", "until"]:
                    units = self._units_based_on_type_limits(field)

        # Return None if there are no units by this point
        if not units:
            return None

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

        :param IDFField field: Field for which the unit conversion is desired
        :rtype: str
        """

        # Get the idd field corresponding to this IDF field
        idd_object = self.idd.idd_object(field.obj_class)
        idd_field = idd_object[field.key]

        # Look-up the default units and any ip-unit exceptions
        units = idd_field.tags.get('units')
        ip_units = idd_field.tags.get('ip-units')

        # Check for another special case where there is no direct indicator of units
        if field.obj_class == 'schedule:compact' and not units and field.index > 1:
            field_type = field.value.split(":")
            if not field_type[0].lower() in ["through", "for", "interpolate", "until"]:
                units = self._units_based_on_type_limits(field)

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

    def _units_based_on_type_limits(self, field):
        """Returns the given field's current display units when based on a 'type limit'.

        :param IDFField field: Field whose units will be returned
        :rtype: str
        """

        type_limits_field = field._outer[1]
        type_limits_objects = self.idf_objects('ScheduleTypeLimits')
        type_limit = None

        if not type_limits_objects:
            return

        for obj in type_limits_objects:
            try:
                if obj[0].value == type_limits_field.value:
                    type_limit = obj[4]
            except IndexError as error:
                type_limit = None

        if not type_limit:
            return None

        return UNIT_TYPES.get(type_limit.value)

    def _based_on_units(self, units, field):
        """Returns units if field's units are based on the content of another field.

        :param str units:
        :param IDFField field: Field whose units will be returned
        :rtype: str
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
        """Accepts field, and returns a string of the value in SI units.

        :param float override_value: Convert this value instead of the field's current value
        :param IDFField field: Field containing the value to be converted
        :rtype: str
        """

        if not field:
            return

        # Get the unit conversion
        conversion = self._unit_conversion(field)
        value = override_value or field.value
        if not conversion:
            return value

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
        """Accepts a field, and returns a string of the value in IP units.

        :param IDFField field: Field containing the value to be converted
        :rtype: str
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
        """Sets or unsets the specified options in this :class:`IDFFile`'s options field

        :param dict options: Dictionary of options to set
        """

        for option, value in options.iteritems():

            if option in ALLOWED_OPTIONS.keys():
                if value == '':
                    # Remove all options of this type
                    for opt in ALLOWED_OPTIONS[option]:
                        try:
                            self.options.pop(self.options.index(opt))
                        except (TypeError, ValueError):
                            continue

                # Replace with only the one we want
                if value and value in ALLOWED_OPTIONS[option]:
                    self.options.append(value)

            else:
                raise ValueError('Invalid option for {}!'.format(option))

    def iter_ordered(self):
        """Not implemented
        """

        #: Todo save order of object as they are being parsed then create a list of objects
        #: according to the sorted list of the objects. Then yield the items here in order.
        #: for obj_class in self._idd.iterkeys():
        #:     yield obj_class, self.idf_objects(obj_class)
        #: This will allow getting rid of the :class:`collections.OrderedDict` class which is slow!
        pass

    def field_by_uuid(self, field_uuid):
        """Looks up the field in the field registry and returns the one matching the uuid

        :param str field_uuid: UUID of field as found in the registry
        :rtype: IDFField
        """

        return self.field_registry.get(field_uuid, None)


class IDFObject(list):
    """Represents objects in IDF files.

    This class is a list of :class:`IDFField` objects in the form:

    .. code-block:: python

        [IDFField1, IDFField2, IDFField3]
    """

    #: TODO This class is almost the same as IDDObject. It should subclass it.

    # Using slots simplifies the internal structure of the object and makes
    # it more memory efficiency
    __slots__ = ['comments', 'comments_special', '_outer', 'obj_class', '_obj_class',
                 '_uuid', 'uuid', 'obj_class_display', '_idd_object']

    def __init__(self, outer, obj_class, **kwargs):
        """Initialize the IDF object

        Use kwargs to pre-populate some values, then remove them from kwargs. Also sets
        the idd file for use by this object.

        :param IDFFile outer: :class:`IDFFile` containing this :class:`IDFObject`
        :param str obj_class: Class type of this :class:`IDFObject`
        """

        # Set various attributes of the IDF object
        self.comments = list()  #: Comments for this :class:`IDFObject`
        self.comments_special = list()  #: Special comments for this :class:`IDFObject`
        self._obj_class = obj_class
        self._outer = outer
        self._uuid = None

        # Call the parent class' init method
        super(IDFObject, self).__init__(**kwargs)

    def __str__(self):
        """String representation of the object.
        """

        field_str = self.obj_class_display + ','
        for field in self:
            field_str += str(field or '') + ','
        field_str = field_str[:-1]
        field_str += ';'
        return field_str

    @property
    def obj_class_display(self):
        """Read-only property of class

        :rtype: str
        """

        return self._outer._idd[self.obj_class].obj_class_display

    @property
    def obj_class(self):
        """Read-only property of lower-case class

        :rtype: str
        """

        return self._obj_class

    @property
    def uuid(self):
        """Read-only property containing uuid

        :rtype: str
        """

        if not self._uuid:
            self._uuid = str(uuid.uuid4())
        return self._uuid

    @property
    def idd_object(self):
        """Read-only property containing the object's class's :class:`IDDObject`

        :rtype: IDDObject
        """

        if not self._idd_object:
            self._idd_object = self._outer._idd.get(self.obj_class)
        return self._idd_object

    def duplicate(self):
        """Create a new :class:`IDFField` object and copy this one's references and value.

        :rtype: IDFObject
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

    def set_defaults(self):
        """Populates the object's fields with their defaults using the given IDD
        """

        idd_object = self.idd_object
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


class IDFField(object):
    """Basic component of the IDF object classes.

    Contains a key and value. Values must always be in metric units.
    Values are always strings because IDF files are text files.
    """

    #: TODO This class is actually the same as IDDField. Merge them?
    #: Create a base class with common attributes and subclass it to add any
    #: differences. When creating a new field, simply copy the IDDField and add
    #: the appropriate attributes like value? Need to reset uuid on copy operations.

    # Using slots simplifies the internal structure of the object and makes
    # it more memory efficiency
    __slots__ = ['key', 'tags', 'value', 'idd_object', 'ref_type',
                 'uuid', '_key', '_tags', '_value', '_idd_object',
                 '_ref_type', '_outer', '_uuid', 'index', '_index']

    def __init__(self, outer, value=None, **kwargs):
        """Initializes a new IDF field

        :param IDFObject outer: :class:`IDFObject` containing this :class:`IDFField`
        :param str value: Value of this field
        """

        self._key = kwargs.pop('key', None)
        self._tags = kwargs.pop('tags', None)
        self._index = kwargs.pop('index', None)
        self._value = value
        self._idd_object = None
        self._ref_type = None
        self._outer = outer
        self._uuid = None

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

        :param str new_value: Value to become new vaule of this field
        """

        # Update the value and then the IDFFile's index
        self._value = new_value
        self._outer._outer._upsert_field_index([self])

    @property
    def tags(self):
        """Returns a dict of this field's tags

        :rtype: dict
        """

        if not self._tags:
            self._tags = self.idd_object[self.key].tags
        return self._tags

    @property
    def name(self):
        """Return this field's name (the 'field' tag from the IDD file)

        :rtype: str
        """

        return self.tags.get('field', str())

    @property
    def obj_class(self):
        """Returns this field's outer object's (:class:`IDFObject`) class

        :rtype: str
        """

        return self._outer.obj_class

    @property
    def obj_class_display(self):
        """Returns this field's outer object's (:class:`IDFObject`) class in a nice-to-display form

        :rtype: str
        """

        return self._outer.obj_class_display

    @property
    def index(self):
        """Read-only property that returns the index of this field in its containing object

        :rtype: int
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
            my_id = (self.obj_class_display,
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
        """Read-only property containing this field's corresponding :class:`IDDObject`

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

        :param list(str) tags_to_check:
        :rtype: list(str)
        """

        return list(set(self.tags) & set(tags_to_check))
