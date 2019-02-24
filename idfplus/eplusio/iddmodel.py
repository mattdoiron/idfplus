#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The IDD model file contains the data structure for IDD files.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# Package imports
from odict.pyodict import _odict
# from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

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
ALLOWED_OPTIONS = {'sort_order': ['SortedOrder', 'OriginalOrderTop', 'OriginalOrderBottom'],
                   'special_formatting': ['UseSpecialFormat'],
                   'save_units': ['ViewInIPunits'],  # Yes, the u is lower case!
                   'save_hidden_classes': ['HideEmptyClasses'],
                   'save_hide_groups': ['HideGroups']}


class IDDError(Exception):
    """Base class for IDD exceptions.
    """

    def __init__(self, message, version, *args, **kwargs):
        """Initializes the object

        :param str message: Message to carry along with exception
        :param str version: Expected version of IDD file
        """

        self.message = message
        self.version = version
        super(IDDError, self).__init__(*args, **kwargs)


class MyDict(PersistentMapping):
    """Subclass PersistentMapping in order to override __getitem__ to always use lower case.
    """

    def __getitem__(self, key):
        return super(MyDict, self).__getitem__(key.lower())


class PODict(_odict, MyDict):
    """Persistent ordered dictionary
    """

    def _dict_impl(self):
        return MyDict


class IDDFile(PODict):
    """Primary object representing idd file and container for idd objects.

    Is an :class:`collections.OrderedDict` of :class:`IDDObject` s with the class type as a
    key. All keys are lower case. For example:

    .. code-block:: python

       {'scheduletypelimits': IDDObject,
        'simulationcontrol':  IDDObject}
    """

    def __init__(self, data=(), **kwargs):
        """Initializes the idd file

        :param data: Data to be passed to :class:`PODict` constructor
        :param str version: IDD file version
        :param str parser_version: Version of parser that was used to generate this IDD file
        """

        # Various attributes of the idd file
        self._groups = list()
        self._conversions = list()
        self._version_set = False
        self._version = kwargs.pop('version', None)
        self._parser_version = kwargs.pop('parser_version', None)
        self.options = list()  #: List of option associated with this IDF file
        self.tags = dict()  #: Dictionary of tags associated with this IDF file
        self.file_path = None  #: String containing the file path for this IDF file
        self.object_lists = dict()  #: The object lists for this IDF file
        self._object_list_length = 0
        self._ureg = UNITS_REGISTRY

        # Call the parent class' init method
        super(IDDFile, self).__init__(data, **kwargs)

    def __reduce__(self):
        return super(IDDFile, self).__reduce__()

    def get(self, key, default=None):
        """Override get to ensure lower case key
        """

        return super(IDDFile, self).get(key.lower(), default)

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
        """Read-only property containing IDF file version.
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

    @property
    def object_list_length(self):
        """Read-only property containing length of the nested object_lists variable.
        """

        return self._object_list_length

    def idd_object(self, obj_class):
        """Returns the specified :class:`IDDObject`.

        :param str obj_class: Object class of desired :class:`IDDObject`
        :rtype: IDDObject(IDDField)
        """

        return self.get(obj_class, None)

    def valid_class(self, obj_class):
        """Returns True if provided class is valid

        :param str obj_class: Object class to validate
        :returns: True or False
        :rtype: bool
        """

        if obj_class in self:
            return True
        else:
            return False

    def field(self, obj_class, index):
        """Returns the specified field. Convenience function.

        :param str index: IDD field index such as A1, N1, A2, N2, etc
        :param str obj_class: Object class of desired field
        :rtype: IDFField
        """

        try:
            idd_object = self[obj_class]
            if isinstance(index, int):
                idd_field_key = idd_object.key(index)
            else:
                idd_field_key = index
            field = idd_object[idd_field_key]
        except IndexError:
            field = None
        return field


class IDDObject(dict):
    """Represents objects in idd files.

    This class is a dictionary of fields in the form: {'A1':IDDField1, 'N1':IDDField2}
    """

    def __init__(self, outer, data=(), **kwargs):
        """Use kwargs to pre-populate some values, then remove them from kwargs

        Also sets the idd file for use by this object.

        :param str obj_class_display: Class type of this IDF object (for display purposes)
        :param str group: group to which this IDD object belongs
        :param str comments: Comments for this object
        :param str comments_special: Special comments for this object
        :param IDDFile outer: the outer object for this object
        :param data: Data to be passed to dict's constructor
        """

        # Set various attributes of the IDF object
        self._obj_class_display = kwargs.pop('obj_class_display', None)
        self._group = kwargs.pop('group', None)
        self._ordered_fields = list()
        self._idd = outer
        self._extensible = None
        self.tags = dict()  #: Tags belonging to this :class:`IDDObject`
        self.comments = kwargs.pop('comments', None)  #: Comments for this :class:`IDDObject`
        self.comments_special = kwargs.pop('comments_special', None)  #: Special comments for this :class:`IDDObject`

        # Call the parent class' init method
        super(IDDObject, self).__init__(data)

    @property
    def obj_class(self):
        """Read-only property containing idd object's class type in standardized lower case

        :returns: Returns the obj_class string
        :rtype: str
        """

        return self._obj_class_display.lower()

    @property
    def obj_class_display(self):
        """Read-only property containing idd object's class type in a nice-caps version

        :returns: Returns the obj_class_display string
        :rtype: str
        """

        return self._obj_class_display

    # def index(self, key):
    #     """Read-only property that returns the index of this field
    #
    #     :rtype: int
    #     :return: The index of this field in its outer class
    #     """
    #
    #     return self._ordered_fields.index(key)

    @property
    def group(self):
        """Read-only property containing idd object's group.

        :rtype: str
        """

        return self._group

    def key(self, index):
        """Finds the key from the given index.

        :param int index: The index of the field for which they key is to be returned
        :return: The object's key, eg. A1, N3
        :rtype: str
        """

        try:
            result = self._ordered_fields[index]
        except IndexError:
            # Test for extensible field set:
            if self._extensible > 0:
                field_count = len(self._ordered_fields)
                extensible_start = field_count - self._extensible - 1
                extensible_index = extensible_start + (index % self._extensible)
                result = self._ordered_fields[extensible_index]
            else:
                raise IndexError

        return result

    def ordered_fields(self):
        """Read-only version of the list of field keys.
        """

        return self._ordered_fields

    def get_info(self):
        """Read-only property returning a collection of comments/notes about the obj

        :rtype: str
        """

        # Prepare the info variable and add the object class
        info = 'Class: {}'.format(self.obj_class_display)

        # Grab the object memo, if any
        memo = self.tags.get('memo')
        if memo:
            info += '<br/><br/>'
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
        info += '<br/>'
        info += '<br/>Unique: {}'.format(unique or 'No')
        info += '<br/>Required: {}'.format(required or 'No')
        info += '<br/>Minimum Fields: {}'.format(min_fields) if min_fields else ''
        info += '<br/>Object Obsolete: {}'.format(obsolete) if obsolete else ''

        return info


