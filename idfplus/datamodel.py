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

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
from collections import OrderedDict
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from odict.pyodict import _odict
import uuid
import copy
import networkx as nx

# Package imports
from . import refmodel
from . import config

# Investigate as replacement for large lists
# https://pypi.python.org/pypi/blist

# Unit Registry
# Eventually store this somewhere else - put it here for now
UNITS_REGISTRY = {
    '$': {'$': 1},
    '$/(m3/s)': {'$/(ft3/min)': 0.000472000059660808},
    '$/(W/K)': {'$/(Btu/h-F)': 0.52667614683731},
    '$/kW': {'$/(kBtuh/h)': 0.293083235638921},
    '$/m2': {'$/ft2': 0.0928939733269818},
    '$/m3': {'$/ft3': 0.0283127014102352},
    '(kg/s)/W': {'(lbm/sec)/(Btu/hr)': 0.646078115385742},
    '1/hr': {'1/hr': 1},
    '1/K': {'1/F': 0.555555555555556},
    '1/m': {'1/ft': 0.3048},
    'A': {'A': 1},
    'A/K': {'A/F': 0.555555555555556},
    'A/V': {'A/V': 1},
    'Ah': {'Ah': 1},
    'Availability': {'Availability': 1},
    'C': {'F': (1.8, 32)},
    'cm': {'in': 0.3937},
    'cm2': {'inch2': 0.15500031000062},
    'Control': {'Control': 1},
    'cycles/hr': {'cycles/hr': 1},
    'days': {'days': 1},
    'deg': {'deg': 1},
    'deltaC': {'deltaF': 1.8},
    'deltaC/hr': {'deltaF/hr': 1.8},
    'deltaJ/kg': {'deltaBtu/lb': 0.0004299},
    'dimensionless': {'dimensionless': 1},
    'eV': {'eV': 1},
    'g/GJ': {'lb/MWh': 0.00793664091373665},
    'g/kg': {'grains/lb': 7},
    'g/MJ': {'lb/MWh': 7.93664091373665},
    'g/mol': {'lb/mol': 0.0022046},
    'g/m-s': {'lb/ft-s': 0.000671968949659},
    'g/m-s-K': {'lb/ft-s-F': 0.000373574867724868},
    'GJ': {'ton-hrs': 78.9889415481832},
    'hr': {'hr': 1},
    'J': {'Wh': 0.000277777777777778},
    'J/J': {'J/J': 1},
    'J/K': {'Btu/F': 526.565},
    'J/kg': {'Btu/lb': 0.00042986},
    'J/kg-K': {'Btu/lb-F': 0.000239005736137667},
    'J/kg-K2': {'Btu/lb-F2': 0.000132889924714692},
    'J/kg-K3': {'Btu/lb-F3': 7.38277359526066E-05},
    'J/m2-K': {'Btu/ft2-F': 4.89224766847393E-05},
    'J/m3': {'Btu/ft3': 2.68096514745308E-05},
    'J/m3-K': {'Btu/ft3-F': 1.49237004739337E-05},
    'K': {'R': 1.8},
    'K/m': {'F/ft': 0.54861322767449},
    'kg': {'lb': 2.2046},
    'kg/J': {'lb/Btu': 2325.83774250441},
    'kg/kg': {'kg/kg': 1},
    'kg/kg-K': {'lb/lb-F': 0.555555555555556},
    'kg/m': {'lb/ft': 0.67196893069637},
    'kg/m2': {'lb/ft2': 0.204794053596664},
    'kg/m3': {'lb/ft3': 0.062428},
    'kg/m-s': {'lb/ft-s': 0.67196893069637},
    'kg/m-s-K': {'lb/ft-s-F': 0.373316072609094},
    'kg/m-s-K2': {'lb/ft-s-F2': 0.207397818116164},
    'kg/Pa-s-m2': {'lb/psi-s-ft2': 1412.00523459398},
    'kg/s': {'lb/s': 2.20462247603796},
    'kg/s2': {'lb/s2': 2.2046},
    'kg/s-m': {'lb/s-ft': 0.67196893069637},
    'kg-H2O/kg-air': {'kg-H2O/kg-air': 1},
    'kJ/kg': {'Btu/lb': 0.429925},
    'kmol': {'kmol': 1},
    'kmol/s': {'kmol/s': 1},
    'kPa': {'psi': 0.145038, 'inHg': 0.29523},
    'L/day': {'pint/day': 2.11337629827348},
    'L/GJ': {'gal/kWh': 0.000951022349025202},
    'L/kWh': {'pint/kWh': 2.11337629827348},
    'L/MJ': {'gal/kWh': 0.951022349025202},
    'lux': {'foot-candles': 0.092902267},
    'm': {'ft': 3.28083989501312, 'in': 39.3700787401575},
    'm/hr': {'ft/hr': 3.28083989501312},
    'm/s': {'ft/min': 196.850393700787, 'miles/hr': 2.2369362920544},
    'm/yr': {'inch/yr': 39.3700787401575},
    'm2': {'ft2': 10.7639104167097},
    'm2/m': {'ft2/ft': 3.28083989501312},
    'm2/person': {'ft2/person': 10.764961},
    'm2/s': {'ft2/s': 10.7639104167097},
    'm2-K/W': {'ft2-F-hr/Btu': 5.678263},
    'm3': {'ft3': 35.3146667214886, 'gal': 264.172037284185},
    'm3/GJ': {'ft3/MWh': 127.13292},
    'm3/hr': {'ft3/hr': 35.3146667214886},
    'm3/hr-m2': {'ft3/hr-ft2': 3.28083989501312},
    'm3/hr-person': {'ft3/hr-person': 35.3146667214886},
    'm3/kg': {'ft3/lb': 16.018},
    'm3/m2': {'ft3/ft2': 3.28083989501312},
    'm3/m3': {'m3/m3': 1},
    'm3/MJ': {'ft3/kWh': 127.13292},
    'm3/person': {'ft3/person': 35.3146667214886},
    'm3/s': {'ft3/min': 2118.88000328931, 'gal/min': 15850.3222370511},
    'm3/s-m': {'ft3/min-ft': 645.89},
    'm3/s-m2': {'ft3/min-ft2': 196.85},
    'm3/s-person': {'ft3/min-person': 2118.6438},
    'm3/s-W': {'(ft3/min)/(Btu/h)': 621.099127332943},
    'micron': {'micron': 1},
    'minutes': {'minutes': 1},
    'Mode': {'Mode': 1},
    'ms': {'ms': 1},
    'N-m': {'lbf-in': 8.85074900525547},
    'N-s/m2': {'lbf-s/ft2': 0.0208857913669065},
    'Pa': {'psi': 0.000145037743897283, 'ftH2O': 0.00033455, 'inH2O': 0.00401463, 'inHg': 0.00029613, 'Pa': 1},
    'Percent': {'Percent': 1.0},
    'percent/K': {'percent/F': 0.555555555555556},
    'person/m2': {'person/ft2': 0.0928939733269818},
    's/m': {'s/ft': 0.3048},
    'V/K': {'V/F': 0.555555555555556},
    'W': {'Btu/h': 3.4121412858518, 'W': 1},
    'W/(m3/s)': {'W/(ft3/min)': 0.0004719475},
    'W/K': {'Btu/h-F': 1.89563404769544},
    'W/m': {'Btu/h-ft': 1.04072},
    'W/m2': {'Btu/h-ft2': 0.316957210776545, 'W/ft2': 0.09290304, 'W/m2': 1},
    'W/m2-K': {'Btu/h-ft2-F': 0.176110194261872},
    'W/m2-K2': {'Btu/h-ft2-F2': 0.097826},
    'W/m-K': {'Btu-in/h-ft2-F': 6.93481276005548, 'Btu/h-ft-F': 0.577796066000163},
    'W/m-K2': {'Btu/h-F2-ft': 0.321418310071648},
    'W/m-K3': {'Btu/h-F3-ft': 0.178565727817582},
    'W/person': {'Btu/h-person': 3.4121412858518, 'W/person': 1},
}

