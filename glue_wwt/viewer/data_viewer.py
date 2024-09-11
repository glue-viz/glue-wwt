"""Base WWT data viewer implementation, generic over Qt and Jupyter backends."""

from __future__ import absolute_import, division, print_function

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from glue.core.coordinates import WCSCoordinates
from glue.logger import logger
from pywwt import ViewerNotAvailableError
from pywwt.layers import guess_lon_lat_columns
from threading import Timer
from numpy import datetime64

from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist
from .viewer_state import WWTDataViewerState

__all__ = ['WWTDataViewerBase']


class WWTDataViewerBase(object):
    LABEL = 'Earth/Planet/Sky Viewer (WWT)'
    _wwt = None

    _state_cls = WWTDataViewerState

    _GLUE_TO_WWT_ATTR_MAP = {
        "galactic": "galactic_mode",
        "equatorial_grid": "grid",
        "equatorial_grid_color": "grid_color",
        "equatorial_text": "grid_text"
    }

    _CLOCK_SETTINGS = [
        "play_time", "clock_rate"
    ]

    _UPDATE_SETTINGS = [
        "equatorial_grid", "equatorial_grid_color", "equatorial_text",
        "ecliptic_grid", "ecliptic_grid_color", "ecliptic_text",
        "alt_az_grid", "alt_az_grid_color", "alt_az_text",
        "galactic_grid", "galactic_grid_color", "galactic_text",
        "constellation_boundary_color", "constellation_selection_color",
        "constellation_figures", "constellation_figure_color",
        "constellation_labels", "constellation_pictures", "crosshairs",
        "ecliptic", "ecliptic_color", "precession_chart",
        "precession_chart_color"
    ]

    _IMAGERY_UPDATE_SETTINGS = ["foreground", "background", "foreground_opacity", "galactic"]

    def __init__(self):
        self._initialize_wwt()
        self._wwt.actual_planet_scale = True
        self.state.imagery_layers = list(self._wwt.available_layers)

        # The more obvious thing to do would be to listen to the WWT widget's "wwt_view_state" message,
        # which contains information about WWT's internal time. But we only get those messages when something
        # changes with the WWT view, so we can't rely on that here.
        # This just kicks off the first timer; the method repeatedly time-calls itself
        self._current_time_timer = Timer(1.0, self._update_time)
        self._current_time_timer.start()

        self.state.add_global_callback(self._update_wwt)

        self._update_wwt(force=True)

    # NB: Specific frontend implementations need to call this
    # We just consolidate the logic here
    def _cleanup(self):
        self._current_time_timer.cancel()

    def _initialize_wwt(self):
        raise NotImplementedError('subclasses should set _wwt here')

    def _update_wwt(self, force=False, **kwargs):
        if force or 'mode' in kwargs:
            self._wwt.set_view(self.state.mode)
            # Only show SDSS data when in Universe mode
            self._wwt.solar_system.cosmos = self.state.mode == 'Universe'
            # Only show local stars when not in Universe or Milky Way mode
            self._wwt.solar_system.stars = self.state.mode not in ['Universe', 'Milky Way']
            force = True

        if force or 'constellation_boundaries' in kwargs:
            self._wwt.constellation_boundaries = self.state.constellation_boundaries != 'None'
            self._wwt.constellation_selection = self.state.constellation_boundaries == 'Selection only'

        if force or 'current_time' in kwargs:
            self._wwt.set_current_time(Time(self.state.current_time))

        if force or any(setting in kwargs for setting in self._CLOCK_SETTINGS):
            if self.state.play_time:
                self._wwt.play_time(self.state.clock_rate)
            else:
                self._wwt.pause_time()

        for setting in self._UPDATE_SETTINGS:
            if force or setting in kwargs:
                wwt_attr = self._GLUE_TO_WWT_ATTR_MAP.get(setting, setting)
                setattr(self._wwt, wwt_attr, getattr(self.state, setting, None))

        show_imagery = self.state.mode == 'Sky'
        if show_imagery:
            for setting in self._IMAGERY_UPDATE_SETTINGS:
                if force or setting in kwargs:
                    setattr(self._wwt, setting, getattr(self.state, setting, None))

    def get_layer_artist(self, cls, **kwargs):
        "In this package, we must override to append the wwt_client argument."
        return cls(self.state, wwt_client=self._wwt, **kwargs)

    def get_data_layer_artist(self, layer=None, layer_state=None):
        if len(layer.pixel_component_ids) == 2:
            if not isinstance(layer.coords, WCSCoordinates):
                raise ValueError('WWT cannot render image layer {}: it must have WCS coordinates'.format(layer.label))
            cls = WWTImageLayerArtist
        elif layer.ndim == 1:
            cls = WWTTableLayerArtist
        else:
            raise ValueError('WWT does not know how to render the data of {}'.format(layer.label))

        return cls(self.state, wwt_client=self._wwt, layer=layer, layer_state=layer_state)

    def get_subset_layer_artist(self, layer=None, layer_state=None):
        # At some point maybe we'll use different classes for this?
        return self.get_data_layer_artist(layer=layer, layer_state=layer_state)

    def __gluestate__(self, context):
        state = super(WWTDataViewerBase, self).__gluestate__(context)
        try:
            center = self._wwt.get_center()
            camera = {
                "ra": center.ra.deg,
                "dec": center.dec.deg,
                "fov": self._wwt.get_fov().value
            }
            if hasattr(self._wwt, 'get_roll'):
                camera["roll"] = self._wwt.get_roll().value
            state["camera"] = camera
        except ViewerNotAvailableError:
            logger.error("Unable to export camera parameters as WWT viewer is not responding.")
        return state

    @classmethod
    def __setgluestate__(cls, rec, context):
        viewer = super(WWTDataViewerBase, cls).__setgluestate__(rec, context)
        if "camera" in rec:
            camera = rec["camera"]
            ra = camera.get("ra", 0)
            dec = camera.get("dec", 0)
            fov = camera.get("fov", 60)
            roll = camera.get("roll", None)
            camera_kwargs = dict(fov=fov * u.deg, instant=True)
            if hasattr(viewer._wwt, 'get_roll') and roll is not None:
                camera_kwargs["roll"] = roll * u.deg
            viewer._wwt.center_on_coordinates(SkyCoord(ra, dec, unit=u.deg), **camera_kwargs)
        return viewer

    def add_data(self, data):
        add = super().add_data(data)
        if add and len(self.state.layers) == 1:
            colnames = [c.label for c in data.components]
            lon, lat = guess_lon_lat_columns(colnames)
            if lon is not None and lat is not None:
                self.state.lon_att = data.id[lon]
                self.state.lat_att = data.id[lat]
        return add

    def _update_time(self):
        try:
            self.state.current_time = datetime64(self._wwt.get_current_time().to_string())
        except ViewerNotAvailableError:
            pass

        self._current_time_timer = Timer(1.0, self._update_time)
        self._current_time_timer.start()
