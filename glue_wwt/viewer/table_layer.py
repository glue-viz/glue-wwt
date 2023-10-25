from __future__ import absolute_import, division, print_function

from .utils import center_fov
from .viewer_state import MODES_3D

from datetime import datetime
import random

from glue.config import colormaps
from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.core.exceptions import IncompatibleAttribute
from glue.core.state_objects import StateAttributeLimitsHelper
from echo import (CallbackProperty,
                  SelectionCallbackProperty, delay_callback,
                  keep_in_sync)
from glue.logger import logger
from glue.viewers.common.layer_artist import LayerArtist
from glue.viewers.common.state import LayerState

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from numpy import datetime_as_string, size


__all__ = ['WWTTableLayerArtist']


RESET_TABLE_PROPERTIES = ('mode', 'frame', 'lon_att', 'lat_att', 'alt_att',
                          'alt_unit', 'size_att', 'cmap_att', 'size_mode',
                          'color_mode', 'time_series', 'time_att')


class WWTTableLayerState(LayerState):
    """
    A state object for WWT layers
    """

    layer = CallbackProperty()
    color = CallbackProperty()
    size = CallbackProperty()
    alpha = CallbackProperty()

    size_mode = SelectionCallbackProperty(default_index=0)
    size = CallbackProperty()
    size_att = SelectionCallbackProperty()
    size_vmin = CallbackProperty()
    size_vmax = CallbackProperty()
    size_scaling = CallbackProperty(1)

    color_mode = SelectionCallbackProperty(default_index=0)
    cmap_att = SelectionCallbackProperty()
    cmap_vmin = CallbackProperty()
    cmap_vmax = CallbackProperty()
    cmap = CallbackProperty()
    cmap_mode = color_mode

    time_att = SelectionCallbackProperty()
    time_decay_value = CallbackProperty(16)
    time_decay_unit = SelectionCallbackProperty(default_index=0, display_func=lambda value: value.long_names[0])
    time_series = CallbackProperty(False)

    size_limits_cache = CallbackProperty({})
    cmap_limits_cache = CallbackProperty({})

    img_data_att = SelectionCallbackProperty(default_index=0)

    def __init__(self, layer=None, **kwargs):

        self._sync_markersize = None

        super(WWTTableLayerState, self).__init__(layer=layer)

        self._sync_color = keep_in_sync(self, 'color', self.layer.style, 'color')
        self._sync_alpha = keep_in_sync(self, 'alpha', self.layer.style, 'alpha')
        self._sync_size = keep_in_sync(self, 'size', self.layer.style, 'markersize')

        self.color = self.layer.style.color
        self.size = self.layer.style.markersize
        self.alpha = self.layer.style.alpha

        self.size_att_helper = ComponentIDComboHelper(self, 'size_att',
                                                      numeric=True,
                                                      categorical=False)
        self.cmap_att_helper = ComponentIDComboHelper(self, 'cmap_att',
                                                      numeric=True,
                                                      categorical=False)
        self.time_att_helper = ComponentIDComboHelper(self, 'time_att',
                                                      datetime=True,
                                                      numeric=False,
                                                      categorical=False)
        self.img_data_att_helper = ComponentIDComboHelper(self, 'img_data_att',
                                                          numeric=True,
                                                          categorical=False)

        self.size_lim_helper = StateAttributeLimitsHelper(self, attribute='size_att',
                                                          lower='size_vmin', upper='size_vmax',
                                                          cache=self.size_limits_cache)

        self.cmap_lim_helper = StateAttributeLimitsHelper(self, attribute='cmap_att',
                                                          lower='cmap_vmin', upper='cmap_vmax',
                                                          cache=self.cmap_limits_cache)

        self.add_callback('layer', self._on_layer_change)
        if layer is not None:
            self._on_layer_change()

        self.cmap = colormaps.members[0][1]

        modes = ['Fixed', 'Linear']
        WWTTableLayerState.color_mode.set_choices(self, modes)
        WWTTableLayerState.size_mode.set_choices(self, modes)
        WWTTableLayerState.time_decay_unit.set_choices(self, [u.day, u.year, u.Myr, u.Gyr])

        self.update_from_dict(kwargs)

    def _on_layer_change(self, layer=None):
        with delay_callback(self, 'cmap_vmin', 'cmap_vmax', 'size_vmin', 'size_vmax'):
            if self.layer is None:
                self.cmap_att_helper.set_multiple_data([])
                self.size_att_helper.set_multiple_data([])
                self.time_att_helper.set_multiple_data([])
                self.img_data_att_helper.set_multiple_data([])
            else:
                self.cmap_att_helper.set_multiple_data([self.layer])
                self.size_att_helper.set_multiple_data([self.layer])
                self.time_att_helper.set_multiple_data([self.layer])
                self.img_data_att_helper.set_multiple_data([self.layer])

    def update_priority(self, name):
        return 0 if name.endswith(('vmin', 'vmax')) else 1

    def _layer_changed(self):

        super(WWTTableLayerState, self)._layer_changed()

        if self._sync_markersize is not None:
            self._sync_markersize.stop_syncing()

        if self.layer is not None:
            self.size = self.layer.style.markersize
            self._sync_markersize = keep_in_sync(self, 'size', self.layer.style, 'markersize')

    def flip_size(self):
        self.size_lim_helper.flip_limits()

    def flip_cmap(self):
        self.cmap_lim_helper.flip_limits()


