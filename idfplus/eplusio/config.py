#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
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
import appdirs
import logging

# Constants
FILE_ENCODING = 'latin_1'
IDD_FILE_NAME_ROOT = 'EnergyPlus_IDD_v{}.dat'
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
DATA_DIR = appdirs.user_data_dir(APP_NAME, COMPANY_NAME)
DEFAULT_IDD_VERSION = '8.2'
__version__ = '0.0.3'

# Make sure necessary folders exist
for directory in [DATA_DIR]:
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise

# Global variables
log = logging.getLogger(__name__)
