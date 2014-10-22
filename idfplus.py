#!/usr/bin/python
# -*- coding: utf-8 -*-
""""
Copyright (c) 2014, Matthew Doiron All rights reserved.

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

# Standard library imports
import sys

# PySide imports
from PySide import QtGui

# Local imports
from idfplus import logger
from idfplus.main import IDFPlus
from idfplus import idfsettings

# Setup logging
log = logger.setup_logging(idfsettings.LOG_LEVEL, 'IDFPlus')


def main():
    """Main function to start the program."""

    # Retrieve the currently running instance or make a new one
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication(sys.argv)

    import faulthandler
    faulthandler.enable()

    # Create the main window and show it
    idf_plus_window = IDFPlus()
    idf_plus_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    log.info('Launching IDFPlus')
    main()
