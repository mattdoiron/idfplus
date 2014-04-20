# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 17:24:48 2014

@author: matt
"""

import json
from blitzdb import Document
from blitzdb import FileBackend

db = FileBackend("./my-db2")


class IDFObject(Document):
    '''Test of blitzdb'''

    pass


class IDFFile(Document):
    '''Test of blitzdb'''

    pass

idf_obj1 = IDFObject({'A1': 'objectname1',
                      'N1': 24.22,
                      'A2': 'october'})
idf_obj2 = IDFObject({'A1': 'objectname2',
                      'N1': 34.22,
                      'A2': 'november'})
idf_file = IDFFile({'name': '5zonesamplefile.idf',
                    'version': '8.1.0.0',
                    'objects': [idf_obj1, idf_obj2]})
idf_obj2.name = idf_file.name

print idf_file.name
print idf_file.version
print idf_obj1.N1

#db.save(idf_file)
#db.commit()

#print db.get(IDFObject, {'A1': 'objectname1'})

queryset = db.filter(IDFObject,{'$and' : [{'A1': 'objectname1'}, {'N1': 24.22}]})

print len(queryset)

for item in queryset:
    print item.A2
