from __future__ import absolute_import, division, print_function

import numpy as np

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from .utils import center_fov

__all__ = ['WWTMarkersHelper']


# The empty table can't actually be empty
EMPTY_TABLE = Table()
EMPTY_TABLE['ra'] = [0.]
EMPTY_TABLE['dec'] = [0.]


class WWTMarkersHelper(object):
    """
    This class takes care of showing all the markers in WWT.
    """

    def __init__(self, wwt_client):
        self._wwt_client = wwt_client
        self.layers = {}
        self._wwt_layers = {}

    def allocate(self, label):
        if label in self.layers:
            raise ValueError("Layer {0} already exists".format(label))
        else:
            self.layers[label] = {'coords': None,
                                  'color': '0.5',
                                  'alpha': 1.,
                                  'zorder': 0,
                                  'size': 10,
                                  'visible': True}
            self._wwt_layers[label] = self._wwt_client.layers.add_data_layer(table=EMPTY_TABLE, frame='Sky',
                                                                             lon_att='ra', lat_att='dec')

    def deallocate(self, label):
        self.layers.pop(label)
        layer = self._wwt_layers.pop(label)
        layer.remove()

    def center(self, label):
        if self.layers[label]['coords'] is None:
            return
        ra, dec = self.layers[label]['coords']
        ra_cen, dec_cen, sep_max = center_fov(ra, dec)
        if ra_cen is None:
            return
        fov = min(60, sep_max * 3)
        self._wwt_client.center_on_coordinates(SkyCoord(ra_cen, dec_cen, unit=u.degree, frame='icrs'), fov * u.degree, instant=False)

    def set(self, label, **kwargs):
        changed = {}
        for key, value in kwargs.items():

            # Get rid of any values that are not finite or in valid coordinate
            # range since these may cause issues.
            if key == 'coords' and value is not None:
                ra, dec = value
                keep = ((ra >= -360) & (ra <= 360) &
                        (dec >= -90) & (dec <= 90))
                if np.any(keep):
                    value = ra[keep], dec[keep]
                else:
                    value = None

            if (key == 'coords' and value is not None) or value != self.layers[label][key]:
                self.layers[label][key] = value
                changed[key] = value

        if 'zorder' in changed or 'visible' in changed or 'coords' in changed:
            for label in sorted(self.layers, key=lambda x: self.layers[x]['zorder']):
                self._update_layer(label, force_update=True)
        else:
            self._update_layer(label, **changed)

    def _update_layer(self, label, force_update=False, **kwargs):

        # FIXME: support zorder

        if label in self._wwt_layers:
            wwt_layer = self._wwt_layers[label]
        else:
            return

        if force_update or 'visible' in kwargs or 'coords' in kwargs:
            if self.layers[label]['visible'] and self.layers[label]['coords'] is not None:
                ra, dec = self.layers[label]['coords']
                tab = Table()
                tab['ra'] = ra * u.degree
                tab['dec'] = dec * u.degree
                wwt_layer.update_data(table=tab)
            else:
                wwt_layer.update_data(table=EMPTY_TABLE)

        if force_update or 'size' in kwargs:
            wwt_layer.size_scale = self.layers[label]['size'] * 5

        if force_update or 'color' in kwargs:
            wwt_layer.color = self.layers[label]['color']

        if force_update or 'alpha' in kwargs:
            wwt_layer.opacity = self.layers[label]['alpha']
