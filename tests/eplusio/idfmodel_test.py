#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os, codecs

# Package imports
from idfplus.eplusio import parser, iddmodel, idfmodel, config
from idfplus.eplusio import idfmodel

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')


class TestIDFModel(object):

    def setup(self):
        print('Setup...')

    def teardown(self):
        print('Teardown...')

    def test_idf(self):

        file_path = os.path.join(APP_ROOT, 'resources', '5ZoneBoilerOutsideAirReset.idf')

        print("Loading idf file: {}".format(file_path))
        idf_file = idfmodel.IDFFile()
        with codecs.open(file_path, 'r',
                         encoding=config.FILE_ENCODING,
                         errors='backslashreplace') as raw_idf:
            idf_parser = parser.IDFParser(idf_file, default_version="8.1")
            for progress in idf_parser.parse_idf(raw_idf, file_path):
                pass

        assert progress == 100
        assert idf_file.version == "8.1"
        assert isinstance(idf_file.idd, iddmodel.IDDFile)
        assert isinstance(idf_file.get("Version")[0], idfmodel.IDFObject)
        assert isinstance(idf_file.get("version")[0], idfmodel.IDFObject)
        assert isinstance(idf_file["version"][0], idfmodel.IDFObject)
