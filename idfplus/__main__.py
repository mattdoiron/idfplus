#!/usr/bin/python
# -*- coding: utf-8 -*-
""""Starup script for IDFPlus

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

#TODO from __feature__ import snake_case, true_property
# https://www.pythonguis.com/faq/pyside2-vs-pyside6/

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


def get_darkModePalette(app=None):
    # example of colour palettes
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, Qt.white)
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127), )

    return darkPalette


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
            # app.setPalette(get_darkModePalette(app))

        # Create the main window and show it
        idf_plus_window = IDFPlus(args=parsed_args)
        idf_plus_window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
