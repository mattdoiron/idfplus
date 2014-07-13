# !/usr/bin/python
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

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
import os
import shelve
import datetime as dt
import transaction
from persistent.list import PersistentList

# Package imports
from . import datamodel
from . import logger
from .datamodel import IDDFileDoesNotExist

# Constants
from . import idfsettings as c

OPTIONS_LIST = ['OriginalOrderTop', 'UseSpecialFormat']
COMMENT_DELIMITER_GENERAL = '!'
COMMENT_DELIMITER_SPECIAL = '!-'
TAG_LIST = ['\\field',
            '\\note',
            '\\required-field',
            '\\begin-extensible',
            '\\units',
            '\\ip-units',
            '\\unitsBasedOnField',
            '\\minimum>',
            '\\minimum',
            '\\maximum<',
            '\\maximum',
            '\\default',
            '\\deprecated',
            '\\autosizeable',
            '\\autocalculatable',
            '\\type',
            '\\retaincase',
            '\\key',
            '\\object-list',
            '\\reference',
            '\\memo',
            '\\unique-object',
            '\\required-object',
            '\\min-fields',
            '\\obsolete',
            '\\extensible:',
            '\\begin-extensible',
            '\\format',
            '\\group']

# Setup logging
log = logger.setup_logging(c.LOG_LEVEL, __name__)

#test_line1 = '0.0,15.2,3.0;  !- X,Y,Z ==> Vertex 4 {m} '
#test_line2 = '0.0,15.2,3.0 ;  !test '
#test_line3 = '0.0,15.2,3.0;  !test  !- X,Y,Z ==> Vertex 4 {m}  '
#test_line4 = '0.0,15.2,3.0;  !- X,Y,Z ==> Vertex 4 {m}!test  '
#test_line5 = '0.0,15.2  ,3.0;  '
#test_line6 = ' ! comment 123'
#test_line7 = '  !- comment 456'
#test_line8 = '  BuildingSurface:Detailed,'
#test_line9 = '    ,            !- Outside Boundary Condition Object'
#test_line10 = '    SunExposed,              !- Sun Exposure'
#test_line11 = '    SunExposed,,,;              !- Sun Exposure'
#test_line12 = '  !  '
#test_line13 = '  !- one !-two  '
#test_line14 = '     \memo Note that the following 3 fields'
#test_line15 = ' N1; \memothis is a test'
#test_line16 = '  '
#test_line17 = '!'

#tag_line1 = 'SimulationControl,'
#tag_line2 = '      \unique-object'
#tag_line3 = '     \memo Note that the following 3 fields are related to the Sizing:Zone, Sizing:System,'
#tag_line4 = '      \key Yes'
#tag_line5 = 'SimulationControl, \memo this is a test'
#tag_line6 = ' SimulationControl, \memothis is a test'

#print 'Comments:'
#print '- line 1: "' + str(getGeneralComment(test_line1)) + '"'
#print '- line 2: "' + str(getGeneralComment(test_line2)) + '"'
#print '- line 3: "' + str(getGeneralComment(test_line3)) + '"'
#print '- line 4: "' + str(getGeneralComment(test_line4)) + '"'
#print '- line 5: "' + str(getGeneralComment(test_line5)) + '"'
#print '- line 6: "' + str(getGeneralComment(test_line6)) + '"'
#print '- line 7: "' + str(getGeneralComment(test_line7)) + '"'
#print '- line 8: "' + str(getGeneralComment(test_line8)) + '"'
#print '- line 9: "' + str(getGeneralComment(test_line9)) + '"'
#print '- line 10: "' + str(getGeneralComment(test_line10)) + '"'
#print '- line 11: "' + str(getGeneralComment(test_line11)) + '"'
#print '- line 12: "' + str(getGeneralComment(test_line12)) + '"'
#print '- line 13: "' + str(getGeneralComment(test_line13)) + '"'
#print '- line 14: "' + str(getGeneralComment(test_line14)) + '"'
#print '- line 15: "' + str(getGeneralComment(test_line15)) + '"'
#print '- line 16: "' + str(getGeneralComment(test_line16)) + '"'
#print '- line 17: "' + str(getGeneralComment(test_line17)) + '"'

