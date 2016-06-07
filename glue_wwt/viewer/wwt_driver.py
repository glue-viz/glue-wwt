from __future__ import absolute_import, division, print_function

from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from glue.external.qt import QtCore

__all__ = ['WWTDriver']


class WWTDriver(QtCore.QObject):

    def __init__(self, webdriver_class, parent=None):
        super(WWTDriver, self).__init__(parent)
        print("INIT WWTDriver")
        self._driver = None
        self._driver_class = webdriver_class or webdriver.Firefox
        self._last_opac = None
        self._opacity = 100
        self._opac_timer = QtCore.QTimer()

    def setup(self):
        print("SETUP WWTDriver")
        self._driver = self._driver_class()
        self._driver.get('http://127.0.0.1/~tom/wwt.html')
        # import time
        # time.sleep(10)

        self._opac_timer.timeout.connect(self._update_opacity)
        self._opac_timer.start(200)

    def set_opacity(self, value):
        self._opacity = value

    def _update_opacity(self):
        if self._opacity == self._last_opac:
            return
        self._last_opac = self._opacity
        js = 'wwt.setForegroundOpacity(%i)' % self._opacity
        self.run_js(js)

    def run_js(self, js, async=False):
        print("RUNNING JS", repr(js))
        if async:
            try:
                self._driver.execute_async_script(js)
            except TimeoutException:
                pass
        else:
            # print("WAITING 5 seconds")
            # import time
            # time.sleep(5)
            self._driver.execute_script(js)
            # import time
            # time.sleep(5)
