from __future__ import absolute_import, division, print_function

import os
from io import BytesIO
from collections import OrderedDict
from xml.etree.ElementTree import ElementTree

import requests
from glue.logger import logger

from qtpy.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, WEBENGINE
from qtpy import QtWidgets, QtCore

from .wwt_markers_helper import WWTMarkersHelper

__all__ = ['WWTQtWidget']

WWT_HTML_FILE = os.path.join(os.path.dirname(__file__), 'wwt.html')

with open(WWT_HTML_FILE) as f:
    WWT_HTML = f.read()

SURVEYS_URL = 'http://www.worldwidetelescope.org/wwtweb/catalog.aspx?W=surveys'


def get_imagery_layers():

    available_layers = OrderedDict()

    # Get the XML describing the available surveys
    response = requests.get(SURVEYS_URL)
    assert response.ok
    b = BytesIO(response.content)
    e = ElementTree()
    t = e.parse(b)

    # For now only look at the ImageSets at the root of the
    # XML since these seem to be the main surveys.
    for survey in t.findall('ImageSet'):
        name = survey.attrib['Name']
        thumbnail_url = survey.find('ThumbnailUrl').text
        if not thumbnail_url:
            thumbnail_url = None
        available_layers[name] = {'thumbnail': thumbnail_url}

    return available_layers


class WWTQWebEnginePage(QWebEnginePage):
    """
    Subclass of QWebEnginePage that can check when WWT is ready for
    commands.
    """

    wwt_ready = QtCore.Signal()

    def __init__(self, parent=None):
        super(WWTQWebEnginePage, self).__init__(parent=parent)
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_ready)
        self._timer.start(500)
        self._check_running = False
        if not WEBENGINE:
            self._frame = self.mainFrame()

    if WEBENGINE:

        def _wwt_ready_callback(self, result):
            if result == 1:
                self._timer.stop()
                self.wwt_ready.emit()
            self._check_running = False

        def javaScriptConsoleMessage(self, level=None, message=None, line_number=None, source_id=None):
            if not self._check_running or 'wwt_ready' not in message:
                print(message)

        def _check_ready(self):
            if not self._check_running:
                self._check_running = True
                self.runJavaScript('wwt_ready;', self._wwt_ready_callback)

    else:

        def runJavaScript(self, code):
            result = self._frame.evaluateJavaScript(code)
            return result

        def _check_ready(self):
            result = self.runJavaScript('wwt_ready;')
            if result == 1:
                self._timer.stop()
                self.wwt_ready.emit()


class WWTQtWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(WWTQtWidget, self).__init__(parent=parent)
        self.web = QWebEngineView()
        self.page = WWTQWebEnginePage()
        self.page.setView(self.web)
        self.web.setPage(self.page)
        self.web.setHtml(WWT_HTML)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.web)
        self.imagery_layers = get_imagery_layers()
        self.markers = WWTMarkersHelper(self)
        self._wwt_ready = False
        self._js_queue = ""
        self.page.wwt_ready.connect(self._on_wwt_ready)
        self._opacity = 50

    @property
    def foreground_opacity(self):
        return self._opacity

    @foreground_opacity.setter
    def foreground_opacity(self, value):
        if value < 0 or value > 100:
            raise ValueError('opacity should be in the range [0:100]')
        self._opacity = value
        self._update_opacity()

    def _update_opacity(self):
        self.run_js('wwt.setForegroundOpacity({0})'.format(self.foreground_opacity))

    @property
    def galactic(self):
        return self._galactic

    @galactic.setter
    def galactic(self, value):
        if not isinstance(value, bool):
            raise TypeError('galactic should be set to a boolean value')
        self.run_js('wwt.settings.set_galacticMode({0});'.format(str(value).lower()))

    @property
    def foreground(self):
        return self._foreground

    @foreground.setter
    def foreground(self, value):
        if value not in self.imagery_layers:
            raise ValueError('unknown foreground: {0}'.format(value))
        self.run_js('wwt.setForegroundImageByName("{0}");'.format(value))
        self._update_opacity()

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        if value not in self.imagery_layers:
            raise ValueError('unknown background: {0}'.format(value))
        self.run_js('wwt.setBackgroundImageByName("{0}");'.format(value))
        self._update_opacity()

    def _on_wwt_ready(self):
        self._wwt_ready = True
        self.run_js(self._js_queue)
        self._js_queue = ""

    def run_js(self, js):
        if not js:
            return
        if self._wwt_ready:
            logger.debug('Running javascript: %s' % js)
            self.page.runJavaScript(js)
        else:
            logger.debug('Caching javascript: %s' % js)
            self._js_queue += js + '\n'
