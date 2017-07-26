from __future__ import absolute_import, division, print_function

import numpy as np

from glue.logger import logger
from glue.core.layer_artist import LayerArtistBase
from glue.core.exceptions import IncompatibleAttribute
from glue.external.echo import CallbackProperty, keep_in_sync

from astropy import units as u
from astropy.coordinates import SkyCoord

from .state import WWTLayerState
from .wwt_widget import WWTMarkerCollection

__all__ = ['WWTLayer', 'circle']


def circle(x, y, label, color, radius=3):
    result = """%(label)s = wwt.createCircle("%(color)s");
    %(label)s.setCenter(%(x)f, %(y)f);
    %(label)s.set_fillColor("%(color)s");
    %(label)s.set_radius(%(radius)f);""" % {'x': x, 'y': y, 'label': label,
                                            'color': color, 'radius': radius}
    return result


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

        self.markers = WWTMarkerCollection(self._wwt_widget)

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self._sync_zorder = keep_in_sync(self, 'zorder', self.state, 'zorder')
        self._sync_visible = keep_in_sync(self, 'visible', self.state, 'visible')

        self.state.add_global_callback(self.update)

    def clear(self):
        self.markers.clear()

    def update(self, **kwargs):

        logger.debug("updating WWT for %s" % self.layer.label)

        self.markers.clear()

        if not self.visible:
            return

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

        if len(ra) == 0:
            self.disable('No data in layer')
            return

        try:
            coord = SkyCoord(ra, dec, unit=(u.deg, u.deg))
        except ValueError as exc:
            self.disable(str(exc))
            return

        self.enable()

        self.markers.draw(coord, color=self.state.color)

        ra_med = np.nanmedian(ra)
        dec_med = np.nanmedian(dec)
        coord_med = SkyCoord(ra_med, dec_med, unit=(u.deg, u.deg))
        self._wwt_widget.move(coord_med)

    def redraw(self):
        pass
