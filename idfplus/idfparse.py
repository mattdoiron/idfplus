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
from __future__ import (print_function, division, with_statement, absolute_import)

# System imports
import os
import datetime as dt
import ZODB
import transaction

# Package imports
from . import idfmodel

# Constants
FIELD_TAGS = ['\\field',
             '\\note',
             '\\required-field',
             '\\begin-extensible',
             '\\units',
             '\\ip-units',
             '\\unitsBasedOnField',
             '\\minimum',
             '\\minimum>',
             '\\maximum',
             '\\maximum<',
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

OPTIONS_LIST = ['OriginalOrderTop', 'UseSpecialFormat']

# field_tag_delimiter = '\\'
COMMENT_DELIMITER_GENERAL = '!'
COMMENT_DELIMITER_SPECIAL = '!-'

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
    def write_idf(idf, idd, options):
        """Write an IDF from the specified idfObject
        :param idf: :type IDFObject
        :param idd: :type IDDObject
        :param options: :type list: List of options
        """

        print('Writing file: ' + idf.file_path + '_test')

        # Check for special options
        use_special_format = False
        if 'UseSpecialFormat' in options:
            use_special_format = True
            print('Special formatting requested, but not yet implemented.')

        # Open file and write
        try:
            with open(idf.file_path + '_test', 'w') as file:
                for obj_class, obj_list in idf.iteritems():

                    for obj in obj_list:
                        # Write special comments if there are any
                        if obj['comments_special'] is not None:
                            for comment in obj['comments_special']:
                                file.write("!-{}\n".format(comment))

                        # Write comments if there are any
                        if obj['comments'] is not None:
                            for comment in obj['comments']:
                                file.write("!{}\n".format(comment))

                        # Some objects are on one line and some fields are grouped!
                        # If enabled, check IDD file for special formatting instructions
                        if use_special_format:
                            pass

                        # Write the object name
                        file.write("  {},\n".format(obj_class))

                        # Write the fields
                        if obj['fields']:
                            field_count = len(obj['fields'])
                            for i, field in enumerate(obj['fields']):
                                if i == field_count - 1:
                                    file.write("    {};\n".format(field))
                                else:
                                    file.write("    {},\n".format(field))

                        # Add newline at the end of the object
                        file.write("\n")

            print('File written!')
            return True
        except IOError as e:
            print('File not written! Exception!' + str(e.strerror))
            return False

    @staticmethod
    def write_idd(idd, options):
        """Write an IDD from the specified iddObject
        :param idd:
        :param options:
        """

        print('Writing file: ' + idd.file_path)

        # how will this be written? shelve? ZODB?
        # probably just shelve...


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

        global FIELD_TAGS
        tag_result = dict()

        # Create a list containing any tags found in line_in
        match = [x for x in FIELD_TAGS if x in line_in]

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
            tag_result = dict(tag=match[0],
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
                    field_tags=tags,
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
            self.idd = idfmodel.IDDFile()

        # Call the parent class' init method
        super(IDDParser, self).__init__(*args, **kwargs)

    def parse_idd(self, file_path):
        """Parse the provided idd (or idf) file
        :rtype : generator
        :param file_path: 
        """
        #TODO write parser for unit conversion comments!
        #TODO rename to load_idd?

        global COMMENT_DELIMITER_SPECIAL  # Avoid these...

        total_size = os.path.getsize(file_path)
        total_read = 0.0

        print('Parsing IDD file: {} ({} bytes)'.format(file_path, total_size))

        # Open the specified file in a safe way
        with open(file_path, 'r') as idd_file:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            field_tag_list = list()
            field_tag_dict = dict()
            options = list()
            group = None
            group_list = list()
            conversions = list()
            end_object = False
            version = None
            idd_object = idfmodel.IDDObject(self.idd)

            # Cycle through each line in the file (yes, use while!)
            while True:

                # Parse this line using readline (so last one is a blank)
                line = idd_file.readline()
                total_read += len(line)
                line_parsed = self.parse_line(line)

                # Detect end of line character for use when re-writing file
                if line.endswith('\r\n'):
                    self.idd._eol_char = '\r\n'
                else:
                    self.idd._eol_char = '\n'

                # If previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Check for special options
                if line_parsed['options']:
                    self.idd.options.extend(line_parsed['options'])

                # If there are any comments save them
                if line_parsed['comments']:
                    comment_list.append(line_parsed['comments'])

                    # Detect file version
                    if 'IDD_Version' in line_parsed['comments']:
                        version_raw = line_parsed['comments'].split()[1].strip()
                        version = '.'.join(version_raw.split('.')[0:2])
                        self.idd._version = version

                # Check for special comments and options
                if line_parsed['comments_special']:
                    comment_list_special.append(line_parsed['comments_special'])

                # If there are any fields save them
                if line_parsed['fields']:
                    field_list.extend(line_parsed['fields'])

                # Check for the end of an object before checking for new tags
                if (end_object and empty_line) or line_parsed['fields']:
                    if field_tag_dict:
                        field_tag_list.append(field_tag_dict.copy())
                        field_tag_dict = dict()

                # If there are any field tags for this object save them
                if line_parsed['field_tags']:
                    tag = line_parsed['field_tags']['tag']
                    value = line_parsed['field_tags']['value']

                    # If this tag is already present, try to append its value
                    if tag in field_tag_dict:
                        try:
                            field_tag_dict[tag].append(value)
                        except AttributeError:
                            field_tag_dict[tag] = [field_tag_dict[tag], value]

                    # Check for the special group tag
                    if line_parsed['field_tags']['tag'] == '\\group':
                        group = line_parsed['field_tags']['value']
                        if group not in group_list:
                            group_list.append(group)

                # If this is the end of an object then save it
                if end_object and empty_line:

                    # The first field is the object class name
                    obj_class = field_list.pop(0)

                    # Create IDDField objects for all fields
                    for i, field in enumerate(field_list):
                        new_field = idfmodel.IDDField(idd_object)
                        new_field.key = field
                        new_field.value = None
                        try:
                            new_field.tags = field_tag_list[i]
                        except IndexError:
                            new_field.tags = dict()
                        idd_object.update({field:new_field})

                    # Save the parsed variables in the idd_object
                    idd_object._obj_class = obj_class
                    idd_object._group = group
                    idd_object.comments_special = comment_list_special
                    idd_object.comments = comment_list

                    # Add the group to the idd's list if it isn't already there
                    if group not in self.idd._groups:
                        self.idd._groups.append(group)

                    # Save the new object as part of the IDD file
                    self.idd._classes[obj_class] = idd_object

                    # Reset variables for next object
                    field_list = list()
                    comment_list = list()
                    comment_list_special = list()
                    field_tag_list = list()
                    field_tag_dict = dict()
                    end_object = False
                    idd_object = idfmodel.IDDObject(self.idd)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # Yield the current progress for progress bars
                yield total_read

            self.idd._conversions = conversions
            self.idd._groups = group_list
            self.idd._tree_model = None

        print('Parsing IDD complete!')

    #        return True

def save_idd(idd):
    """Shelves a copy of the IDD file object.
    :raises : Exception
    :rtype : bool
    """
    print('saving idd')
    print('received idd with keys: {}'.format(len(idd._classes.keys())))
    if not idd.version:
        raise Exception("Missing IDD file version")

    # sys.setrecursionlimit(50000)
    version = idd.version
    data_dir = 'data'
    file_name_root = 'EnergyPlus_IDD_v{}.dat'
    file_name = file_name_root.format(version)
    idd_path = os.path.join(idfmodel.APP_ROOT, data_dir, file_name)

    # storage = ZODB.FileStorage.FileStorage(idd_path)
    print('opening idd dat file: {}'.format(idd_path))
    db = ZODB.DB(idd_path)
    # connection = db.open()
    root = db.open().root

    print('saving idd to root obj: {}'.format(type(idd)))
    # database = shelve.open(idd_path)
    # print('idd data type is: {}'.format(idd))
    # database['idd'] = idd._classes
    # database['date_generated'] = dt.datetime.now()
    # database.close()

    root.idd = idd
    root.date_generated = dt.datetime.now()
    print('committing transaction')
    transaction.commit()
    db.close()
    return True


#---------------------------------------------------------------------------
class IDFParser(Parser):
    """IDF file parser that handles opening, parsing and returning."""

    def __init__(self, idf=None, *args, **kwargs):
        """Initializes the IDFParser class with an option idf file.
        :param idf:
        :param args:
        :param kwargs:
        """

        if idf is not None:
            self.idf = idf
        else:
            self.idf = idfmodel.IDFFile()

        # Call the parent class' init method
        super(IDFParser, self).__init__(*args, **kwargs)

    def parse_idf(self):  # rename to loadIDF?
        """Parse the provided idf file and return an IDFObject.
        :rtype : iterator
        """

        global OPTIONS_LIST  # Avoid these?

        file_path = self.idf.file_path  # TODO this will be None if blank idf used!
        total_size = os.path.getsize(file_path)
        total_read = 0.0

        print('Parsing IDF file: {} ({} bytes)'.format(file_path, total_size))

        # Open the specified file in a safe way
        with open(file_path, 'r') as idf:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            group = None
            end_object = False
            idf_object = idfmodel.IDFObject(self.idf)

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
                        print('idf version detected as: {}'.format(version))
                        print('checking for idd')
                        if not self.idf._idd:
                            print('no idd found')
                            self.idf._idd = self.idf.load_idd()
                        print('idd loaded as version: {}'.format(self.idf._idd.version))

                # If this is the end of an object save it
                if end_object and empty_line:

                    # The first field is the object name
                    obj_class = field_list.pop(0)

                    # Create IDFField objects for all fields
                    for i, field in enumerate(field_list):
                        idd_fields = self.idf._idd._classes[obj_class].items()
                        new_field = idfmodel.IDFField(idf_object)
                        new_field.key = idd_fields[i].key
                        new_field.value = field
                        new_field.tags = idd_fields[i].tags
                        idf_object.update({field:new_field})

                    # Save the parsed variables in the idf_object
                    idf_object._obj_class = obj_class
                    idf_object._group = group
                    idf_object.comments_special = comment_list_special
                    idf_object.comments = comment_list

                    # Set the object's group from the idd file
                    group = self.idf._idd._classes[obj_class].group

                    # If this is an IDF file, perform checks against IDD
                    # file here (mandatory fields, unique objects, etc)

                    # Save the new object to the IDF file (canNOT use setdefault)
                    if obj_class in self.idf._classes:
                        try:
                            self.idf._classes[obj_class].append(idf_object)
                        except AttributeError:
                            self.idf._classes[obj_class] = [idf_object]

                    # Reset lists for next object
                    field_list = list()
                    comment_list = list()
                    comment_list_special = list()
                    end_object = False
                    idf_object = idfmodel.IDFObject(self.idf)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # yield the current progress for progress bars
                yield total_read

        print('Parsing IDF complete!')

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
