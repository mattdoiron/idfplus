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


class MissingIDDFile(Exception):
    pass


class MissingFilePath(Exception):
    pass


class InvalidIDFClass(Exception):
    pass


class InvalidIDFObject(Exception):
    pass


class InvalidField(Exception):
    pass


class IDDFile(OrderedDict):
    '''Primary object representing idd file and container for idd objects.'''

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
    '''Primary object representing idf file and container for idf objects.'''

    version = None      # EnergyPlus vesion number (eg. 8.1.0.800)
    options = []        # options that may have been found in idf file
    file_path = None    # full, absolute path to idf file
    eol_char = None     # depends on file (could be \n or \r\n, etc)
    idd = None          # IDDFile object containing precompiled idd file

    def __init__(self, file_path, *args, **kwargs):
        super(IDFFile, self).__init__(*args, **kwargs)

        if not file_path:
            raise MissingFilePath
        else:
            self.file_path = file_path

        self.__load(self)

#    def options(self):
#        '''Retrieves current options for the idf file.'''
#        return self.options

#    def setOptions(self, opts):
#        '''Sets options for the idf file'''
#        if opts in self.options:
#            return True
#        if not opts in self.options:
#            self.options.append(opts)
#            return True
#        else:
#            return False

#    def addObject(self, cls, index, obj):
#        '''adds a new idf object to the specified idf file.
#        Validates entries and required fields against the idd file.'''
#        if cls in self:
#            try:
#                self[cls].insert(index, obj)
#                return True
#            except IndexError:
#                raise InvalidIDFObject
#        else:
#            raise InvalidIDFClass

#    def removeObject(self, cls, index):
#        '''deletes the specified idf object'''
#        if cls in self:
#            try:
#                self[cls].pop(index)
#                return True
#            except IndexError:
#                raise InvalidIDFObject
#        else:
#            raise InvalidIDFClass

#    def idfObject(self, cls, index, contains=None):
#        '''retrieves and idf object from the given idf file'''
#        if cls in self:
#            try:
#                return self[cls][index]
#            except IndexError:
#                raise InvalidIDFObject
#        else:
#            raise InvalidIDFClass

#    def idfClass(self, cls):
#        '''retrieves all idf objects of a certain class from the
#        given idf file'''
#        if cls in self:
#            return self[cls]
#        else:
#            raise InvalidIDFClass

    def find(self, contains=None):
        '''Searches within the file for objects having "contains"'''
        pass

    def __load(self):
        '''parses and loads an idf file into the object (instance
        variable stores it)'''

        import idfparse

        (count, eol_char, options, idd,
         group_list, objects, version) = idfparse.Parser(self.file_path)

        self.version = version
        self.options = options
        self.eol_char = eol_char
        self._OrderedDict__update(objects)
        self.idd = idd

        # parse idf file then
        # set class types to be empty IDFClass objects then
        # set groups, version, eol_char, etc
        pass

    def save(self, file_path):
        '''Handles writing of the idf file to disk.'''
        pass


#class IDFClass(list):
#    '''Container for idf objects'''  # is this needed?
#
#    group = None
#    class_type = None
#
#    def __init__(self, group, class_type, *args, **kwargs):
#        super(IDFClass, self).__init__(*args, **kwargs)
#        self.group = group
#        self.class_type = class_type


class IDDObject(OrderedDict):
    '''Represents objects in idd files.'''

    obj_tags = None
    comments_special = None
    group = None
    obj_class = None
    tags = None  # expand to show all possible tags as properties?

    def __init__(self, *args, **kwargs):
        # Use kwargs to prepopulate some values, then remove them from kwargs
        self.obj_tags = kwargs.pop('obj_tags', None)
        self.comments_special = kwargs.pop('comments_special', None)
        self.group = kwargs.pop('group', None)
        self.obj_class = kwargs.pop('obj_class', None)
        super(IDDObject, self).__init__(*args, **kwargs)


class IDFObject(OrderedDict):
    '''Represents objects in idf files.'''

    idd = None
    comments = None         # User comments for field
    obj_class = None        # Class type of object
#    incomming_links = []
#    outgoing_links = []

    def __init__(self, idd, *args, **kwargs):
        # Use kwargs to prepopulate some values, then remove them from kwargs
        self.obj_tags = kwargs.pop('obj_tags', None)
        self.field_tags = kwargs.pop('field_tags', None)
        self.comments = kwargs.pop('comments', None)
        self.comments_special = kwargs.pop('comments_special', None)
        self.group = kwargs.pop('group', None)
        self.obj_class = kwargs.pop('obj_class', None)
        super(IDFObject, self).__init__(*args, **kwargs)

    def field(self, fld):
        '''Returns a field object of type IDFField'''
        if type(fld) is int:
            return self[self.keys()[fld]]
        elif type(fld) is str:
            self.get(fld)

    @property
    def tags(self):
        '''Returns list of tags like "default", "required", etc, from idd.'''
        return self.idd[self.obj_class].tags

    @property
    def comments_pecial(self):
        '''Returns the comments from idd file'''
        pass

    @property
    def group(self):
        '''Returns the group to which this obj belongs (from idd file)'''
        pass

    @property
    def incomming_links(self):
        '''Returns list of notes that reference any fields in this object.
        (How will it know that a field is a node? not sure it's possible.
        Check idd file)'''
        pass

    @property
    def outgoing_links(self):
        '''Returns list of nodes referenced by any fields in this object.
        (How will it know that a field is a node? not sure it's possible.
        Check idd file?)'''
        pass


class IDFField(object):
    '''Basic component of the idf object classes.'''

    idd = None
    obj_class = None
    value = None
    field_id = None

    def __init__(self, idd, obj_class, field_id, value, *args, **kwargs):
        super(IDFField, self).__init__(*args, **kwargs)
        self.idd = idd
        self.obj_class = obj_class
        self.field_id = field_id
        self.value = value

    def __repr__(self):
        return self.value

    @property
    def fieldType(self):
        '''Returns field type (eg: alphanumeric, number, choice, etc) from idd'''
        pass

    @property
    def tags(self):
        '''Returns list of tags like "default", "required", etc, from idd.'''
        return self.idd[self.obj_class][self.field_id].tags

    @property
    def comments(self):
        '''Returns comments for field from idd.'''
        pass