#print 'Fields:'
#print '- line 1: "' + str(get_fields(test_line1)) + '"'
#print '- line 2: "' + str(get_fields(test_line2)) + '"'
#print '- line 3: "' + str(get_fields(test_line3)) + '"'
#print '- line 4: "' + str(get_fields(test_line4)) + '"'
#print '- line 5: "' + str(get_fields(test_line5)) + '"'
#print '- line 6: "' + str(get_fields(test_line6)) + '"'
#print '- line 7: "' + str(get_fields(test_line7)) + '"'
#print '- line 8: "' + str(get_fields(test_line8)) + '"'
#print '- line 9: "' + str(get_fields(test_line9)) + '"'
#print '- line 10: "' + str(get_fields(test_line10)) + '"'
#print '- line 11: "' + str(get_fields(test_line11)) + '"'
#print '- line 12: "' + str(get_fields(test_line12)) + '"'
#print '- line 13: "' + str(get_fields(test_line13)) + '"'
#print '- line 14: "' + str(get_fields(test_line14)) + '"'
#print '- line 15: "' + str(get_fields(test_line15)) + '"'
#print '- line 16: "' + str(get_fields(test_line16)) + '"'

#print 'Whole Line:'
#print parse_line(test_line1)
#print parse_line(test_line2)
#print parse_line(test_line3)
#print parse_line(test_line4)
#print parse_line(test_line5)
#print parse_line(test_line6)
#print parse_line(test_line7)
#print parse_line(test_line8)
#print parse_line(test_line9)
#print parse_line(test_line10)
#print parse_line(test_line11)
#print parse_line(test_line12)
#print parse_line(test_line13)
#print parse_line(test_line14)
#print parse_line(test_line15)
#print parse_line(test_line16)


class Writer(object):
    """Class to take care of writing idf and idd files."""

    def __init__(self):
        pass

    @staticmethod
    def write_idf(idf):
        """Write an IDF from the specified idfObject
        :param idf: :type IDFObject
        :param idd: :type IDDObject
        :param options: :type list: List of options
        """

        idd = idf._idd
        options = idf.options
        eol_char = idf._eol_char
        test_file_name = idf.file_path + '_test'

        print('Writing file: {}'.format(test_file_name))

        # Check for special options
        use_special_format = False
        if 'UseSpecialFormat' in options:
            use_special_format = True
            print('Special formatting requested, but not yet implemented.')

        # Open file and write
        try:
            with open(test_file_name, 'w') as file:
                for obj_class, obj_list in idf.iteritems():

                    for obj in obj_list:
                        # Write special comments if there are any
                        # if obj['comments_special'] is not None:
                        # for comment in obj.tags.get('comments_special', []):
                        #     file.write("!-{}{}".format(comment, eol_char))

                        # Write comments if there are any
                        # if obj['comments'] is not None:
                        for comment in obj.comments:
                            file.write("!{}".format(comment))

                        # Some objects are on one line and some fields are grouped!
                        # If enabled, check IDD file for special formatting instructions
                        if use_special_format:
                            pass

                        # Write the object name
                        file.write("  {},\n".format(obj_class))

                        # Write the fields
                        # if obj['fields']:
                        field_count = len(obj)
                        for i, field in enumerate(obj):
                            field_note = idd[obj_class][i].tags.get('field', None)
                            if field_note:
                                note = ' !-{}'.format(field_note)
                            else:
                                note = ''
                            if i == field_count - 1:
                                file.write("    {};{}\n".format(field.value, note))
                            else:
                                file.write("    {},{}\n".format(field.value, note))

                        # Add newline at the end of the object
                        file.write(eol_char)

            print('File written!')
            return True
        except IOError as e:
            print('File not written! Exception!' + str(e.strerror))
            return False

    # @staticmethod
    # def write_idd(idd, options):
    #     """Write an IDD from the specified iddObject
    #     :param idd:
    #     :param options:
    #     """
    #
    #     print('Writing file: ' + idd.file_path)
    #
    #     # how will this be written? shelve? ZODB?
    #     # probably just shelve...


# Write the idf file
#writeIDF('testoutput.idf', options, objects)


#print get_tags(tag_line1)
#print get_tags(tag_line2)
#print get_tags(tag_line3)
#print get_tags(tag_line4)
#print get_tags(tag_line5)
#print get_tags(tag_line6)


