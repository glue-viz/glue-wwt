from __future__ import absolute_import, division, print_function

from glue_jupyter.view import IPyWidgetView
from glue_jupyter.link import link, dlink
from glue_jupyter.widgets import LinkedDropdown, Color, Size

from pywwt.jupyter import WWTJupyterWidget

from ipywidgets import HBox, Tab, VBox, FloatSlider, FloatText

from .data_viewer import WWTDataViewerBase
from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist


class JupterViewerOptions(VBox):
    def __init__(self, viewer_state, available_layers):

        self.state = viewer_state

        self.widget_mode = LinkedDropdown(self.state, "mode", label="Mode:")
        self.widget_frame = LinkedDropdown(self.state, "frame", label="Frame:")

        self.widget_ra = LinkedDropdown(self.state, "lon_att", label="RA:")
        self.widget_dec = LinkedDropdown(self.state, "lat_att", label="Dec:")

        self.widget_alt_type = LinkedDropdown(self.state, "alt_type", label="Height Type:")
        self.widget_alt = LinkedDropdown(self.state, "alt_att", label="Height Column:")
        self.widget_alt_unit = LinkedDropdown(self.state, "alt_unit", label="Height Unit:")
        self.alt_opts = VBox([self.widget_alt_type, self.widget_alt, self.widget_alt_unit])
        dlink((self.state, 'mode'), (self.alt_opts.layout, 'display'), lambda value: '' if value != 'Sky' else 'none')

        self.widget_foreground = LinkedDropdown(self.state, "foreground", label='Forground:')
        self.widget_foreground_opacity = FloatSlider(description="Opacity:", min=0, max=1,
                                                     value=self.state.foreground_opacity, step=0.01)
        link((self.widget_foreground_opacity, 'value'), (self.state, 'foreground_opacity'))
        self.widget_background = LinkedDropdown(self.state, 'background', label='Background:')
        self.widget_allskyimg = VBox([self.widget_foreground, self.widget_foreground_opacity, self.widget_background])
        dlink((self.state, 'mode'), (self.widget_allskyimg.layout, 'display'),
              lambda value: '' if value == 'Sky' else 'none')

        super().__init__([self.widget_mode, self.widget_frame, self.widget_ra,
                          self.widget_dec, self.alt_opts, self.widget_allskyimg])


class JupyterImageLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state

        self.data_att = LinkedDropdown(self.state, 'img_data_att', 'Component')

        if self.state.alpha is None:
            self.state.alpha = 1.0
        self.alpha = FloatSlider(description='alpha', min=0, max=1, value=self.state.alpha, step=0.01)
        link((self.state, 'alpha'), (self.alpha, 'value'))

        self.cmap = LinkedDropdown(self.state, 'cmap', 'Colormap')
        self.stretch = LinkedDropdown(self.state, 'stretch', 'Stretch')

        self.vmin = FloatText(description='Min Val')
        self.vmax = FloatText(description='Max Val')
        self.lims = VBox([self.vmin, self.vmax])
        link((self.state, 'vmin'), (self.vmin, 'value'), lambda value: value or 0)
        link((self.state, 'vmax'), (self.vmax, 'value'), lambda value: value or 1)

        super().__init__([self.data_att, self.alpha, self.cmap, self.stretch, self.lims])


class JupyterTableLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state
        self.color_widgets = Color(state=self.state)
        self.size_widgets = Size(state=self.state)

        # self.recenter_widget = Button(description='Center view on layer')
        # self.recenter_widget.on_click(viewer_state.)

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
