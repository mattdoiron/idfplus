#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Logging module

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# System imports
import logging
import logging.handlers
import sys

# PySide2 imports
from PySide2.QtCore import Signal, QObject


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
    console_handler = ConsoleLogHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Setup logger
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(file_handler)
    log.addHandler(console_handler)
    log.addHandler(logging.NullHandler())

    # Duplicate stderr to log file also
    sys.stderr = StdErrToLogger(log)

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


class StdErrToLogger(object):
    """File-like object that redirects a duplicate stderr message to logger.
    """

    def __init__(self, logger, log_level=logging.ERROR):
        self.logger = logger
        self.log_level = log_level
        self.std_err = sys.stderr
        sys.stderr = self

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if line != "\n" and line:
                self.logger.log(self.log_level, line.strip())
                self.std_err.write(buf)

    def flush(self):
        self.std_err.flush()
