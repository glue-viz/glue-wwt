from __future__ import absolute_import, division, print_function

from collections import defaultdict

import numpy as np

try:
    from matplotlib.colors import to_hex
except ImportError:
    from matplotlib.colors import rgb2hex, colorConverter
    def to_hex(color):  # noqa
        return str(rgb2hex(colorConverter.to_rgb(color)))

from .utils import center_fov

__all__ = ['WWTMarkersHelper']


class WWTMarkersHelper(object):
    """
    This class takes care of showing all the markers in WWT, and tries to make
    updates with minimal Javascript code.
    """

    def __init__(self, wwt_widget):
        self._wwt_widget = wwt_widget
        self.layers = {}
        self.markers = defaultdict(list)
        self._js_paused = False
        self._js_buffer = ''

    def run_js(self, js):
        if not js.strip():
            return
        if self._js_paused:
            self._js_buffer += js
        else:
            self._wwt_widget.run_js(js)

    def pause_js(self):
        self._js_paused = True

    def resume_js(self):
        self._js_paused = False
        self.run_js(self._js_buffer)
        self._js_buffer = ''

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
        self.run_js("wwt.gotoRaDecZoom({0}, {1}, {2}, false);".format(ra_cen, dec_cen, fov))

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

        js_code = ""

        if force_update or 'zorder' in kwargs or 'visible' in kwargs or 'coords' in kwargs:

            for marker in self.markers[label]:
                js_code += 'wwt.removeAnnotation({0});\n'.format(marker)

            self.markers[label] = []

            if not self.layers[label]['visible']:
                self.run_js(js_code)
                return

            if self.layers[label]['coords'] is None:
                self.run_js(js_code)
                return

            for imarker, marker in enumerate(range(len(self.layers[label]['coords'][0]))):
                marker_name = "marker_{0}_{1}".format(label, imarker)
                js_code += '{0} = wwt.createCircle(true);\n'.format(marker_name)
                js_code += 'wwt.addAnnotation({0});\n'.format(marker_name)
                self.markers[label].append(marker_name)

            force_update = True

        if force_update or 'coords' in kwargs:
            ra, dec = self.layers[label]['coords']
            for imarker, marker in enumerate(self.markers[label]):
                js_code += '{0}.setCenter({1}, {2});\n'.format(marker, ra[imarker], dec[imarker])

        if force_update or 'size' in kwargs:
            size = self.layers[label]['size']
            for marker in self.markers[label]:
                js_code += '{0}.set_radius({1});\n'.format(marker, size)

        if force_update or 'color' in kwargs:
            color = to_hex(self.layers[label]['color'])
            for marker in self.markers[label]:
                js_code += '{0}.set_fillColor("{1}");\n'.format(marker, color)
                js_code += '{0}.set_lineColor("{1}");\n'.format(marker, color)

        if force_update or 'alpha' in kwargs:
            alpha = self.layers[label]['alpha']
            for marker in self.markers[label]:
                js_code += '{0}.set_opacity({1});\n'.format(marker, alpha)

        self.run_js(js_code)
