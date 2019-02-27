from __future__ import absolute_import, division, print_function

from distutils.version import LooseVersion

import pywwt

from astropy import units as u

from glue.config import colormaps

from glue.external.echo import (CallbackProperty, ListCallbackProperty,
                                SelectionCallbackProperty, delay_callback,
                                keep_in_sync)

from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.core.state_objects import StateAttributeLimitsHelper
from glue.viewers.common.state import ViewerState, LayerState

PYWWT_LT_06 = LooseVersion(pywwt.__version__) < '0.6'

MODES_BODIES = ['Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars',
                'Jupiter', 'Callisto', 'Europa', 'Ganymede', 'Io', 'Saturn',
                'Uranus', 'Neptune', 'Pluto']

MODES_3D = ['Solar System', 'Milky Way', 'Universe']

ALT_UNITS = [u.m, u.km, u.AU, u.lyr, u.pc, u.kpc, u.Mpc,
             u.imperial.ft, u.imperial.inch, u.imperial.mi]

ALT_TYPES = ['Altitude', 'Depth', 'Distance']

CELESTIAL_FRAMES = ['ICRS', 'FK5', 'FK4', 'Galactic']


class WWTDataViewerState(ViewerState):

    mode = SelectionCallbackProperty(default_index=0)
    frame = SelectionCallbackProperty(default_index=0)

    lon_att = SelectionCallbackProperty(default_index=0)
    lat_att = SelectionCallbackProperty(default_index=1)
    alt_att = SelectionCallbackProperty(default_index=0)
    alt_unit = SelectionCallbackProperty(default_index=0)
    alt_type = SelectionCallbackProperty(default_index=0)

    foreground = SelectionCallbackProperty(default_index=1)
    foreground_opacity = CallbackProperty(1)
    background = SelectionCallbackProperty(default_index=8)

    galactic = CallbackProperty(False)

    layers = ListCallbackProperty()

    # For now we need to include this here otherwise when loading files, the
    # imagery layers are only available asynchronously and the session loading
    # fails.
    imagery_layers = ListCallbackProperty()

    def __init__(self, **kwargs):

        super(WWTDataViewerState, self).__init__()

        WWTDataViewerState.mode.set_choices(self, ['Sky'] + MODES_3D + MODES_BODIES)
        WWTDataViewerState.frame.set_choices(self, CELESTIAL_FRAMES)
        WWTDataViewerState.alt_unit.set_choices(self, [str(x) for x in ALT_UNITS])
        WWTDataViewerState.alt_type.set_choices(self, ALT_TYPES)

        self.add_callback('imagery_layers', self._update_imagery_layers)

        self.lon_att_helper = ComponentIDComboHelper(self, 'lon_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False)

        self.lat_att_helper = ComponentIDComboHelper(self, 'lat_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False)

        self.alt_att_helper = ComponentIDComboHelper(self, 'alt_att',
                                                     numeric=True,
                                                     categorical=False,
                                                     world_coord=True,
                                                     pixel_coord=False,
                                                     none='None')

        self.add_callback('layers', self._on_layers_changed)
        self._on_layers_changed()

        self.update_from_dict(kwargs)

    def _on_layers_changed(self, *args):
        self.lon_att_helper.set_multiple_data(self.layers_data)
        self.lat_att_helper.set_multiple_data(self.layers_data)
        self.alt_att_helper.set_multiple_data(self.layers_data)

    def _update_imagery_layers(self, *args):
        WWTDataViewerState.foreground.set_choices(self, self.imagery_layers)
        WWTDataViewerState.background.set_choices(self, self.imagery_layers)

    def _update_priority(self, name):
        if name == 'layers':
            return 2
        elif name == 'imagery_layers':
            return 1
        else:
            return 0


class WWTLayerState(LayerState):
    """
    A state object for volume layers
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

    size_limits_cache = CallbackProperty({})
    cmap_limits_cache = CallbackProperty({})

    def __init__(self, layer=None, **kwargs):

        self._sync_markersize = None

        super(WWTLayerState, self).__init__(layer=layer)

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

        # Color and size encoding depending on attributes is only available
        # in PyWWT 0.6 or later.
        if PYWWT_LT_06:
            modes = ['Fixed']
        else:
            modes = ['Fixed', 'Linear']

        WWTLayerState.color_mode.set_choices(self, modes)
        WWTLayerState.size_mode.set_choices(self, modes)

        self.update_from_dict(kwargs)

    def _on_layer_change(self, layer=None):

        with delay_callback(self, 'cmap_vmin', 'cmap_vmax', 'size_vmin', 'size_vmax'):

            if self.layer is None:
                self.cmap_att_helper.set_multiple_data([])
                self.size_att_helper.set_multiple_data([])
            else:
                self.cmap_att_helper.set_multiple_data([self.layer])
                self.size_att_helper.set_multiple_data([self.layer])

    def update_priority(self, name):
        return 0 if name.endswith(('vmin', 'vmax')) else 1

    def _layer_changed(self):

        super(WWTLayerState, self)._layer_changed()

        if self._sync_markersize is not None:
            self._sync_markersize.stop_syncing()

        if self.layer is not None:
            self.size = self.layer.style.markersize
            self._sync_markersize = keep_in_sync(self, 'size', self.layer.style, 'markersize')

    def flip_size(self):
        self.size_lim_helper.flip_limits()

    def flip_cmap(self):
        self.cmap_lim_helper.flip_limits()
