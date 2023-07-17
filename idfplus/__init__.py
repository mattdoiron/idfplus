#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

import subprocess

git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
label = subprocess.check_output(["git", "describe"]).strip().decode('UTF-8')
# print(git_hash)
# print(label)

__version__ = "{}-{}".format(label, git_hash)
