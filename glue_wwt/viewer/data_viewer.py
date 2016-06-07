from __future__ import absolute_import, division, print_function

import numpy as np

from glue.viewers.common.qt.data_viewer import DataViewer
from glue.core.exceptions import IncompatibleAttribute

from glue.external.qt import QtCore
from glue.external.qt.QtCore import Qt
from glue.logger import logger
from PyQt4.QtWebKit import QWebView

from .layer_artist import circle, WWTLayer
from .options_widget import WWTOptionPanel
from .wwt_driver import WWTDriver

__all__ = ['WWTDataViewer']


class WWTDataViewer(DataViewer):

    LABEL = 'WorldWideTelescope (WWT)'

    run_js = QtCore.Signal(str)

    def __str__(self):
        return "WWTDataViewer"

    def __init__(self, session, parent=None, webdriver_class=None):
        super(WWTDataViewer, self).__init__(session, parent=parent)

        self.option_panel = WWTOptionPanel(self)

        # self._worker_thread = QtCore.QThread()

        self._browser = QWebView()
        self._browser.setUrl(QtCore.QUrl('http://localhost/~tom/wwt.html'))

        self._browser.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self._browser.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

        self._driver = WWTDriver(self._browser)

        self._ra = '_RAJ2000'
        self._dec = '_DEJ2000'

        # l = QtGui.QLabel("See browser")
        # pm = QtGui.QPixmap(":/wwt_icon.png")
        # size = pm.size()
        # l.setPixmap(pm)
        # l.resize(size)
        # w = QtGui.QWidget()
        # layout = QtGui.QHBoxLayout()
        # layout.addWidget(l)
        # layout.setContentsMargins(0, 0, 0, 0)
        # w.setLayout(layout)
        # w.setContentsMargins(0, 0, 0, 0)
        # w.resize(size)
        self.setCentralWidget(self._browser)
        self.resize(self._browser.size())
        self.setWindowTitle("WWT")

        self.run_js.connect(self._driver.run_js)

        self._update_foreground()
        self._update_background()

    def __contains__(self, layer):
        return layer in self._layer_artist_container

    def __len__(self):
        return len(self._layer_artist_container)

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

    def _update_foreground(self):
        self._run_js('wwt.setForegroundImageByName("%s");' % self.option_panel.foreground)

    def _update_background(self):
        self._run_js('wwt.setBackgroundImageByName("%s");' % self.option_panel.background)

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
        self._layer_artist_container.append(artist)
        assert len(self._layer_artist_container[layer]) > 0, self._layer_artist_container[layer]
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
        print('registering to hub')
        from glue.core import message as m
        super(WWTDataViewer, self).register_to_hub(hub)

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
                      lambda msg: self.add_subset(msg.subset))

    def _update_layer(self, layer):
        print('updating layer', layer)
        for a in self._layer_artist_container[layer]:
            print('updating', a)
            a.xatt = self.ra
            a.yatt = self.dec
            a.update()

    def _update_all(self):
        for l in self._layer_artist_container.layers:
            self._update_layer(l)

    def _remove_layer(self, layer):
        for l in self._layer_artist_container[layer]:
            print('removing')
            self._layer_artist_container.remove(l)
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

    wwt = WWTDataViewer(dc)
    wwt.show()
    app.exec_()


if __name__ == "__main__":
    main()
