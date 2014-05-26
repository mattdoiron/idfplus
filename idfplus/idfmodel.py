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


class IDDFileDoesNotExist(Exception):
    pass


class VersionAlreadySet(Exception):
    pass


class IDDFile(OrderedDict):
    """Primary object representing idd file and container for idd objects.

    Contains an OrderedDict of lists of IDDObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': IDDObject,
         'SimulationControl':  IDDObject}

    :attr version: IDD file version
    :attr groups: List of groups to which classes can belong
    """

    def __init__(self, version=None, *args, **kwargs):
        """Initializes the idd file

        :param version: IDD file version
        :param groups: list of groups from the idd file
        :param conversions: list of unit conversions from the idd file
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Various attributes of the idd file
        self._version_set = False
        self._idd_file_name = 'EnergyPlus_IDD_v{}.dat'
        self._data_path = 'data'
        self._version = version

        # Continue only if a version is specified, else a blank IDD file
        if version:

            # Create the full path to the idd file
            file_name = os.path.join(self._data_path,
                                     self._idd_file_name.format(version))

            # Check if the file name is a file and then open the idd file
            if os.path.isfile(file_name):
                f = shelve.open(file_name)

                # Set some more attributes with using the idd file
                self._groups = f['groups']
                self._conversions = f.get('conversions', None)
                #self._class_tree = f['class_tree']  # To be implemented
                self._OrderedDict__update(f['idd'])

                f.close()
            else:
                raise IDDFileDoesNotExist("Can't find IDD file: {}".format(file_name))

        # Call the parent class' init method
        super(IDDFile, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, IDDObject):
            raise TypeError('Only items of type IDDObject can be added!')

        super(IDDFile, self).__setitem__(self, key, value)

    def _set_version(self, version):
        """Method used to set the version of the IDD file. Can only
        be set once for safety and sanity."""
        if self._version_set is True:
            raise VersionAlreadySet('Version can be set only once.')
        else:
            self._version = version
            self._version_set = True

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


class IDDObject(OrderedDict):
    """Represents objects in idd files.

    Contains an OrderedDict of fields in the form:
        {'A1': IDDField1,
         'N1': IDDField2,
         'A2': IDDField3}
    """

    def __init__(self, obj_class, group, parent, *args, **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param obj_class: Class type of this idf object
        :param group: group that this idd object belongs to
        :param parent: the parent object for this object (type IDDFile)
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self._obj_class = obj_class
        self._group = group
        self._parent = parent
        self.comments = kwargs.pop('comments', None)
        self.comments_special = kwargs.pop('comments_special', None)

        # Call the parent class' init method
        super(IDDObject, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, IDDField):
            raise TypeError('Only items of type IDDField can be added!')

        super(IDDObject, self).__setitem__(key, value, dict_setitem)

    @property
    def obj_class(self):
        """Read-only property containing idd object's class type"""
        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idd object's group"""
        return self._group


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
    :attr version: EnergyPlus vesion number (eg. 8.1.0.008)
    :attr eol_char: depends on file (could be \n or \r\n, etc)
    :attr options: options that may have been found in idf file
    :attr file_path: full, absolute path to idf file
    """

    def __init__(self, file_path=None, *args, **kwargs):
        """Initializes a new idf, blank or opens the given file_path

        :param file_path:
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Various attributes of the idf file
        self._version_set = False
        self._idd = None
        self._eol_char = None
        self.file_path = None
        self.options = []

        # Load the idf file if specified, otherwise prepare a blank one
        if file_path:
            import idfparse
#            idf = idfparse.IDFParser(file_path)
            self.file_path = file_path
            parser = idfparse.IDFParser(self)
            for progress in parser.parseIDF(file_path):
                print progress