#print 'Whole Line:'
#print parseLineIDD(test_line1)
#print parseLineIDD(test_line2)
#print parseLineIDD(test_line3)
#print parseLineIDD(test_line4)
#print parseLineIDD(test_line5)
#print parseLineIDD(test_line6)
#print parseLineIDD(test_line7)
#print parseLineIDD(test_line8)
#print parseLineIDD(test_line9)
#print parseLineIDD(test_line10)
#print parseLineIDD(test_line11)
#print parseLineIDD(test_line12)
#print parseLineIDD(test_line13)
#print parseLineIDD(test_line14)
#print parseLineIDD(test_line15)
#print parseLineIDD(test_line16)

class Parser(object):
    """Base class for more specialized parsers"""

    def __init__(self, *args, **kwargs):
        #        self.msg = msg  # Communicate()
        pass

    @staticmethod
    def get_fields(line_in):
        """Strips all comments, etc and returns what's left
        :rtype : list:
        :param line_in:
        """
        global COMMENT_DELIMITER_GENERAL
        global COMMENT_DELIMITER_SPECIAL
        fields = list()

        # Partition the line twice
        part_a = line_in.partition(COMMENT_DELIMITER_SPECIAL)
        part_b = part_a[0].partition(COMMENT_DELIMITER_GENERAL)

        if part_b[0].strip().startswith('\\'):
            # This is a tag and not a comment
            fields = list()

        elif part_b[0].strip():
            # Split the list into fields at the commas
            fields = part_b[0].expandtabs().strip().split(',')

            # Check for and remove items created by a trailing comma
            if not fields[-1] and len(fields) > 1:
                fields.pop(-1)

            # Strip away any spaces from each field
            fields = map(lambda i: i.expandtabs().strip(), fields)

            # Remove any list items that are actually tags
            fields = [item for item in fields if not item.startswith('\\')]

            # Check for and remove semicolon in field at the end of an object
            if fields:
                if fields[-1].find(';') != -1:
                    fields[-1] = fields[-1].partition(';')[0].strip()
                    fields.extend([';'])

        # Return list of fields
        return fields

    @staticmethod
    def get_comments_general(line_in):
        """Parses a string and returns the general comment if it exists
        :param line_in:
        :rtype : str:
        """
        global COMMENT_DELIMITER_GENERAL
        global COMMENT_DELIMITER_SPECIAL
        comments = str()

        if line_in.find(COMMENT_DELIMITER_GENERAL) == -1:
            # No comments found at all
            comments = str()

        elif line_in.find(COMMENT_DELIMITER_SPECIAL) == -1:
            # No special comment found so parse simply
            part = line_in.partition(COMMENT_DELIMITER_GENERAL)
            comments = part[-1].expandtabs()

        elif line_in.find(COMMENT_DELIMITER_SPECIAL) != -1 and \
             line_in.count(COMMENT_DELIMITER_GENERAL) == 1:
            # Special comment found, but no general comment
            comments = str()

        else:
            # Both types of comments may be present so parse in more detail
            part_a = line_in.partition(COMMENT_DELIMITER_SPECIAL)

            if part_a[0].find(COMMENT_DELIMITER_GENERAL) != -1:
                # General comment precedes special comment, repartition
                part_b = line_in.partition(COMMENT_DELIMITER_GENERAL)
                comments = part_b[-1].expandtabs()

            elif part_a[-1].find(COMMENT_DELIMITER_GENERAL) != -1:
                # General comment is in the last item (part of special comment)
                comments = str()

        # Return comments
        return comments

    @staticmethod
    def get_comments_special(line_in):
        """Parses a line and returns any special comments present.
        :rtype : str
        :param line_in:
        """
        global COMMENT_DELIMITER_SPECIAL
        line_clean = line_in.expandtabs().lstrip()
        comment_list_special = str()

        if line_clean.startswith(COMMENT_DELIMITER_SPECIAL):
            comment_list_special = line_clean.lstrip(COMMENT_DELIMITER_SPECIAL)

        # Return comments
        return comment_list_special

    @staticmethod
    def get_tags(line_in):
        """Parses a line and gets any fields tags present
        :rtype : dict:
        :param line_in: 
        """

        global TAG_LIST
        tag_result = dict()

        # Create a list containing any tags found in line_in
        match = [x for x in TAG_LIST if x in line_in]

        # If there are any matches, save the first one
        if match:

            # Partition the line at the match
            part = line_in.strip().partition(match[0])

            # If there is a value save it
            if part[-1]:
                value = part[-1].lstrip()
            else:
                value = True

            # Save results
            tag_result = dict(tag=match[0].strip('\\'),
                              value=value)

        # Return results
        return tag_result

    @staticmethod
    def get_options(line_in):
        """Parses a line and returns any options present.
        :rtype : list
        :param line_in:
        """
        global OPTIONS_LIST
        line_clean = line_in.expandtabs().lstrip()
        matches = list()

        if line_clean.startswith('!-Option'):
            matches = [x for x in OPTIONS_LIST if x in line_clean]

        # Return matches
        return matches

    def parse_line(self, line_in):
        """Parses a line from the IDD/IDF file and returns results
        :rtype : dict:
        :param line_in: 
        """

        # Get results
        fields = self.get_fields(line_in)
        comments = self.get_comments_general(line_in)
        comments_special = self.get_comments_special(line_in)
        options = self.get_options(line_in)
        tags = self.get_tags(line_in)
        end_object = False
        empty_line = False

        # Check for an empty line
        if not (fields or comments or tags or comments_special or options):
            empty_line = True

        # Check for and remove the semicolon, indicating the end of an object
        elif fields:
            if fields[-1] == ';':
                fields.pop(-1)
                end_object = True

        # Return a dictionary of results
        return dict(fields=fields,
                    comments=comments,
                    comments_special=comments_special,
                    options=options,
                    tags=tags,
                    end_object=end_object,
                    empty_line=empty_line)


