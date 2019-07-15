from __future__ import absolute_import, division, print_function

from glue_jupyter.view import IPyWidgetView
from glue_jupyter.link import link
from glue_jupyter.widgets import LinkedDropdown, Color, Size

from .layer_artist import WWTLayer
from .options_widget import WWTOptionPanel
from .state import WWTDataViewerState, MODES_BODIES, MODES_3D, CELESTIAL_FRAMES
from .layer_style_editor import WWTLayerStyleEditor
from pywwt.jupyter import WWTJupyterWidget
from ipywidgets import HBox, Tab, VBox, Dropdown, FloatSlider, Button


class JupterViewerOptions(VBox):
    def __init__(self, viewer_state, available_layers):

        self.state = viewer_state

        self.widget_mode = Dropdown(   options=['Sky']+MODES_BODIES+MODES_3D,
                                       value=self.state.mode,
                                       description='Mode:')
        link((self.widget_mode, 'value'), (self.state, 'mode'))

        self.widget_frame = Dropdown (options = CELESTIAL_FRAMES,
                                      value = self.state.frame,
                                      description = "Frame:")
        link((self.widget_frame, 'value'), (self.state, 'frame'))

        self.widget_ra = LinkedDropdown(self.state, "lon_att", label="RA:")

        self.widget_dec = LinkedDropdown(self.state, "lat_att", label="Dec:")


        self.widget_foreground = Dropdown(   options=available_layers,
                                       value=self.state.foreground,
                                       description='Forground:')
        link((self.widget_foreground, 'value'), (self.state, 'foreground'))

        self.widget_foreground_opacity = FloatSlider(description = "Opacity:", min = 0, max = 1,
                                                     value = self.state.foreground_opacity, step = 0.01 )
        link((self.widget_foreground_opacity, 'value'), (self.state, 'foreground_opacity'))

        self.widget_background = Dropdown(   options=available_layers,
                                       value=self.state.background,
                                       description='Background:')
        link((self.widget_background, 'value'), (self.state, 'background'))

        super().__init__([self.widget_mode, self.widget_frame, self.widget_ra, self.widget_dec, self.widget_foreground,
                          self.widget_foreground_opacity, self.widget_background])

class JupyterLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state
        self.color_widgets = Color(state = self.state)
        self.size_widgets = Size(state = self.state)
        self.recenter_widget = Button(description='Center view on layer')
        #self.recenter_widget.on_click(viewer_state.)
        super().__init__([self.size_widgets, self.color_widgets])

class WWTJupyterViewer(IPyWidgetView):
    _state_cls = WWTDataViewerState
    _data_artist_cls = WWTLayer
    _subset_artist_cls = WWTLayer
    _layer_style_widget_cls = JupyterLayerOptions
    def __init__(self, session, state=None):

        super(WWTJupyterViewer, self).__init__(session, state=state)

        self._wwt_client = WWTJupyterWidget()
        self._wwt_client.actual_planet_scale = True

        self.state.imagery_layers = list(self._wwt_client.available_layers)

        self.state.add_global_callback(self._update_wwt_client)

        self._update_wwt_client(force=True)
        self._layout_viewer_options = JupterViewerOptions(self.state, self.state.imagery_layers)
        #self._layout_layer_options = JupyterLayerOptions(self.state)
        self._layout_tab = Tab([self._layout_viewer_options,
                                self._layout_layer_options])
        self._layout_tab.set_title(0, "General")
        self._layout_tab.set_title(1, "Layers")

        self._layout = HBox([self.figure_widget, self._layout_tab])


    def closeEvent(self, event):
        return super(WWTJupyterViewer, self).closeEvent(event)

    def redraw(self):
        self._update_wwt_client()

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
