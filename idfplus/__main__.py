#!/usr/bin/python
# -*- coding: utf-8 -*-
""""Starup script for IDFPlus

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# Standard library imports
import sys
import os
import faulthandler
import argparse

# PySide imports
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

# Local imports
from idfplus import __version__ as version
from idfplus import config
from idfplus.main import IDFPlus


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
        app = QApplication.instance()
        if app is None:
            app = QApplication(qt_args)
            app.setApplicationName("IDF+ Editor")
            app.setApplicationVersion(version)


            # setup stylesheet
            # apply_stylesheet(app, theme='dark_teal.xml')
            # app.setPalette(get_darkModePalette(app))

        # Create the main window and show it
        idf_plus_window = IDFPlus(args=parsed_args)
        idf_plus_window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
