#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, Matthew Doiron All rights reserved.

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

# System imports
import os
from nose.tools import *

# Package imports
from idfplus import idfparse
from idfplus import idfmodel

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

def setup():
    print("SETUP!")

def teardown():
    print("TEAR DOWN!")

def test_basic():
    print('basic parsing test:')
    file_path = os.path.join(APP_ROOT, 'data', 'EnergyPlus_IDD_v8.1.0.008.idd')
    parser = idfparse.IDDParser()
    idd = idfmodel.IDDFile()
    parser = idfparse.IDDParser(idd)
    for progress in parser.parse_idd(file_path):
        pass
