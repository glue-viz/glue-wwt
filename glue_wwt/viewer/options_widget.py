from __future__ import absolute_import, division, print_function

import os

from glue.external.qt import QtCore, QtGui
from glue.external.qt.QtCore import Qt
from glue.external.six.moves.urllib.request import urlopen
from glue.utils.qt import load_ui
from glue.utils.qt.widget_properties import ValueProperty, CurrentComboDataProperty

__all__ = ['WWTOptionPanel']


class WWTOptionPanel(QtGui.QWidget):

    background = CurrentComboDataProperty('ui.combo_background')
    foreground = CurrentComboDataProperty('ui.combo_foreground')
    options = ValueProperty('ui.value_opacity')

    def __init__(self, viewer, parent=None):

        super(WWTOptionPanel, self).__init__(parent=parent)

        self.viewer = viewer
        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        self._setup_combos()
        self._connect()

    def _setup_combos(self):
        layers = ['Digitized Sky Survey (Color)',
                  'VLSS: VLA Low-frequency Sky Survey (Radio)',
                  'WMAP ILC 5-Year Cosmic Microwave Background',
                  'SFD Dust Map (Infrared)',
                  'WISE All Sky (Infrared)',
                  'GLIMPSE/MIPSGAL',
                  'Hydrogen Alpha Full Sky Map'][3:]
        labels = ['DSS',
                  'VLSS',
                  'WMAP',
                  'SFD',
                  'WISE',
                  'GLIMPSE',
                  'H Alpha'][3:]
        thumbnails = ['DSS',
                      'VLA',
                      'wmap5yr_ilc_200uk',
                      'dust',
                      'glimpsemipsgaltn',
                      'halpha'][3:]
        base = ('http://www.worldwidetelescope.org/wwtweb/'
                'thumbnail.aspx?name=%s')

        for i, row in enumerate(zip(layers, labels, thumbnails)):
            layer, text, thumb = row
            url = base % thumb
            data = urlopen(url).read()
            pm = QtGui.QPixmap()
            pm.loadFromData(data)
            icon = QtGui.QIcon(pm)

            self.ui.combo_foreground.addItem(icon, text, layer)
            self.ui.combo_foreground.setItemData(i, layer, role=Qt.ToolTipRole)
            self.ui.combo_background.addItem(icon, text, layer)
            self.ui.combo_background.setItemData(i, layer, role=Qt.ToolTipRole)

        self.ui.combo_foreground.setIconSize(QtCore.QSize(60, 60))
        self.ui.combo_background.setIconSize(QtCore.QSize(60, 60))

    def _connect(self):

        self.ui.combo_foreground.currentIndexChanged.connect(self.viewer._update_foreground)
        self.ui.combo_background.currentIndexChanged.connect(self.viewer._update_background)
        self.ui.value_opacity.valueChanged.connect(self.viewer._update_opacity)

        self.opacity = 100
