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

# System imports
import os
import codecs
import math
import logging
import cPickle as pickle
from cStringIO import StringIO

# Package imports
from . import idfmodel
from . import iddmodel
from . import config
from . import __version__
from .iddmodel import IDDError

# Setup logging
log = logging.getLogger(__name__)

OPTIONS_LIST = ['OriginalOrderTop', 'UseSpecialFormat',
                'ViewInIPunits', 'SortedOrder', 'HideEmptyClasses']
COMMENT_DELIMITER_GENERAL = '!'
COMMENT_DELIMITER_SPECIAL = '!-'
OBJECT_END_DELIMITER = ';'
TAG_LIST = ['\\field', '\\Field',
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


class InvalidIDFObject(Exception):
    """Exception called when an invalid/unknown idf object is encountered.
    """

    def __init__(self, message):
        self.message = message


class Writer(object):
    """Class to take care of writing idf and idd files.
    """

    def __init__(self):
        super(Writer, self).__init__()

    @staticmethod
    def write_idf(idf):
        """Write an IDF from the specified idfObject

        :param idf: IDFObject to write
        :type idf: IDFObject
        """

        idd = idf._idd
        options = ' '.join(idf.options)
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

                idf_file.write("!-Generator IDF+ v{}{}".format(__version__, eol_char))
                idf_file.write("!-Option {}{}".format(options, eol_char))
                idf_file.write("!-NOTE: All comments with '!-' are ignored by the "
                               "IDFEditor and are generated "
                               "automatically.{}".format(eol_char))
                idf_file.write("!-      Use '!' comments if they need to be retained "
                               "when using the IDFEditor.{}".format(eol_char))

                if 'OriginalOrderTop' in idf.options or 'OriginalOrderBottom' in idf.options:
                    idf_items = idf.iteritems()
                else:
                    idf_items = idf.iteritems()  # idf.iter_ordered() (not implemented)

                for obj_class, obj_list in idf_items:

                    for obj in obj_list:
                        # Write special comments if there are any
                        # if obj['comments_special'] is not None:
                        # for comment in obj.tags.get('comments_special', []):
                        #     file.write("!-{}{}".format(comment, eol_char))

                        # Write comments if there are any
                        for comment in obj.comments:

                            # Don't use '.format' here due to potential incorrect
                            # encodings introduced by user
                            idf_file.write("!"+comment.rstrip()+"{}".format(eol_char))

                        # Some objects are on one line and some fields are grouped!
                        # If enabled, check IDD file for special formatting instructions
                        if use_special_format:
                            pass

                        # Write the object name
                        idf_file.write("  {},{}".format(obj_class, eol_char))

                        # Write the fields
                        field_count = len(obj)
                        for i, field in enumerate(obj):
                            idd_field = idd.field(obj_class, i)
                            _units = idd_field.units or ''
                            units = _units if not _units.startswith('BasedOnField') else None
                            units_note = ' {{{}}}'.format(units) if units else ''
                            field_note = idd_field.tags.get('field', None)
                            if field_note:
                                note = '  !- {}{}'.format(field_note, units_note)
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


class Parser(object):
    """Base class for more specialized parsers
    """

    def __init__(self):
        super(Parser, self).__init__()

    @staticmethod
    def fields(line_in):
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
    def comments_general(line_in):
        """Parses a string and returns the general comment if it exists

        :param line_in:
        :rtype str:
        """

        comments = None

        if line_in.find(COMMENT_DELIMITER_GENERAL) == -1:
            # No comments found at all
            comments = None

        elif line_in.find(COMMENT_DELIMITER_SPECIAL) == -1:
            # No special comment found so parse simply
            part = line_in.partition(COMMENT_DELIMITER_GENERAL)
            comments = part[-1].expandtabs()

        elif line_in.find(COMMENT_DELIMITER_SPECIAL) != -1 and \
             line_in.count(COMMENT_DELIMITER_GENERAL) == 1:
            # Special comment found, but no general comment
            comments = None

        else:
            # Both types of comments may be present so parse in more detail
            part_a = line_in.partition(COMMENT_DELIMITER_SPECIAL)

            if part_a[0].find(COMMENT_DELIMITER_GENERAL) != -1:
                # General comment precedes special comment, repartition
                part_b = line_in.partition(COMMENT_DELIMITER_GENERAL)
                comments = part_b[-1].expandtabs()

            elif part_a[-1].find(COMMENT_DELIMITER_GENERAL) != -1:
                # General comment is in the last item (part of special comment)
                comments = None

        # Return comments
        return comments

    @staticmethod
    def comments_special(line_in):
        """Parses a line and returns any special comments present.

        :rtype str:
        :param line_in:
        """

        line_clean = line_in.expandtabs().lstrip()
        comment_list_special = str()

        if line_clean.startswith(COMMENT_DELIMITER_SPECIAL):
            comment_list_special = line_clean.lstrip(COMMENT_DELIMITER_SPECIAL)

        # Return comments
        return comment_list_special

    @staticmethod
    def tags(line_in):
        """Parses a line and gets any fields tags present

        :rtype : dict:
        :param line_in:
        """

        tag_result = dict()

        # Create a list containing any tags found in line_in
        match = [x for x in TAG_LIST if x in line_in]

        # Hack for note field. Why is this needed!?
        if '\\note' in line_in:
            match.append('\\note')

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
    def options(line_in):
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
        fields = self.fields(line_in)
        comments = self.comments_general(line_in)
        comments_special = self.comments_special(line_in)
        options = self.options(line_in)
        tags = self.tags(line_in)
        end_object = False
        empty_line = False

        # Check for an empty line
        if not (fields or tags or options):
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
    """

    __parser_version__ = '0.1.0'

    def __init__(self, idd=None):
        """Initialize the parser

        :type idd: IDDFile
        :param idd:
        """

        # Call the parent class' init method
        super(IDDParser, self).__init__()

        if idd is not None:
            log.debug('IDD received by parser - using it.')
            self.idd = idd
        else:
            log.debug('No IDD received by parser - using a blank one.')
            self.idd = iddmodel.IDDFile(parser_version=self.__parser_version__)

    def parse_idd(self, file_path):
        """Parse the provided idd (or idf) file

        :rtype : generator
        :param file_path: 
        """

        # TODO write parser for unit conversion comments!
        total_size = os.path.getsize(file_path)
        total_read = 0.0
        self.idd.file_path = file_path
        idd = self.idd
        eol_char = os.linesep
        object_lists = self.idd.object_lists
        log.info('Parsing IDD file: {} ({} bytes)'.format(file_path,
                                                          total_size))

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
            ordered_fields = list()
            version = None
            group = None
            group_list = list()
            conversions = list()
            end_object = False
            object_list_length = 0
            idd_object = iddmodel.IDDObject(idd)

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
                    comment_list.append(line_parsed['comments'].rstrip() + eol_char)

                    # Detect file version
                    if 'IDD_Version' in line_parsed['comments']:
                        version_raw = line_parsed['comments'].split()[1].strip()
                        version = '.'.join(version_raw.split('.')[0:2])
                        idd._version = version
                        log.debug('Found idd version in idd file: {}'.format(version))

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
                    for i, field_key in enumerate(field_list):
                        new_field = iddmodel.IDDField(idd_object, field_key)
                        new_field.value = None
                        ordered_fields.append(field_key)
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
                                    object_list_length += 1
                            else:
                                try:
                                    object_lists[tags['reference']].add(obj_class)
                                except KeyError:
                                    object_lists[tags['reference']] = {obj_class}
                                object_list_length += 1

                        idd_object[field_key] = new_field

                    # Save the parsed variables in the idd_object
                    idd_object._obj_class = obj_class
                    idd_object._group = group
                    idd_object._ordered_fields = ordered_fields
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
                    ordered_fields = list()
                    end_object = False
                    idd_object = iddmodel.IDDObject(idd)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

                # Yield the current progress for progress bars
                yield math.ceil(100 * total_read / total_size)

            idd._conversions = conversions
            idd._groups = group_list
            idd._tree_model = None
            idd._object_list_length = object_list_length

        # Save changes
        file_name = config.IDD_FILE_NAME_ROOT.format(version)
        idd_path = os.path.join(config.DATA_DIR, file_name)
        with open(idd_path, 'wb') as fp:
            pickle.dump(idd, fp, 2)
        log.info('Parsing IDD complete!')

        # Yield the final progress for progress bars
        yield math.ceil(100.0 * total_read / total_size)

    def load_idd(self, version):
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
                log.debug('Testing loaded IDD file for appropriate '
                          'version/format...')
                message = "Test successful!"
                if idd.version is None:
                    message = "IDD file does not contain version information!"
                    log.debug(message)
                    raise IDDError(message, version)
                elif idd.parser_version != self.__parser_version__:
                    message = "This IDD fle was processed by an old " \
                              "and/or incompatible version of IDF+ " \
                              "parser ({})! It must be reprocessed to be " \
                              "compatible with the current version ({}).". \
                              format(idd.parser_version,
                                     self.__parser_version__)
                    log.debug(message)
                    raise IDDError(message, version)
                log.debug(message)
            except AttributeError:
                message = "Can't find required IDD file attribute " \
                          "(IDD Version or parser version)."
                log.debug(message)
                raise IDDError(message, version)
            else:
                return idd
        else:
            message = "Can't find IDD file: {}".format(idd_path)
            log.debug(message)
            raise IDDError(message, version)


class IDFParser(Parser):
    """IDF file parser that handles opening, parsing and returning.
    """

    def __init__(self, idf=None):
        """Initializes the IDFParser class with an option idf file.

        :param idf:
        """

        # Set idf if it's given
        if idf is not None:
            self.idf = idf
        else:
            self.idf = idfmodel.IDFFile()
        self.idd = self.idf.idd

        # Call the parent class' init method
        super(IDFParser, self).__init__()

    def parse_idf(self, file_path):
        """Parse the provided idf file and populate an IDFFile object with objects.

        :param file_path:
        :rtype : iterator
        """

        self.idf.file_path = file_path
        total_size = os.path.getsize(file_path)
        total_read = 0.0
        log.info('Parsing IDF file: {} ({} bytes)'.format(file_path,
                                                          total_size))

        # Open the specified file in a safe way
        with codecs.open(file_path, 'r',
                         encoding=config.FILE_ENCODING,
                         errors='backslashreplace') as raw_idf:

            # Prepare some variables to store the results
            fields = StringIO()
            field_objects = list()
            comment_list = list()
            comment_list_special = list()

            # Cycle through each line in the file (yes, use while!)
            while True:

                # Parse this line using readline (so last one is a blank)
                line = raw_idf.readline()
                total_read += len(line)

                # Split out any comments and save them
                part, sep, comment = line.partition(COMMENT_DELIMITER_GENERAL)
                comment_cleaned = comment.strip()
                if comment_cleaned.startswith('-'):
                    if comment_cleaned.lower().startswith('-options'):
                        self.idf.options.extend(self.options(comment_cleaned))
                    else:
                        comment_list_special.append(comment_cleaned)
                else:
                    comment_list.append(comment)

                # Write new fields to string containing previous fields
                fields.write(part)

                # Detect end of file and break. Do it this way to be sure
                # the last line can be identified as last AND still be processed!
                if not line:
                    break

                # Check for end of an object and skip rest of loop unless we find one
                if part.find(OBJECT_END_DELIMITER) == -1:
                    continue

                # ---- If we've gotten this far, we're at the end of an object ------

                # Clean up the fields and strip spaces, end of line chars
                fields = map(str.strip, fields.getvalue().split(','))
                fields[-1] = fields[-1].replace(OBJECT_END_DELIMITER, '')

                # The first field is the object class name
                obj_class = fields.pop(0)

                # Detect idf file version and use it to select idd file
                if obj_class.lower() == 'version':
                    self.assign_idd(fields[0])

                # Create a new IDF Object to contain the fields
                idf_object = idfmodel.IDFObject(self.idf, obj_class)

                # Save the comment variables to the idf_object
                idf_object.comments_special = comment_list_special
                idf_object.comments = comment_list

                # Strip white spaces, end of line chars from last comment
                if idf_object.comments:
                    last_comment = idf_object.comments[-1]
                    idf_object.comments[-1] = last_comment.rstrip()

                # Create local copies of some methods to speed lookups
                append_idf_object = idf_object.append
                create_field = idfmodel.IDFField
                append_new_field = field_objects.append

                # Create IDFField objects for all fields and add them to the IDFObject
                for index, value in enumerate(fields):
                    new_field = create_field(idf_object, value, index=index)
                    append_idf_object(new_field)

                    # Store the field in a list to be passed to SQL later
                    append_new_field((new_field.uuid,
                                      obj_class.lower(),
                                      new_field.ref_type,
                                      value))

                # Save the new object to the IDF
                self.idf.add_objects(obj_class, idf_object, update=False)

                # Reset variables for next object
                fields = StringIO()
                comment_list = list()
                comment_list_special = list()

                # Yield the current progress for progress bars
                yield math.ceil(100.0 * total_read / total_size)

        # Execute the SQL to insert the new objects
        insert_operation = "INSERT INTO idf_objects VALUES (?,?,?,?)"
        self.idf.db.executemany(insert_operation, field_objects)
        self.idf.db.commit()

        log.info('Parsing IDF complete!')

    def assign_idd(self, version):
        """Verifies that an idd of the correct version is available

        :param version:
        """

        log.debug('IDF version detected: {}'.format(version))
        log.debug('Checking for IDD...')
        if not self.idd:
            log.debug('No IDD currently selected!')
            idd_parser = IDDParser()
            try:
                idd = idd_parser.load_idd(version)
            except IDDError as e:
                raise IDDError(e.message, e.version)
            self.idf.set_idd(idd)
            self.idd = idd
        log.debug("IDD version loaded: {}".format(self.idd.version))
