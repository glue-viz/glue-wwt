from __future__ import absolute_import, division, print_function

import random
import numpy as np

from astropy.wcs import WCS

from glue.logger import logger
from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.core.exceptions import IncompatibleAttribute
from glue.viewers.common.layer_artist import LayerArtist
from glue.viewers.common.state import LayerState
from echo import (CallbackProperty,
                  SelectionCallbackProperty,
                  keep_in_sync)

from pywwt.layers import VALID_COLORMAPS, VALID_STRETCHES


__all__ = ['WWTImageLayerArtist']

RESET_IMAGE_PROPERTIES = ()


class WWTImageLayerState(LayerState):
    """A state object for WWT image layers

    """
    layer = CallbackProperty()
    color = CallbackProperty()
    alpha = CallbackProperty()
    vmin = CallbackProperty()
    vmax = CallbackProperty()

    img_data_att = SelectionCallbackProperty(default_index=0)
    stretch = SelectionCallbackProperty(
        default_index=0,
        choices=VALID_STRETCHES
    )
    cmap = SelectionCallbackProperty(
        default_index=0,
        choices=VALID_COLORMAPS
    )

    def __init__(self, layer=None, **kwargs):
        super(WWTImageLayerState, self).__init__(layer=layer)

        self.color = self.layer.style.color
        self.alpha = self.layer.style.alpha

        self._sync_color = keep_in_sync(self, 'color', self.layer.style, 'color')
        self._sync_alpha = keep_in_sync(self, 'alpha', self.layer.style, 'alpha')

        self.img_data_att_helper = ComponentIDComboHelper(self, 'img_data_att',
                                                          numeric=True,
                                                          categorical=False)

        self.add_callback('layer', self._on_layer_change)
        if layer is not None:
            self._on_layer_change()

        self.update_from_dict(kwargs)

    def _on_layer_change(self, layer=None):
        if self.layer is None:
            self.img_data_att_helper.set_multiple_data([])
        else:
            self.img_data_att_helper.set_multiple_data([self.layer])

    def update_priority(self, name):
        return 0 if name.endswith(('vmin', 'vmax')) else 1


class WWTImageLayerArtist(LayerArtist):
    _layer_state_cls = WWTImageLayerState
    _removed = False

    def __init__(self, viewer_state, wwt_client=None, layer_state=None, layer=None):
        super(WWTImageLayerArtist, self).__init__(viewer_state,
                                                  layer_state=layer_state,
                                                  layer=layer)

        self.wwt_layer = None
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

    def remove(self):
        self._removed = True
        self.clear()

    def _update_presentation(self, force=False, **kwargs):
        changed = set() if force else self.pop_changed_properties()

        logger.debug("updating WWT for 2D image %s" % self.layer.label)

        if self.visible is False:
            self.clear()
            return

        if force or 'mode' in changed or self.wwt_layer is None:
            self.clear()
            force = True

        if force or any(x in changed for x in RESET_IMAGE_PROPERTIES):
            self.clear()

            if not isinstance(self.layer.coords, WCS):
                raise ValueError('oh no not wcs')
            wcs = self.layer.coords

            try:
                data = self.layer[self.state.img_data_att]
            except IncompatibleAttribute:
                self.disable_invalid_attributes(self.state.img_data_att)
                return

            self.wwt_layer = self.wwt_client.layers.add_image_layer((data, wcs))
            default_lims = np.percentile(data, [5., 95.])
            self.state.vmin = default_lims[0]
            self.state.vmax = default_lims[1]
            force = True

        if force or 'alpha' in changed:
            if self.state.alpha is not None:
                self.wwt_layer.opacity = float(self.state.alpha)

        if force or 'stretch' in changed:
            if self.state.stretch is not None:
                self.wwt_layer.stretch = self.state.stretch

        if force or 'vmin' in changed:
            if self.state.vmin is not None:
                self.wwt_layer.vmin = self.state.vmin

        if force or 'vmax' in changed:
            if self.state.vmax is not None:
                self.wwt_layer.vmax = self.state.vmax

        if force or 'cmap' in changed:
            if self.state.cmap is not None:
                self.wwt_layer.cmap = self.state.cmap

        self.enable()

    def redraw(self):
        pass

    def update(self):
        self._update_presentation(force=True)
