from __future__ import absolute_import, division, print_function

import random

from glue.logger import logger
from glue.core.exceptions import IncompatibleAttribute
from glue.viewers.common.layer_artist import LayerArtist

from astropy import units as u
from astropy.coordinates import SkyCoord

from .state import WWTLayerState

__all__ = ['WWTLayer']


class WWTLayer(LayerArtist):

    _layer_state_cls = WWTLayerState

    def __init__(self, wwt_client, viewer_state, layer_state=None, layer=None):

        super(WWTLayer, self).__init__(viewer_state, layer_state=layer_state, layer=layer)

        self.layer_id = "{0:08x}".format(random.getrandbits(32))
        self.markers = wwt_client.markers
        self.markers.allocate(self.layer_id)

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self.state.add_global_callback(self._update_markers)

        self._update_markers(force=True)

    def clear(self):
        self.markers.set(self.layer_id, visible=False)

    def _update_markers(self, force=False, **kwargs):

        logger.debug("updating WWT for %s" % self.layer.label)

        coords = {}

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

            if len(ra) > 0:

                try:
                    coord = SkyCoord(ra, dec, unit=(u.deg, u.deg))
                except ValueError as exc:
                    # self.disable(str(exc))
                    return

                coord_icrs = coord.icrs
                ra = coord_icrs.ra.degree
                dec = coord_icrs.dec.degree

                coords = {'coords': (ra, dec)}

        self.enable()

        self.markers.set(self.layer_id, color=self.state.color,
                         alpha=self.state.alpha, visible=self.visible,
                         zorder=self.zorder, size=self.state.size, **coords)

    def center(self, *args):
        self.markers.center(self.layer_id)

    def redraw(self):
        pass

    def update(self):
        self._update_markers(force=True)
