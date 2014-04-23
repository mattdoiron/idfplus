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

from collections import OrderedDict


class IDDFile(OrderedDict):
    '''
    Primary object representing idd file and container for idd objects.
    Contains an OrderedDict of IDDObjects with the class type as key.
    '''

    # Various properties of the idd file
    version = None      # EnergyPlus vesion number (eg. 8.1.0.800)
    groups = []         # Groups to which various classes can belong
    data_path = 'data/EnergyPlus_IDD_v{}.dat'

    def __init__(self, version, *args, **kwargs):
        super(IDDFile, self).__init__(*args, **kwargs)

        import shelve  # should use ZODB eventually

        try:
            version, groups, idd = shelve.open(self.data_path.format(version))
        except Exception, err:  # should catch more specific error
            return err

        self.version = version
        self.groups = groups  # make this an iterator, not a list
        self._OrderedDict__update(idd)


class IDFFile(OrderedDict):
    '''
    Primary object representing idf file and container for idf objects.
    Contains an OrderedDict of IDFObjects with the class type as key.
    '''

    # Various properties of the idf file
    version = None      # EnergyPlus vesion number (eg. 8.1.0.800)
    options = []        # options that may have been found in idf file
    file_path = None    # full, absolute path to idf file
    eol_char = None     # depends on file (could be \n or \r\n, etc)
    idd = None          # IDDFile object containing precompiled idd file

    def __init__(self, file_path, *args, **kwargs):
        super(IDFFile, self).__init__(*args, **kwargs)
        self.__load(self)

    def __load(self):
        '''
        Parses and loads an idf file into the object instance variable.
        Also sets some properties of the file.
        '''

        import idfparse

        (count, eol_char, options, idd,
         group_list, objects, version) = idfparse.Parser(self.file_path)

        self.version = version
        self.options = options
        self.eol_char = eol_char
        self._OrderedDict__update(objects)
        self.idd = idd

    def find(self, contains=None):
        '''Searches within the file for objects having "contains"'''
        pass

    def save(self, file_path):
        '''Handles writing of the idf file back to disk.'''
        pass


class IDFObject(OrderedDict):
    '''
    Represents objects in idf files.

    Contains an OrderedDIct of fields in the form:
        {'A1': 'field1 value',
         'N1': 123.23,
         'A2': 'field value 213'}
    '''

    # Various properties of the idf object
    idd = None
    comments = None         # User comments for field
    obj_class = None        # Class type of object
    group = None            # Group to which this object belongs
    incomming_links = {}    # List of objects that link to this one
    outgoing_links = {}     # List of objects to which this one links

    def __init__(self, idd, *args, **kwargs):
        '''
        Use kwargs to prepopulate some values, then remove them from kwargs
        Also sets the idd file for use by this object.
        '''
        self.idd = idd
        self.comments = kwargs.pop('comments', None)
        self.obj_class = kwargs.pop('obj_class', None)
        self.group = kwargs.pop('group', None)
        super(IDFObject, self).__init__(*args, **kwargs)

    def field(self, fld):
        '''Returns a field's value by id or index'''
        if type(fld) is int:
            return self[self.keys()[fld]]
        elif type(fld) is str:
            self.get(fld)

    def add_link(self, obj, field_id, incomming=False, outgoing=False):
        '''
        Ads a link to and/or from this object.
        obj should be another IDFObject and field_id like 'A1' or 'N2'
        '''
        if not incomming and not outgoing:
            return False
        if incomming:
            self.incomming_links.update({field_id: obj})
        if outgoing:
            self.outgoing_links.update({field_id: obj})
        return True

    def incomming_links(self):
        '''Returns list of notes that reference any fields in this object.
        (How will it know that a field is a node? not sure it's possible.
        Check idd file)'''
        pass

    def outgoing_links(self):
        '''Returns list of nodes referenced by any fields in this object.
        (How will it know that a field is a node? not sure it's possible.
        Check idd file?)'''
        pass


class IDDObject(OrderedDict):
    '''Represents objects in idd files.

    Simply a regular OrderedDict containing IDDField objects with the keys
    being the class type.
    '''

    pass


class IDDField(object):
    '''Basic component of the idd object classes.

    Simply a regular dict containing keys in the form of 'A1' or 'N2' and
    values for each of the idd field properties in the following list:
        required, field, type, minimum, etc.
    '''

    pass
