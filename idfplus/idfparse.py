# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 11:34:45 2014

@author: Matt Doiron <mattdoiron@gmail.com>
"""

#from PySide.QtCore import QObject, Signal
from contextlib import closing

#fieldTags = set('\\field',
#                '\\note',
#                '\\required-field',
#                '\\begin-extensible',
#                '\\units',
#                '\\ip-units',
#                '\\unitsBasedOnField',
#                '\\minimum',
#                '\\minimum>',
#                '\\maximum',
#                '\\maximum<',
#                '\\default',
#                '\\deprecated',
#                '\\autosizeable',
#                '\\autocalculatable',
#                '\\type',
#                '\\retaincase',
#                '\\key',
#                '\\object-list',
#                '\\reference',
#                '\\memo',
#                '\\unique-object',
#                '\\required-object',
#                '\\min-fields',
#                '\\obsolete',
#                '\\extensible:',
#                '\\begin-extensible',
#                '\\format',
#                '\\group')

fieldTags = ['\\field',
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

options_list = ['OriginalOrderTop', 'UseSpecialFormat']

field_tag_delimiter = '\\'
comment_delimiter_general = '!'
comment_delimiter_special = '!-'

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
#
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
#print '- line 1: "' + str(getFields(test_line1)) + '"'
#print '- line 2: "' + str(getFields(test_line2)) + '"'
#print '- line 3: "' + str(getFields(test_line3)) + '"'
#print '- line 4: "' + str(getFields(test_line4)) + '"'
#print '- line 5: "' + str(getFields(test_line5)) + '"'
#print '- line 6: "' + str(getFields(test_line6)) + '"'
#print '- line 7: "' + str(getFields(test_line7)) + '"'
#print '- line 8: "' + str(getFields(test_line8)) + '"'
#print '- line 9: "' + str(getFields(test_line9)) + '"'
#print '- line 10: "' + str(getFields(test_line10)) + '"'
#print '- line 11: "' + str(getFields(test_line11)) + '"'
#print '- line 12: "' + str(getFields(test_line12)) + '"'
#print '- line 13: "' + str(getFields(test_line13)) + '"'
#print '- line 14: "' + str(getFields(test_line14)) + '"'
#print '- line 15: "' + str(getFields(test_line15)) + '"'
#print '- line 16: "' + str(getFields(test_line16)) + '"'


#def parseLineIDF(line_in):
#    '''Parses a line from the IDF file and returns results'''
#
#    # Get results
#    fields = getFields(line_in)
#    comment = getGeneralComment(line_in)
#    end_object = False
#
#    # Check for and remove the semicolon, indicating the end of an object
#    if fields:
#        if fields[-1] == ';':
#            fields.pop(-1)
#            end_object = True
#
#    # Return a dictionary of results
#    return dict(fields=fields,
#                comment=comment,
#                end_object=end_object)


#print 'Whole Line:'
#print parseLine(test_line1)
#print parseLine(test_line2)
#print parseLine(test_line3)
#print parseLine(test_line4)
#print parseLine(test_line5)
#print parseLine(test_line6)
#print parseLine(test_line7)
#print parseLine(test_line8)
#print parseLine(test_line9)
#print parseLine(test_line10)
#print parseLine(test_line11)
#print parseLine(test_line12)
#print parseLine(test_line13)
#print parseLine(test_line14)
#print parseLine(test_line15)
#print parseLine(test_line16)


#def parseIDF(filename):
#    '''Parse the provided IDF file'''
#
#    print 'Parsing IDF file: ' + filename
#    global comment_delimiter_special
#
#    # Open the specified file in a safe way
#    with open(filename, 'r') as file:
#        # Prepare some variables to store the results
#        objects = []
#        field_list = []
#        comment_list = []
#        comment_list_special = []
#        options = []
#        object_index = 0
#
#        # Cycle through each line in the file
#        for i, line in enumerate(file):
#            line_parsed = parseLineIDF(line)
#
#            line_clean = line.expandtabs().lstrip()
#            if line_clean.startswith(comment_delimiter_special):
#                # Special comment found, save it
#                comment_list_special.append(
#                    line_clean.lstrip(comment_delimiter_special).rstrip()
#                )
#
#                # Check for special options
#                if line_clean.startswith('!-Option'):
#                    if line_clean.find('UseSpecialFormat') != -1:
#                        options.append('UseSpecialFormat')
#                    if line_clean.find('OriginalOrderTop') != -1:
#                        options.append('OriginalOrderTop')
#
#            # If there are any fields save them
#            if line_parsed['fields']:
#                field_list.extend(line_parsed['fields'])
#
#            # If there are any comments save them
#            if line_parsed['comment'] is not None:
#                comment_list.append(line_parsed['comment'])
#
#            # If this is the end of an object save it
#            if line_parsed['end_object'] is True:
#                if not comment_list:
#                    comment_list = None
#
#                # The first field is the object name
#                object_name = field_list[0]
#                field_list.pop(0)
#
##                if len(field_list) == 0 or not field_list[0]:
##                    field_list = None
#
##                print 'here! ' + object_name  + str(field_list)
#                # Perform check for object here (against IDD file)
#
#                # Save the object
#                objects.append(dict(name=object_name,
#                                    fields=field_list,
#                                    comments=comment_list,
#                                    comments_special=comment_list_special,
#                                    order=object_index))
#
#                # Reset lists for next object
#                field_list = []
#                comment_list = []
#                comment_list_special = []
#                object_index += 1
#
#    print 'Parsing IDF complete!'
#    return (i + 1, len(objects), options, objects)
#

# Parse these idf files
#idf_file = 'RefBldgLargeOfficeNew2004_Chicago.idf'
#idf_file2 = '5ZoneBoilerOutsideAirReset.idf'
#lines, object_count, options, objects = parseIDF(idf_file2)

class Writer(object):

    def __init__(self):
        pass

    def writeIDF(self, filename, options, idf_file):
        '''Write an IDF from the specified idfObject'''

        print 'Writing file: ' + filename + '_test'

        # Check for special options
#        if options and options is not None:
#            options = []
#            if options.count('UseSpecialFormat') >= 1:
#                print 'Special formatting requested, but not yet implemented.'

        # Open file and write
        try:
            with open(filename + '_test', 'w') as file:
                for obj_class, obj_list in idf_file.iteritems():

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
#                        if options.count('UseSpecialFormat') >= 1:
#                            pass

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

            print 'File written!'
            return True
        except IOError as e:
            print 'File not written! Exception!' + e.strerror
            return False

# Write the idf file
#writeIDF('testoutput.idf', options, objects)


#print getTags(tag_line1)
#print getTags(tag_line2)
#print getTags(tag_line3)
#print getTags(tag_line4)
#print getTags(tag_line5)
#print getTags(tag_line6)


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

    def __init__(self, msg):
        self.msg = msg  # Communicate()

    def getFields(self, str_in):
        '''Strips all comments, etc and returns what's left'''
        global comment_delimiter_general
        global comment_delimiter_special

        # Partition the line twice
        partA = str_in.partition(comment_delimiter_special)
        partB = partA[0].partition(comment_delimiter_general)

        if partB[0].strip().startswith('\\'):
            # This is a tag and not a comment
            return None

        elif partB[0].strip():
            # Split the list into fields at the commas
            fields = partB[0].expandtabs().strip().split(',')

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
        else:
            return None

    def getGeneralComment(self, str_in):
        '''Parses a string and returns the general comment if it exists'''
        global comment_delimiter_general
        global comment_delimiter_special

        if str_in.find(comment_delimiter_general) == -1:
            # No comments found at all
            return None

        elif str_in.find(comment_delimiter_special) == -1:
            # No special comment found so parse simply
            part = str_in.partition(comment_delimiter_general)
            return part[-1].expandtabs().rstrip()

        elif str_in.find(comment_delimiter_special) != -1 and \
                str_in.count(comment_delimiter_general) == 1:
            # Special comment found, but no general comment
            return None

        else:
            # Both types of comments may be present so parse in more detail
            partA = str_in.partition(comment_delimiter_special)

            if partA[0].find(comment_delimiter_general) != -1:
                # General comment precedes special comment, repartition
                partB = str_in.partition(comment_delimiter_general)

            elif partA[-1].find(comment_delimiter_general) != -1:
                # General comment is in the last item (part of special comment)
                return None

            return partB[-1].expandtabs()

    def getTags(self, line_in):
        '''Parses a line and gets any fields tags present'''

        global fieldTags
        tag_result = None

        # Create a list containing any tags found in line_in
        match = [x for x in fieldTags if x in line_in]

        # If there are any matches, save the first one
        if match:

            # Partition the line at the match
            part = line_in.strip().partition(match[0])

            # If there is a value save it
            if part[-1]:
                value = part[-1].lstrip()
            else:
                value = None

            # Save results
            tag_result = dict(tag=match[0],
                              value=value)

        # Return results
        return tag_result

    def parseLineIDD(self, line_in):
        '''Parses a line from the IDD file and returns results'''

        # Get results
        fields = self.getFields(line_in) or None
        comment = self.getGeneralComment(line_in)  # Preserve blanks!
        tags = self.getTags(line_in) or None
        end_object = False
        empty_line = False

        # Check for an empty line
        if not fields and not comment and not tags:
            empty_line = True

        # Check for and remove the semicolon, indicating the end of an object
        if fields:
            if fields[-1] == ';':
                fields.pop(-1)
                end_object = True

        # Return a dictionary of results
        return dict(fields=fields,
                    comment=comment,
                    field_tags=tags,
                    end_object=end_object,
                    empty_line=empty_line)

    def parseIDD(self, filename):
        '''Parse the provided idd (or idf) file'''
        import shelve
        import os
        from collections import OrderedDict

        global comment_delimiter_special
        global options_list

#        myIDD = shelve.open('myIDD.dat')  # This should be done using 'with'
#        idd = myIDD['idd']

        total_size = os.path.getsize(filename)
        total_read = 0.0

        print 'Parsing IDD file: {} ({} bytes)'.format(filename, total_size)

        # Open the specified file in a safe way
        with open(filename, 'r') as file, closing(shelve.open('data/myIDD.dat')) as myIDD:
            # Prepare some variables to store the results
            idd = myIDD['idd']
            objects = OrderedDict()
            field_list = []
            comment_list = []
            comment_list_special = []
            field_tag_list = []
            field_tag_sublist = []
            options = []
            group = None
            group_list = []
            end_object = False
            eol_char = None  # Detect this and save it

            # Cycle through each line in the file
            while True:

                # Parse this line using readline (so last one is a blank)
                line = file.readline()
                total_read += len(line)
                self.msg.msg.emit(total_read)
                line_parsed = self.parseLineIDD(line)

                # If the previous line was not the end of an object check this one
                if end_object is False:
                    end_object = line_parsed['end_object']
                empty_line = line_parsed['empty_line']

                # Check for special comments and options (write a func for this?)
                line_clean = line.expandtabs().lstrip()
                if line_clean.startswith(comment_delimiter_special):
                    # Special comment found, save it
                    comment_list_special.append(
                        line_clean.lstrip(comment_delimiter_special).rstrip()
                    )

                # Check for special options (write a separate function for this?)
                if line_clean.startswith('!-Option'):
                    match = [x for x in options_list if x in line_clean]
                    options.extend(match)

                # If there are any comments save them
                if line_parsed['comment'] is not None:
                    comment_list.append(line_parsed['comment'])

                # If there are any fields save them
                if line_parsed['fields']:
                    field_list.extend(line_parsed['fields'])

                # Check for the end of an object before checking for new tags
                if (end_object and empty_line) or line_parsed['fields']:
                    if field_tag_sublist:
                        field_tag_list.append(field_tag_sublist)
                        field_tag_sublist = []

                # If there are any field tags for this object save them
                if line_parsed['field_tags']:
                    field_tag_sublist.append(line_parsed['field_tags'])
                    if line_parsed['field_tags']['tag'] == '\\group':
                        group = line_parsed['field_tags']['value']

                # If this is the end of an object save it
                if end_object and empty_line:

                    # The first field is the object name
                    object_name = field_list[0]
                    field_list.pop(0)

                    # Make sure there are values or return None
                    field_list = field_list or None
                    field_tag_list = field_tag_list or None
                    comment_list = comment_list or None
                    comment_list_special = comment_list_special or None

                    # If this is an IDF file, perform checks against IDD
                    # file here (mandatory fields, unique objects, etc)

                    # Search idd file for object name
                    if object_name in idd:
                        group = idd[object_name][0]['group']

                    # Add the group to the list if it isn't already there
                    if group not in group_list:
                        group_list.append(group)

                    # Save the object
                    obj = dict(fields=field_list,
                               comments=comment_list,
                               comments_special=comment_list_special,
                               field_tags=field_tag_list,
                               group=group)

                    # Assign or append results
                    if object_name in objects:
                        objects[object_name].append(obj)
                    else:
                        objects[object_name] = [obj]

                    # Reset lists for next object
                    field_list = []
                    comment_list = []
                    comment_list_special = []
                    field_tag_list = []
                    field_tag_sublist = []
                    end_object = False

                # Detect end of file and break. Do it this way to be sure
                # the last line can be processed AND identified as last!
                if not line:
                    break

#        myIDD.close()
        print 'Parsing IDD complete!'
        return (len(objects), eol_char, options, group_list, objects)


## Parse this idd file
#idd_file = 'Energy+.idd'
#idf_file = 'RefBldgLargeOfficeNew2004_Chicago.idf'
idf_file2 = '5ZoneBoilerOutsideAirReset.idf'
#idf_file3 = 'ChicagoSM.idf'
#object_count, eol_char, options, groups, objects = parseIDD(idf_file2)
##writeIDF('testoutput.idf', options, objects)
#import json
#encoded = json.dumps(objects)
#obj = json.loads(encoded)


#import shelve
#database = shelve.open('myIDD.dat')
#database['idd'] = objects
#database['groups'] = groups[1:]
#tree_model = None
#database['tree_model'] = tree_model
#database.close()