#            self._idd = idf.idd
#            self._version = idf.version
#            self._eol_char = idf.eol_char
#            self.options = idf.options
#            self._OrderedDict__update(objects)
        else:
            default = '8.1'  # retrieve this from settings eventually
            self._version = kwargs.pop('version', default)
            self._idd = IDDFile(self._version)

        # Call the parent class' init method
        super(IDFFile, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        """Override the default __setitem__ to ensure that only certain
        object types are allowed."""

        if not isinstance(value, list):
            raise TypeError('Only lists of IDFObjects can be added!')

        for val in value:
            if not isinstance(val, IDFObject):
                raise TypeError('Only items of type IDFObject can be added!')

        super(IDFFile, self).__setitem__(self, key, value)

#    def _load(self):
#        """Parses and loads an idf file into the object instance variable.
#        Also sets some attributes of the file.
#        """
#
#        import idfparse
#
#        (count, eol_char, options, idd,
#         group_list, objects, version) = idfparse.Parser(self.file_path)
#
#        self._idd = idd
#        self._version = version
#        self._eol_char = eol_char
#        self.options = options
#        self._OrderedDict__update(objects)

    def _load_idd(self):
        """Loads an idd file in the case where this is a blank idf file."""

        default = '8.1'  # retrieve this from settings eventually
        self.idd = IDDFile(self._version or default)

    def _set_version(self, version):
        """Method used to set the version of the IDF file. Can only
        be set once for safety and sanity."""
        if self._version_set is True:
            raise VersionAlreadySet('Version can be set only once.')
        else:
            self._version = version
            self._version_set = True

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

        :param contains:  (Default value = None)
        """
        pass

    def save(self, file_path):
        """Handles writing of the idf file back to disk.

        :param file_path: The absolute file path to the corresponding idf
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


class IDFObject(list):
    """Represents objects in idf files.

    Contains a list of fields in the form:
        [IDFField1, IDFField2, IDFField3]

    :attr obj_class: Class type of object
    :attr group: Group to which this object belongs
    :attr idd: Contains the IDD file used by this IDF object
    :attr comments: User comments for this object
    :attr incomming_links: List of tupples of objects that link to this
    :attr outgoing_links: List of tupples of objects to which this links
    """

    def __init__(self, obj_class, group, parent, idd, *args, **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param idd: idd file used by this idf file
        :param obj_class: Class type of this idf object
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary
        """

        # Set various attributes of the idf object
        self._group = group
        self._obj_class = obj_class
        self._idd = idd
        self._incomming_links = []
        self._outgoing_links = []
        self._parent = parent
        self.comments = kwargs.pop('comments', None)

        # Call the parent class' init method
        super(IDFObject, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        if 'IPUnits' in self._parent.options:
            return self.toIP(super(IDFObject, self).__getitem__(key),
                             self._obj_class,
                             key)
        else:
            return super(IDFObject, self).__getitem__(key)

    def __repr__(self):
        """Returns a string representation of the object in idf format"""
        values = [str(val) for val in self.values()]
        str_list = ','.join(values)
        return self._obj_class + ',' + str_list + ';'

    @property
    def idd(self):
        """Read-only property containing idd file"""
        return self._idd

    @property
    def obj_class(self):
        """Read-only property containing idf object's class type"""
        return self._obj_class

    @property
    def group(self):
        """Read-only property containing idf object's group"""
        return self._group

    @property
    def incomming_links(self):
        """Read-only property containing incomming links"""
        return self._incomming_links

    @property
    def outgoing_links(self):
        """Read-only property containing outgoing links"""
        return self._outgoing_links

    @property
    def parent(self):
        """Read-only property containing the parent of this obj"""
        return self._parent

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
        if incomming and link not in self._incomming_links:
            self._incomming_links.append((obj, field_id))
        if outgoing and link not in self._outgoing_links:
            self._outgoing_links.append((obj, field_id))
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
        if incomming and link in self._incomming_links:
            self._incomming_links.remove(link)
        if outgoing and link in self._outgoing_links:
            self._outgoing_links.remove(link)
        return True


class IDFField(dict):
    """Basic component of the idf object classes.

    Simply a regular dict containing keys which are the names of various
    field tags from the following list:
        required, field, type, minimum, etc.
    """

    def __init__(self, key, value, parent, *args, **kwargs):
        """Initializes a new idf field"""
        self._key = key
        self._value = value
        self._parent = parent

        # Call the parent class' init method
        super(IDFField, self).__init__(*args, **kwargs)

    def __repr__(self):
        return self._parent.obj_class + ':' + self.__key

    def __toIP__(self, value, obj_class, key):
        """Converts incomming value to IP units
        1. Get units of specified obj_class:key combo.
        2. Lookup equivalent IP unit (where?)
        3. Retrieve conversion factor from parent
        4. Return input value multiplied by conversion factor"""

#        conversion_type = 'm=>ft'
#        conversion_factor = self._parent.conversions[conversion_type]
#        return value * conversion_factor
        return value

    def value(self, ip=False):
        if ip:
            return self.__toIP__(self._value,
                                 self._parent.obj_class,
                                 self._key)
        else:
            return self._value
