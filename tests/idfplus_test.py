#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
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


class TestIDFPlus(object):

    def setup(self):
        print('Setup...')

    def teardown(self):
        print('Teardown...')

    def test_idd(self):

        file_path = os.path.join(APP_ROOT, 'resources', 'eplus',
                                 'EnergyPlus_IDD_v8.1.0.009.idd')

        print('Testing blank parser...')
        idd_parser_blank = parser.IDDParser()
        assert isinstance(idd_parser_blank, parser.IDDParser)

        print('Testing IDD file')
        idd_file = iddmodel.IDDFile()
        assert isinstance(idd_file, iddmodel.IDDFile)

        print('Testing IDD parser with real IDD file')
        idd_parser = parser.IDDParser(idd_file)
        assert isinstance(idd_parser, parser.IDDParser)
        for progress in idd_parser.parse_idd(file_path):
            pass
        assert progress == 100
        assert isinstance(idd_file["version"], iddmodel.IDDObject)
        assert isinstance(idd_file["version"]["A1"], iddmodel.IDDField)
        assert idd_file["version"]["A1"].tags.get('default') == "7.0"

