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

        self._update_markers(force=True)

    def clear(self):
        if self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            self._coords = [], []

    def _update_markers(self, force=False, **kwargs):

        logger.debug("updating WWT for %s" % self.layer.label)

        if self.visible is False and self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            return

        if force or 'frame' in kwargs or self.wwt_layer is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
                self._coords = [], []
            force = True

        if force or 'ra_att' in kwargs or 'dec_att' in kwargs:

            try:
                ra = self.layer[self.state.ra_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self.state.ra_att)
                return

            try:
                dec = self.layer[self.state.dec_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self.state.dec_att)
                return

            # First deal with data/coordinates

            if len(ra) > 0:

                try:
                    coord = SkyCoord(ra, dec, unit=(u.deg, u.deg))
                except ValueError as exc:
                    # self.disable(str(exc))
                    return

                coord_icrs = coord.icrs
                ra = coord_icrs.ra.degree
                dec = coord_icrs.dec.degree

                keep = ((ra >= -360) & (ra <= 360) &
                        (dec >= -90) & (dec <= 90))

                ra, dec = ra[keep], dec[keep]

                tab = Table()
                tab['ra'] = ra * u.degree
                tab['dec'] = dec * u.degree

                if self.wwt_layer is None:
                    self.wwt_layer = self.wwt_client.layers.add_data_layer(tab, frame=self.state.frame)
                else:
                    self.wwt_layer.update_data(table=tab)

                self._coords = ra, dec

            else:

                if self.wwt_layer is not None:
                    self.wwt_layer.remove()
                    self.wwt_layer = None
                    self._coords = [], []
                return

        if force or 'size' in kwargs:
            self.wwt_layer.size_scale = self.state.size * 5

        if force or 'color' in kwargs:
            self.wwt_layer.color = self.state.color

        if force or 'alpha' in kwargs:
            self.wwt_layer.opacity = self.state.alpha

        self.enable()

        # TODO: deal with visible, zorder, frame

    def center(self, *args):

        ra, dec = self._coords

        if len(ra) == 0:
            return

        ra_cen, dec_cen, sep_max = center_fov(ra, dec)

        if ra_cen is None:
            return

        fov = min(60, sep_max * 3)

        self.wwt_client.center_on_coordinates(SkyCoord(ra_cen, dec_cen, unit=u.degree, frame='icrs'), fov * u.degree, instant=False)

    def redraw(self):
        pass

    def update(self):
        self._update_markers(force=True)
