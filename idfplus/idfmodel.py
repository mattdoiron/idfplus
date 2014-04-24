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
along with Foobar. If not, see <http://www.gnu.org/licenses/>.
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

    :property version: IDD file version
    :type version: string
    :property groups: List of groups to which classes can belong
    :type groups: list of strings
    :property idd_path: file name of idd files, minus version number
    :type idd_path: string
    :property data_path: Folder where idd files are found (relative to root)
    :type data_path: string

    """

    # Various properties of the idd file
    version = None      # EnergyPlus vesion number (eg. 8.1.0.800)
    groups = []         # Groups to which various classes can belong
    idd_file = 'EnergyPlus_IDD_v{}.dat'
    data_path = 'data'

    def __init__(self, version, *args, **kwargs):
        """

        :param version: IDD file version
        :type version: string
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary

        """
        super(IDDFile, self).__init__(*args, **kwargs)

        file_name = os.path.join(self.data_path,
                                 self.idd_file.format(version))

        if os.path.isfile(file_name):
            with shelve.open(file_name) as f:
                version, groups, idd = f
        else:
            raise IOError

        self.version = version
        self.groups = groups
        self._OrderedDict__update(idd)


class IDDObject(OrderedDict):
    """Represents objects in idd files.

    Contains an OrderedDict of fields in the form:
        {'A1': IDDField1,
         'N1': IDDField2,
         'A2': IDDField3}

    """
    pass


class IDDField(dict):
    """Basic component of the idd object classes.

    Simply a regular dict containing keys in the form of 'A1' or 'N2' and
    values for each of the idd field properties in the following list:
        required, field, type, minimum, etc.

    """
    pass


class IDFFile(OrderedDict):
    """Primary object representing idf file and container for idf objects.

    Contains an OrderedDict of lists of IDFObjects with the class type as a
    key. For example:
        {'ScheduleTypeLimits': [IDFObject1, IDFObject2, IDFObject3],
         'SimulationControl':  [IDFObject4]}

    """

    # Various properties of the idf file
    idd = None          # IDDFile object containing precompiled idd file
    version = None      # EnergyPlus vesion number (eg. 8.1.0.800)
    options = []        # options that may have been found in idf file
    file_path = None    # full, absolute path to idf file
    eol_char = None     # depends on file (could be \n or \r\n, etc)

    def __init__(self, file_path, *args, **kwargs):
        """

        :param file_path:
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary

        """
        super(IDFFile, self).__init__(*args, **kwargs)
        self.file_path = file_path
        self.__load()

    def __load(self):
        """Parses and loads an idf file into the object instance variable.
        Also sets some properties of the file.


        """

        import idfparse

        (count, eol_char, options, idd,
         group_list, objects, version) = idfparse.Parser(self.file_path)

        self.idd = idd
        self.version = version
        self.options = options
        self.eol_char = eol_char
        self._OrderedDict__update(objects)

    def find(self, contains=None):
        """Searches within the file for objects having "contains"

        :param contains:  (Default value = None)

        """
        pass

    def save(self, file_path):
        """Handles writing of the idf file back to disk.

        :param file_path:

        """
        pass


class IDFObject(OrderedDict):
    """Represents objects in idf files.

    Contains an OrderedDict of fields in the form:
        {'A1': 'field1 value',
         'N1': 123.23,
         'A2': 'field value 213'}


    """

    # Various properties of the idf object
    idd = None
    comments = None         # User comments for field
    obj_class = None        # Class type of object
    group = None            # Group to which this object belongs
    incomming_links = []    # List of tupples of objects that link to this
    outgoing_links = []     # List of tupples of objects to which this links

    def __init__(self, idd, *args, **kwargs):
        """Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.

        :param idd:
        :param *args: arguments to pass to dictionary
        :param **kwargs: keyword arguments to pass to dictionary

        """
        self.idd = idd
        self.comments = kwargs.pop('comments', None)
        self.obj_class = kwargs.pop('obj_class', None)
        self.group = kwargs.pop('group', None)
        super(IDFObject, self).__init__(*args, **kwargs)

    def value(self, fld):
        """

        :param fld:

        """
        if type(fld) is int:
            # return self.items()[fld][1] (alternate method)
            return self[self.keys()[fld]]
        elif type(fld) is str:
            return self[fld]
        else:
            raise TypeError('Invalid key type - must be string or int')

    def add_link(self, obj, field_id, incomming=False, outgoing=False):
        """Ads a link to and/or from this object.
        obj should be another IDFObject and field_id like 'A1' or 'N2'

        :param obj:
        :param field_id:
        :param incomming:  (Default value = False)
        :param outgoing:  (Default value = False)

        """
        if not incomming and not outgoing:
            raise ValueError('Must specify either incomming or outgoing.')
        if not isinstance(obj, IDFObject) or not isinstance(field_id, str):
            raise TypeError('Invalid object or field_id type.')
        if incomming:
            self.incomming_links.append((obj, field_id))
        if outgoing:
            self.outgoing_links.append((obj, field_id))
        return True
