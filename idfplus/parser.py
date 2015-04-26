#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
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
import os
# import shelve
# import datetime as dt
# import transaction
import codecs
# from persistent.list import PersistentList
import networkx as nx
import math
import cPickle as pickle

# Package imports
from . import datamodel
from . import logger
from .datamodel import IDDError

# Constants
from . import config

OPTIONS_LIST = ['OriginalOrderTop', 'UseSpecialFormat',
                'ViewInIPunits', 'SortedOrder', 'HideEmptyClasses']
COMMENT_DELIMITER_GENERAL = '!'
COMMENT_DELIMITER_SPECIAL = '!-'
TAG_LIST = ['\\field', '\\Field,'
            '\\note', '\\Note',
            '\\required-field', '\\Required-field',
            '\\units', '\\Units',
            '\\ip-units', '\\Ip-units',
            '\\unitsBasedOnField', '\\UnitsBasedOnField',
            '\\minimum>', '\\Minimum>',
            '\\minimum', '\\Minimum',
            '\\maximum<', '\\Maximum<',
            '\\maximum', '\\Maximum',
            '\\default', '\\Default',
            '\\deprecated', '\\Deprecated',
            '\\autosizeable', '\\Autosizeable',
            '\\autocalculatable', '\\Autocalculatable',
            '\\type', '\\Type',
            '\\retaincase', '\\Retaincase',
            '\\key', '\\Key',
            '\\object-list', '\\Object-list',
            '\\reference', '\\Reference',
            '\\memo', '\\Memo',
            '\\unique-object', '\\Unique-object',
            '\\required-object', '\\Required-object',
            '\\min-fields', '\\Min-fields',
            '\\obsolete', '\\Obsolete',
            '\\extensible:', '\\Extensible:',
            '\\begin-extensible', '\\Begin-extensible',
            '\\format', '\\Format',
            '\\group', '\\Group']

# Setup logging
log = logger.setup_logging(config.LOG_LEVEL, __name__, config.LOG_PATH)

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

class InvalidIDFObject(Exception):
    """Exception called when an invalid/unknown idf object is encountered."""
    def __init__(self, message):
        self.message = message


