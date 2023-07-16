#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration specific to eplusio module

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os
import appdirs

# Constants
FILE_ENCODING = 'latin_1'
IDD_FILE_NAME_ROOT = 'EnergyPlus_IDD_v{}.dat'
COMPANY_NAME = 'mindfulmodeller'
APP_NAME = "IDFPlus"
DATA_DIR = appdirs.user_data_dir(APP_NAME, COMPANY_NAME)
DEFAULT_IDD_VERSION = '8.8'

# Make sure necessary folders exist
for directory in [DATA_DIR]:
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise
