# !/usr/bin/python
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
from __future__ import (print_function, division, absolute_import)

# System imports
import os

# System imports
import logging
import logging.handlers

# Package imports
from . import idfsettings


def setup_logging(_level, name):
    """Sets up and configures the logger
    :rtype : logging.logger
    :param _level: 
    :param name: 
    :param silent: 
    """

    level = getattr(logging, _level)

    # Setup handler and formatter
    log_file = os.path.join(idfsettings.APP_ROOT, 'data', 'logs', 'idfplus.log')
    handler = logging.handlers.RotatingFileHandler(log_file,
                                                   maxBytes=2000000,
                                                   backupCount=5)
    handler.setLevel(level)
    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_)
    handler.setFormatter(formatter)

    # Setup logger
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)

    return log