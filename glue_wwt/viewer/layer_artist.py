from __future__ import absolute_import, division, print_function

import random

import numpy as np

from glue.core import Data
from glue.logger import logger
from glue.core.layer_artist import LayerArtistBase
from glue.core.exceptions import IncompatibleAttribute
from glue.external.echo import CallbackProperty, keep_in_sync

from astropy import units as u
from astropy.coordinates import SkyCoord

from .state import WWTLayerState

__all__ = ['WWTLayer']


class WWTLayer(LayerArtistBase):

    zorder = CallbackProperty()
    visible = CallbackProperty()

    def __init__(self, wwt_widget, viewer_state, layer_state=None, layer=None):

        super(WWTLayer, self).__init__(layer)

        self.layer = layer or layer_state.layer

        self._wwt_widget = wwt_widget
        self._viewer_state = viewer_state

        # Set up a state object for the layer artist
        self.state = layer_state or WWTLayerState(viewer_state=viewer_state,
                                                  layer=self.layer)
        if self.state not in self._viewer_state.layers:
            self._viewer_state.layers.append(self.state)

        self.layer_id = "{0:08x}".format(random.getrandbits(32))
        self.markers = self._wwt_widget.markers
        self.markers.allocate(self.layer_id)

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self._sync_zorder = keep_in_sync(self, 'zorder', self.state, 'zorder')
        self._sync_visible = keep_in_sync(self, 'visible', self.state, 'visible')

        self.state.add_global_callback(self.update)

        self.update(force=True)

    def clear(self):
        self.markers.set(self.layer_id, visible=False)

    def update(self, force=False, **kwargs):

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
                    self.disable(str(exc))
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
