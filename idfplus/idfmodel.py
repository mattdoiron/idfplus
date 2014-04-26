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

import shelve
import os.path
from collections import OrderedDict


class IDDFile(OrderedDict):
    """Primary object representing idd file and container for idd objects.

    Contains an OrderedDict of lists of IDDObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': IDDObject,
         'SimulationControl':  IDDObject}

    :attr version: IDD file version
    :attr groups: List of groups to which classes can belong
    """

    def __init__(self, version, *args, **kwargs):
        """Initializes the idd file

        :param version: IDD file version
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Various attributes of the idd file
        self.__idd_file = 'EnergyPlus_IDD_v{}.dat'
        self.__data_path = 'data'

        # Call the parent class' init method
        super(IDDFile, self).__init__(*args, **kwargs)

        # Create the full path to the idd file
        file_name = os.path.join(self.__data_path,
                                 self.__idd_file.format(version))

        # Check if the file name is a file and then open the idd file
        if os.path.isfile(file_name):
            with shelve.open(file_name) as f:
                # Set some more attributes with using the idd file
                self.__version = f['version']
                self.__groups = f['groups']
                self.__conversions = f['conversions']
                self._OrderedDict__update(f['idd'])
        else:
            raise IOError

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, IDDObject):
            raise TypeError('Only items of type IDDObject can be added!')

        super(IDDFile, self).__setitem__(key, value, dict_setitem)

    @property
    def version(self):
        """Read-only property containing idf file version"""
        return self.__version

    @property
    def groups(self):
        """Read-only property containing list of all possible class groups"""
        return self.__groups

    @property
    def conversions(self):
        """Read-only property containing list unit conversions"""
        return self.__conversions


class IDDObject(OrderedDict):
    """Represents objects in idd files.

    Contains an OrderedDict of fields in the form:
        {'A1': IDDField1,
         'N1': IDDField2,
         'A2': IDDField3}
    """

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, IDDField):
            raise TypeError('Only items of type IDDField can be added!')

        super(IDDObject, self).__setitem__(key, value, dict_setitem)


class IDDField(dict):
    """Basic component of the idd object classes.

    Simply a regular dict containing keys which are the names of various
    field tags from the following list:
        required, field, type, minimum, etc.
    """
    pass


class IDFFile(OrderedDict):
    """Primary object representing idf file and container for idf objects.

    Contains an OrderedDict of lists of IDFObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': [IDFObject1, IDFObject2, IDFObject3],
         'SimulationControl':  [IDFObject4]}

    :attr idd: IDDFile object containing precompiled idd file
    :attr version: EnergyPlus vesion number (eg. 8.1.0.800)
    :attr eol_char: depends on file (could be \n or \r\n, etc)
    :attr options: options that may have been found in idf file
    :attr file_path: full, absolute path to idf file
    """

    def __init__(self, file_path, *args, **kwargs):
        """Initializes a new idf file with the given file_path

        :param file_path:
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """
        # Call the parent class' init method
        super(IDFFile, self).__init__(*args, **kwargs)

        # Various attributes of the idf file
        self.__idd = None
        self.__version = None
        self.__eol_char = None
        self.options = []
        self.file_path = file_path

        # Call the load method to parse and save the idf file
        self.__load__()

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, list):
            raise TypeError('Only lists of IDFObjects can be added!')

        for val in value:
            if not isinstance(val, IDFObject):
                raise TypeError('Only items of type IDFObject can be added!')

        super(IDFFile, self).__setitem__(key, value, dict_setitem)

    def __load__(self):
        """Parses and loads an idf file into the object instance variable.
        Also sets some attributes of the file.
        """

        import idfparse

        (count, eol_char, options, idd,
         group_list, objects, version) = idfparse.Parser(self.file_path)

        self.__idd = idd
        self.__version = version
        self.__eol_char = eol_char
        self.options = options
        self._OrderedDict__update(objects)

    @property
    def version(self):
        """Read-only property containing idf file version"""
        return self.__version

    @property
    def idd(self):
        """Read-only property containing idd file"""
        return self.__idd

    @property
    def eol_char(self):
        """Read-only property containing the end of line characters"""
        return self.__eol_char

    def find(self, contains=None):
        """Searches within the file for objects having 'contains'

        :param contains:  (Default value = None)
        """
        pass

    def save(self, file_path):
        """Handles writing of the idf file back to disk.

        :param file_path: The absolute file path to the corresponding idf
        """
        pass


class IDFObject(OrderedDict):
    """Represents objects in idf files.

    Contains an OrderedDict of fields in the form:
        {'A1': 'field1 value',
         'N1': 123.23,
         'A2': 'field value 213'}

    :attr idd: Contains the IDD file used by this IDF object
    :attr obj_class: Class type of object
    :attr group: Group to which this object belongs
    :attr comments: User comments for this object
    :attr incomming_links: List of tupples of objects that link to this
    :attr outgoing_links: List of tupples of objects to which this links
    """

    def __init__(self, idd, obj_class, parent, *args, **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param idd: idd file used by this idf file
        :param obj_class: Class type of this idf object
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self.__idd = idd
        self.__obj_class = obj_class
        self.__incomming_links = []
        self.__outgoing_links = []
        self.__parent = parent
        self.comments = kwargs.pop('comments', None)

        # Call the parent class' init method
        super(IDFObject, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        if 'IPUnits' in self.__parent.options:
            return self.toIP(super(IDFObject, self).__getitem__(key),
                             self.__obj_class,
                             key)
        else:
            return super(IDFObject, self).__getitem__(key)

    def __repr__(self):
        """Returns a string representation of the object in idf format"""
        values = [str(val) for val in self.values()]
        str_list = ','.join(values)
        return self.__obj_class + ',' + str_list + ';'

    @property
    def idd(self):
        """Read-only property containing idd file"""
        return self.__idd

    @property
    def obj_class(self):
        """Read-only property containing idf object's class type"""
        return self.__obj_class

    @property
    def group(self):
        """Read-only property containing idf object's group"""
        return self.__group

    @property
    def incomming_links(self):
        """Read-only property containing incomming links"""
        return self.__incomming_links

    @property
    def outgoing_links(self):
        """Read-only property containing outgoing links"""
        return self.__outgoing_links

    @property
    def parent(self):
        """Read-only property containing the parent of this obj"""
        return self.__parent

    def value(self, field):
        """Returns the value of the specified field.

        :param field: Field id or key to be retrieved
        :raises TypeError: If field is not a string or an int
        """

        # Check for proper types and return the value
        if isinstance(field, int):
            return self[self.keys()[field]]
        elif isinstance(field, str):
            return self[field]
        else:
            raise TypeError('Invalid key type - must be string or int')

    def addLink(self, obj, field_id, incomming=False, outgoing=False):
        """Ads a link to and/or from this object.

        :param obj: Another object of type IDFObject
        :param field_id: A field id like 'A1' or 'N1'
        :param incomming:  (Default value = False)
        :param outgoing:  (Default value = False)
        :raises ValueError: If neither incomming nor outgoing is True
        :raises TypeError: If either field_id or obj are not a valid types
        """

        # Checks for valid inputs
        if not incomming and not outgoing:
            raise ValueError('Must specify either incomming or outgoing.')
        if not isinstance(obj, IDFObject) or not isinstance(field_id, str):
            raise TypeError('Invalid object or field_id type.')

        # Adds the specified objects to the list(s) of links
        link = (obj, field_id)
        if incomming and link not in self.__incomming_links:
            self.__incomming_links.append((obj, field_id))
        if outgoing and link not in self.__outgoing_links:
            self.__outgoing_links.append((obj, field_id))
        return True

    def removeLink(self, obj, field_id, incomming=False, outgoing=False):
        """Removes a link to and/or from this object.

        :param obj: Another object of type IDFObject
        :param field_id: A field id like 'A1' or 'N1'
        :param incomming:  (Default value = False)
        :param outgoing:  (Default value = False)
        :raises ValueError: If neither incomming nor outgoing is True
        :raises TypeError: If either field_id or obj are not a valid types
        """

        # Checks for valid inputs
        if not incomming and not outgoing:
            raise ValueError('Must specify either incomming or outgoing.')
        if not isinstance(obj, IDFObject) or not isinstance(field_id, str):
            raise TypeError('Invalid object or field_id type.')

        # Removes the specified objects to the list(s) of links
        link = (obj, field_id)
        if incomming and link in self.__incomming_links:
            self.__incomming_links.remove(link)
        if outgoing and link in self.__outgoing_links:
            self.__outgoing_links.remove(link)
        return True


class IDFField(dict):
    """Basic component of the idf object classes.

    Simply a regular dict containing keys which are the names of various
    field tags from the following list:
        required, field, type, minimum, etc.
    """

    def __init__(self, key, value, parent, *args, **kwargs):
        """Initializes a new idf field"""
        self.__key = key
        self.__value = value
        self.__parent = parent

        # Call the parent class' init method
        super(IDFField, self).__init__(*args, **kwargs)

    def __repr__(self):
        return self.__parent.obj_class + ':' + self.__key

    def __toIP__(self, value, obj_class, key):
        """Converts incomming value to IP units
        1. Get units of specified obj_class:key combo.
        2. Lookup equivalent IP unit (where?)
        3. Retrieve conversion factor from parent
        4. Return input value multiplied by conversion factor"""

#        conversion_type = 'm=>ft'
#        conversion_factor = self.__parent.conversions[conversion_type]
#        return value * conversion_factor
        return value

    def value(self, ip=False):
        if ip:
            return self.__toIP__(self.__value,
                                 self.__parent.obj_class,
                                 self.__key)
        else:
            return self.__value
