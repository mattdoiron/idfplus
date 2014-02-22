# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 11:34:45 2014

@author: Matt Doiron <mattdoiron@gmail.com>
"""

comment_delimiter_general = "!"
comment_delimiter_special = "!-"

test_line1 = '0.0,15.2,3.0;  !- X,Y,Z ==> Vertex 4 {m} '
test_line2 = '0.0,15.2,3.0 ;  !test '
test_line3 = '0.0,15.2,3.0;  !test  !- X,Y,Z ==> Vertex 4 {m}  '
test_line4 = '0.0,15.2,3.0;  !- X,Y,Z ==> Vertex 4 {m}!test  '
test_line5 = '0.0,15.2  ,3.0;  '
test_line6 = ' ! comment 123'
test_line7 = '  !- comment 456'
test_line8 = '  BuildingSurface:Detailed,'
test_line9 = '    ,            !- Outside Boundary Condition Object'
test_line10 = '    SunExposed,              !- Sun Exposure'
test_line11 = '    SunExposed,,,;              !- Sun Exposure'
test_line12 = '  !  '
test_line13 = '  !- one !-two  '


def getGeneralComment(str_in):
    '''Parses a string and returns the general comment if it exists'''
    global comment_delimiter_general
    global comment_delimiter_special

    if str_in.find(comment_delimiter_general) == -1:
        # No comments found at all
        return None

    elif str_in.find(comment_delimiter_special) == -1:
        # No special comment found so parse simply
        part = str_in.partition(comment_delimiter_general)
        return part[-1].expandtabs().strip()

    elif str_in.find(comment_delimiter_special) != -1 and \
            str_in.count(comment_delimiter_general) == 1:
        # Special comment found, but no general comment
        return None

    elif str_in.count()

    else:
        # Both types of comments found so parse in more detail
        partA = str_in.partition(comment_delimiter_special)

        if partA[0].find(comment_delimiter_general) != -1:
            # General comment is in the first item
            partB = partA[0].partition(comment_delimiter_general)

        elif partA[-1].find(comment_delimiter_general) != -1:
            # General comment is in the last item
            partB = partA[-1].partition(comment_delimiter_general)

        return partB[-1].expandtabs().strip()

print 'Comments:'
print '- line 1: "' + str(getGeneralComment(test_line1)) + '"'
print '- line 2: "' + str(getGeneralComment(test_line2)) + '"'
print '- line 3: "' + str(getGeneralComment(test_line3)) + '"'
print '- line 4: "' + str(getGeneralComment(test_line4)) + '"'
print '- line 5: "' + str(getGeneralComment(test_line5)) + '"'
print '- line 6: "' + str(getGeneralComment(test_line6)) + '"'
print '- line 7: "' + str(getGeneralComment(test_line7)) + '"'
print '- line 8: "' + str(getGeneralComment(test_line8)) + '"'
print '- line 9: "' + str(getGeneralComment(test_line9)) + '"'
print '- line 10: "' + str(getGeneralComment(test_line10)) + '"'
print '- line 11: "' + str(getGeneralComment(test_line11)) + '"'
print '- line 12: "' + str(getGeneralComment(test_line12)) + '"'
print '- line 13: "' + str(getGeneralComment(test_line13)) + '"'


def getFields(str_in):
    '''Strips all comments, etc and returns what's left'''
    global comment_delimiter_general
    global comment_delimiter_special

    # Partition the line twice
    partA = str_in.partition(comment_delimiter_special)
    partB = partA[0].partition(comment_delimiter_general)

    if partB[0].split():
        # Split the list into fields at the commas
        fields = partB[0].expandtabs().strip().split(',')

        # Check for and remove items created by a trailing comma
        if not fields[-1] and len(fields) > 1:
            fields.pop(-1)

        # Strip away any spaces from each field
        fields = map(lambda i: i.expandtabs().strip(), fields)

        # Check for and remove semicolon in last field
        if fields:
            if fields[-1].find(';') != -1:
                fields[-1] = fields[-1].strip(';').strip()
                fields.extend([';'])

        # Return list of fields
        return fields
    else:
        return None

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


def parseLine(line_in):
    '''Parses a line from the IDF file and returns results'''

    # Get results
    fields = getFields(line_in)
    comment = getGeneralComment(line_in)
    end_object = False

    # Check for and remove the semicolon, indicating the end of an object
    if fields:
        if fields[-1] == ';':
            fields.pop(-1)
            end_object = True

    # Return a dictionary of results
    return dict(fields=fields,
                comment=comment,
                end_object=end_object)


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


def parseIDF(filename):
    '''Parse the provided file name'''

    print 'Parsing IDF file: ' + filename
    line_count = 0
    object_count = 0

    # Open the specified file in a safe way
    with open(filename, 'r') as file:
        # Prepare some variables to store the results
        object_list = []
        field_list = []
        comment_list = []

        # Cycle through each line in the file
        for line in file:
            line_parsed = parseLine(line)
            line_count += 1

            # If there are any fields save them
            if line_parsed['fields']:
                field_list.extend(line_parsed['fields'])

            # If there are any comments save them
            if line_parsed['comment'] is not None:
                comment_list.append(line_parsed['comment'])

            # If this is the end of an object save it
            if line_parsed['end_object'] is True:
                if not comment_list:
                    comment_list = None

                # The first field is the object name
                object_name = field_list[0]
                field_list.pop(0)

                # Perform check for object here (against IDD file)

                # Save the object
                object_list.append(dict(name=object_name,
                                        fields=field_list,
                                        comments=comment_list))

                # Reset lists for next object
                field_list = []
                comment_list = []
                object_count += 1

    print 'Parsing complete!'
    return (line_count, object_count, object_list)


# Parse these idf files
idf_file = 'RefBldgLargeOfficeNew2004_Chicago.idf'
idf_file2 = '5ZoneBoilerOutsideAirReset.idf'
#lines, object_count, objects = parseIDF(idf_file2)


def writeIDF(filename, idfObject):
    '''Write an IDF from the specified idfObject'''

    with open(filename, 'w') as file:
        for obj in idfObject:

            # Write comments if there are any
            if obj['comments'] is not None:
                for comment in obj['comments']:
                    file.write("! {}\n".format(comment))

            # Check IDD file here for special formatting instructions

            # Write the object name
            file.write("  {},\n".format(obj['name']))

            # Write the fields
            field_count = len(obj['fields'])
            for i, field in enumerate(obj['fields']):
                if i == field_count - 1:
                    file.write("    {};\n".format(field))
                else:
                    file.write("    {},\n".format(field))

            # Add newline at the end of the object
            file.write("\n")

    print 'File written!'

# Write the idf file
#writeIDF('testoutput.idf', objects)
