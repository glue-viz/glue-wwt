from __future__ import absolute_import, division, print_function

import os
import numpy as np

from glue.viewers.common.qt.data_viewer import DataViewer
from glue.core.exceptions import IncompatibleAttribute
from glue.logger import logger

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWebEngineWidgets import QWebEngineView

from .layer_artist import circle, WWTLayer
from .options_widget import WWTOptionPanel
from .wwt_driver import WWTDriver
from glue.viewers.common.qt.toolbar import BasicToolbar

__all__ = ['WWTDataViewer']


class WWTDataViewer(DataViewer):

    LABEL = 'WorldWideTelescope (WWT)'
    _toolbar_cls = BasicToolbar

    run_js = QtCore.Signal(str)

    def __str__(self):
        return "WWTDataViewer"

    def __init__(self, session, parent=None, webdriver_class=None):
        super(WWTDataViewer, self).__init__(session, parent=parent)

        self._browser = QWebEngineView()
        url = QtCore.QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), 'wwt.html'))
        self._browser.setUrl(url)

        # self._browser.page().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        # self._browser.page().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

        self._driver = WWTDriver(self._browser)

        self.option_panel = WWTOptionPanel(self)

        self.setCentralWidget(self._browser)
        self.resize(self._browser.size())
        self.setWindowTitle("WWT")

        self.run_js.connect(self._driver.run_js)

        self._browser.page().loadFinished.connect(self._on_load_finish)

    def _on_load_finish(self, event):
        self._update_foreground()
        self._update_background()
        self._update_opacity(100)

    def __contains__(self, layer):
        return layer in self._layer_artist_container

    def __len__(self):
        return len(self._layer_artist_container)

    def options_widget(self):
        return self.option_panel

    def catalog(self, layer):
        logger.debug("adding %s" % layer.label)
        x = layer[self.option_panel.ra]
        y = layer[self.option_panel.dec]
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
        if data in self:
            return
        self._add_layer(data, center)

        for s in data.subsets:
            self.add_subset(s, center=False)

        self.option_panel.add_data(data)

        return True

    def add_subset(self, subset, center=True):
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
            x = np.median(layer[self.option_panel.ra])
            y = np.median(layer[self.option_panel.dec])
        except IncompatibleAttribute:
            return
        self.move(x, y)

    def register_to_hub(self, hub):
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
        for a in self._layer_artist_container[layer]:
            a.xatt = self.option_panel.ra
            a.yatt = self.option_panel.dec
            a.update()

    def _update_all(self):
        for l in self._layer_artist_container.layers:
            self._update_layer(l)

    def _remove_layer(self, layer):
        for l in self._layer_artist_container[layer]:
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
    from glue.utils.qt import get_qapp
    from glue.core.session import Session
    import numpy as np

    app = get_qapp()

    d = Data(label="data", _RAJ2000=np.random.random((100)) + 0,
             _DEJ2000=np.random.random((100)) + 85)
    dc = DataCollection([d])
    session = Session(data_collection=dc)

    wwt = WWTDataViewer(session)
    wwt.show()
    app.exec_()


if __name__ == "__main__":
    main()
