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

# Standard library imports
import sys
import os
import faulthandler
import argparse

# PySide imports
from PySide import QtGui

# Local imports
from . import config
from .main import IDFPlus


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?', default=None)
    return parser.parse_known_args()


def main():
    """Main function to start the program.
    """

    with open(os.path.join(config.LOG_DIR, 'idfplus_error_dump.txt'), 'w') as f:
        faulthandler.enable(file=f)

        # Parse command-line arguments
        parsed_args, unparsed_args = process_args()
        qt_args = sys.argv[:1] + unparsed_args

        # Retrieve the currently running instance or make a new one
        app = QtGui.QApplication.instance()
        if app is None:
            app = QtGui.QApplication(qt_args)

        # Create the main window and show it
        idf_plus_window = IDFPlus(args=parsed_args)
        idf_plus_window.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
