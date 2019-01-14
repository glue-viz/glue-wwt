from __future__ import absolute_import, division, print_function

import random

from glue.logger import logger
from glue.core.exceptions import IncompatibleAttribute
from glue.viewers.common.layer_artist import LayerArtist

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from .state import WWTLayerState
from .utils import center_fov

__all__ = ['WWTLayer']


class WWTLayer(LayerArtist):

    _layer_state_cls = WWTLayerState

    def __init__(self, wwt_client, viewer_state, layer_state=None, layer=None):

        super(WWTLayer, self).__init__(viewer_state, layer_state=layer_state, layer=layer)

        self.wwt_layer = None
        self._coords = [], []

        self.layer_id = "{0:08x}".format(random.getrandbits(32))
        self.wwt_client = wwt_client

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self.state.add_global_callback(self._update_markers)
        self._viewer_state.add_global_callback(self._update_markers)

        self._update_markers(force=True)

    def clear(self):
        if self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            self._coords = [], []

    def _update_markers(self, force=False, **kwargs):

        if self._viewer_state.lon_att is None or self._viewer_state.lat_att is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
            return

        logger.debug("updating WWT for %s" % self.layer.label)

        if self.visible is False and self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            return

        # FIXME: for some reason changing units doesn't cause the layer to refrsh
        if 'alt_unit' in kwargs:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
                self._coords = [], []
            force = True

        if force or 'mode' in kwargs or self.wwt_layer is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
                self._coords = [], []
            force = True

        if force or 'mode' in kwargs or 'lon_att' in kwargs or 'lat_att' in kwargs or 'alt_att' in kwargs:

            try:
                lon = self.layer[self._viewer_state.lon_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self._viewer_state.lon_att)
                return

            try:
                lat = self.layer[self._viewer_state.lat_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self._viewer_state.dec_att)
                return

            if self._viewer_state.alt_att is not None:
                try:
                    alt = self.layer[self._viewer_state.alt_att]
                except IncompatibleAttribute:
                    self.disable_invalid_attributes(self._viewer_state.alt_att)
                    return

            # First deal with data/coordinates

            if len(lon) > 0:

                tab = Table()
                tab['lon'] = lon * u.degree
                tab['lat'] = lat * u.degree
                if self._viewer_state.alt_att is not None:
                    # FIXME: allow arbitrary units
                    tab['alt'] = alt
                    alt_att = {'alt_att': 'alt'}
                else:
                    alt_att = {}

                if self.wwt_layer is None:
                    self.wwt_layer = self.wwt_client.layers.add_data_layer(tab, frame=self._viewer_state.mode,
                                                                           lon_att='lon', lat_att='lat', **alt_att)
                else:
                    self.wwt_layer.update_data(table=tab)

                self._coords = lon, lat

            else:

                if self.wwt_layer is not None:
                    self.wwt_layer.remove()
                    self.wwt_layer = None
                    self._coords = [], []
                return

        if force or 'alt_unit' in kwargs:
            self.wwt_layer.alt_unit = self._viewer_state.alt_unit

        if force or 'alt_type' in kwargs:
            self.wwt_layer.alt_type = self._viewer_state.alt_type.lower()

        if force or 'size' in kwargs:
            self.wwt_layer.size_scale = self.state.size * 5

        if force or 'color' in kwargs:
            self.wwt_layer.color = self.state.color

        if force or 'alpha' in kwargs:
            self.wwt_layer.opacity = self.state.alpha

        self.enable()

        # TODO: deal with visible, zorder, frame

    def center(self, *args):

        lon, lat = self._coords

        if len(lon) == 0:
            return

        lon_cen, lat_cen, sep_max = center_fov(lon, lat)

        if lon_cen is None:
            return

        fov = min(60, sep_max * 3)

        self.wwt_client.center_on_coordinates(SkyCoord(lon_cen, lat_cen, unit=u.degree, frame='icrs'), fov * u.degree, instant=False)

    def redraw(self):
        pass

    def update(self):
        self._update_markers(force=True)
