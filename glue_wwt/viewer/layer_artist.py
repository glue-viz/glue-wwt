from __future__ import absolute_import, division, print_function

import random

from glue.logger import logger
from glue.core.exceptions import IncompatibleAttribute
from glue.viewers.common.layer_artist import LayerArtist

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from .state import WWTLayerState, MODES_3D
from .utils import center_fov

__all__ = ['WWTLayer']


RESET_DATA_PROPERTIES = ('mode', 'frame', 'lon_att', 'lat_att', 'alt_att',
                         'alt_unit', 'size_att', 'cmap_att', 'size_mode',
                         'color_mode')


class WWTLayer(LayerArtist):

    _layer_state_cls = WWTLayerState
    _removed = False

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

    def remove(self):
        self._removed = True
        if self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            self._coords = [], []

    def _update_markers(self, force=False, **kwargs):

        if self._removed:
            return

        changed = set() if force else self.pop_changed_properties()

        if self._viewer_state.lon_att is None or self._viewer_state.lat_att is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
            return

        logger.debug("updating WWT for %s" % self.layer.label)

        if self.visible is False:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
            return

        if force or 'mode' in changed or self.wwt_layer is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
                self._coords = [], []
            force = True

        # FIXME: kpc isn't yet a valid unit in WWT/PyWWT:
        # https://github.com/WorldWideTelescope/wwt-web-client/pull/197
        # for now we set unit to pc and scale values accordingly, so if the
        # unit changes we need to refresh the data just in case

        if force or any(x in changed for x in RESET_DATA_PROPERTIES):

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

            if self.state.size_mode == 'Linear' and self.state.size_att is not None:
                try:
                    size_values = self.layer[self.state.size_att]
                except IncompatibleAttribute:
                    self.disable_invalid_attributes(self.state.size_att)
                    return
            else:
                size_values = None

            if self.state.color_mode == 'Linear' and self.state.cmap_att is not None:
                try:
                    cmap_values = self.layer[self.state.cmap_att]
                except IncompatibleAttribute:
                    self.disable_invalid_attributes(self.state.cmap_att)
                    return
            else:
                cmap_values = None

            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
                self._coords = [], []

            if len(lon) > 0:

                if self._viewer_state.mode in MODES_3D:
                    ref_frame = 'Sky'
                else:
                    ref_frame = self._viewer_state.mode

                if ref_frame == 'Sky':
                    try:
                        coord = SkyCoord(lon, lat, unit=u.deg, frame=self._viewer_state.frame.lower()).icrs
                    except Exception as exc:
                        self.disable(str(exc))
                        return

                    lon = coord.spherical.lon.degree
                    lat = coord.spherical.lat.degree

                # For some reason in 3D mode, when the frame is Sky, we need to
                # shift the longitudes by 180 degrees.
                if self._viewer_state.mode in MODES_3D:
                    lon = lon + 180
                    lon[lon > 360] -= 360

                # FIXME: kpc isn't yet a valid unit in WWT/PyWWT:
                # https://github.com/WorldWideTelescope/wwt-web-client/pull/197
                # for now we set unit to pc and scale values accordingly
                if self._viewer_state.alt_att is not None and self._viewer_state.alt_unit == 'kpc':
                    alt = alt * 1000

                data_kwargs = {}

                tab = Table()

                tab['lon'] = lon * u.degree
                tab['lat'] = lat * u.degree

                if self._viewer_state.alt_att is not None:
                    # FIXME: allow arbitrary units
                    tab['alt'] = alt
                    data_kwargs['alt_att'] = 'alt'

                if size_values is not None:
                    tab['size'] = size_values
                    data_kwargs['size_att'] = 'size'

                if cmap_values is not None:
                    tab['cmap'] = cmap_values
                    data_kwargs['cmap_att'] = 'cmap'

                self.wwt_layer = self.wwt_client.layers.add_table_layer(tab, frame=ref_frame,
                                                                        lon_att='lon', lat_att='lat', **data_kwargs)

                self.wwt_layer.far_side_visible = self._viewer_state.mode in MODES_3D

                self._coords = lon, lat

                force = True

            else:
                return

        if force or 'alt_unit' in changed:
            # FIXME: kpc isn't yet a valid unit in WWT/PyWWT:
            # https://github.com/WorldWideTelescope/wwt-web-client/pull/197
            # for now we set unit to pc and scale values accordingly
            if self._viewer_state.alt_unit == 'kpc':
                self.wwt_layer.alt_unit = u.pc
            else:
                self.wwt_layer.alt_unit = self._viewer_state.alt_unit

        if force or 'alt_type' in changed:
            self.wwt_layer.alt_type = self._viewer_state.alt_type.lower()

        if force or 'size' in changed or 'size_mode' in changed or 'size_scaling' in changed:
            if self.state.size_mode == 'Linear':
                self.wwt_layer.size_scale = self.state.size_scaling
            else:
                self.wwt_layer.size_scale = self.state.size * 5 * self.state.size_scaling

        if force or 'color' in changed:
            self.wwt_layer.color = self.state.color

        if force or 'alpha' in changed:
            self.wwt_layer.opacity = self.state.alpha

        if force or 'size_vmin' in changed:
            self.wwt_layer.size_vmin = self.state.size_vmin

        if force or 'size_vmax' in changed:
            self.wwt_layer.size_vmax = self.state.size_vmax

        if force or 'cmap_vmin' in changed:
            self.wwt_layer.cmap_vmin = self.state.cmap_vmin

        if force or 'cmap_vmax' in changed:
            self.wwt_layer.cmap_vmax = self.state.cmap_vmax

        if force or 'cmap' in changed:
            self.wwt_layer.cmap = self.state.cmap

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
