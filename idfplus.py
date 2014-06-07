#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, IDFPlus Inc. All rights reserved.

IDFPlus is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDFPlus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDFPlus. If not, see <http://www.gnu.org/licenses/>.
"""

# Prepare for Python 3
from __future__ import (print_function, division, with_statement, absolute_import)

# PySide import
import PySide
from PySide import QtGui
from PySide import QtCore

# Custom imports
import sys
from idfplus.idfplus import IDFPlus


def main():
    """Main function to start the program."""

    app = QtGui.QApplication(sys.argv)
#    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
#    app.setOrganizationName("IDF Plus Inc.")
#    app.setOrganizationDomain("idfplus.com")
#    app.setApplicationName("IDFPlus Editor")

    idf_plus_window = IDFPlus()
    idf_plus_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()