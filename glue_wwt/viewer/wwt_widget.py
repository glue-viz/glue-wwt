from __future__ import absolute_import, division, print_function

import os
import numpy as np
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from glue.viewers.common.qt.data_viewer import DataViewer
from glue.core.exceptions import IncompatibleAttribute

from glue.external.qt import QtCore, QtGui
from glue.external.qt.QtCore import Qt
from glue.external.six.moves.urllib.request import urlopen
from glue.logger import logger
from glue.utils.qt import load_ui

from .layer_artist import circle, WWTLayer


class WWTDriver(QtCore.QObject):
    def __init__(self, webdriver_class, parent=None):
        super(WWTDriver, self).__init__(parent)
        self._driver = None
        self._driver_class = webdriver_class or webdriver.Firefox
        self._last_opac = None
        self._opacity = 100
        self._opac_timer = QtCore.QTimer()

    def setup(self):
        self._driver = self._driver_class()
        self._driver.get('http://www.ifa.hawaii.edu/users/beaumont/wwt.html')
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
        print(js)
        if async:
            try:
                self._driver.execute_async_script(js)
            except TimeoutException:
                pass
        else:
            self._driver.execute_script(js)


class WWTWidget(DataViewer):
    run_js = QtCore.Signal(str)

    def __str__(self):
        return "WWTWidget"

    def __init__(self, session, parent=None, webdriver_class=None):
        super(WWTWidget, self).__init__(session, parent=parent)

        self.option_panel = QtGui.QWidget()
        self.ui = load_ui('wwt.ui', self.option_panel, directory=os.path.dirname(__file__))
        self._worker_thread = QtCore.QThread()

        self._driver = WWTDriver(webdriver_class)
        self._driver.moveToThread(self._worker_thread)
        self._worker_thread.start()
        self._driver.setup()

        self._ra = '_RAJ2000'
        self._dec = '_DEJ2000'

        l = QtGui.QLabel("See browser")
        pm = QtGui.QPixmap(":/icons/wwt_icon.png")
        size = pm.size()
        print(size)
        l.setPixmap(pm)
        l.resize(size)
        w = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        layout.addWidget(l)
        layout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(layout)
        w.setContentsMargins(0, 0, 0, 0)
        w.resize(size)
        self.setCentralWidget(w)
        self.resize(w.size())
        self.setWindowTitle("WWT")

        self._setup_combos()
        self._connect()

    def __contains__(self, layer):
        return layer in self._container

    def __len__(self):
        return len(self._container)

    @property
    def ra(self):
        return self._ra

    @ra.setter
    def ra(self, value):
        self._ra = value
        self._update_all()

    @property
    def dec(self):
        return self._dec

    @dec.setter
    def dec(self, value):
        self._dec = value
        self._update_all()

    def options_widget(self):
        return self.option_panel

    def _setup_combos(self):
        layers = ['Digitized Sky Survey (Color)',
                  'VLSS: VLA Low-frequency Sky Survey (Radio)',
                  'WMAP ILC 5-Year Cosmic Microwave Background',
                  'SFD Dust Map (Infrared)',
                  'WISE All Sky (Infrared)',
                  'GLIMPSE/MIPSGAL',
                  'Hydrogen Alpha Full Sky Map']
        labels = ['DSS',
                  'VLSS',
                  'WMAP',
                  'SFD',
                  'WISE',
                  'GLIMPSE',
                  'H Alpha']
        thumbnails = ['DSS',
                      'VLA',
                      'wmap5yr_ilc_200uk',
                      'dust',
                      'glimpsemipsgaltn',
                      'halpha']
        base = ('http://www.worldwidetelescope.org/wwtweb/'
                'thumbnail.aspx?name=%s')

        for i, row in enumerate(zip(layers, labels, thumbnails)):
            layer, text, thumb = row
            url = base % thumb
            data = urlopen(url).read()
            pm = QtGui.QPixmap()
            pm.loadFromData(data)
            icon = QtGui.QIcon(pm)
            self.ui.foreground.addItem(icon, text, layer)
            self.ui.foreground.setItemData(i, layer, role=Qt.ToolTipRole)
            self.ui.background.addItem(icon, text, layer)
            self.ui.background.setItemData(i, layer, role=Qt.ToolTipRole)
        self.ui.foreground.setIconSize(QtCore.QSize(60, 60))
        self.ui.background.setIconSize(QtCore.QSize(60, 60))

    def _connect(self):
        self.ui.foreground.currentIndexChanged.connect(self._update_foreground)
        self.ui.background.currentIndexChanged.connect(self._update_background)
        self.ui.opacity.valueChanged.connect(self._update_opacity)
        self.ui.opacity.setValue(100)
        self._update_foreground()
        self._update_background()
        self.run_js.connect(self._driver.run_js)

    def _update_foreground(self):
        layer = str(self.ui.foreground.itemData(
            self.ui.foreground.currentIndex()))
        self._run_js('wwt.setForegroundImageByName("%s");' % layer)

    def _update_background(self):
        layer = str(self.ui.background.itemData(
            self.ui.background.currentIndex()))
        self._run_js('wwt.setBackgroundImageByName("%s");' % layer)

    def _update_opacity(self, value):
        self._driver.set_opacity(value)

    def catalog(self, layer):
        logger.debug("adding %s" % layer.label)
        x = layer[self.ra]
        y = layer[self.dec]
        circles = []
        for i in range(x.size):
            label = "%s_%i" % (layer.label.replace(' ', '_').replace('.', '_'),
                               i)
            circles.append(circle(x[i], y[i], label, layer.style.color))
            circles.append("wwt.addAnnotation(%s);" % label)
        js = "\n".join(circles)
        xcen = x.mean()
        ycen = y.mean()
        fov = y.max() - y.min()
        self._run_js(js)
        self.move(xcen, ycen, fov)
        return True

    def add_data(self, data, center=True):
        print('add data')
        if data in self:
            return
        self._add_layer(data, center)

        for s in data.subsets:
            self.add_subset(s, center=False)
        return True

    def add_subset(self, subset, center=True):
        print('add subset')
        if subset in self:
            return
        self._add_layer(subset, center)
        return True

    def _add_layer(self, layer, center=True):
        if layer in self:
            return
        artist = WWTLayer(layer, self._driver)
        self._container.append(artist)
        assert len(self._container[layer]) > 0, self._container[layer]
        self._update_layer(layer)
        if center:
            self._center_on(layer)
        return True

    def _center_on(self, layer):
        """Center view on data"""
        try:
            x = np.median(layer[self.ra])
            y = np.median(layer[self.dec])
        except IncompatibleAttribute:
            return
        self.move(x, y)

    def register_to_hub(self, hub):
        from ...core import message as m
        super(WWTWidget, self).register_to_hub(hub)

        hub.subscribe(self, m.DataUpdateMessage,
                      lambda msg: self._update_layer(msg.sender),
                      lambda msg: msg.data in self)

        hub.subscribe(self, m.SubsetUpdateMessage,
                      lambda msg: self._update_layer(msg.sender),
                      lambda msg: msg.subset in self)

        hub.subscribe(self, m.DataCollectionDeleteMessage,
                      lambda msg: self._remove_layer(msg.data),
                      lambda msg: msg.data in self)

        hub.subscribe(self, m.SubsetDeleteMessage,
                      lambda msg: self._remove_layer(msg.subset),
                      lambda msg: msg.subset in self)

        hub.subscribe(self, m.SubsetCreateMessage,
                      lambda msg: self.add_subset(msg.subset),
                      lambda msg: msg.subset.data in self)

    def _update_layer(self, layer):
        print('updating layer', layer)
        for a in self._container[layer]:
            print('updating', a)
            a.xatt = self.ra
            a.yatt = self.dec
            a.update()

    def _update_all(self):
        for l in self._container.layers:
            self._update_layer(l)

    def _remove_layer(self, layer):
        for l in self._container[layer]:
            print('removing')
            self._container.remove(l)
        assert layer not in self

    def unregister(self, hub):
        hub.unsubscribe_all(self)

    def _run_js(self, js):
        self.run_js.emit(js)

    def move(self, ra, dec, fov=60):
        js = "wwt.gotoRaDecZoom(%f, %f, %f, true);" % (ra, dec, fov)
        self._run_js(js)


def main():

    from glue.core import Data, DataCollection
    from glue.qt import get_qapp
    import numpy as np

    app = get_qapp()

    d = Data(label="data", _RAJ2000=np.random.random((100)) + 0,
             _DEJ2000=np.random.random((100)) + 85)
    dc = DataCollection([d])

    wwt = WWTWidget(dc)
    wwt.show()
    app.exec_()


if __name__ == "__main__":
    main()
