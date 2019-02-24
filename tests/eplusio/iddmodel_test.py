#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os

# Package imports
from idfplus.eplusio import parser
from idfplus.eplusio import iddmodel

# Constants
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')


class TestIDDModel(object):

    def setup(self):
        print('Setup...')

    def teardown(self):
        print('Teardown...')

    def test_idd(self):
        print("placeholder")
