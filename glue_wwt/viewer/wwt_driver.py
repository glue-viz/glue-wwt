from __future__ import absolute_import, division, print_function

import os
import random

from glue.logger import logger

from qtpy.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from qtpy import QtWidgets, QtCore

__all__ = ['WWTQtWidget']

WWT_HTML_FILE = os.path.join(os.path.dirname(__file__), 'wwt.html')

LAYERS = {'DSS': {'name': 'Digitized Sky Survey (Color)',
                  'thumbnail': 'DSS'},
          'VLSS': {'name': 'VLSS: VLA Low-frequency Sky Survey (Radio)',
                   'thumbnail': 'VLA'},
          'WMAP': {'name': 'WMAP ILC 5-Year Cosmic Microwave Background',
                   'thumbnail': 'wmap5yr_ilc_200uk'},
          'SFD': {'name': 'SFD Dust Map (Infrared)',
                  'thumbnail': 'dust'},
          # 'WISE': {'name': 'WISE  Sky (Infrared)',
          #          'thumbnail': ???},
          'GLIMPSE': {'name': 'GLIMPSE/MIPSGAL',
                      'thumbnail': 'glimpsemipsgaltn'},
          'H Alpha': {'name': 'Hydrogen Alpha Full Sky Map',
                      'thumbnail': 'halpha'}}


CIRCLE_JS = """
{label:s} = wwt.createCircle("{color:s}");
{label:s}.setCenter({ra:f}, {dec:f});
{label:s}.set_fillColor("{color:s}");
{label:s}.set_radius({radius:d});
wwt.addAnnotation({label:s});
"""


class WWTMarkerCollection(object):

    def __init__(self, wwt_widget=None):
        self.wwt_widget = wwt_widget
        self.markers = {}
        self.layer_id = "{0:08x}".format(random.getrandbits(32))
        self.labels = []

    def draw(self, skycoord, color, radius=3):

        skycoord_icrs = skycoord.icrs
        ra = skycoord_icrs.ra.degree
        dec = skycoord_icrs.dec.degree

        js_code = ""

        for i in range(ra.size):
            label = "marker_{0}_{1}".format(self.layer_id, i)
            js_code += CIRCLE_JS.format(ra=ra[i], dec=dec[i],
                                        label=label, color=color,
                                        radius=radius)
            self.labels.append(label)

        self.wwt_widget.run_js(js_code)

    def clear(self):
        js_code = '\n'.join("wwt.removeAnnotation({0});".format(l)
                            for l in self.labels)
        self.wwt_widget.run_js(js_code)


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
        self._callback = False
        self._check_running = False
        self._console = ''

    def _js_callback(self, result):
        print("CALLBACK", repr(result))
        self._callback = True

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        self._console += message + '\n'

    def _check_ready(self):
        if self._check_running:
            if self._callback:
                if 'wwt is not defined' in self._console:
                    self._console = ''
                    self._callback = False
                    self.runJavaScript('wwt;', self._js_callback)
                else:
                    self._check_running = False
                    self._timer.stop()
                    self.wwt_ready.emit()
        else:
            self._check_running = True
            self.runJavaScript('wwt;', self._js_callback)


class WWTQtWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(WWTQtWidget, self).__init__(parent=parent)
        self.web = QWebEngineView()
        self.page = WWTQWebEnginePage()
        self.page.setView(self.web)
        self.web.setPage(self.page)
        url = QtCore.QUrl.fromLocalFile(WWT_HTML_FILE)
        self.web.setUrl(url)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.web)
        # self.javaScriptConsoleMessage.connect(self._console_log)

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        if value < 0 or value > 100:
            raise ValueError('opacity should be in the range [0:100]')
        self.run_js('wwt.setForegroundOpacity({0})'.format(value))
        self._opacity = value

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
        if value not in LAYERS:
            raise ValueError('unknown foreground: {0}'.format(value))
        self.run_js('wwt.setForegroundImageByName("{0}");'.format(LAYERS[value]['name']))

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        if value not in LAYERS:
            raise ValueError('unknown background: {0}'.format(value))
        self.run_js('wwt.setBackgroundImageByName("{0}");'.format(LAYERS[value]['name']))

    def run_js(self, js, async=False):
        print("Running javascript: %s" % js)
        logger.debug("Running javascript: %s" % js)
        self.page.runJavaScript(js)
