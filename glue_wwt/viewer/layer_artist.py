from __future__ import absolute_import, division, print_function

from glue.logger import logger
from glue.core.layer_artist import LayerArtistBase
from glue.core.exceptions import IncompatibleAttribute


__all__ = ['WWTLayer', 'circle']


def circle(x, y, label, color, radius=3):
    result = """%(label)s = wwt.createCircle("%(color)s");
    %(label)s.setCenter(%(x)f, %(y)f);
    %(label)s.set_fillColor("%(color)s");
    %(label)s.set_radius(%(radius)f);""" % {'x': x, 'y': y, 'label': label,
                                            'color': color, 'radius': radius}
    return result


class WWTLayer(LayerArtistBase):

    def __init__(self, layer, driver):
        super(WWTLayer, self).__init__(layer)
        self._driver = driver  # base class stores as "axes"; misnomer here
        self.xatt = None
        self.yatt = None
        self.markers = {}

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        self.update()

    def clear(self):
        js = '\n'.join("wwt.removeAnnotation(%s);" % l
                       for l in self.markers.keys())
        self._driver.run_js(js)
        self.markers = {}

    def _sync_style(self):
        pass

    def update(self, view=None):
        logger.debug("updating WWT for %s" % self.layer.label)
        self.clear()
        layer = self.layer
        if not self.visible:
            return

        try:
            ra = self.layer[self.xatt]
            dec = self.layer[self.yatt]
        except IncompatibleAttribute:
            print("Cannot fetch attributes %s and %s" % (self.xatt, self.yatt))
            return

        for i in range(ra.size):
            label = "marker_%s_%i" % (layer.label.replace(' ', '_').replace('.', '_'), i)
            cmd = circle(ra[i], dec[i], label, layer.style.color)
            self.markers[label] = cmd

        js = '\n'.join(self.markers.values())
        js += '\n'.join(["wwt.addAnnotation(%s);" % l for l in self.markers])
        self._driver.run_js(js)

    def redraw(self):
        """Override MPL superclass, do nothing"""
        pass