UNIT_TYPES = {
    'Dimensionless': 'dimensionless',
    'Temperature': 'C',
    'DeltaTemperature': 'C',
    'PrecipitationRate': 'm/hr',
    'Angle': 'degrees',
    'ConvectionCoefficient': 'W/m2-K',
    'ActivityLevel': 'W/person',
    'Velocity': 'm/s',
    'Capacity': 'W',
    'Power': 'W',
    'Availability': 'Availability',
    'Percent': 'Percent',
    'Control': 'Control',
    'Mode': 'Mode'
}


class IDDError(Exception):
    """Base class for IDD exceptions.
    """

    def __init__(self, message, version, *args, **kwargs):
        self.message = message
        self.version = version
        super(IDDError, self).__init__(*args, **kwargs)


class IDFError(Exception):
    """Base class for IDF exceptions.
    """

    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(IDFError, self).__init__(*args, **kwargs)


class PODict(_odict, PersistentMapping):
    """Persistent ordered dictionary
    """

    def _dict_impl(self):
        return PersistentMapping


class IDDFile(PODict):
    """Primary object representing idd file and container for idd objects.

    Is an OrderedDict of IDDObjects with the class type as a
    key. For example:

    .. code-block:: python

    {'ScheduleTypeLimits': IDDObject,
    'SimulationControl':  IDDObject}

    :attr str version: IDD file version
    :attr list groups: List of groups to which classes can belong
    """

    def __init__(self, data=(), **kwargs):
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
        self._version = kwargs.pop('version', None)
        self._parser_version = kwargs.pop('parser_version', None)
        self.options = list()
        self.tags = dict()
        self.object_lists = dict()
        self._ureg = UNITS_REGISTRY

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
        """Read-only property containing idf file version.
        """

        return self._version

    @property
    def parser_version(self):
        """Read-only property containing version of the parser used to generate file.
        """

        return self._parser_version

    @property
    def groups(self):
        """Read-only property containing list of all possible class groups
        """

        return self._groups

    @property
    def conversions(self):
        """Read-only property containing list unit conversions
        """

        return self._conversions

    def idd_object(self, obj_class):
        """Returns the specified object class.

        :param obj_class:
        """

        return self.get(obj_class, PersistentList())

    def valid_class(self, obj_class):
        """Returns True if provided class is valid

        :param obj_class: Object class to validate
        """

        if obj_class in self:
            return True
        elif obj_class.lower() in self:
            return True
        elif obj_class.upper() in self:
            return True
        else:
            return False

    def field(self, obj_class, index):
        """Returns the specified field. Convenience function.

        :param index:
        :param obj_class:
        """

        try:
            idd_object = self[obj_class]
            idd_field_key = idd_object.key(index)
            field = idd_object[idd_field_key]
        except IndexError:
            field = None
        return field


