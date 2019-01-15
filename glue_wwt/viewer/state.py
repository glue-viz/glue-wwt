from __future__ import absolute_import, division, print_function

from astropy import units as u

from glue.external.echo import (CallbackProperty, ListCallbackProperty,
                                SelectionCallbackProperty,
                                keep_in_sync)

from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.viewers.common.state import ViewerState, LayerState

from pywwt.layers import VALID_FRAMES

MODES_BODIES = ['Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars',
                'Jupiter', 'Callisto', 'Europa', 'Ganymede', 'Io', 'Saturn',
                'Uranus', 'Neptune', 'Pluto']

MODES_3D = ['Solar System', 'Milky Way', 'Universe']

ALT_UNITS = [u.m, u.km, u.AU, u.lyr, u.pc, u.Mpc,
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

    layer = CallbackProperty()
    color = CallbackProperty()
    size = CallbackProperty()
    alpha = CallbackProperty()
    zorder = CallbackProperty(0)
    visible = CallbackProperty(True)

    def __init__(self, viewer_state=None, **kwargs):

        super(WWTLayerState, self).__init__()

        self.viewer_state = viewer_state

        self.update_from_dict(kwargs)

        self.color = self.layer.style.color
        self.alpha = self.layer.style.alpha
        self.size = self.layer.style.markersize

        self._sync_color = keep_in_sync(self, 'color', self.layer.style, 'color')
        self._sync_alpha = keep_in_sync(self, 'alpha', self.layer.style, 'alpha')
        self._sync_size = keep_in_sync(self, 'size', self.layer.style, 'markersize')

    def _update_priority(self, name):
        if name == 'layer':
            return 1
        else:
            return 0

    def _att_changed(self, *args):
        self.viewer_state._sync_all_attributes(reference=self)
