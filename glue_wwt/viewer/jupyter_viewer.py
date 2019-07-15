from __future__ import absolute_import, division, print_function

from glue_jupyter.view import IPyWidgetView

from .layer_artist import WWTLayer
from .options_widget import WWTOptionPanel
from .state import WWTDataViewerState
from .layer_style_editor import WWTLayerStyleEditor
from pywwt.jupyter import WWTJupyterWidget
from ipywidgets import HBox, Tab, VBox, Output


class WWTJupyterViewer(IPyWidgetView):
    _state_cls = WWTDataViewerState
    _data_artist_cls = WWTLayer
    _subset_artist_cls = WWTLayer
    def __init__(self, session, state=None):

        super(WWTJupyterViewer, self).__init__(session, state=state)

        self._wwt_client = WWTJupyterWidget()
        self._wwt_client.actual_planet_scale = True

        self.state.imagery_layers = list(self._wwt_client.available_layers)

        self.state.add_global_callback(self._update_wwt_client)

        self._update_wwt_client(force=True)
        self._layout = VBox([self.figure_widget])


    def closeEvent(self, event):
        return super(WWTJupyterViewer, self).closeEvent(event)

    @property
    def figure_widget(self):
        return self._wwt_client


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
