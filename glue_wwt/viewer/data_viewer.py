"""Base WWT data viewer implementation, generic over Qt and Jupyter backends."""

from __future__ import absolute_import, division, print_function

from astropy.wcs import WCS

from glue.core import Subset

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

    _UPDATE_SETTINGS = [
        "foreground", "background", "foreground_opacity", "galactic",
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

    def __init__(self):
        self._initialize_wwt()
        self._wwt.actual_planet_scale = True
        self.state.imagery_layers = list(self._wwt.available_layers)

        self.state.add_global_callback(self._update_wwt)
        self._update_wwt(force=True)

    def _initialize_wwt(self):
        raise NotImplementedError('subclasses should set _wwt here')

    def _update_wwt(self, force=False, **kwargs):
        if force or 'mode' in kwargs:
            self._wwt.set_view(self.state.mode)
            # Only show SDSS data when in Universe mode
            self._wwt.solar_system.cosmos = self.state.mode == 'Universe'
            # Only show local stars when not in Universe or Milky Way mode
            self._wwt.solar_system.stars = self.state.mode not in ['Universe', 'Milky Way']

        if force or 'constellation_boundaries' in kwargs:
            self._wwt.constellation_boundaries = self.state.constellation_boundaries != 'None'
            self._wwt.constellation_selection = self.state.constellation_boundaries == 'Selection only'

        for setting in self._UPDATE_SETTINGS:
            if force or setting in kwargs:
                wwt_attr = self._GLUE_TO_WWT_ATTR_MAP.get(setting, setting)
                setattr(self._wwt, wwt_attr, getattr(self.state, setting, None))

    def get_layer_artist(self, cls, **kwargs):
        "In this package, we must override to append the wwt_client argument."
        return cls(self.state, wwt_client=self._wwt, **kwargs)

    def get_data_layer_artist(self, layer=None, layer_state=None):

        if isinstance(layer, Subset):
            coords = layer.data.coords
        else:
            coords = layer.coords

        if len(layer.pixel_component_ids) == 2:
            if not isinstance(coords, WCS):
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
