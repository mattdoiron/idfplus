#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This submodule reads/parses IDD and IDF files as well as writes IDF files.

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
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

OPTIONS_LIST = ['OriginalOrderTop', 'UseSpecialFormat', 'HideGroups',
                'ViewInIPunits', 'SortedOrder', 'HideEmptyClasses']
COMMENT_DELIMITER_GENERAL = '!'
COMMENT_DELIMITER_SPECIAL = '!-'
OBJECT_END_DELIMITER = ';'
TAG_LIST = ['\\field',
            '\\note',
            '\\required-field',
            '\\units',
            '\\ip-units',
            '\\unitsbasedonfield',
            '\\minimum>',
            '\\minimum',
            '\\maximum<',
            '\\maximum',
            '\\default',
            '\\deprecated',
            '\\autosizable',
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


class InvalidIDFObject(Exception):
    """Exception called when an invalid/unknown idf object is encountered.
    """

    def __init__(self, message):
        """Exception indicating an invalid IDF object

        :param str message: Message to go along with exception
        """

        self.message = message


class Writer(object):
    """Class to take care of writing IDF files.
    """

    @staticmethod
    def write_idf(idf):
        """Write an IDF from the specified idfObject

        :param IDFObject idf: IDFObject to write
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
                        idf_file.write("  {},{}".format(obj.obj_class_display, eol_char))

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

    @staticmethod
    def fields(line_in):
        """Strips all comments, etc and returns what's left

        :param str line_in: Raw string input (line from IDF file)
        :returns: List of strings representing IDF fields
        :rtype: list
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

        :param str line_in: Raw string input (line from IDF file)
        :returns: General comments from the given line
        :rtype: str
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

        :param str line_in: Raw string input (line from IDF file)
        :returns: String containing special comments from given line
        :rtype: str
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

        :param str line_in: Raw string input (line from IDF file)
        :returns: A dictionary of tags. Keys are tag names, values are tag values.
        :rtype: dict
        """

        tag_result = dict()

        # Don't process comment lines
        line_clean = line_in.expandtabs().lstrip()
        if line_clean.startswith(COMMENT_DELIMITER_GENERAL):
            return tag_result

        # Create a list containing any tags found in line_in
        match = [x for x in TAG_LIST if x in line_in.lower()]

        # If there are any matches, save the first one
        if match:

            # Partition the line at the match
            part = line_in.strip().partition(match[0])

            # If there is a value save it, otherwise it's a boolean so set True
            if part[-1]:
                value = part[-1].lstrip()
            else:
                value = True

            # Save results
            tag_result = dict(tag=match[0].strip('\\'), value=value)

        # Return results
        return tag_result

    @staticmethod
    def options(line_in):
        """Parses a line and returns any options present.

        :param str line_in: Raw string input (line from IDF file)
        :returns: A list of strings representing IDF file options found on the given line
        :rtype: list
        """

        line_clean = line_in.expandtabs().lstrip().lower()
        matches = list()

        if line_clean.startswith('!-option'):
            matches = [x.lower() for x in OPTIONS_LIST if x in line_clean]

        # Return matches
        return matches

    def parse_line(self, line_in):
        """Parses a line from the IDD/IDF file and returns results

        :param str line_in: Raw string input (line from IDF file)
        :returns: A dictionary containing all of the fields, comments, options and tags from the
                  given line
        :rtype: dict
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

    :param IDDFile idd: IDD file to populate while parsing
    """

    __parser_version__ = '0.1.2'

    def __init__(self, idd=None):
        """Initialize the parser

        :param IDDFile idd: IDD file to populate during parsing
        """

        # Call the parent class' init method
        super(IDDParser, self).__init__()

        if idd is not None:
            log.debug('IDD received by parser - using it.')
            self.idd = idd
        else:
            log.debug('No IDD received by parser - using a blank one.')
            log.debug('Parser version being set to: {}'.format(self.__parser_version__))
            self.idd = iddmodel.IDDFile(parser_version=self.__parser_version__)
            log.debug('Parser reports as being version: {}'.format(self.idd.parser_version))

    def parse_idd(self, file_path, write=True):
        """Parse the provided idd file

        :param bool write: Whether or not to write the resulting file to disk.
        :param str file_path: Absolute file path in which to look for IDD file to parse.
        :returns: Yields a progress counter between 0 and 100
        :rtype: generator
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
                            if isinstance(tag_dict[tag], list):
                                if value not in tag_dict[tag]:
                                    tag_dict[tag].append(value)
                            else:
                                if value != tag_dict[tag]:
                                    tag_dict[tag] = [tag_dict[tag], value]
                        else:
                            # Otherwise simply assign it
                            tag_dict[tag] = value

                    # Check for the special group tag
                    if line_parsed['tags']['tag'] == 'group':
                        group = line_parsed['tags']['value']
                        if group not in group_list:
                            group_list.append(group)

                # If this is the end of an object then save it
                if end_object and empty_line:

                    # The first field is the object class name
                    obj_class_display = field_list.pop(0)
                    obj_class = obj_class_display.lower()

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

                        # Check for extensible objects
                        if 'extensible:' in obj_tag_dict:
                            set_length = int(obj_tag_dict['extensible:'][0])
                            idd_object._extensible = set_length

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
                    idd_object._obj_class_display = obj_class_display
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
                    if obj_class not in ['lead input', 'simulation data']:
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
        if write:
            self.write_idd(idd)

        # Yield the final progress for progress bars
        log.info('Parsing IDD complete!')
        yield math.ceil(100.0 * total_read / total_size)

    @staticmethod
    def write_idd(idd):
        """Writes the specified IDD file to disk

        :param IDDFile idd:
        """

        file_name = config.IDD_FILE_NAME_ROOT.format(idd.version)
        idd_path = os.path.join(config.DATA_DIR, file_name)
        with open(idd_path, 'wb') as fp:
            pickle.dump(idd, fp, 2)

    def load_idd(self, version):
        """Loads an idd file into the object instance variable.

        Also sets some attributes of the file.

        :param str version:
        :raise IDDError:
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

    def __init__(self, idf=None, idd=None, default_version=None):
        """Initializes the IDFParser class with an option idf file.

        :param IDFFile idf: IDF file to be populated by the parser
        :param IDDFile idd: IDD file to use while parsing
        :param str default_version: Default version of the IDD file to use
        """

        # Set idf if it's given. Use either one supplied on init or a blank one
        if idf is not None and isinstance(idf, idfmodel.IDFFile):
            self.idf = idf
        else:
            self.idf = idfmodel.IDFFile()

        # Set the idd if it's given
        if idd is not None and isinstance(idd, iddmodel.IDDFile):
            self.idd = idd
        else:
            self.idd = self.idf.idd

        self.default_version = default_version

        # Call the parent class' init method
        super(IDFParser, self).__init__()

    def parse_idf(self, raw_idf, file_path=None):
        """Parse the provided idf file and populate an IDFFile object with objects.

        :param raw_idf: File-like object containing idf to parse
        :param str file_path: option file path to use to fetch an idf to parse
        :returns: Yields a progress counter between 0 and 100
        :rtype: generator
        """

        self.idf.file_path = file_path
        if file_path:
            total_size = os.path.getsize(file_path)
        else:
            total_size = len(raw_idf.getvalue())
        total_read = 0.0
        log.info('Parsing IDF: {} ({} bytes)'.format(file_path or 'pasted text', total_size))

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
                if comment_cleaned.lower().startswith('-option'):
                    options = [x for x in OPTIONS_LIST if x in comment_cleaned]
                    self.idf.options.extend(options)
                else:
                    comment_list_special.append(comment_cleaned)
            elif sep:
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
            obj_class = fields.pop(0).lower()

            # Detect idf file version and use it to select idd file
            if obj_class == 'version':
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

            try:
                # Create IDFField objects for all fields and add them to the IDFObject
                for index, value in enumerate(fields):
                    new_field = create_field(idf_object, value, index=index)
                    append_idf_object(new_field)

                    # Store the field in a list to be passed to SQL later
                    if file_path is not None:
                        append_new_field((new_field.uuid,
                                          obj_class,
                                          new_field.obj_class_display,
                                          new_field.ref_type,
                                          value))
            except IDDError:
                self.assign_idd()

            # Save the new object to the IDF
            self.idf.add_objects(obj_class, idf_object, update=False)

            # Reset variables for next object
            fields = StringIO()
            comment_list = list()
            comment_list_special = list()

            # Yield the current progress for progress bars
            yield math.ceil(100.0 * total_read / total_size)

        # Be sure we're finished at this point (bytes read is not always accurate!)
        yield 100.0

        # Execute the SQL to insert the new objects
        if file_path is not None:
            insert_operation = "INSERT INTO idf_objects VALUES (?,?,?,?,?)"
            self.idf.db.executemany(insert_operation, field_objects)
            self.idf.db.commit()

        log.info('Parsing IDF complete!')

    def assign_idd(self, _version=None):
        """Verifies that an idd of the correct version is available

        :param str _version:
        """

        if self.idd:
            return

        # Detect appropriate version
        if _version:
            log.debug('IDF version detected: {}'.format(_version))
            version = _version
        else:
            log.debug('Using default IDF version: {}'.format(self.default_version))
            version = self.default_version

        # Attempt to load the idd file
        try:
            idd_parser = IDDParser()
            idd = idd_parser.load_idd(version)
        except IDDError as e:
            raise IDDError(e.message, e.version)
        self.idf.set_idd(idd)
        self.idd = idd
        log.debug("IDD version loaded: {}".format(self.idd.version))
