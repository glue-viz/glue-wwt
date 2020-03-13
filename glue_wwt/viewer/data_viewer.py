"""Base WWT data viewer implementation, generic over Qt and Jupyter backends."""

from __future__ import absolute_import, division, print_function

from glue.core.coordinates import WCSCoordinates

from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist
from .viewer_state import WWTDataViewerState

__all__ = ['WWTDataViewerBase']


class WWTDataViewerBase(object):
    LABEL = 'Earth/Planet/Sky Viewer (WWT)'
    _wwt = None

    _state_cls = WWTDataViewerState

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

        if force or 'foreground' in kwargs:
            self._wwt.foreground = self.state.foreground

        if force or 'background' in kwargs:
            self._wwt.background = self.state.background

        if force or 'foreground_opacity' in kwargs:
            self._wwt.foreground_opacity = self.state.foreground_opacity

        if force or 'galactic' in kwargs:
            self._wwt.galactic_mode = self.state.galactic

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