class IDDParser(Parser):
    """Class that handles all parsing related specifically to IDD files.
    :param idd:
    :param args:
    :param kwargs:
    """

    def __init__(self, idd=None, *args, **kwargs):
        """Initialize the parser
        :type idd: IDDFile
        :param idd:
        :param args:
        :param kwargs:
        """

        if idd is not None:
            print('custom idd received by parser')
            self.idd = idd
        else:
            print('no custom idd received by parser. using blank')
            self.idd = datamodel.IDDFile()

        # Call the parent class' init method
        super(IDDParser, self).__init__(*args, **kwargs)

    @staticmethod
    def init_db(idd):
        """Initializes a shelve database and saves the idd file to it.
        :param idd:
        :return Shelve Database:
        """

        data_dir = 'data'
        version = 'IDDTEMP'
        file_name_root = 'EnergyPlus_IDD_v{}.dat'
        file_name = file_name_root.format(version)
        idd_path = os.path.join(datamodel.APP_ROOT, data_dir, file_name)

        try:
            print('Opening idd dat file: {}'.format(idd_path))
            database = shelve.open(idd_path, protocol=2, writeback=True)
            print('idd type is: {}'.format(type(idd)))
            database['idd'] = idd
            database['date_generated'] = dt.datetime.now()
            return database
        except IOError as e:
            return False
        except Exception as e:
            print(e.message)

    @staticmethod
    def rename_idd(version):
        """Renames the idd once the version is known."""

        print('Renaming temp idd file.')
        file_name_root = 'EnergyPlus_IDD_v{}.dat'
        file_name = file_name_root.format(version)
        new = os.path.join(datamodel.APP_ROOT, 'data', file_name)
        old = new.replace(version, 'IDDTEMP')
        os.rename(old, new)

    def parse_idd(self, file_path):
        """Parse the provided idd (or idf) file
        :rtype : generator
        :param file_path: 
        """

        #TODO write parser for unit conversion comments!
        global COMMENT_DELIMITER_SPECIAL  # Avoid these...

        total_size = os.path.getsize(file_path)
        total_read = 0.0

        print('Parsing IDD file: {} ({} bytes)'.format(file_path, total_size))

        # Create an on-disk database in which to store the new idd
        db = self.init_db(self.idd)
        idd = db['idd']

        # Open the specified file in a safe way
        with open(file_path, 'r') as idd_file:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            tag_list = list()
            tag_dict = dict()
            # obj_tag_list = list()
            obj_tag_dict = dict()
            version = None
            group = None
            group_list = list()
            conversions = list()
            end_object = False
            idd_object = datamodel.IDDObject(idd)

            # Cycle through each line in the file (yes, use while!)
            while True:

                # Parse this line using readline (so last one is a blank)
                line = idd_file.readline()
                total_read += len(line)
                line_parsed = self.parse_line(line)

                # Detect end of line character for use when re-writing file
                if line.endswith('\r\n'):
                    idd._eol_char = '\r\n'
                else:
                    idd._eol_char = '\n'

                # If previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Check for special options
                if line_parsed['options']:
                    idd.options.extend(line_parsed['options'])

                # If there are any comments save them
                if line_parsed['comments']:
                    comment_list.append(line_parsed['comments'])

                    # Detect file version
                    if 'IDD_Version' in line_parsed['comments']:
                        version_raw = line_parsed['comments'].split()[1].strip()
                        version = '.'.join(version_raw.split('.')[0:2])
                        idd._version = version
                        print('Found idd version in idd file: '.format(db['idd']._version))

                # Check for special comments and options
                if line_parsed['comments_special']:
                    comment_list_special.append(line_parsed['comments_special'])

                # If there are any fields save them
                if line_parsed['fields']:
                    field_list.extend(line_parsed['fields'])

                # Check for the end of an object before checking for new tags
                if (end_object and empty_line) or line_parsed['fields']:
                    if tag_dict:
                        tag_list.append(tag_dict)
                        tag_dict = dict()
                    if obj_tag_dict:
                        obj_tag_dict.update(obj_tag_dict)
                        # obj_tag_dict = dict()

                # If there are any field tags for this object save them
                if line_parsed['tags']:
                    tag = line_parsed['tags']['tag']
                    value = line_parsed['tags']['value']
                    # print('tag: {}, val: {}'.format(tag, value))

                    # If there are tags, but no fields then these are object-level tags
                    if len(field_list) <= 1:
                        # print('found object-level tag')
                        if tag in obj_tag_dict:
                            try:
                                obj_tag_dict[tag].append(value)
                            except AttributeError:
                                obj_tag_dict[tag] = [obj_tag_dict[tag], value]
                        else:
                            # Otherwise simply add it
                            obj_tag_dict[tag] = value
                        # print('obj lvl: tag: {}, value: {}'.format(tag, value))
                    else:
                        # If this tag is already present, try to append its value
                        # print('found field-level tag')
                        if tag in tag_dict:
                            try:
                                tag_dict[tag].append(value)
                            except AttributeError:
                                tag_dict[tag] = [tag_dict[tag], value]
                        else:
                            # Otherwise simply add it
                            tag_dict[tag] = value
                        # print('field lvl: tag: {}, value: {}'.format(tag, value))

                    # Check for the special group tag
                    if line_parsed['tags']['tag'] == 'group':
                        # print('found group tag: {}'.format(line_parsed['tags']['value']))
                        group = line_parsed['tags']['value']
                        if group not in group_list:
                            group_list.append(group)

                # If this is the end of an object then save it
                if end_object and empty_line:

                    # The first field is the object class name
                    obj_class = field_list.pop(0)

                    # Create IDDField objects for all fields
                    for i, field in enumerate(field_list):
                        new_field = datamodel.IDDField(idd_object)
                        new_field.key = field
                        new_field.value = None
                        try:
                            # print('field_tag_list: {}'.format(field_tag_list))
                            new_field.tags = tag_list[i]
                        except IndexError:
                            new_field.tags = dict()
                        # print('new_field.tags: {}'.format(new_field.tags))
                        idd_object.append(new_field)
                        # print('setting field tags: {}'.format(new_field.tags))
                        # idd_object.update({field:new_field})

                    # Save the parsed variables in the idd_object
                    idd_object._obj_class = obj_class
                    idd_object._group = group
                    idd_object.comments_special = comment_list_special
                    idd_object.comments = comment_list
                    idd_object.tags = obj_tag_dict
                    # print('setting object tags: {}'.format(idd_object.tags))

                    # Add the group to the idd's list if it isn't already there
                    if group not in idd._groups:
                        idd._groups.append(group)

                    # Save the new object as part of the IDD file
                    if obj_class not in ['Lead Input', 'Simulation Data']:
                        idd[obj_class] = idd_object

                    # Reset variables for next object
                    field_list = list()
                    comment_list = list()
                    comment_list_special = list()
                    tag_list = list()
                    tag_dict = dict()
                    # obj_tag_list = list()
                    obj_tag_dict = dict()
                    end_object = False
                    idd_object = datamodel.IDDObject(idd)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # Yield the current progress for progress bars
                yield total_read

            idd._conversions = conversions
            idd._groups = group_list
            idd._tree_model = None

        # Save changes and rename temp idd file because we now know the version
        db.close()
        self.rename_idd(version)
        print('Parsing IDD complete!')

    @staticmethod
    def save_idd(idd):
        """Shelves a copy of the IDD file object.
        :param idd:
        :raises : Exception
        :rtype : bool
        """
        print('Saving idd...')
        print('Received idd with {} keys'.format(len(idd.keys())))
        if not idd.version:
            raise Exception("Missing IDD file version")

        version = idd.version
        data_dir = 'data'
        file_name_root = 'EnergyPlus_IDD_v{}.dat'
        file_name = file_name_root.format(version)
        idd_path = os.path.join(datamodel.APP_ROOT, data_dir, file_name)

        try:
            # storage = ZODB.FileStorage.FileStorage(idd_path)
            print('Opening idd dat file: {}'.format(idd_path))
            # db = ZODB.DB(idd_path)
            # connection = db.open()
            # root = db.open().root

            # print('saving idd to root obj: {}'.format(type(idd)))
            database = shelve.open(idd_path, protocol=2, writeback=True)
            print('idd type is: {}'.format(type(idd)))
            print('test 1 idd for keys: {}'.format(idd.keys()[:20]))
            database['idd'] = idd
            database['date_generated'] = dt.datetime.now()
            database.close()

            # root.idd = idd
            # root.date_generated = dt.datetime.now()
            print('Saving idd file to disk...')
            # transaction.commit()
            # db.close()
            print('test 2 idd for keys: {}'.format(idd.keys()[:20]))
            return True
        except IOError as e:
            return False
        except Exception as e:
            print(e.message)

    @staticmethod
    def load_idd(version):
        """Loads an idd file into the object instance variable.
        Also sets some attributes of the file.
        :rtype : IDDFile
        :param version:
        :return: :raise IDDFileDoesNotExist:
        """

        print("Loading idd file...")
        idd_file_name = 'EnergyPlus_IDD_v{}.dat'.format(version)
        data_dir = 'data'

        # Create the full path to the idd file
        idd_path = os.path.join(datamodel.APP_ROOT, data_dir, idd_file_name)

        print('Checking for idd version: {}'.format(version))
        print(idd_path)

        # Check if the file name is a file and then open the idd file
        if os.path.isfile(idd_path):
            print('idd found, loading...')
            database = shelve.open(idd_path, flag='r')
            idd = database['idd']
            date_generated = database['date_generated']
            database.close()
            try:
                print('Testing if loaded idd file has a version attribute')
                print('Version found! (v{})'.format(idd.version))
                print('test 3 idd for keys: {}'.format(idd.keys()[:5]))
                return idd
            except AttributeError:
                print('No version attribute found!')
                raise IDDFileDoesNotExist("Can't find version attribute in IDD file.",
                                          version)
        else:
            print('idd not found')
            raise IDDFileDoesNotExist("Can't find IDD file: {}".format(idd_path),
                                      version)