class Writer(object):
    """Class to take care of writing idf and idd files."""

    def __init__(self):
        super(Writer, self).__init__()

    @staticmethod
    def write_idf(idf):
        """Write an IDF from the specified idfObject
        :param idf: :type IDFObject
        :param idd: :type IDDObject
        :param options: :type list: List of options
        """

        idd = idf._idd
        options = ' '.join(idf.options)
        print('writing options: {}'.format(idf.options))
        eol_char = os.linesep
        file_path = idf.file_path

        log.info('Saving file: {}'.format(file_path))

        # Check for special options
        use_special_format = False
        if 'UseSpecialFormat' in idf.options:
            use_special_format = True
            log.debug('Special formatting requested, but not yet implemented.')

        # Open file and write
        try:
            with codecs.open(file_path, 'w',
                             encoding=config.FILE_ENCODING,
                             errors='backslashreplace') as idf_file:

                idf_file.write("!-Generator IDFPlus {}{}".format(config.__version__,
                                                                 eol_char))
                idf_file.write("!-Option {}{}".format(options, eol_char))
                idf_file.write("!-NOTE: All comments with '!-' are ignored by the "
                               "IDFEditor and are generated "
                               "automatically.{}".format(eol_char))
                idf_file.write("!-      Use '!' comments if they need to be retained "
                               "when using the IDFEditor.{}".format(eol_char))

                for obj_class, obj_list in idf.iteritems():

                    for obj in obj_list:
                        # Write special comments if there are any
                        # if obj['comments_special'] is not None:
                        # for comment in obj.tags.get('comments_special', []):
                        #     file.write("!-{}{}".format(comment, eol_char))

                        # Write comments if there are any
                        for comment in obj.comments:

                            # Don't use '.format' here due to potential incorrect
                            # encodings introduced by user
                            idf_file.write("!" + comment.rstrip() + "{}".format(eol_char))

                        # Some objects are on one line and some fields are grouped!
                        # If enabled, check IDD file for special formatting instructions
                        if use_special_format:
                            pass

                        # Write the object name
                        idf_file.write("  {},{}".format(obj_class, eol_char))

                        # Write the fields
                        # if obj['fields']:
                        field_count = len(obj)
                        for i, field in enumerate(obj):

                            field_note = idd[obj_class][i].tags.get('field', None)
                            if field_note:
                                note = '  !- {}'.format(field_note)
                            else:
                                note = ''

                            if i == field_count - 1:
                                sep = ';'
                            else:
                                sep = ','

                            if field:
                                value = (field.value or '') + sep
                            else:
                                value = sep
                            line = "    {!s:23}{}{}".format(value, note, eol_char)
                            idf_file.write(line)

                        # Add newline at the end of the object
                        idf_file.write(eol_char)

            log.info('File written!')
            return True
        except IOError as e:
            log.debug('File not written! Exception!' + str(e.strerror))
            return False


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
        super(Parser, self).__init__(*args, **kwargs)

    @staticmethod
    def get_fields(line_in):
        """Strips all comments, etc and returns what's left
        :rtype : list:
        :param line_in:
        """
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
            tag_result = dict(tag=match[0].strip('\\').lower(),
                              value=value)

        # Return results
        return tag_result

    @staticmethod
    def get_options(line_in):
        """Parses a line and returns any options present.
        :rtype : list
        :param line_in:
        """
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

        # Call the parent class' init method
        super(IDDParser, self).__init__(*args, **kwargs)

        if idd is not None:
            log.debug('IDD received by parser - using it.')
            self.idd = idd
        else:
            log.debug('No IDD received by parser - using a blank one.')
            self.idd = datamodel.IDDFile()

    def parse_idd(self, file_path):
        """Parse the provided idd (or idf) file
        :rtype : generator
        :param file_path: 
        """

        #TODO write parser for unit conversion comments!
        total_size = os.path.getsize(file_path)
        total_read = 0.0
        idd = self.idd
        eol_char = os.linesep
        object_lists = self.idd.object_lists
        log.info('Parsing IDD file: {} ({} bytes)'.format(file_path, total_size))

        # Open the specified file in a safe way
        with codecs.open(file_path, 'r',
                         encoding=config.FILE_ENCODING,
                         errors='backslashreplace') as idd_file:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            tag_list = list()
            tag_dict = dict()
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

                # If previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Check for special options
                if line_parsed['options']:
                    idd.options.extend(line_parsed['options'])

                # If there are any comments save them
                if line_parsed['comments']:
                    comment_list.append(line_parsed['comments'].rstrip()
                                        + eol_char)

                    # Detect file version
                    if 'IDD_Version' in line_parsed['comments']:
                        version_raw = line_parsed['comments'].split()[1].strip()
                        version = '.'.join(version_raw.split('.')[0:2])
                        idd._version = version
                        log.debug('Found idd version in idd file: {}'.format(idd._version))

                # Check for special comments and options
                if line_parsed['comments_special']:
                    comment_list_special.append(line_parsed['comments_special'].rstrip()
                                                + eol_char)

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

                # If there are any field tags for this object save them
                if line_parsed['tags']:
                    tag = line_parsed['tags']['tag']
                    value = line_parsed['tags']['value']

                    # If there are tags, but no fields then these are object-level tags
                    if len(field_list) <= 1:
                        if tag in obj_tag_dict:
                            try:
                                obj_tag_dict[tag].append(value)
                            except AttributeError:
                                obj_tag_dict[tag] = [obj_tag_dict[tag], value]
                        else:
                            # Otherwise simply add it
                            obj_tag_dict[tag] = value
                    else:
                        # If this tag is already present, try to append its value
                        if tag in tag_dict:
                            try:
                                tag_dict[tag].append(value)
                            except AttributeError:
                                tag_dict[tag] = [tag_dict[tag], value]
                        else:
                            # Otherwise simply add it
                            tag_dict[tag] = value

                    # Check for the special group tag
                    if line_parsed['tags']['tag'] == 'group':
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
                            new_field.tags = tag_list[i]
                        except IndexError:
                            new_field.tags = dict()
                        tags = new_field.tags

                        # Check for reference tag to construct ref-lists
                        if 'reference' in tags:
                            if isinstance(tags['reference'], list):
                                for tag in tags['reference']:
                                    try:
                                        object_lists[tag].add(obj_class)
                                    except KeyError:
                                        object_lists[tag] = {obj_class}
                            else:
                                try:
                                    object_lists[tags['reference']].add(obj_class)
                                except KeyError:
                                    object_lists[tags['reference']] = {obj_class}

                        idd_object.append(new_field)

                    # Save the parsed variables in the idd_object
                    idd_object._obj_class = obj_class
                    idd_object._group = group
                    idd_object.comments_special = comment_list_special
                    idd_object.comments = comment_list
                    idd_object.tags = obj_tag_dict

                    # Strip white spaces and end of line chars from last comment
                    if idd_object.comments:
                        idd_object.comments[-1] = idd_object.comments[-1].rstrip()

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
                    obj_tag_dict = dict()
                    end_object = False
                    idd_object = datamodel.IDDObject(idd)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # Yield the current progress for progress bars
                yield math.ceil(100 * total_read / total_size)

            idd._conversions = conversions
            idd._groups = group_list
            idd._tree_model = None

        # Save changes
        file_name = config.IDD_FILE_NAME_ROOT.format(version)
        idd_path = os.path.join(config.DATA_DIR, file_name)
        with open(idd_path, 'wb') as fp:
            pickle.dump(idd, fp, 2)
        log.info('Parsing IDD complete!')

        # Yield the final progress for progress bars
        yield math.ceil(100 * total_read / total_size)

    @staticmethod
    def load_idd(version):
        """Loads an idd file into the object instance variable.
        Also sets some attributes of the file.
        :rtype : IDDFile
        :param version:
        :return: :raise IDDFileDoesNotExist:
        """

        # Create the full path to the idd file
        log.info("Loading IDD file...")
        file_name = config.IDD_FILE_NAME_ROOT.format(version)
        idd_path = os.path.join(config.DATA_DIR, file_name)
        log.debug('Checking for IDD version: {}'.format(version))
        log.debug(idd_path)

        # Check if the file name is a file and then open the idd file
        if os.path.isfile(idd_path):
            log.debug('IDD found, loading...')
            with open(idd_path, 'rb') as fp:
                idd = pickle.load(fp)
            try:
                log.debug('Testing loaded idd file for appropriate version/format...')
                message = "Test successful!"
                if idd.version is None:
                    message = "IDD file does not contain version information!"
                    log.debug(message)
                    raise IDDError(message, version)
                elif idd.parser_version != config.PARSER_VERSION:
                    message = "This IDD fle was processed by an old and/or " \
                              "incompatible version of IDFPlus' parser ({})! It must " \
                              "be reprocessed to be compatible with the current " \
                              "version ({}).".format(idd.parser_version, config.PARSER_VERSION)
                    log.debug(message)
                    raise IDDError(message, version)
                log.debug(message)
            except AttributeError:
                message = "Can't find required IDD file attribute (IDD Version or " \
                          "parser version)."
                log.debug(message)
                raise IDDError(message, version)
            else:
                return idd
        else:
            message = "Can't find IDD file: {}".format(idd_path)
            log.debug(message)
            raise IDDError(message, version)


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
        ref_graph = nx.DiGraph()
        self.idf._ref_graph = ref_graph
        self.idf.file_path = file_path
        total_size = os.path.getsize(file_path)
        total_read = 0
        eol_char = os.linesep
        # object_lists = self.idf.object_lists
        log.info('Parsing IDF file: {} ({} bytes)'.format(file_path, total_size))

        # Open the specified file in a safe way
        with codecs.open(file_path, 'r',
                         encoding=config.FILE_ENCODING,
                         errors='backslashreplace') as idf:

            # Prepare some variables to store the results
            field_list = list()
            comment_list = list()
            comment_list_special = list()
            group = None
            end_object = False
            idf_object = datamodel.IDFObject(self.idf)
            obj_index = 0
            prev_obj_class = None

            # Cycle through each line in the file (yes, use while!)
            while True:

                # Parse this line using readline (so last one is a blank)
                line = idf.readline()
                total_read += len(line)
                line_parsed = self.parse_line(line)

                # If previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Check for special options
                if line_parsed['options']:
                    self.idf.options.extend(line_parsed['options'])

                # If there are any comments save them
                if line_parsed['comments']:
                    comment_list.append(line_parsed['comments'].rstrip()
                                        + eol_char)

                # Check for special comments and options
                if line_parsed['comments_special']:
                    comment_list_special.append(line_parsed['comments_special'].rstrip()
                                                + eol_char)

                # If there are any fields save them
                if line_parsed['fields']:
                    field_list.extend(line_parsed['fields'])

                    # Detect idf file version and use it to select idd file
                    if field_list[0].lower() == 'version' and len(field_list) > 1:
                        version = field_list[1]
                        self.idf._version = version
                        log.debug('idf detected as version: {}'.format(version))
                        log.debug('Checking for idd...')
                        if not self.idd:
                            log.debug('No idd currently selected!')
                            idd_parser = IDDParser()
                            idd = idd_parser.load_idd(version)
                            self.idf._idd = idd
                            self.idd = idd

                            # Use the list of object classes from the idd to populate
                            # the idf file's object classes. This must be done early
                            # so that all objects added later are saved in the proper
                            # order.
                            self.idf.update((k, list()) for k, v in idd.iteritems())
                            self.idf.ref_lists.update((k, dict()) for k, v in self.idf._idd.object_lists.iteritems())
                            # print(self.idf.ref_lists)
                        log.debug('idd loaded as version: {}'.format(self.idd.version))

                # If this is the end of an object save it
                if end_object and empty_line:

                    # The first field is the object class name
                    obj_class = field_list.pop(0)

                    # Reset index if obj_class has changed
                    if obj_class != prev_obj_class:
                        obj_index = 0
                    prev_obj_class = obj_class

                    try:
                        idd_fields = self.idd[obj_class]
                    except KeyError as e:
                        if obj_class.lower() == 'version':
                            obj_class = 'Version'
                            idd_fields = self.idd[obj_class]
                            prev_obj_class = obj_class
                        else:
                            raise InvalidIDFObject('Invalid or unknown idf object: {}'.format(obj_class))

                    # Create IDFField objects for all fields
                    for i, field in enumerate(field_list):
                        if idd_fields:
                            key = idd_fields[i].key
                            tags = idd_fields[i].tags
                        else:
                            key = obj_class
                            tags = dict()
                        new_field = datamodel.IDFField(idf_object)
                        new_field.key = key
                        new_field.value = field
                        new_field.tags = tags

                        # Check if field should be a reference. Ignore 'node' and
                        # 'external-list' for now because they are a whole other issue!
                        tag_set = set(tags)
                        ref_set = {'object-list', 'reference'}
                        if (tag_set & ref_set) and field:

                            # Add the node to the graph
                            ref_graph.add_node(new_field._uuid, data=new_field)

                            try:
                                # Ensure we have a list of object classes
                                obj_list_names = tags['reference']
                                if not isinstance(obj_list_names, list):
                                    obj_list_names = [tags['reference']]

                                # Save the node in the idf file's reference list
                                for object_list in obj_list_names:
                                    id_tup = (new_field._uuid, new_field)
                                    val = new_field.value
                                    try:
                                        self.idf.ref_lists[object_list][val].append(id_tup)
                                    except (AttributeError, KeyError) as e:
                                        self.idf.ref_lists[object_list][val] = [id_tup]

                            except KeyError as e:
                                pass

                        # Add the field to the object
                        idf_object.append(new_field)

                    # Save the parsed variables in the idf_object
                    idf_object._obj_class = obj_class
                    idf_object._group = group
                    idf_object.comments_special = comment_list_special
                    idf_object.comments = comment_list

                    # Strip white spaces and end of line chars from last comment
                    if idf_object.comments:
                        idf_object.comments[-1] = idf_object.comments[-1].rstrip()

                    # Set the object's group from the idd file
                    group = self.idd[obj_class]._group

                    # TODO validate IDF against IDD
                    # If this is an IDF file, perform checks against IDD
                    # file here (mandatory fields, unique objects, etc)

                    # Save the new object to the IDF file (canNOT use setdefault)
                    # due to apparent incompatibility with ZODB
                    #TODO don't use ZODB anymore, use setdefault?
                    if obj_class in self.idd:

                        # Add the object
                        try:
                            self.idf[obj_class].append(idf_object)
                        except (AttributeError, KeyError) as e:
                            self.idf[obj_class] = [idf_object]
                        obj_index += 1

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
                yield math.ceil(100 * 0.5 * total_read / total_size)

        # Now that required nodes have been created, connect them as needed
        for progress in self.connect_references():
            yield progress

        log.info('Parsing IDF complete!')

    def connect_references(self):
        """Processes the reference graph to connect its nodes."""

        graph = self.idf._ref_graph
        node_count = graph.number_of_nodes()

        # Cycle through only nodes to avoid cycling through all objects
        for k, node in enumerate(graph.nodes_iter(data=True)):

            try:
                field = node[1]['data']
                object_list_name = field.tags['object-list']

                # Ensure we have a list to simplify later operations
                if not isinstance(object_list_name, list):
                    object_list_name = [field.tags['object-list']]

                # Cycle through all class names in the object lists
                for cls_list in object_list_name:
                    ref_node = self.idf.ref_lists[cls_list][field.value]
                    for ref_uuid, ref in ref_node:
                        graph.add_edge(field._uuid,
                                       ref_uuid,
                                       obj_list=object_list_name)
                    yield math.ceil(50 + (100 * 0.5 * (k+1) / node_count))

            except (IndexError, KeyError) as e:
                continue

            yield math.ceil(50 + (100 * 0.5 * (k+1) / node_count))
