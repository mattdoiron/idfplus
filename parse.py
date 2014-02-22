# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 20:17:03 2011

@author: matt
"""

import re
#from pysqlite2 import dbapi2 as sqlite

#import idd_schema as idd

# Define some global variables
idf_file = "RefBldgLargeOfficeNew2004_Chicago.idf"
#idd_file = "Energy+2.idd"
idd_file = "Energy+.idd"

DEBUG = False

"""
Proceedure:
    - Open idf file
    - start parsing until the Version number is found
    - Load the idd file for the appropriate version
    - continue parsing
    - uppon finding the start of an object, find the corresponding object in
        the idd file
    - continue parsing comparing each field that follows to each field in
        the idd file for that object
    - verify that the value and type of the input from the idf file matches
        the required type and raneg of values for that field from the idd file
    - If the field matches, save it in the database and continue.
    - If any mandatory fields or objects are missing, or if any data types
        are incorrect, raise an error and quit

"""

comment_delimiter_general = "!"
comment_delimiter_special = "!-"
object_delimiter = ";"
object_category_delimiter = ":"
field_delimiter = ","

def hasGeneralComment(str_in):
    global comment_delimiter_general
    test = str_in.partition(comment_delimiter_general)
    if test[0] == test:
        return True
    else:
        return False

def hasSpecialComment(str_in):
    global comment_delimiter_special
    test = str_in.partition(comment_delimiter_special)
    if test[0] == test:
        return True
    else:
        return False

def stripGeneralComment(str_in):
    global comment_delimiter_general
    test = str_in.partition(comment_delimiter_general)
    return test[0]

def stripSpecialComment(str_in):
    global comment_delimiter_special
    test = str_in.partition(comment_delimiter_special)
    return test[0]

def getGeneralComment(str_in):
    global comment_delimiter_general
    global comment_delimiter_special
    partA = str_in.partition(comment_delimiter_special)
    print partA
    partB = partA[-1].partition(comment_delimiter_special)
    print partB
    if partB[0] != partA[-1]:
        return partB[0].expandtabs().strip()
    else:
        return partB[-1].expandtabs().strip()

def getSpecialComment(str_in):
    global comment_delimiter_special
    test = str_in.partition(comment_delimiter_special)
    return test[-1]

def parse_IDF(file, objects):
    comment_count = 0
    comment_count_special = 0
    comment_count_field_special = 0
    comment_count_field_general = 0
    object_start_count = 0
    object_end_count = 0
    line_count = 0
    empty_line_count = 0
    field_count = 0
    parse_mode = "INITIAL"
    object_dict = []
    version = ''

    # Cycle through each line in the file, one at a time
    for line_in in file:

        # general prep
        obj_comments = []
        file_comments = []
        line_count += 1

        # get rid of tabs, then leading spaces
        line_clean = line_in.expandtabs().lstrip()

        # Check for empty lines
        if not line_clean:
            empty_line_count += 1

        # If we're currently looking for fields...
        if parse_mode == "INITIAL":

            # If line starts with !- then it's a special/field comment
            if line_clean.startswith('!-'):
                #ignore these lines
                comment_count_special += 1

            # If line starts with ! then it's a general comment
            elif line_clean.startswith('!'):
                # save this line as a global comment for the top of the file
                comment_count += 1
                file_comments.append(line_clean)

        # Otherwise, the line is useful so do some stuff
        else:

            # Partition line at the !- if it exists
            line_part1 = line_clean.partition('!-')
            if line_part1[0] == line_clean:
                # there is no '!-'
                pass
            else:
                # there is a '!-', count it
                comment_count_field_special += 1

            # Discard any !-comments or blank array items
            line_part1 = line_part1[0]

            # Partition line resulting from prev step at the ! if it exists
            line_part2 = line_part1.partition('!')
            if line_part2[0] == line_part1:
                # there is no '!'
                pass
            else:
                # there is a '!', count it and save it
                obj_comments.append(line_part2[0])
                comment_count_field_general += 1

            # Split the remaining part of the line at the commas, if any.
            line_split = line_part2[0].split(',')

            # Strip away any spaces or commas from each list item
            line_items = map(lambda i: i.strip().strip(','), line_split)

            # If we're currently looking for fields...
            if parse_mode == "FIELD":

                # Store the list of potential fields
                fields = line_list

                # Check for the end of an object
                if line_items[-1].endswith(';'):
                    # found a ;, remove it and count it
                    line_items[-1] = line_items[-1].strip(';')

                    field_count += len(line_items)
                    object_end_count += 1

                    # Start looking for objects again
                    parse_mode = "OBJECT"

            # If we're currently looking for the start of an object...
            elif parse_mode == "OBJECT":

                # Store the potential object name
                pot_obj = line_list[0]

                # Check for special object
                if pot_obj == 'Version':
                    # store the vesion number and stop here
                    version = line_list[1]
                    continue

                # Check for start of an object.
                if pot_obj.isalpha() or pot_obj.find(':') != -1:

                    # Check if the object name is valid
                    if not objects.has_key(pot_obj):
                        print "Object not found! ("+pot_obj+")"
                        return {}

                    # Found the start of an object, count it and save it
                    object_start_count += 1
                    object_dict.append(pot_obj)

                    # Start looking for fields
                    parse_mode = "FIELD"

    print "number of comment lines: " + str(comment_count)
    print "number of objects: " + str(object_count)
    print "number of objects 2: " + str(object_count_2)
    print "number of lines: " + str(line_count)
    print "number of empty lines: " + str(empty_line_count)

    return object_dict

# Parse the IDD file specified by the file handle 'file'
def parse_IDD(file):
    comment_count = 0
    object_count = 0
    object_count_2 = 0
    line_count = 0
    empty_line_count = 0
    parse_mode = "object"
    object_dict = {}
    version = ''
    current_object = ''
    current_field = ''
    field_comments = ['field', 'note', 'required-field', 'units', 'ip-units',
                       'unitsBasedOnField', 'minimum', 'minimum>', 'maximum',
                       'maximum<', 'default', 'deprecated', 'autosizable',
                       'autocalculatable', 'type', 'retaincase', 'key',
                       'object-list', 'reference', 'begin-extensible',
                       'Note', 'Units']
    object_comments = ['memo', 'unique-object', 'required-object', 'min-fields',
                       'obsolete', 'extensible', 'format']
    other_comments = ['group', 'Group']

    # Find the version number of this idd file
    version_line = file.readline(150)
    if not version_line.startswith('!IDD_Version'):
        print "This file does not appear to be a valid IDD file."
        return {}
    version = version_line.split(' ')[1]

    # Cycle through each line in the file, one at a time
    for line in file:

        # get rid of tabs, then leading/trailing spaces
        line = line.expandtabs().strip()

        # If line starts with ! then it's a comment
        if line.startswith('!'):
            comment_count += 1

        # Check for empty lines
        elif not line:
            empty_line_count += 1

        # Otherwise, it's useful so do some stuff
        else:

            # If the line starts with a \ then this is an object or field
            # comment and should be parsed accordingly
            if line.startswith('\\'):
                part = line.partition(' ')
                comment = part[0].strip().strip('\\')
                value = part[-1].strip()

                # Verify that the comment is valid
                if ( comment not in object_comments and
                     comment not in field_comments and
                     comment not in other_comments and
                     comment.find('extensible:') == -1):
                    if DEBUG: print 'Unknown object or field comment found on line '+str(line_count)+'! ('+comment+')'
                    return {}

                # Add the comment depending on which parse mode is active
                if parse_mode == "object_comment":
                    if object_dict[current_object]['comments'].has_key(comment):
                        object_dict[current_object]['comments'][comment].append(value)
                    else:
                        object_dict[current_object]['comments'][comment] = [value]
                    if DEBUG: print '  object comment ('+comment+') for object '+current_object
                elif parse_mode == "field_comment":
                    if object_dict[current_object]['fields'][current_field].has_key(comment):
                        object_dict[current_object]['fields'][current_field][comment].append(value)
                    else:
                        object_dict[current_object]['fields'][current_field][comment] = [value]
                    if DEBUG: print '  field comment ('+comment+') for field '+current_field
                continue

            # Split the line at the commas
            obj = line.split(',')

            # Regex for field name
            field_name = re.match(r'^[A|N][0-9]+', obj[0])

            # Check for start of an object. The first list item that is all
            # alphas or contains a : or ; denotes the start (and possibly
            # the end) of a new object

            # use a regex for this!
            if (obj[0].isalpha() or obj[0].find(':') != -1 or obj[0].find(';') != -1) and not field_name:
                object_count_2 += 1
                if DEBUG: print "START_OBJECT -----------------------------------------"
                if DEBUG: print obj
                parse_mode = "object_comment"
                obj_cleaned = obj[0].strip(';')
                current_object = obj_cleaned
                object_dict[obj_cleaned] = {'comments': {}, 'fields': {}}

            # Check for a valid field name
            if field_name:
                if DEBUG: print obj
                current_field = field_name.group(0)
                object_dict[current_object]['fields'][current_field] = {}
                end_comment = obj[-1].strip()
                if end_comment.startswith('\\'):
                    part = end_comment.partition(' ')
                    end_field = part[0].strip().strip('\\')
                    value = part[-1].strip()
                    if object_dict[current_object]['fields'][current_field].has_key(end_field):
                        object_dict[current_object]['fields'][current_field][end_field].append(value)
                    else:
                        object_dict[current_object]['fields'][current_field][end_field] = value
                    if DEBUG: print '  field comment ('+end_field+') for field '+current_field + ' (next to field name)'
                parse_mode = "field_comment"

            # If the last item has a ; then this signals the end of an object
            # so split it further to extract any comment for the last field.
            if obj[-1].find(';') != -1:
                new_obj = obj[-1].split(';')
                obj[-1] = new_obj[0]
                end_comment = new_obj[1].strip()
                obj.append(end_comment)
                if end_comment.startswith('\\'):
                    part = end_comment.partition(' ')
                    end_field = part[0].strip().strip('\\')
                    value = part[-1].strip()
                    if parse_mode == "field_comment":
                        if object_dict[current_object]['fields'][current_field].has_key(end_field):
                            object_dict[current_object]['fields'][current_field][end_field].append(value)
                        else:
                            object_dict[current_object]['fields'][current_field][end_field] = value
                        if DEBUG: print '  field comment ('+end_field+') for field '+current_field + ' (next to end of object)'
                    elif parse_mode == "object_comment":
                        if object_dict[current_object]['comments'].has_key(end_field):
                            object_dict[current_object]['comments'][end_field].append(value)
                        else:
                            object_dict[current_object]['comments'][end_field] = value
                        if DEBUG: print '  object comment ('+end_field+') for object '+current_object + ' (next to end of object comment)'
                object_count += 1

            # Strip white spaces from all array items
            for i, item in enumerate(obj):
                obj[i] = item.strip()

        # Count the line
        line_count += 1

    print "number of comment lines: " + str(comment_count)
    print "number of objects: " + str(object_count)
    print "number of objects 2: " + str(object_count_2)
    print "number of lines: " + str(line_count)
    print "number of empty lines: " + str(empty_line_count)
    print 'Version found: ' + version

    return object_dict

# Open the specified file (safely) and parse it
with open(idd_file, 'r') as file:
    objects = parse_IDD(file)

with open(idf_file, 'r') as file:
    model = parse_IDF(file, objects)


#with sqlite.connect('../CaliperTest.sqlite') as db:
#    cur = db.cursor()
#    query = 'SELECT "name" FROM "idd"'
#    cur.execute(query)
#    print cur.fetchall()


