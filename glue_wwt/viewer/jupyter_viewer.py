from __future__ import absolute_import, division, print_function

from glue_jupyter.view import IPyWidgetView
from glue_jupyter.link import link
from glue_jupyter.widgets import LinkedDropdown, Color, Size

from pywwt.jupyter import WWTJupyterWidget
from pywwt.layers import VALID_STRETCHES

from ipywidgets import HBox, Tab, VBox, Dropdown, FloatSlider, Button

from .data_viewer import WWTDataViewerBase
from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist
from .viewer_state import WWTDataViewerState, MODES_BODIES, MODES_3D, CELESTIAL_FRAMES


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


class JupyterImageLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state

        self.data_att = LinkedDropdown(self.state, 'img_data_att', 'Component')

        if self.state.alpha is None:
            self.state.alpha = 1.0
        self.alpha = FloatSlider(description='alpha', min=0, max=1, value=self.state.alpha)
        link((self.state, 'alpha'), (self.alpha, 'value'))

        self.stretch = LinkedDropdown(self.state, 'stretch', 'Stretch')
        
        super().__init__([self.data_att, self.alpha])


class JupyterTableLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state
        self.color_widgets = Color(state = self.state)
        self.size_widgets = Size(state = self.state)

        #self.recenter_widget = Button(description='Center view on layer')
        #self.recenter_widget.on_click(viewer_state.)

        super().__init__([self.size_widgets, self.color_widgets])


class WWTJupyterViewer(WWTDataViewerBase, IPyWidgetView):
    _layer_style_widget_cls = {
        WWTImageLayerArtist: JupyterImageLayerOptions,
        WWTTableLayerArtist: JupyterTableLayerOptions,
    }

    def __init__(self, session, state=None):
        IPyWidgetView.__init__(self, session, state=state)
        WWTDataViewerBase.__init__(self)

        # In Glue+Jupyter Notebook, we need to explicitly specify this to get
        # the widget to fill up the horizontal space.
        self._wwt.layout.width = '100%'

        self._layout_viewer_options = JupterViewerOptions(self.state, self.state.imagery_layers)
        self._layout_tab = Tab([self._layout_viewer_options,
                                self._layout_layer_options])
        self._layout_tab.set_title(0, "General")
        self._layout_tab.set_title(1, "Layers")
        self._layout = HBox([self.figure_widget, self._layout_tab])


    def _initialize_wwt(self):
        self._wwt = WWTJupyterWidget()


    def redraw(self):
        self._update_wwt()


    @property
    def figure_widget(self):
        return self._wwt
