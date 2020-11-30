from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets
from glue.utils.qt import load_ui
from echo.qt import autoconnect_callbacks_to_qt

from .viewer_state import MODES_BODIES

__all__ = ['WWTOptionPanel']


class WWTOptionPanel(QtWidgets.QWidget):

    def __init__(self, viewer_state, session=None, parent=None):

        super(WWTOptionPanel, self).__init__(parent=parent)

        self._viewer_state = viewer_state

        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        connect_kwargs = {'foreground_opacity': dict(value_range=(0, 1))}

        self._connect = autoconnect_callbacks_to_qt(self._viewer_state, self.ui, connect_kwargs)

        self._viewer_state.add_callback('mode', self._update_visible_options)
        self._viewer_state.add_callback('frame', self._update_visible_options)
        self._update_visible_options()

    def _update_visible_options(self, *args, **kwargs):

        show_frame = self._viewer_state.mode not in MODES_BODIES
        self.ui.label_frame.setVisible(show_frame)
        self.ui.combosel_frame.setVisible(show_frame)

        show_imagery = self._viewer_state.mode == 'Sky'
        self.ui.label_foreground.setVisible(show_imagery)
        self.ui.combosel_foreground.setVisible(show_imagery)
        self.ui.label_opacity.setVisible(show_imagery)
        self.ui.value_foreground_opacity.setVisible(show_imagery)
        self.ui.label_background.setVisible(show_imagery)
        self.ui.combosel_background.setVisible(show_imagery)
        self.ui.bool_galactic.setVisible(show_imagery)

        show_alt = self._viewer_state.mode != 'Sky'
        self.ui.combosel_alt_type.setVisible(show_alt)
        self.ui.combosel_alt_att.setVisible(show_alt)
        self.ui.combosel_alt_unit.setVisible(show_alt)

        if self._viewer_state.mode in MODES_BODIES:
            self.ui.label_lon_att.setText('Longitude')
            self.ui.label_lat_att.setText('Latitude')
        else:
            if self._viewer_state.frame in ['ICRS', 'FK5', 'FK4']:
                self.ui.label_lon_att.setText('RA')
                self.ui.label_lat_att.setText('Dec')
            else:
                self.ui.label_lon_att.setText('Longitude')
                self.ui.label_lat_att.setText('Latitude')
