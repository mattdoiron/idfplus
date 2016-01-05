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
from setuptools import setup
from setuptools import find_packages
from codecs import open

# Package importd
from idfplus.__version__ import version


def read(*file_names):
    buf = []
    here = os.path.abspath(os.path.dirname(__file__))
    for filename in file_names:
        with open(os.path.join(here, filename), encoding='utf-8') as f:
            buf.append(f.read())
    return '\n'.join(buf)

setup(
    name='idfplus',
    version=version,
    author='Matt Doiron',
    author_email='matt@mindfulmodeller.ca',
    url='https://bitbucket.org/mattdoiron/idfplus/',
    description='Advanced editor for EnergyPlus simulation input files.',
    long_description=read('README.rst'),
    keywords='idd idf energyplus idfplus idf+ energy+',
    packages=find_packages(exclude=['build', 'dist', 'docs', 'tests']),
    platforms='any',
    license='GPLv3',
    install_requires=[
        "appdirs==1.4.0",
        "networkx==1.10",
        "odict==1.5.1",
        "persistent==4.1.1",
        "pyside==1.2.4",
        "whoosh==2.7.0"
    ],
    extras_require={
        'dev': ["pip-review==0.4",
                "pip-tools==1.4.2",
                "pyinstaller==3.0",
                "sphinx==1.3.3"],
        'test': ['nose==1.3.7'],
    },
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
        ]
)
