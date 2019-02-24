#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
import os

# Package imports
from idfplus.eplusio import parser
from idfplus.eplusio import iddmodel

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')


class TestMain(object):

    def setup(self):
        print('Setup...')

    def teardown(self):
        print('Teardown...')

    def test_idd(self):

        file_path = os.path.join(APP_ROOT, 'resources', 'eplus', 'EnergyPlus_IDD_v8.1.0.009.idd')

        print('Testing blank parser...')
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
        assert idd_file.parser_version == '0.1.2'

