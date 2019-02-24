#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module that handles help widgets

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

# # System imports
# import logging
#
# # PySide imports
# from PySide import QtWebKit
# from PySide import QtGui
# from PySide import QtCore
#
# # Setup logging
# log = logging.getLogger(__name__)
#
#
# class WebViewer(QtWebKit.QWebView):
#
#     def __init__(self, parent=None):
#         super(WebViewer, self).__init__(parent)
#         self.settings = QtWebKit.QWebSettings.globalSettings()
#         # self.settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessFileUrls, True)
#         # self.settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessRemoteUrls, True)
#         self.settings.setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
#
#
# class HelpWindow(QtGui.QMainWindow):
#
#     def __init__(self, *args, **kwargs):
#         super(HelpWindow, self).__init__(*args, **kwargs)
#         self.web_view = WebViewer(self)
#         self.web_view.load(QtCore.QUrl('http://bigladdersoftware.com/epx/docs/8-6/index.html'))
#         self.setWindowTitle(self.web_view.title())
#         layout = QtGui.QHBoxLayout()
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self.web_view)
#         self.setLayout(layout)
#         self.setCentralWidget(self.web_view)
