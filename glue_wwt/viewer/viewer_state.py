from __future__ import absolute_import, division, print_function

from astropy import units as u

from echo import (CallbackProperty, ListCallbackProperty,
                  SelectionCallbackProperty)

from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.viewers.common.state import ViewerState
from numpy import datetime64, timedelta64

MODES_BODIES = ['Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars',
                'Jupiter', 'Callisto', 'Europa', 'Ganymede', 'Io', 'Saturn',
                'Uranus', 'Neptune', 'Pluto']

MODES_3D = ['Solar System', 'Milky Way', 'Universe']

ALT_UNITS = [u.m, u.km, u.AU, u.lyr, u.pc, u.kpc, u.Mpc,
             u.imperial.ft, u.imperial.inch, u.imperial.mi]

ALT_TYPES = ['Altitude', 'Depth', 'Distance']

CELESTIAL_FRAMES = ['ICRS', 'FK5', 'FK4', 'Galactic']


class WWTDataViewerState(ViewerState):

    mode = SelectionCallbackProperty(default_index=0)
    frame = SelectionCallbackProperty(default_index=0)

    lon_att = SelectionCallbackProperty(default_index=0)
    lat_att = SelectionCallbackProperty(default_index=1)
    alt_att = SelectionCallbackProperty(default_index=0)
    alt_unit = SelectionCallbackProperty(default_index=0)
    alt_type = SelectionCallbackProperty(default_index=0)

    foreground = SelectionCallbackProperty(default_index=1)
    foreground_opacity = CallbackProperty(1)
    background = SelectionCallbackProperty(default_index=8)

    galactic = CallbackProperty(False)

    equatorial_grid = CallbackProperty(False)
    equatorial_grid_color = CallbackProperty("white")
    equatorial_text = CallbackProperty(False)
    ecliptic_grid = CallbackProperty(False)
    ecliptic_grid_color = CallbackProperty("green")
    ecliptic_text = CallbackProperty(False)
    alt_az_grid = CallbackProperty(False)
    alt_az_grid_color = CallbackProperty("magenta")
    alt_az_text = CallbackProperty(False)
    galactic_grid = CallbackProperty(False)
    galactic_grid_color = CallbackProperty("cyan")
    galactic_text = CallbackProperty(False)

    constellation_boundaries = SelectionCallbackProperty(default_index=0)
    constellation_boundary_color = CallbackProperty("blue")
    constellation_selection_color = CallbackProperty("yellow")
    constellation_labels = CallbackProperty(False)
    constellation_figures = CallbackProperty(False)
    constellation_figure_color = CallbackProperty("red")
    constellation_pictures = CallbackProperty(False)

    crosshairs = CallbackProperty(False)
    crosshairs_color = CallbackProperty("white")
    ecliptic = CallbackProperty(False)
    ecliptic_color = CallbackProperty("blue")
    precession_chart = CallbackProperty(False)
    precession_chart_color = CallbackProperty("orange")

    play_time = CallbackProperty(False)
    clock_rate = CallbackProperty(1)
    current_time = CallbackProperty(datetime64('now'))
    min_time = CallbackProperty(datetime64("2000-01-01"))
    max_time = CallbackProperty(datetime64("now"))

    layers = ListCallbackProperty()

    # For now we need to include this here otherwise when loading files, the
    # imagery layers are only available asynchronously and the session loading
    # fails.
    imagery_layers = ListCallbackProperty()

    def __init__(self, **kwargs):

        super(WWTDataViewerState, self).__init__()

        WWTDataViewerState.mode.set_choices(self, ['Sky'] + MODES_3D + MODES_BODIES)
        WWTDataViewerState.frame.set_choices(self, CELESTIAL_FRAMES)
        WWTDataViewerState.alt_unit.set_choices(self, [str(x) for x in ALT_UNITS])
        WWTDataViewerState.alt_type.set_choices(self, ALT_TYPES)
        WWTDataViewerState.constellation_boundaries.set_choices(self, ['None', 'All', 'Selection only'])

        self.add_callback('imagery_layers', self._update_imagery_layers)

        self.add_callback('min_time', self._on_min_time_update)
        self.add_callback('max_time', self._on_max_time_update)
        self.add_callback('current_time', self._on_current_time_update)

        self.lon_att_helper = ComponentIDComboHelper(self, 'lon_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False)

        self.lat_att_helper = ComponentIDComboHelper(self, 'lat_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False)

        self.alt_att_helper = ComponentIDComboHelper(self, 'alt_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False,
                                                     none='None')

        self.add_callback('layers', self._on_layers_changed)
        self._on_layers_changed()

        self.update_from_dict(kwargs)

    def _on_layers_changed(self, *args):
        self.lon_att_helper.set_multiple_data(self.layers_data)
        self.lat_att_helper.set_multiple_data(self.layers_data)
        self.alt_att_helper.set_multiple_data(self.layers_data)

    def _update_imagery_layers(self, *args):
        WWTDataViewerState.foreground.set_choices(self, self.imagery_layers)
        WWTDataViewerState.background.set_choices(self, self.imagery_layers)

    def _update_priority(self, name):
        if name == 'layers':
            return 2
        elif name == 'imagery_layers':
            return 1
        else:
            return 0

    # Unlike e.g. viewer bounds, there's no use case for min_time < max_time
    # so we use the next few methods to ensure that min_time <= current_time <= max_time
    def _on_min_time_update(self, time):
        if self.max_time <= time:
            self.max_time = time + timedelta64(1, 'D')
        if self.current_time < time:
            self.current_time = time

    def _on_max_time_update(self, time):
        if self.min_time >= time:
            self.min_time = time - timedelta64(1, 'D')
        if self.current_time > time:
            self.current_time = time

    def _on_current_time_update(self, time):
        if time < self.min_time:
            self.current_time = self.min_time
            self.play_time = False
        elif time > self.max_time:
            self.current_time = self.max_time
            self.play_time = False