#---------------------------------------------------------------------------
class IDFParser(Parser):
    """IDF file parser that handles opening, parsing and returning."""

    def __init__(self, idf=None, *args, **kwargs):
        """Initializes the IDFParser class with an option idf file.
        :param idf:
        :param args:
        :param kwargs:
        """

        # Set idf if it's given
        if idf is not None:
            self.idf = idf
        else:
            self.idf = datamodel.IDFFile()
        self.idd = None

        # Call the parent class' init method
        super(IDFParser, self).__init__(*args, **kwargs)

    def parse_idf(self, file_path):
        """Parse the provided idf file and return an IDFObject.
        :param file_path:
        :rtype : iterator
        """

        global OPTIONS_LIST  # Avoid these?

        # file_path = self.idf.file_path  # TODO this will be None if blank idf used!
        self.idf.file_path = file_path
        total_size = os.path.getsize(file_path)
        total_read = 0.0

        log.info('Parsing IDF file: {} ({} bytes)'.format(file_path, total_size))
        print('Parsing IDF file: {} ({} bytes)'.format(file_path, total_size))

        # Open the specified file in a safe way
        with open(file_path, 'r') as idf:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            group = None
            end_object = False
            idf_object = datamodel.IDFObject(self.idf)

            # Cycle through each line in the file (yes, use while!)
            while True:

                # Parse this line using readline (so last one is a blank)
                line = idf.readline()
                total_read += len(line)
                line_parsed = self.parse_line(line)

                # Detect end of line character for use when re-writing file
                if line.endswith('\r\n'):
                    self.idf._eol_char = '\r\n'
                else:
                    self.idf._eol_char = '\n'

                # If previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Clean the input line (get rid of tabs and left white spaces)
                line_clean = line.expandtabs().lstrip()

                # Check for special options
                if line_parsed['options']:
                    self.idf.options.extend(line_parsed['options'])

                # If there are any comments save them
                if line_parsed['comments']:
                    comment_list.append(line_parsed['comments'])

                # Check for special comments and options
                if line_parsed['comments_special']:
                    comment_list_special.append(line_parsed['comments_special'])

                # If there are any fields save them
                if line_parsed['fields']:
                    field_list.extend(line_parsed['fields'])

                    # Detect idf file version and use it to select idd file
                    if field_list[0] == 'Version':
                        version = field_list[1]
                        self.idf._version = version
                        print('idf detected as version: {}'.format(version))
                        print('Checking for idd...')
                        if not self.idd:
                            print('No idd currently selected!')
                            idd_parser = IDDParser()
                            idd = idd_parser.load_idd(version)
                            self.idf._idd = idd
                            self.idd = idd

                            # Use the list of object classes from the idd to populate
                            # the idf file's object classes. This must be done early
                            # so that all objects added later are added to properly
                            # ordered classes.
                            self.idf.update((k, PersistentList()) for k, v in idd.iteritems())

                        print('idd loaded as version: {}'.format(self.idd.version))

                # If this is the end of an object save it
                if end_object and empty_line:

                    # The first field is the object class name
                    obj_class = field_list.pop(0)

                    # The fields to use are defined in the idd file
                    idd_fields = self.idd[obj_class]

                    # Create IDFField objects for all fields
                    for i, field in enumerate(field_list):
                        if idd_fields:
                            # print(idd_fields[i])
                            key = idd_fields[i].key
                            tags = idd_fields[i].tags
                        else:
                            key = obj_class
                            tags = dict()
                        new_field = datamodel.IDFField(idf_object)
                        new_field.key = key
                        new_field.value = field
                        new_field.tags = tags
                        idf_object.append(new_field)
                        # idf_object.update({field:new_field})

                    # Save the parsed variables in the idf_object
                    idf_object._obj_class = obj_class
                    idf_object._group = group
                    idf_object.comments_special = comment_list_special
                    idf_object.comments = comment_list

                    # Set the object's group from the idd file
                    # print('group test: {}'.format(self.idd[obj_class]._group))
                    # print('Checking for idf object group for class: {}'.format(obj_class))
                    # print('idd keys: {}'.format(self.idd.keys()[:20]))
                    group = self.idd[obj_class]._group

                    # TODO validate IDF against IDD
                    # If this is an IDF file, perform checks against IDD
                    # file here (mandatory fields, unique objects, etc)

                    # Save the new object to the IDF file (canNOT use setdefault)
                    # due to apparent incompatibility with ZODB
                    if obj_class in self.idd:
                        try:
                            self.idf[obj_class].append(idf_object)
                        except (AttributeError, KeyError) as e:
                            self.idf[obj_class] = [idf_object]

                    # Reset lists for next object
                    field_list = list()
                    comment_list = list()
                    comment_list_special = list()
                    end_object = False
                    idf_object = datamodel.IDFObject(self.idf)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # yield the current progress for progress bars
                yield total_read

        # Save changes
        transaction.get().note('Load file')
        transaction.commit()
        print('Parsing IDF complete!')
        # print(self.idf.keys())

## Parse this idd file
#idd_file = 'Energy+.idd'
#idf_file = 'RefBldgLargeOfficeNew2004_Chicago.idf'
#idf_file2 = '5ZoneBoilerOutsideAirReset.idf'
#idf_file3 = 'ChicagoSM.idf'
#object_count, eol_char, options, groups, objects = parse_idd(idf_file2)
##writeIDF('testoutput.idf', options, objects)
#import json
#encoded = json.dumps(objects)
#obj = json.loads(encoded)
