#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
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

# System imports
import logging
import logging.handlers

# PySide imports
from PySide.QtCore import Signal
from PySide.QtCore import QObject


def setup_logging(_level, name, log_path):
    """Sets up and configures the logger

    :rtype: logging.logger
    :param _level: 
    :param name:
    :param log_path:
    """

    # Setup log level, path and formatters
    level = getattr(logging, _level)
    _format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(_format)

    # Setup handler for on-disk log file
    file_handler = logging.handlers.RotatingFileHandler(log_path,
                                                        mode='w',
                                                        maxBytes=2000000,
                                                        backupCount=5)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Setup handler for in-app log viewer
    stream_handler = ConsoleLogHandler(level)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    # Setup logger
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(file_handler)
    log.addHandler(stream_handler)

    return log


class Communicate(QObject):
    """Create a new signal on the fly and name it 'speak'
    """

    signal = Signal(str)


class ConsoleLogHandler(logging.StreamHandler):
    """Handles console log
    """

    com = Communicate()

    def emit(self, record):
        """

        :param record:
        :raise:
        """

        try:
            self.com.signal.emit(self.format(record))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
