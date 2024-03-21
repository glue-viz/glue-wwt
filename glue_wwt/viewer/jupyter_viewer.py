from __future__ import absolute_import, division, print_function
from datetime import datetime

from glue_jupyter.view import IPyWidgetView
from glue_jupyter.link import link, dlink
from glue_jupyter.widgets import LinkedDropdown, Color, Size

from pywwt.jupyter import WWTJupyterWidget

from ipywidgets import Accordion, GridBox, HBox, Label, Layout, Output, Tab, VBox, FloatSlider, FloatText
from ipywidgets.widgets.widget_datetime import NaiveDatetimePicker
from numpy import datetime64

from .data_viewer import WWTDataViewerBase
from .image_layer import WWTImageLayerArtist
from .jupyter_utils import linked_checkbox, linked_color_picker, linked_float_text, set_enabled_from_checkbox
from .table_layer import WWTTableLayerArtist


class JupterViewerOptions(VBox):
    def __init__(self, viewer_state, available_layers):

        self.fit_content_layout = Layout(width="fit-content")

        self.state = viewer_state

        self.widget_output = Output()

        self.widget_mode = LinkedDropdown(self.state, "mode", label="Mode:")
        self.widget_frame = LinkedDropdown(self.state, "frame", label="Frame:")

        self.widget_ra = LinkedDropdown(self.state, "lon_att", label="RA:")
        self.widget_dec = LinkedDropdown(self.state, "lat_att", label="Dec:")

        self.widget_alt_type = LinkedDropdown(self.state, "alt_type", label="Height Type:")
        self.widget_alt = LinkedDropdown(self.state, "alt_att", label="Height Column:")
        self.widget_alt_unit = LinkedDropdown(self.state, "alt_unit", label="Height Unit:")
        self.alt_opts = VBox([self.widget_alt_type, self.widget_alt, self.widget_alt_unit])
        dlink((self.state, 'mode'), (self.alt_opts.layout, 'display'), lambda value: '' if value != 'Sky' else 'none')

        self.widget_foreground = LinkedDropdown(self.state, "foreground", label='Foreground:')
        self.widget_foreground_opacity = FloatSlider(description="Opacity:", min=0, max=1,
                                                     value=self.state.foreground_opacity, step=0.01)
        link((self.widget_foreground_opacity, 'value'), (self.state, 'foreground_opacity'))
        self.widget_background = LinkedDropdown(self.state, 'background', label='Background:')
        self.widget_allskyimg = VBox([self.widget_foreground, self.widget_foreground_opacity, self.widget_background])
        dlink((self.state, 'mode'), (self.widget_allskyimg.layout, 'display'),
              lambda value: '' if value == 'Sky' else 'none')

        self.widget_crosshairs = linked_checkbox(self.state, 'crosshairs', description="Show crosshairs")
        self.widget_galactic_plane_mode = linked_checkbox(self.state, 'galactic', description="Galactic Plane mode")

        self.general_settings = VBox(children=[self.widget_mode, self.widget_frame, self.widget_ra,
                                               self.widget_dec, self.alt_opts, self.widget_allskyimg,
                                               self.widget_crosshairs, self.widget_galactic_plane_mode])

        self.widget_alt_az_grid = linked_checkbox(self.state, 'alt_az_grid', description="Alt/Az")
        self.widget_alt_az_text = linked_checkbox(self.state, 'alt_az_text', description="Text")
        set_enabled_from_checkbox(self.widget_alt_az_text, self.widget_alt_az_grid)
        self.widget_alt_az_grid_color = linked_color_picker(self.state, 'alt_az_grid_color')
        set_enabled_from_checkbox(self.widget_alt_az_grid_color, self.widget_alt_az_grid)

        self.widget_ecliptic_grid = linked_checkbox(self.state, 'ecliptic_grid', description="Ecliptic")
        self.widget_ecliptic_text = linked_checkbox(self.state, 'ecliptic_text', description="Text")
        set_enabled_from_checkbox(self.widget_ecliptic_text, self.widget_ecliptic_grid)
        self.widget_ecliptic_grid_color = linked_color_picker(self.state, 'ecliptic_grid_color')
        set_enabled_from_checkbox(self.widget_ecliptic_grid_color, self.widget_ecliptic_grid)

        self.widget_equatorial_grid = linked_checkbox(self.state, 'equatorial_grid', "Equatorial")
        self.widget_equatorial_text = linked_checkbox(self.state, 'equatorial_text', "Text")
        set_enabled_from_checkbox(self.widget_equatorial_text, self.widget_equatorial_grid)
        self.widget_equatorial_grid_color = linked_color_picker(self.state, 'equatorial_grid_color')
        set_enabled_from_checkbox(self.widget_equatorial_grid_color, self.widget_equatorial_grid)

        self.widget_galactic_grid = linked_checkbox(self.state, 'galactic_grid', description="Galactic")
        self.widget_galactic_text = linked_checkbox(self.state, 'galactic_text', description="Text")
        set_enabled_from_checkbox(self.widget_galactic_text, self.widget_galactic_grid)
        self.widget_galactic_grid_color = linked_color_picker(self.state, 'galactic_grid_color')
        set_enabled_from_checkbox(self.widget_galactic_grid_color, self.widget_galactic_grid)

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
        self.widget_constellation_boundary_color = linked_color_picker(self.state, 'constellation_boundary_color',
                                                                       description="Boundary")
        dlink((self.widget_constellation_boundaries, 'value'), (self.widget_constellation_boundary_color, 'disabled'),
              lambda value: value != "All")
        self.widget_constellation_selection_color = linked_color_picker(self.state, 'constellation_selection_color',
                                                                        description="Selection")
        dlink((self.widget_constellation_boundaries, 'value'), (self.widget_constellation_selection_color, 'disabled'),
              lambda value: value == "None")

        self.widget_constellation_figures = linked_checkbox(self.state, 'constellation_figures', description="Figures")
        self.widget_constellation_figure_color = linked_color_picker(self.state, 'constellation_figure_color',
                                                                     description="Figure")
        set_enabled_from_checkbox(self.widget_constellation_figure_color, self.widget_constellation_figures)
        self.widget_constellation_labels = linked_checkbox(self.state, 'constellation_labels',
                                                           description="Labels")
        self.widget_constellation_pictures = linked_checkbox(self.state, 'constellation_pictures',
                                                             description="Pictures")

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
        self.widget_ecliptic = linked_checkbox(self.state, 'ecliptic', description="Show")
        self.widget_ecliptic_color = linked_color_picker(self.state, 'ecliptic_color')
        set_enabled_from_checkbox(self.widget_ecliptic_color, self.widget_ecliptic)

        self.widget_precession_chart_label = Label("Precession Chart:")
        self.widget_precession_chart = linked_checkbox(self.state, 'precession_chart', description="Show")
        self.widget_precession_chart_color = linked_color_picker(self.state, 'precession_chart_color')
        set_enabled_from_checkbox(self.widget_precession_chart_color, self.widget_precession_chart)

        self.widget_play_time = linked_checkbox(self.state, "play_time", description="Play Time")
        self.widget_clock_rate = FloatText(description="Clock Rate:")
        link((self.state, 'clock_rate'), (self.widget_clock_rate, 'value'))

        self.widget_current_time_label = Label("Current Time:")
        self.widget_current_time = FloatSlider(readout=False, min=0, max=1, step=0.001)
        self.state.add_callback('min_time', self._update_slider_fraction)
        self.state.add_callback('max_time', self._update_slider_fraction)

        # We can't just use `link` here because the time granularity of the slider will not be the same as WWT
        # and so when we update the time, we'll get a time -> slider -> time update
        # where the second time lies exactly on a widget step.
        self.state.add_callback('current_time', self._on_current_time_update)
        self.widget_current_time.observe(self._on_slider_update, names=["value"])

        self.widget_min_time = NaiveDatetimePicker(description="Min Time:")
        link((self.state, 'min_time'), (self.widget_min_time, 'value'),
             lambda time: self._datetime64_to_utc_datetime(time),
             lambda value: datetime64(value))
        self.widget_max_time = NaiveDatetimePicker(description="Max Time:")
        link((self.state, 'max_time'), (self.widget_max_time, 'value'),
             lambda time: self._datetime64_to_utc_datetime(time),
             lambda value: datetime64(value))

        self.other_settings = VBox(children=[
                                       GridBox(children=[self.widget_ecliptic_label, self.widget_ecliptic,
                                                         self.widget_ecliptic_color, self.widget_precession_chart_label,
                                                         self.widget_precession_chart,
                                                         self.widget_precession_chart_color],
                                               layout=Layout(grid_template_columns="60% 20% 20%", width="100%",
                                                             grid_gap="2px 10px")),
                                       VBox(children=[self.widget_play_time, self.widget_clock_rate,
                                                      self.widget_current_time_label, self.widget_current_time,
                                                      self.widget_min_time, self.widget_max_time])
                                   ])

        self.settings = Accordion(children=[self.general_settings, self.grid_settings,
                                            self.constellation_settings, self.other_settings],
                                  layout=Layout(width="350px"))
        self.settings.set_title(0, "General")
        self.settings.set_title(1, "Grids")
        self.settings.set_title(2, "Constellations")
        self.settings.set_title(3, "Other")
        self.settings.selected_index = 0

        super().__init__([self.settings])

    def _datetime64_to_utc_datetime(self, dt64):
        dt = dt64.item()
        if not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())
        return dt

    def _update_slider_fraction(self, *args):
        fraction = (self.state.current_time - self.state.min_time) / (self.state.max_time - self.state.min_time)
        value = self.widget_current_time.min + fraction * (self.widget_current_time.max - self.widget_current_time.min)
        self.widget_current_time.value = value

    def _on_current_time_update(self, time):
        self._update_slider_fraction()
        self.widget_current_time_label.value = f"Current Time: {time}"

    def _on_slider_update(self, changed):
        fraction = (changed["new"] - self.widget_current_time.min) / \
                   (self.widget_current_time.max - self.widget_current_time.min)
        time = self.state.min_time + fraction * (self.state.max_time - self.state.min_time)
        n_steps = (self.widget_current_time.max - self.widget_current_time.min) / self.widget_current_time.step
        step_timegap = (self.state.max_time - self.state.min_time) / n_steps
        if abs(time - self.state.current_time) >= step_timegap:
            self.state.current_time = time


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

        self.vmin = linked_float_text(self.state, 'vmin', description='Min Val')
        self.vmax = linked_float_text(self.state, 'vmax', description='Max Val', default=1)
        self.lims = VBox([self.vmin, self.vmax])

        super().__init__([self.data_att, self.alpha, self.cmap, self.stretch, self.lims])


class JupyterTableLayerOptions(VBox):
    def __init__(self, layer_state):
        self.state = layer_state
        self.color_widgets = Color(state=self.state)
        self.size_widgets = Size(state=self.state)

        self.widget_time_series = linked_checkbox(self.state, 'time_series', description="Time series")
        self.widget_time_att = LinkedDropdown(self.state, 'time_att', 'Time att')
        self.widget_time_decay_value = linked_float_text(self.state, 'time_decay_value',
                                                         default=0, description='Time decay')
        self.widget_time_decay_unit = LinkedDropdown(self.state, 'time_decay_unit', label='')
        self.time_decay_widgets = HBox([self.widget_time_decay_value, self.widget_time_decay_unit])
        self.time_widgets = VBox([self.widget_time_series, self.widget_time_att, self.time_decay_widgets])

        # self.recenter_widget = Button(description='Center view on layer')
        # self.recenter_widget.on_click(viewer_state.)

        super().__init__([self.size_widgets, self.color_widgets, self.time_widgets])


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
