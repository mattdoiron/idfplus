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

# PySide imports
from PySide import QtWebKit
from PySide import QtNetwork
from PySide import QtGui
from PySide import QtCore

# Setup logging
log = logging.getLogger(__name__)


class PDFViewer(QtWebKit.QWebView):
    # pdf_viewer_page = 'web/web/viewer.html'
    pdf_viewer_page = 'http://bigladdersoftware.com/epx/docs/8-4/input-output-reference/'

    def __init__(self, parent=None):
        super(PDFViewer, self).__init__(parent)
        self.settings = QtWebKit.QWebSettings.globalSettings()
        self.settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessFileUrls, True)
        self.settings.setAttribute(QtWebKit.QWebSettings.LocalContentCanAccessRemoteUrls, True)
        self.settings.setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
        nam = QtNetwork.QNetworkAccessManager()
        page = QtWebKit.QWebPage(self)
        page.setNetworkAccessManager(nam)
        self.setPage(page)
        self.loadFinished.connect(self.onLoadFinish)
        self.setUrl(QtCore.QUrl(self.pdf_viewer_page))

    def onLoadFinish(self, success):
        if success:
            self.page().mainFrame().evaluateJavaScript("init();")


class HelpWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(HelpWindow, self).__init__(*args, **kwargs)
        self.web_view = PDFViewer(self)

        self.setWindowTitle(self.web_view.title())
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.setCentralWidget(self.web_view)
