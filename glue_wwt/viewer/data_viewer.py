from __future__ import absolute_import, division, print_function

from glue.viewers.common.qt.data_viewer import DataViewer

from .layer_artist import WWTLayer
from .options_widget import WWTOptionPanel
from .state import WWTDataViewerState
from .layer_style_editor import WWTLayerStyleEditor
from .wwt_markers_helper import WWTMarkersHelper

# We import the following to register the save tool
from . import tools  # noqa

__all__ = ['WWTDataViewer']


class WWTDataViewer(DataViewer):

    LABEL = 'WorldWideTelescope (WWT)'

    _state_cls = WWTDataViewerState
    _data_artist_cls = WWTLayer
    _subset_artist_cls = WWTLayer

    _options_cls = WWTOptionPanel
    _layer_style_widget_cls = WWTLayerStyleEditor

    large_data_size = 100

    subtools = {'save': ['wwt:save']}

    def __init__(self, session, parent=None, state=None):

        super(WWTDataViewer, self).__init__(session, parent=parent)

        from pywwt.qt import WWTQtClient
        self._wwt_client = WWTQtClient()
        self._wwt_client.actual_planet_scale = True

        self._wwt_client.markers = WWTMarkersHelper(self._wwt_client)

        self.setCentralWidget(self._wwt_client.widget)
        self.resize(self._wwt_client.widget.size())
        self.setWindowTitle("WorldWideTelescope")

        self.state.imagery_layers = list(self._wwt_client.available_layers)

        self.state.add_global_callback(self._update_wwt_client)

        self.options_widget().setEnabled(False)
        self.layer_view().setEnabled(False)

        self._wwt_client.widget.page.wwt_ready.connect(self._on_wwt_ready)

        self._update_wwt_client(force=True)

    def closeEvent(self, event):
        self._wwt_client.widget.close()
        return super(WWTDataViewer, self).closeEvent(event)

    def _on_wwt_ready(self):
        self.options_widget().setEnabled(True)
        self.layer_view().setEnabled(True)

    def _update_wwt_client(self, force=False, **kwargs):

        if force or 'foreground' in kwargs:
            self._wwt_client.foreground = self.state.foreground

        if force or 'background' in kwargs:
            self._wwt_client.background = self.state.background

        if force or 'foreground_opacity' in kwargs:
            self._wwt_client.foreground_opacity = self.state.foreground_opacity

        if force or 'galactic' in kwargs:
            self._wwt_client.galactic_mode = self.state.galactic

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        return cls(self._wwt_client, self.state, layer=layer, layer_state=layer_state)
