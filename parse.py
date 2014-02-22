# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 22:09:24 2011

@author: matt
"""

import re
from pysqlite2 import dbapi2 as sqlite

# Define some global variables
idf_file = "RefBldgLargeOfficeNew2004_Chicago.idf"
idd_file = "Energy+2.idd"
obj_global = []

def parse_idd(file):
    
    comment_count = 0
    empty_line_count = 0
    version = ""
    line_count = 0
    obj = []
    object_count = 0
    
    # Find the version number of this idd file
    version_line = file.readline(150)
    if not version_line.startswith('!IDD_Version'):
        return "This file does not appear to be a valid IDD file."
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

        # It must be a valid line, so save it
        else:
            obj.append(line)
        
        # Check for the end of an object and parse it
        if line.find(';') != -1:
            parse_obj(obj)
            obj = []
            object_count += 1
            
        # Count the line
        line_count += 1
    
    print "number of comment lines: " + str(comment_count)
    print "number of objects: " + str(object_count)
#    print "number of objects 2: " + str(object_count_2)
    print "number of lines: " + str(line_count)
    print "number of empty lines: " + str(empty_line_count)
    print 'Version found: ' + version

def parse_obj(obj):
    print len(obj)
    obj_global.append(obj)
      
# Open the specified file (safely)
with open(idd_file, 'r') as file:
    # Open the specified file (safely) and parse it
    version = parse_idd(file)