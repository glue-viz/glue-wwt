from __future__ import absolute_import, division, print_function

from glue.external.qt import QtCore

__all__ = ['WWTDriver']


class WWTDriver(object):

    def __init__(self, browser, parent=None):
        self._browser = browser
        self._frame = self._browser.page().mainFrame()
        self._last_opac = None
        self._opacity = 100
        self._opac_timer = QtCore.QTimer()
        self._opac_timer.timeout.connect(self._update_opacity)
        self._opac_timer.start(200)

    def set_opacity(self, value):
        self._opacity = value

    def set_galactic_plane_mode(self, mode):
        js = 'wwt.settings.set_galacticMode({0});'.format(str(mode).lower())
        self.run_js(js)

    def _update_opacity(self):
        if self._opacity == self._last_opac:
            return
        self._last_opac = self._opacity
        js = 'wwt.setForegroundOpacity(%i)' % self._opacity
        self.run_js(js)

    def run_js(self, js, async=False):
        self._frame.evaluateJavaScript(js)
