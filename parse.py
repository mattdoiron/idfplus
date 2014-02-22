# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 20:17:03 2011

@author: matt
"""

import re
from pysqlite2 import dbapi2 as sqlite

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

def parse_IDF(file):
    comment_count = 0
    object_count = 0
    object_count_2 = 0
    line_count = 0
    empty_line_count = 0
    parse_mode = "object"
    object_dict = []

    # Cycle through each line in the file, one at a time
    for line_in in file:
        
        # get rid of tabs, then leading/trailing spaces
        line = line_in.expandtabs().strip()
        
        # If line starts with ! then it's a comment
        if line.startswith('!'):
            comment_count += 1
        
        # Check for empty lines
        elif not line:
            empty_line_count += 1
            
        # Otherwise, it's useful so do some stuff
        else:

            # Split the line at the commas
            obj = line.split(',')
            
            # Check for start of an object. The first list item that is all
            # alphas or contains a : denotes the start of a new object
            if parse_mode == "object" and (obj[0].isalpha() or obj[0].find(':') != -1):
                object_count_2 += 1
#                print "START_OBJECT -----------------------------------------"
                parse_mode = "field"
                object_dict.append(obj[0])
                if not objects.has_key(obj[0]):
                    print "Object not found! ("+obj[0]+")"
                    return {}
                
            # If the last item has a ; then this signals the end of an object
            # so split it further to extract any comment for the last field.
            if obj[-1].find(';') != -1:
                new_obj = obj[-1].split(';')
                obj[-1] = new_obj[0]
                obj.append(new_obj[1].strip())
                object_count += 1
                parse_mode = "object"
                
            # Strip white spaces from all array items
            for i, item in enumerate(obj):
                obj[i] = item.strip()
            
            # Print the line
#            print obj
#            if obj[0].isdigit():
#                print float(obj[0])
        
        # Count the line
        line_count += 1
    
    print "number of comment lines: " + str(comment_count)
    print "number of objects: " + str(object_count)
    print "number of objects 2: " + str(object_count_2)
    print "number of lines: " + str(line_count)
    print "number of empty lines: " + str(empty_line_count)

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
    model = parse_IDF(file)


#with sqlite.connect('../CaliperTest.sqlite') as db:
#    cur = db.cursor()
#    query = 'SELECT "name" FROM "idd"'
#    cur.execute(query)
#    print cur.fetchall()


