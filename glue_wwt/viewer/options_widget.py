from __future__ import absolute_import, division, print_function

import os

from glue.core import Subset
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt
from glue.external.six.moves.urllib.request import urlopen
from glue.utils.qt import load_ui
from glue.utils.qt.widget_properties import ValueProperty, CurrentComboDataProperty, ButtonProperty
from glue.core.qt.data_combo_helper import ComponentIDComboHelper

__all__ = ['WWTOptionPanel']


class WWTOptionPanel(QtWidgets.QWidget):

    ra_att = CurrentComboDataProperty('ui.combo_ra_att')
    dec_att = CurrentComboDataProperty('ui.combo_dec_att')

    background = CurrentComboDataProperty('ui.combo_background')
    opacity = ValueProperty('ui.value_opacity')
    foreground = CurrentComboDataProperty('ui.combo_foreground')

    galactic_plane = ButtonProperty('ui.checkbox_galactic_plane')

    def __init__(self, viewer, parent=None):

        super(WWTOptionPanel, self).__init__(parent=parent)

        self.viewer = viewer
        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        self._setup_combos()
        self._connect()

    @property
    def ra(self):
        if self.ra_att is None:
            return None
        else:
            return self.ra_att[0]

    @property
    def dec(self):
        if self.dec_att is None:
            return None
        else:
            return self.dec_att[0]

    def _setup_combos(self):
        layers = ['Digitized Sky Survey (Color)',
                  'VLSS: VLA Low-frequency Sky Survey (Radio)',
                  'WMAP ILC 5-Year Cosmic Microwave Background',
                  'SFD Dust Map (Infrared)',
                  'WISE All Sky (Infrared)',
                  'GLIMPSE/MIPSGAL',
                  'Hydrogen Alpha Full Sky Map']
        labels = ['DSS',
                  'VLSS',
                  'WMAP',
                  'SFD',
                  'WISE',
                  'GLIMPSE',
                  'H Alpha']
        thumbnails = ['DSS',
                      'VLA',
                      'wmap5yr_ilc_200uk',
                      'dust',
                      'glimpsemipsgaltn',
                      'halpha']
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

        self.ra_att_helper = ComponentIDComboHelper(self.ui.combo_ra_att,
                                                    self.viewer._data,
                                                    categorical=False,
                                                    numeric=True)

        self.dec_att_helper = ComponentIDComboHelper(self.ui.combo_dec_att,
                                                     self.viewer._data,
                                                     categorical=False,
                                                     numeric=True)

    def add_data(self, data):
        # TODO: the following logic should go in the component ID helpers. It
        # isn't quite right at the moment because if there are multiple
        # datasets/subsets with the same components, we only want to show those
        # once.
        if isinstance(data, Subset):
            self.ra_att_helper.append_data(data.data)
            self.dec_att_helper.append_data(data.data)
        else:
            self.ra_att_helper.append_data(data)
            self.dec_att_helper.append_data(data)

    def remove_data(self, data):
        if isinstance(data, Subset):
            self.ra_att_helper.remove_data(data.data)
            self.dec_att_helper.remove_data(data.data)
        else:
            self.ra_att_helper.remove_data(data)
            self.dec_att_helper.remove_data(data)

    def _connect(self):

        self.ui.combo_ra_att.currentIndexChanged.connect(self.viewer._update_all)
        self.ui.combo_dec_att.currentIndexChanged.connect(self.viewer._update_all)

        self.ui.combo_foreground.currentIndexChanged.connect(self.viewer._update_foreground)
        self.ui.combo_background.currentIndexChanged.connect(self.viewer._update_background)
        self.ui.value_opacity.valueChanged.connect(self.viewer._update_opacity)
        self.ui.checkbox_galactic_plane.toggled.connect(self.viewer._update_galactic_plane_mode)

        self.opacity = 100
