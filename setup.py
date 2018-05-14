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
import subprocess
from codecs import open
from setuptools import setup
from setuptools import Command
from setuptools.command.test import test as _test
from setuptools.dist import DistutilsOptionError

if sys.platform.startswith('win'):
    from distutils.command.bdist_msi import bdist_msi as _bdist_msi
else:
    from setuptools import Command as _bdist_msi

if sys.version_info.major != 2 and sys.version_info.minor < 7:
    print("Currently compatible with Python 2.7.x only!")
    sys.exit(1)


project = 'idfplus'
packages = [
    'idfplus',
    'idfplus.widgets',
    'idfplus.models',
    'idfplus.eplusio',
]
requires = [
    "appdirs==1.4.3",
    "faulthandler==3.1",
    "odict==1.6.2",
    "persistent==4.2.4.2",
    "pyside==1.2.4"
]
requires_dev = [
    "pip-review==1.0",
    "pip-tools==2.0.2",
    "pyinstaller==3.3.1",
    "sphinx==1.7.4",
]
requires_test = ['pytest==3.5.1']
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
        if not sys.platform.startswith('win'):
            print("This command is available on Windows only.")
            sys.exit(1)

    def finalize_options(self):
        pass

    def run(self):
        root_path = os.path.dirname(__file__)
        dist_dir = os.path.join(root_path, 'dist')
        build_dir = os.path.join(root_path, 'build')
        bind_dir = os.path.join(dist_dir, project)
        wix_obj = os.path.join(build_dir, '{}.wixobj'.format(project))
        wxs_file = os.path.join(build_dir, '{}.wxs'.format(project))
        msi_file = os.path.join(dist_dir, '{}-v{}.msi'.format(project, version))

        print('Running candle...')
        try:
            subprocess.call(['candle', '-nologo', '-out', wix_obj, wxs_file])
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print('Cannot find "candle" command. Please be sure WiX is installed.')
                sys.exit(1)

        print('Running light...')
        try:
            subprocess.call(['light', '-nologo', '-sacl', '-sval', '-spdb', '-b', bind_dir,
                             '-ext', 'WixUIExtension', '-out', msi_file, wix_obj])
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print('Cannot find "light" command. Please be sure WiX is installed.')
                sys.exit(1)

    def test(self):
        print('No tests available')


class Harvest(Command):
    description = 'Use to harvest files and uuids for use by WiX.'
    user_options = []

    def initialize_options(self):
        if not sys.platform.startswith('win'):
            print("This command is available on Windows only.")
            sys.exit(1)

    def finalize_options(self):
        pass

    def run(self):
        root_path = os.path.dirname(__file__)
        dist_dir = os.path.join(root_path, 'dist')
        build_dir = os.path.join(root_path, 'build')
        source_dir = os.path.join(dist_dir, project)
        harvest_file = os.path.join(build_dir, '{}_harvest.wxs'.format(project))

        try:
            subprocess.call(['heat', 'dir', source_dir, '-nologo', '-g1', '-gg', '-sfrag',
                             '-srd', '-cg', 'IDFPlusComponents', '-template', 'product',
                             '-sw5150', '-sw5151', '-out', harvest_file])
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print('Cannot find "heat" command. Please be sure WiX is installed.')
                sys.exit(1)


class Freeze(Command):
    description = 'Use to freeze the Python app for portability.'
    user_options = [
        ('log-level=', 'l',
         "Log level for PyInstaller"),
    ]

    def _upx_version(self):
        if self.is_win:
            upx_version = 'upx394w'
        elif self.is_32bit:
            upx_version = 'upx-3.94-i386_linux'
        else:
            upx_version = 'upx-3.94-amd64_linux'
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
        spec_file = os.path.join(root_path, project + '.spec')
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
    author_email='mattdoiron@gmail.com',
    url='https://bitbucket.org/mattdoiron/idfplus/',
    download_url='https://bitbucket.org/mattdoiron/idfplus/downloads/',
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
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Physics',
        'Natural Language :: English',
    ],
    entry_points={
        'gui_scripts': [
            'idfplus=idfplus:main',
        ],
    },
    cmdclass={
        'freeze': Freeze,
        'bdist_msi': bdist_msi,
        'harvest': Harvest,
        'test': PyTest,
    },
)
