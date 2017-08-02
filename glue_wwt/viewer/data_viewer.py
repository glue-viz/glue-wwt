from __future__ import absolute_import, division, print_function

from glue.viewers.common.qt.data_viewer import DataViewer
from glue.core import message as m

from .layer_artist import WWTLayer
from .options_widget import WWTOptionPanel
from .wwt_widget import WWTQtWidget
from glue.viewers.common.qt.toolbar import BasicToolbar
from .state import WWTDataViewerState
from .layer_style_editor import WWTLayerStyleEditor

__all__ = ['WWTDataViewer']


class WWTDataViewer(DataViewer):

    LABEL = 'WorldWideTelescope (WWT)'
    _toolbar_cls = BasicToolbar
    _layer_style_widget_cls = WWTLayerStyleEditor

    def __init__(self, session, parent=None, state=None):

        super(WWTDataViewer, self).__init__(session, parent=parent)

        self._wwt_widget = WWTQtWidget()
        self.setCentralWidget(self._wwt_widget)
        self.resize(self._wwt_widget.size())
        self.setWindowTitle("WorldWideTelescope")

        self.state = state or WWTDataViewerState()
        self.state.set_imagery_layers(list(self._wwt_widget.imagery_layers))

        self.option_panel = WWTOptionPanel(self.state)

        self.state.add_global_callback(self._update_wwt_widget)

        self.option_panel.setEnabled(False)
        self._view.setEnabled(False)
        self._wwt_widget.page.wwt_ready.connect(self._on_wwt_ready)

        self._update_wwt_widget(force=True)

    def _on_wwt_ready(self):
        self.option_panel.setEnabled(True)
        self._view.setEnabled(True)

    def _update_wwt_widget(self, force=False, **kwargs):

        if force or 'foreground' in kwargs:
            self._wwt_widget.foreground = self.state.foreground

        if force or 'background' in kwargs:
            self._wwt_widget.background = self.state.background

        if force or 'foreground_opacity' in kwargs:
            self._wwt_widget.foreground_opacity = self.state.foreground_opacity

        if force or 'galactic' in kwargs:
            self._wwt_widget.galactic = self.state.galactic

    def options_widget(self):
        return self.option_panel

    def add_data(self, data, center=True):
        if data in self._layer_artist_container:
            return
        self._add_layer(data, center)
        for s in data.subsets:
            self.add_subset(s, center=False)
        return True

    def add_subset(self, subset, center=True):
        if subset in self._layer_artist_container:
            return
        self._add_layer(subset, center)
        return True

    def _add_layer(self, layer, center=True):
        if layer in self._layer_artist_container:
            return
        artist = WWTLayer(self._wwt_widget, self.state, layer=layer)
        self._layer_artist_container.append(artist)
        return True

    def register_to_hub(self, hub):

        super(WWTDataViewer, self).register_to_hub(hub)

        hub.subscribe(self, m.DataUpdateMessage,
                      lambda msg: self._update_layer(msg.sender),
                      lambda msg: msg.data in self._layer_artist_container)

        hub.subscribe(self, m.SubsetUpdateMessage,
                      lambda msg: self._update_layer(msg.sender),
                      lambda msg: msg.subset in self._layer_artist_container)

        hub.subscribe(self, m.DataCollectionDeleteMessage,
                      lambda msg: self._remove_layer(msg.data),
                      lambda msg: msg.data in self._layer_artist_container)

        hub.subscribe(self, m.SubsetDeleteMessage,
                      lambda msg: self._remove_layer(msg.subset),
                      lambda msg: msg.subset in self._layer_artist_container)

        hub.subscribe(self, m.SubsetCreateMessage,
                      lambda msg: self.add_subset(msg.subset),
                      lambda msg: msg.subset.data in self._layer_artist_container)

    def _update_layer(self, layer):
        for a in self._layer_artist_container[layer]:
            a.update(force=True)

    def _remove_layer(self, layer):
        for l in self._layer_artist_container[layer]:
            self._layer_artist_container.remove(l)

    def unregister(self, hub):
        hub.unsubscribe_all(self)
