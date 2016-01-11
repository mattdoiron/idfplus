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
import sys
import platform

from codecs import open

from setuptools import setup
from setuptools import Command
from setuptools.command.test import test as _test
from setuptools.dist import DistutilsOptionError

if sys.platform.startswith('win'):
    from distutils.command import bdist_msi as _bdist_msi
else:
    from setuptools import Command as _bdist_msi

if sys.version_info.major != 2 and sys.version_info.minor < 7:
    print("Currently compatible with Python 2.7.x only!")
    sys.exit(1)


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
requires_test = ['pytest==2.8.5']
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


class PyTest(_test):
    description = 'Used to run tests.'
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        _test.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


class bdist_msi(_bdist_msi):
    description = 'Used to build an msi installer. Windows only.'
    user_options = []
    all_versions = ['2.7']

    def initialize_options(self):
        print('initializing options')
        if not sys.platform.startswith('win'):
            print("This command is available on Windows only.")
            sys.exit(1)

    def finalize_options(self):
        print('finalizing options')

    def run(self):
        print('executing bdist_msi...')

    def test(self):
        print('no tests available')


class Freeze(Command):
    description = 'Use to freeze the Python app for portability.'
    user_options = [
        ('log-level=', 'l',
         "Log level for PyInstaller"),
    ]

    def _upx_version(self):
        if self.is_win:
            upx_version = 'upx391w'
        elif self.is_32bit:
            upx_version = 'upx-3.91-i386_linux'
        else:
            upx_version = 'upx-3.91-amd64_linux'
        return upx_version

    def initialize_options(self):
        self.pyi_run = None
        self.is_win = False
        self.is_32bit = True
        self.log_level = 'INFO'

    def finalize_options(self):
        print('log level: {}'.format(self.log_level))
        try:
            from PyInstaller.__main__ import run
        except ImportError:
            raise DistutilsOptionError('PyInstaller is not installed')
        else:
            self.pyi_run = run
        self.is_win = platform.system().startswith('Windows')
        self.is_32bit = platform.architecture()[0] == '32bit'

    def run(self):
        root_path = os.path.dirname(__file__)
        spec_file = os.path.join(root_path, 'build', project + '.spec')
        dist_dir = os.path.join(root_path, 'dist')
        build_dir = os.path.join(root_path, 'build')
        upx_dir = os.path.join(root_path, 'resources', 'upx', self._upx_version())
        self.pyi_run(['--clean', '--noconfirm', '--onedir',
                      '--log-level=' + self.log_level,
                      '--distpath=' + dist_dir,
                      '--workpath=' + build_dir,
                      '--upx-dir=' + upx_dir,
                      spec_file])


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
    tests_require=requires_test,
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
    cmdclass={
        'freeze': Freeze,
        'bdist_msi': bdist_msi,
        'test': PyTest,
    },
)
