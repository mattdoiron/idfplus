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
import re

from codecs import open

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

project = 'idfplus'
packages = [
    'idfplus',
    'idfplus.gui',
    'idfplus.eplusio',
]
requires = [
    "appdirs==1.4.0",
    "networkx==1.10",
    "odict==1.5.1",
    "persistent==4.1.1",
    "pyside==1.2.4",
    "whoosh==2.7.0",
]
requires_dev = [
    "pip-review==0.4",
    "pip-tools==1.4.2",
    "pyinstaller==3.0",
    "sphinx==1.3.3",
]
requires_setup = []

with open(os.path.join(project, '__init__.py'), 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('Cannot find version information')
with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()
with open('CHANGELOG.rst', 'r', 'utf-8') as f:
    changelog = f.read()


setup(
    name=project,
    version=version,
    author='Matt Doiron',
    author_email='matt@mindfulmodeller.ca',
    url='https://bitbucket.org/mattdoiron/idfplus/',
    description='Advanced editor for EnergyPlus simulation input files.',
    long_description=readme + '\n\n' + changelog,
    keywords='idd idf energyplus idfplus idf+ energy+',
    packages=packages,
    platforms='any',
    license='GPL3',
    zip_safe=False,
    install_requires=requires,
    setup_requires=requires_setup,
    tests_require=requires_dev,
    test_suite='idfplus.tests.idfplus_tests',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    entry_points={
        'gui_scripts': [
            'idfplus=idfplus',
        ],
    },
)
