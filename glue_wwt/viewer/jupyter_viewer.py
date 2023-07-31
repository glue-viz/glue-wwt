from __future__ import absolute_import, division, print_function

from glue.utils import color2hex
from glue_jupyter.view import IPyWidgetView
from glue_jupyter.link import link, dlink
from glue_jupyter.widgets import LinkedDropdown, Color, Size

from pywwt.jupyter import WWTJupyterWidget

from ipywidgets import Accordion, Checkbox, ColorPicker, GridBox, HBox, Label, Layout, Tab, VBox, FloatSlider, FloatText

from .data_viewer import WWTDataViewerBase
from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist


class JupterViewerOptions(VBox):
    def __init__(self, viewer_state, available_layers):

        self.fit_content_layout = Layout(width="fit-content")

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

        self.widget_crosshairs = self.linked_checkbox('crosshairs', description="Show crosshairs")
        self.widget_galactic_plane_mode = self.linked_checkbox('galactic', description="Galactic Plane mode")

        self.general_settings = VBox(children=[self.widget_mode, self.widget_frame, self.widget_ra,
                                               self.widget_dec, self.alt_opts, self.widget_allskyimg,
                                               self.widget_crosshairs, self.widget_galactic_plane_mode])

        self.widget_alt_az_grid = self.linked_checkbox('alt_az_grid', description="Alt/Az")
        self.widget_alt_az_text = self.linked_checkbox('alt_az_text', description="Text")
        self.set_enabled_from_checkbox(self.widget_alt_az_text, self.widget_alt_az_grid)
        self.widget_alt_az_grid_color = self.linked_color_picker('alt_az_grid_color')
        self.set_enabled_from_checkbox(self.widget_alt_az_grid_color, self.widget_alt_az_grid)

        self.widget_ecliptic_grid = self.linked_checkbox('ecliptic_grid', description="Ecliptic")
        self.widget_ecliptic_text = self.linked_checkbox('ecliptic_text', description="Text")
        self.set_enabled_from_checkbox(self.widget_ecliptic_text, self.widget_ecliptic_grid)
        self.widget_ecliptic_grid_color = self.linked_color_picker('ecliptic_grid_color')
        self.set_enabled_from_checkbox(self.widget_ecliptic_grid_color, self.widget_ecliptic_grid)

        self.widget_equatorial_grid = self.linked_checkbox('equatorial_grid', "Equatorial")
        self.widget_equatorial_text = self.linked_checkbox('equatorial_text', "Text")
        self.set_enabled_from_checkbox(self.widget_equatorial_text, self.widget_equatorial_grid)
        self.widget_equatorial_grid_color = self.linked_color_picker('equatorial_grid_color')
        self.set_enabled_from_checkbox(self.widget_equatorial_grid_color, self.widget_equatorial_grid)

        self.widget_galactic_grid = self.linked_checkbox('galactic_grid', description="Galactic")
        self.widget_galactic_text = self.linked_checkbox('galactic_text', description="Text")
        self.set_enabled_from_checkbox(self.widget_galactic_text, self.widget_galactic_grid)
        self.widget_galactic_grid_color = self.linked_color_picker('galactic_grid_color')
        self.set_enabled_from_checkbox(self.widget_galactic_grid_color, self.widget_galactic_grid)

        self.grid_settings = GridBox(children=[self.widget_alt_az_grid, self.widget_alt_az_text,
                                               self.widget_alt_az_grid_color, self.widget_ecliptic_grid,
                                               self.widget_ecliptic_text, self.widget_ecliptic_grid_color,
                                               self.widget_equatorial_grid, self.widget_equatorial_text,
                                               self.widget_equatorial_grid_color, self.widget_galactic_grid,
                                               self.widget_galactic_text, self.widget_galactic_grid_color],
                                     layout=Layout(grid_template_columns="2fr 2fr 1fr", width="100%",
                                                   grid_gap="2px 10px"))

        self.widget_constellation_boundaries = LinkedDropdown(self.state, 'constellation_boundaries',
                                                              label="Boundaries:")
        self.widget_constellation_boundary_color = self.linked_color_picker('constellation_boundary_color',
                                                                            description="Boundary")
        dlink((self.widget_constellation_boundaries, 'value'), (self.widget_constellation_boundary_color, 'disabled'),
              lambda value: value != "All")
        self.widget_constellation_selection_color = self.linked_color_picker('constellation_selection_color',
                                                                             description="Selection")
        dlink((self.widget_constellation_boundaries, 'value'), (self.widget_constellation_selection_color, 'disabled'),
              lambda value: value == "None")

        self.widget_constellation_figures = self.linked_checkbox('constellation_figures', description="Figures")
        self.widget_constellation_figure_color = self.linked_color_picker('constellation_figure_color',
                                                                          description="Figure")
        self.set_enabled_from_checkbox(self.widget_constellation_figure_color, self.widget_constellation_figures)
        self.widget_constellation_labels = self.linked_checkbox('constellation_labels', description="Labels")
        self.widget_constellation_pictures = self.linked_checkbox('constellation_pictures', description="Pictures")

        constellations_hbox_layout = Layout(gap="10px", justify_content="space-between")
        constellations_vbox_layout = Layout(height="fit-content", gap="2px", padding="5px", flex_direction="column")
        self.constellation_checkboxes = HBox(children=[self.widget_constellation_pictures,
                                                       self.widget_constellation_labels,
                                                       self.widget_constellation_figures],
                                             layout=constellations_hbox_layout)

        self.constellation_colors = VBox(children=[self.widget_constellation_selection_color,
                                                   self.widget_constellation_boundary_color,
                                                   self.widget_constellation_figure_color],
                                         layout=constellations_vbox_layout)

        self.constellation_settings = VBox(children=[self.widget_constellation_boundaries,
                                                     self.constellation_checkboxes,
                                                     self.constellation_colors],
                                           layout=constellations_vbox_layout)

        self.widget_ecliptic_label = Label("Ecliptic:")
        self.widget_ecliptic = self.linked_checkbox('ecliptic', description="Show")
        self.widget_ecliptic_color = self.linked_color_picker('ecliptic_color')
        self.set_enabled_from_checkbox(self.widget_ecliptic_color, self.widget_ecliptic)

        self.widget_precession_chart_label = Label("Precession Chart:")
        self.widget_precession_chart = self.linked_checkbox('precession_chart', description="Show")
        self.widget_precession_chart_color = self.linked_color_picker('precession_chart_color')
        self.set_enabled_from_checkbox(self.widget_precession_chart_color, self.widget_precession_chart)

        self.other_settings = GridBox(children=[self.widget_ecliptic_label, self.widget_ecliptic,
                                                self.widget_ecliptic_color, self.widget_precession_chart_label,
                                                self.widget_precession_chart, self.widget_precession_chart_color],
                                      layout=Layout(grid_template_columns="5fr 1fr 1fr", width="100%",
                                                    grid_gap="2px 10px"))

        self.settings = Accordion(children=[self.general_settings, self.grid_settings,
                                            self.constellation_settings, self.other_settings],
                                  layout=Layout(width="350px"))
        self.settings.set_title(0, "General")
        self.settings.set_title(1, "Grids")
        self.settings.set_title(2, "Constellations")
        self.settings.set_title(3, "Other")
        self.settings.selected_index = 0

        super().__init__([self.settings])

    def linked_checkbox(self, attr, description=''):
        widget = Checkbox(getattr(self.state, 'attr', False), description=description,
                          indent=False, layout=self.fit_content_layout)
        link((self.state, attr), (widget, 'value'))
        return widget

    def linked_color_picker(self, attr, description=''):
        widget = ColorPicker(concise=True, layout=self.fit_content_layout, description=description)
        link((self.state, attr), (widget, 'value'), color2hex)
        return widget

    @staticmethod
    def opposite(value):
        return not value

    def set_enabled_from_checkbox(self, widget, checkbox):
        dlink((checkbox, 'value'), (widget, 'disabled'), self.opposite)


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
        self._layout = HBox([self.figure_widget, self._layout_tab], layout=Layout(height="400px"))

    def _initialize_wwt(self):
        self._wwt = WWTJupyterWidget()

    def redraw(self):
        self._update_wwt()

    @property
    def figure_widget(self):
        return self._wwt