class WWTTableLayerArtist(LayerArtist):
    _layer_state_cls = WWTTableLayerState
    _removed = False

    def __init__(self, viewer_state, wwt_client=None, layer_state=None, layer=None):
        super(WWTTableLayerArtist, self).__init__(viewer_state,
                                                  layer_state=layer_state,
                                                  layer=layer)

        self.wwt_layer = None
        self._coords = [], []

        self.layer_id = "{0:08x}".format(random.getrandbits(32))
        self.wwt_client = wwt_client

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self.state.add_global_callback(self._update_presentation)
        self._viewer_state.add_global_callback(self._update_presentation)

        self._update_presentation(force=True)

    def clear(self):
        if self.wwt_layer is not None:
            self.wwt_layer.remove()
            self.wwt_layer = None
            self._coords = [], []

    def remove(self):
        self._removed = True
        self.clear()

    def _update_presentation(self, force=False, **kwargs):
        if self._removed:
            return

        changed = set() if force else self.pop_changed_properties()

        if self._viewer_state.lon_att is None or self._viewer_state.lat_att is None:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
            return

        logger.debug("updating WWT for table %s" % self.layer.label)

        if self.visible is False:
            if self.wwt_layer is not None:
                self.wwt_layer.remove()
                self.wwt_layer = None
            return

        if force or 'mode' in changed or self.wwt_layer is None:
            self.clear()
            force = True

        # FIXME: kpc isn't yet a valid unit in WWT/PyWWT:
        # https://github.com/WorldWideTelescope/wwt-web-client/pull/197
        # for now we set unit to pc and scale values accordingly, so if the
        # unit changes we need to refresh the data just in case

        if force or any(x in changed for x in RESET_TABLE_PROPERTIES):
            try:
                lon = self.layer[self._viewer_state.lon_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self._viewer_state.lon_att)
                return

            try:
                lat = self.layer[self._viewer_state.lat_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self._viewer_state.lat_att)
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

            if self.state.time_series and self.state.time_att is not None:
                try:
                    # Providing datetime objects as the time values offers noticeably better performance than either datetime strings or astropy Time objects
                    # This is likely due to the time attribute value validation in pywwt
                    time_values = [datetime.fromisoformat(datetime_as_string(t, unit='s', timezone='UTC')) for t in self.layer[self.state.time_att]]
                except IncompatibleAttribute:
                    self.disable_invalid_attributes(self.state.time_att)
                    return
            else:
                time_values = None

            self.clear()

            if not len(lon):
                return

            if self._viewer_state.mode in MODES_3D:
                ref_frame = 'Sky'
            else:
                ref_frame = self._viewer_state.mode

            if ref_frame == 'Sky':
                try:
                    coord = SkyCoord(lon, lat, unit=u.deg,
                                     frame=self._viewer_state.frame.lower()).icrs
                except Exception:
                    if size(lat) < 5:
                        angle_info = f"{lat}"
                    else:
                        angle_info = f"{lat.min()} deg <= angle <= {lat.max()} deg"
                    disable_msg = f"Latitude angle(s) must be within -90 deg <= angle <= 90 deg, got {angle_info}"
                    self.disable(disable_msg)
                    return

                lon = coord.spherical.lon.degree
                lat = coord.spherical.lat.degree

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

            if time_values is not None:
                tab['time'] = time_values
                data_kwargs['time_series'] = self.state.time_series
                data_kwargs['time_att'] = 'time'

            self.wwt_layer = self.wwt_client.layers.add_table_layer(tab, frame=ref_frame,
                                                                    lon_att='lon', lat_att='lat',
                                                                    selectable=False,
                                                                    **data_kwargs)
            if self.state.time_series:
                self.wwt_layer.time_att = 'time'

            self.wwt_layer.far_side_visible = self._viewer_state.mode in MODES_3D

            self._coords = lon, lat

            force = True

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

        if force or 'time_decay_value' in changed or 'time_decay_unit' in changed:
            self.wwt_layer.time_decay = self.state.time_decay_value * self.state.time_decay_unit

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
        self.wwt_client.center_on_coordinates(SkyCoord(lon_cen, lat_cen,
                                                       unit=u.degree, frame='icrs'),
                                              fov * u.degree, instant=False)

    def redraw(self):
        pass

    def update(self):
        self._update_presentation(force=True)
