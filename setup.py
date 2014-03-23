#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import idfplus


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

setup(
    name='idfplus',
    version=idfplus.__version__,
    url='http://google.ca/',
    license='GPL v3.0',
    author='Matt Doiron',
    install_requires=['PySide>=1.2.1'],
    cmdclass={'test': PyTest},
    author_email='mattdoiron@gmail.com',
    description='Advanced editor for EnergyPlus simulation files.',
    long_description=read('README.txt', 'CHANGES.txt'),
    packages=['idfplus'],
    include_package_data=True,
    platforms='any',
    license='LICENSE.txt',
    test_suite='idfplus.test.test_idfplus',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 2 - Pre-Alpha',
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
