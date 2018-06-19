from __future__ import absolute_import, division, print_function

from collections import defaultdict

import numpy as np

from astropy import units as u
from astropy.coordinates import SkyCoord

from .utils import center_fov

__all__ = ['WWTMarkersHelper']


class WWTMarkersHelper(object):
    """
    This class takes care of showing all the markers in WWT.
    """

    def __init__(self, wwt_client):
        self._wwt_client = wwt_client
        self.layers = {}
        self.markers = defaultdict(list)

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

    def deallocate(self, label):
        self.layers.pop(label)

    def center(self, label):
        if self.layers[label]['coords'] is None:
            return
        ra, dec = self.layers[label]['coords']
        ra_cen, dec_cen, sep_max = center_fov(ra, dec)
        if ra_cen is None:
            return
        fov = min(60, sep_max * 3)
        self._wwt_client.center_on_coordinates(SkyCoord(ra_cen, dec_cen, unit=u.degree, frame='icrs'), fov * u.degree)

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

        if force_update or 'zorder' in kwargs or 'visible' in kwargs or 'coords' in kwargs:

            if not self.layers[label]['visible'] or self.layers[label]['coords'] is None:
                for marker in self.markers[label]:
                    marker.remove()
                self.markers[label] = []
                return

            # Figure out the number of annotations needed
            n_markers = len(self.layers[label]['coords'][0])

            # Adjust the number of Circle objects accordingly
            if len(self.markers[label]) < n_markers:
                for imarker in range(n_markers - len(self.markers[label])):
                    self.markers[label].append(self._wwt_client.add_circle(fill=True))
            elif len(self.markers[label]) > n_markers:
                for imarker in range(len(self.markers[label]) - n_markers):
                    self.markers[label][imarker].remove()
                self.markers[label] = self.markers[label][:n_markers]

            force_update = True

        if force_update or 'coords' in kwargs:
            ra, dec = self.layers[label]['coords']
            coords = SkyCoord(ra, dec, unit=u.degree, frame='icrs')
            for imarker, marker in enumerate(self.markers[label]):
                marker.set_center(coords[imarker])

        if force_update or 'size' in kwargs:
            size = self.layers[label]['size']
            for marker in self.markers[label]:
                marker.radius = size * u.pix

        if force_update or 'color' in kwargs:
            color = self.layers[label]['color']
            for marker in self.markers[label]:
                marker.fill_color = color
                marker.line_color = color

        if force_update or 'alpha' in kwargs:
            alpha = self.layers[label]['alpha']
            for marker in self.markers[label]:
                marker.opacity = alpha
