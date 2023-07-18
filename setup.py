#!/usr/bin/python
# -*- coding: utf-8 -*-
""""Setup.py

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import os
from email.utils import formatdate
import sys
import errno
import subprocess
from codecs import open
from setuptools import setup
from setuptools import Command
from setuptools.command.test import test as _test
from setuptools.dist import DistutilsOptionError
import fileinput
from shutil import copyfile

if sys.platform.startswith('win'):
    from distutils.command.bdist_msi import bdist_msi as _bdist_msi
    from setuptools import Command as _bdist
else:
    from setuptools import Command as _bdist_msi
    from distutils.command.bdist import bdist as _bdist

if sys.version_info.major != 3 and sys.version_info.minor < 10:
    print("Currently compatible with Python 3.10.x only!")
    sys.exit(1)


project = 'idfplus'
packages = [
    'idfplus',
    'idfplus.widgets',
    'idfplus.models',
    'idfplus.eplusio',
]
requires = [
    "appdirs==1.4.4",
    "odict==1.9.0",
    "persistent==5.0",
    "PySide2==5.15.2.1"
]
requires_dev = [
    "cffi==1.15.1",
    "pip-tools==7.0.0",
    "pyinstaller==5.13.0",
    "sphinx==6.2.1",
    "pywin32==306 : sys.platform=='win32'"
]
requires_test = [
    'pytest==7.4.0',
    'pytest-qt==4.2.0'
]
requires_setup = ['wheel==0.40.0']

build_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
version_full = subprocess.check_output(['git', 'describe', '--tags', '--always', 'HEAD']).strip().decode()
version = version_full.split('-')[0]

with open(os.path.join(project, '__init__.py'), 'w') as f:
    f.write('''\
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IDF+ is an enhanced editor for idf files—the text-based, simulation input files for EnergyPlus.

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

__version__ = '{}'
__version_full__ = '{}'
__build__ = '{}'
'''.format(version, version_full, build_hash))
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
        error_no = pytest.main(self.pytest_args)
        sys.exit(error_no)


class bdist_msi(_bdist_msi):
    description = 'Used to build an msi installer. Windows only.'
    user_options = []
    all_versions = ['3.10']

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
        resources_dir = os.path.join(root_path, 'resources')
        bind_dir = os.path.join(dist_dir, project)
        wix_obj = os.path.join(build_dir, '{}.wixobj'.format(project))
        wxs_file = os.path.join(resources_dir, '{}.wxs'.format(project))
        msi = '{}_{}.msi'.format(project, version)
        msi_file = os.path.join(dist_dir, msi)
        artifact_dir = os.path.join(root_path, 'artifacts')
        artifact_file = os.path.join(artifact_dir, msi)
        my_env = os.environ.copy()
        if my_env.get("WIX"):
            wix_bin_dir = os.path.join(my_env["WIX"], "bin")
        else:
            wix_bin_dir = os.path.join(resources_dir, 'wix311')
        print("Wix dir: {}".format(wix_bin_dir))

        print('Running candle...')
        try:
            subprocess.call([os.path.join(wix_bin_dir, 'candle'), '-nologo', '-out', wix_obj, wxs_file])
        except OSError as e:
            if e.errno == errno.ENOENT:
                print('Cannot find "candle" command. Please be sure WiX is installed.')
                sys.exit(1)

        print('Running light...')
        try:
            subprocess.call([os.path.join(wix_bin_dir, 'light'), '-nologo', '-sacl', '-sval', '-spdb', '-b', bind_dir,
                             '-ext', 'WixUIExtension', '-out', msi_file, wix_obj])
        except OSError as e:
            if e.errno == errno.ENOENT:
                print('Cannot find "light" command. Please be sure WiX is installed.')
                sys.exit(1)

        # Move resulting msi file to its own folder for easier export as an artifact
        if not os.path.exists(artifact_dir):
            os.makedirs(artifact_dir)
        os.rename(msi_file, artifact_file)
        
        print("Creation of msi complete. See {}.".format(artifact_file))

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
        resources_dir = os.path.join(root_path, 'resources')
        harvest_file = os.path.join(build_dir, '{}_harvest.wxs'.format(project))
        my_env = os.environ.copy()
        if my_env.get("WIX"):
            wix_bin_dir = os.path.join(my_env["WIX"], "bin")
        else:
            wix_bin_dir = os.path.join(resources_dir, 'wix311')
        print("Wix dir: {}".format(wix_bin_dir))

        try:
            subprocess.call([os.path.join(wix_bin_dir, 'heat'), 'dir', source_dir, '-nologo',
                             '-g1', '-gg', '-sfrag', '-ag', '-srd', '-cg', 'IDFPlusComponents',
                             '-template', 'product', '-sw5150', '-sw5151', '-out', harvest_file])
        except OSError as e:
            if e.errno == errno.ENOENT:
                print('Cannot find "heat" command. Please be sure WiX is installed.')
                sys.exit(1)

        print("Harvest complete. See {} for list of files.".format(harvest_file))


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

    def run(self):
        root_path = os.path.dirname(__file__)
        spec_file = os.path.join(root_path, project + '.spec')
        dist_dir = os.path.join(root_path, 'dist')
        build_dir = os.path.join(root_path, 'build')
        # upx_dir = os.path.join(root_path, 'resources', 'upx', self._upx_version())
        self.pyi_run(['--clean', '--noconfirm',
                      '--log-level=' + self.log_level,
                      '--distpath=' + dist_dir,
                      '--workpath=' + build_dir,
                      # '--upx-dir=' + upx_dir,
                      spec_file])


class bdist_deb(_bdist):
    description = 'Used to build a deb installer. Debian/Ubuntu only.'
    user_options = []
    all_versions = ['3.10']

    def initialize_options(self):
        if not sys.platform.startswith('linux'):
            print("This command is available on Debian/Ubuntu only.")
            sys.exit(1)

    def finalize_options(self):
        pass

    def run(self):
        root_path = os.path.dirname(__file__)
        changelog_template = os.path.join(root_path, 'resources', 'deb_changelog')
        changelog_deb = os.path.join(root_path, 'debian', 'changelog')
        deb = '{}_{}-0_all.deb'.format(project, version)
        deb_file = os.path.join('..', root_path, deb)
        artifact_dir = os.path.join(root_path, 'artifacts')

        # Move debian changelog template to debian folder and populate it
        copyfile(changelog_template, changelog_deb)
        self.write_changelog(changelog_deb)

        print('Running dpkg-builddeb...')
        try:
            subprocess.call(['dpkg-buildpackage', '-b', '-tc'])
        except OSError as e:
            if e.errno == errno.ENOENT:
                print('Cannot find "dpkg-buildpackage" command. Please be sure WiX is installed.')
                sys.exit(1)

        # Move resulting deb file to its own folder for easier export as an artifact
        if not os.path.exists(artifact_dir):
            os.makedirs(artifact_dir)
        os.rename(deb_file, os.path.join(artifact_dir, deb))

        os.remove(changelog_deb)
        print("Creation of deb complete. See {}.".format(os.path.join(artifact_dir, deb_file)))

    @staticmethod
    def write_changelog(file_name):
        with fileinput.FileInput(file_name, inplace=True) as file:
            for line in file:
                print(line.replace("<version>", version).replace("<chagelog_timestamp>", formatdate()), end='')

    def test(self):
        print('No tests available')


setup(
    name=project,
    version=version,
    author='Matt Doiron',
    author_email='mattdoiron@gmail.com',
    url='https://github.com/mattdoiron/idfplus/',
    description='Advanced editor for EnergyPlus simulation input files.',
    long_description_content_type='text/x-rst',
    long_description=readme + '\n\n' + changelog,
    keywords='idd idf energyplus idfplus idf+ energy+',
    packages=packages,
    platforms='any',
    license='GPL3',
    zip_safe=False,
    install_requires=requires,
    setup_requires=requires_setup,
    tests_require=requires_test,
    python_requires=">=3.10",
    classifiers=[
        'Programming Language :: Python :: 3.10',
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
    project_urls={
        'Bug Reports': 'https://github.com/mattdoiron/idfplus/issues',
        'Source': 'https://github.com/mattdoiron/idfplus/',
        'Releases': 'https://github.com/mattdoiron/idfplus/releases',
    },
    entry_points={
        'gui_scripts': [
            'idfplus=idfplus.__main__:main',
        ],
    },
    cmdclass={
        'freeze': Freeze,
        'make_installer': bdist_msi if sys.platform.startswith('win') else bdist_deb,
        'harvest': Harvest,
        'test': PyTest,
    },
)
