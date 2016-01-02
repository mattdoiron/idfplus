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
import multiprocessing

# PySide imports
from PySide import QtGui
from PySide import QtCore

# Local imports
from idfplus.main import IDFPlus


def main():
    """Main function to start the program.
    """

    # Retrieve the currently running instance or make a new one
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication(sys.argv)

    # Create the main window and show it
    idf_plus_window = IDFPlus()
    idf_plus_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