class IDDObject(dict):
    """Represents objects in idd files.

    Contains a dictionary of fields in the form: {'A1':IDDField1, 'N1':IDDField2}
    """

    def __init__(self, outer, data=(), **kwargs):
        """Use kwargs to pre-populate some values, then remove them from kwargs

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
        self._ordered_fields = list()
        self._idd = outer
        self.tags = dict()
        self.comments = kwargs.pop('comments', None)
        self.comments_special = kwargs.pop('comments_special', None)

        # Call the parent class' init method
        super(IDDObject, self).__init__(data)

    @property
    def obj_class(self):
        """Read-only property containing idd object's class type

        :returns str: Returns the obj_class string
        """

        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idd object's group.

        :rtype: str
        """

        return self._group

    def key(self, index):
        """Finds the key from the given index.
        :param index:
        """

        return self._ordered_fields[index]

    def ordered_fields(self):
        """Read-only version of the list of field keys.
        """

        return self._ordered_fields

    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj
        """

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
    Examples of tags from are: required, field, type, minimum, etc.
    """

    # TODO merge this class with IDFField?

    def __init__(self, outer, key, **kwargs):

        self._key = key
        self._outer = outer
        self._obj_class = outer.obj_class
        self.value = kwargs.pop('value', None)
        self.tags = dict()

        # Call the parent class' init method
        super(IDDField, self).__init__()

    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj
        """

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
    def key(self):
        """Returns the object's key.

        :rtype: str
        :return: The object's key
        """

        return self._key

    @property
    def obj_class(self):
        """Returns the object's class.

        :rtype: str
        :return: The name of the class from the outer object
        """

        return self._outer._obj_class

    @property
    def units(self):
        """Read-only property containing idd field's SI units.

        :rtype: str
        """

        return self.tags.get('units')

    @property
    def ip_units(self):
        """Read-only property containing idd field's IP units.

        :rtype: str
        """

        return self.tags.get('ip-units')


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
        self._references = refmodel.ReferenceModel()

    def init_blank(self):
        """Sets up a blank idf file
        """

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

        # Ensure we have a list to simplify later operations
        if not isinstance(object_list_name, list):
            object_list_name = [field.tags['object-list']]

        # Cycle through all class names in the object lists and count references
        ref_node_count = 0
        for cls_list in object_list_name:
            if self._references._ref_lists[cls_list].get(field.value, None):
                ref_node_count += 1

        return ref_node_count

    def _populate_obj_classes(self):
        """Pre-allocates the keys of the IDFFile.

        This must be done early so that all objects added later are added
        in the proper order (this is an OrderedDict!).
        """

        self.update((k, list()) for k in self._idd.iterkeys())

    def find(self, contains=None):
        """Searches within the file for objects having 'contains'

        :param str contains:  (Default value = None)
        """

        pass

    def idf_objects(self, obj_class):
        """Returns all the objects in the specified class.

        :param obj_class:
        """

        return self.get(obj_class, PersistentList())

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

    def add_objects(self, new_objects, position=None):
        """Adds the specified object(s) to the IDFFile.

        :param position:
        :param new_objects: List of IDFObjects
        :returns int: Number of objects added
        """

        # Fail if object class is not valid
        obj_class = new_objects[0].obj_class
        if not self._idd.valid_class(obj_class):
            return 0

        # Set insert point to 'position' or end of list
        if position is None:
            position = -1

        # Insert the new object(s)
        self[obj_class][position:position] = new_objects
        idd_obj = self._idd[obj_class]

        # Add nodes for each field.
        for obj in new_objects:
            for j, field in enumerate(obj):
                key = idd_obj.key(j)
                tags = idd_obj[key].tags
                self._references.add_field(field, tags)

        return len(new_objects)

    # def update_object(self, obj_class, index, new_values):
    #     """Updates the specified object.
    #     :param obj_class:
    #     :param index:
    #     :param new_values:
    #     """
    #
    #     self._references.update_reference(obj_class, index, new_values)
    #     self[obj_class][index].update(new_values)

    def field(self, obj_class, index_obj, index_field, create=None):
        """Returns the specified field. Convenience function.

        :param create: Defines whether non-allocated fields should be created
        :param index_field:
        :param index_obj:
        :param obj_class:
        """

        field = None

        try:
            field = self[obj_class][index_obj][index_field]
        except IndexError:
            if create is True:
                # An IndexError means that we're trying to assign a value
                # to a field that has not yet been 'allocated'. Check for max
                # allowable fields and allocate more if necessary.
                max_field_count = len(self._idd.get(obj_class, []))
                idf_object = self[obj_class][index_obj]
                current_field_count = len(idf_object)

                # If within limits allowed, allocate additional field 'slots'
                if index_field < max_field_count:
                    extra_field_count = index_field - current_field_count + 1
                    extra_fields = extra_field_count*[None]
                    idf_object.extend(extra_fields)

                    # Create a new field object, give it a value and save it
                    field = IDFField(self.idf_objects[index_obj])
                    self[obj_class][index_obj][index_field] = field

        return field

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
        self._references.remove_references(objects_to_delete)
        del self[obj_class][first_row:last_row]

    def units(self, field):
        """Returns the given field's current display units.

        :param field:
        """

        if field is None:
            return None

        # Look-up the default units
        units = field.tags.get('units')

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

    def converted_value(self, field, row, column):
        """Converts the value of the field if necessary

        :param field:
        :param row:
        :param column:
        :return: field value
        """

        if not field:
            # Return None if no field is given
            converted_value = None
        elif self.si_units is True:
            # Default is always SI, so don't convert here
            converted_value = field.value
        else:
            # Get the unit conversion
            ip_unit_conversion = self._unit_conversion(field, row, column)

            # If the units were found, perform the conversion
            if ip_unit_conversion:
                converted_value = self._to_ip(field.value, ip_unit_conversion)
            else:
                converted_value = field.value

        return converted_value

    def _unit_conversion(self, field, row, column):
        """Gets the appropriate unit conversion value(s)

        :param field:
        :param row:
        :param column:
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
                based_on_field = None

                # Find which idd object has the specified key
                for fld in idd_object:
                    if fld.key == based_on_field_key:
                        # ind = idd_object.index(f)
                        # if ind >= len(idf_objects[row]):
                        #     return None
                        # based_on_field = idd_object[ind]
                        based_on_field = fld
                        break

                # Use these results to find the actual units to use
                actual_units = UNIT_TYPES.get(based_on_field.value)

                if actual_units:
                    units = actual_units

            # Lookup the dict of unit conversions for this SI unit.
            conv = UNIT_TYPES.get(units)
            if conv:
                # Lookup the desired ip_units in the dict if specified, otherwise get the
                # 'first' (only) one in the dict.
                return conv.get(ip_units, conv.get(conv.keys()[0]))

        return None

    @staticmethod
    def _to_si(value, conversion):
        """Accepts a value and a conversion factor, and returns the value in SI units.

        :param conversion: Conversion factor to use to convert units
        :param value: string value from IDFField object
        """

        # If the units were found, perform the conversion
        try:
            # Convert units and force it back to a string
            data = str(float(value) / conversion)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conversion[0]
            adder = conversion[1]
            data = str((float(value) - adder) / multiplier)
        return data

    @staticmethod
    def _to_ip(value, conversion):
        """Accepts a value and a conversion factor, and returns the value in IP units.

        :param value: string value from IDFField object
        :param conversion: Conversion factor to use to convert units
        """

        # If the units were found, perform the conversion
        try:
            # Convert units and force it back to a string
            data = str(float(value) * conversion)
        except TypeError:
            # If there is a type error, it's actually a tuple (for temperatures)
            multiplier = conversion[0]
            adder = conversion[1]
            data = str(float(value) * multiplier + adder)
        except ValueError:
            data = value
        return data


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

    def __init__(self, outer, **kwargs):
        """Use kwargs to pre-populate some values, then remove them from kwargs

        Also sets the idd file for use by this object.

        :param str group:
        :param str outer:
        :param str args:
        :param IDDFile idd: idd file used by this idf file
        :param str obj_class: Class type of this idf object
        :param \*args: arguments to pass to dictionary
        :param \*\*kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self._outer = outer
        self._ref_graph = None
        self._group = kwargs.pop('group', None)
        self._obj_class = kwargs.pop('obj_class', None)
        self.comments = kwargs.pop('comments', [])
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
        for field in result:
            field._outer = result

        return result

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
        """Populates the field with its defaults

        :param idd:
        """

        idd_objects = idd.get(self.obj_class)
        for i, field in enumerate(idd_objects.itervalues()):
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

    def add_field(self, idf_field, tags):
        """Adds a field to self and takes care of references.

        :param idf_field:
        :param tags:
        """

        # Add the new field to self (a list)
        self.append(idf_field)

        # Update the outer class' (IDF file) references
        self._outer._references.add_field(idf_field, tags)

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

    def __init__(self, outer, *args, **kwargs):
        """Initializes a new idf field

        :param str key:
        :param value:
        :param IDFObject outer:
        """

        self.key = kwargs.pop('key', None)
        self._value = kwargs.pop('value', None)
        self.tags = dict()
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

        # Update the IDFFile's references graph then set the value
        self._outer._outer._references.update_references(self)
        self._value = new_value

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
    def position(self):
        """Read-only property that returns the position (index) of this field

        :rtype: int
        :return: The index of this field in its outer class
        """

        return self._outer.index(self.value)

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
