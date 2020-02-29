#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os, codecs

# Package imports
from idfplus.eplusio import parser, iddmodel, idfmodel, config

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')


class TestParser(object):

    def setup(self):
        print('Setup...')

    def teardown(self):
        print('Teardown...')

    def test_idd(self):

        file_path = os.path.join(APP_ROOT, 'resources', 'eplus', 'EnergyPlus_IDD_v8.1.0.009.idd')
        print("Loading idf file: {}".format(file_path))
        print('Testing blank parser')
        idd_parser_blank = parser.IDDParser()
        assert isinstance(idd_parser_blank, parser.IDDParser)

        print('Testing IDD file')
        idd_file = iddmodel.IDDFile(parser_version='0.1.2')
        assert isinstance(idd_file, iddmodel.IDDFile)

        print('Testing IDD parser with real IDD file')
        idd_parser = parser.IDDParser(idd_file)
        assert isinstance(idd_parser, parser.IDDParser)
        for progress in idd_parser.parse_idd(file_path, write=False):
            pass
        assert progress == 100
        assert isinstance(idd_file["version"], iddmodel.IDDObject)
        assert isinstance(idd_file["version"]["A1"], iddmodel.IDDField)
        assert idd_file["version"]["A1"].tags.get('default') == "7.0"

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

