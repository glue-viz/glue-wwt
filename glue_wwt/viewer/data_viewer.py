from __future__ import absolute_import, division, print_function

from glue.viewers.common.qt.data_viewer import DataViewer

from .layer_artist import WWTLayer
from .options_widget import WWTOptionPanel
from .state import WWTDataViewerState
from .layer_style_editor import WWTLayerStyleEditor

# We import the following to register the save tool
from . import tools  # noqa

from pywwt.qt import WWTQtClient

__all__ = ['WWTDataViewer']


class WWTDataViewer(DataViewer):

    LABEL = 'WorldWideTelescope (WWT)'

    _state_cls = WWTDataViewerState
    _data_artist_cls = WWTLayer
    _subset_artist_cls = WWTLayer

    _options_cls = WWTOptionPanel
    _layer_style_widget_cls = WWTLayerStyleEditor

    large_data_size = 100

    if hasattr(WWTQtClient, 'save_as_html_bundle'):
        save_tools = ['wwt:save_image', 'wwt:save_html']
    else:
        save_tools = ['wwt:save_image']
    subtools = {'save': save_tools}

    def __init__(self, session, parent=None, state=None):

        super(WWTDataViewer, self).__init__(session, parent=parent, state=state)

        self._wwt_client = WWTQtClient()
        self._wwt_client.actual_planet_scale = True

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

        if force or 'mode' in kwargs:
            self._wwt_client.set_view(self.state.mode)
            # Only show SDSS data when in Universe mode
            self._wwt_client.solar_system.cosmos = self.state.mode == 'Universe'
            # Only show local stars when not in Universe or Milky Way mode
            self._wwt_client.solar_system.stars = self.state.mode not in ['Universe', 'Milky Way']

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