class IDDField(object):
    """Basic component of the idd object classes.

    A regular object containing parameters such as key, value, tags.
    Examples of tags from are: required, field, type, minimum, etc.
    """

    # TODO merge this class with IDFField?

    def __init__(self, outer, key, **kwargs):
        """

        :param IDDObject outer: The :class:`IDDObject` to which this field belongs
        :param str key: The key used to access this field (i.e. A1, N2, etc)
        """

        self._key = key
        self._outer = outer
        self.value = kwargs.pop('value', None)
        self.tags = dict()

        # Call the parent class' init method
        super(IDDField, self).__init__()

    def get_info(self):
        """Returns a collection of comments/notes about the obj

        :return: Returns a collection of comments/notes about the obj
        :rtype: str
        """

        # Prepare the info variable and add the field name
        field = self.tags.get('field', 'Un-named')
        info = 'Field: {} ({})'.format(self.key, field)

        # Grab the field note, if any
        note = self.tags.get('note')
        if note:
            info += '<br/><br/>'
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
        info += '<br/>'
        info += '<br/>Default: {}'.format(default or 'n/a')
        info += '<br/>Required: {}'.format(required or 'No')
        if units:
            info += '<br/>Default Units: {}'.format(units)
            if ip_units:
                info += '<br/> ({})'.format(ip_units)
        info += '<br/>Minimum: {}'.format(minimum) if minimum else ''
        info += '<br/>Minimum>: {}'.format(minimum_gt) if minimum_gt else ''
        info += '<br/>Maximum: {}'.format(maximum) if maximum else ''
        info += '<br/>Maximum<: {}'.format(maximum_lt) if maximum_lt else ''
        info += '<br/>Deprecated: Yes' if deprecated else ''
        info += '<br/>Autosizable: Yes' if autosizable else ''
        info += '<br/>Autocalculatable: Yes' if autocalculatable else ''

        return info

    @property
    def key(self):
        """Returns the object's key.

        :rtype: str
        """

        return self._key

    @property
    def index(self):
        """Returns object's index

        :rtype: str
        """

        return self._outer._ordered_fields.index(self._key)

    @property
    def obj_class(self):
        """Returns the name of the class from the outer object

        :rtype: str
        """

        return self._outer.obj_class

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
