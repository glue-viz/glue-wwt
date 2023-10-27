from __future__ import absolute_import, division, print_function

import os
from pywwt.core import ViewerNotAvailableError

from qtpy import QtWidgets
from glue_qt.utils import load_ui
from echo.qt import autoconnect_callbacks_to_qt

from .time_dialog import TimeDialog
from .qt_utils import enabled_if_combosel_in, set_enabled_from_checkbox
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

        self.ui.button_set_current_time.clicked.connect(self._current_time_pressed)

        self._viewer_state.add_callback('mode', self._update_visible_options)
        self._viewer_state.add_callback('frame', self._update_visible_options)
        self._viewer_state.add_callback('current_time', self._update_current_time)
        self._setup_widget_dependencies()
        self._update_visible_options()

    def _setup_widget_dependencies(self):
        set_enabled_from_checkbox(self.ui.bool_alt_az_text, self.ui.bool_alt_az_grid)
        set_enabled_from_checkbox(self.ui.color_alt_az_grid_color, self.ui.bool_alt_az_grid)
        set_enabled_from_checkbox(self.ui.bool_ecliptic_text, self.ui.bool_ecliptic_grid)
        set_enabled_from_checkbox(self.ui.color_ecliptic_grid_color, self.ui.bool_ecliptic_grid)
        set_enabled_from_checkbox(self.ui.bool_equatorial_text, self.ui.bool_equatorial_grid)
        set_enabled_from_checkbox(self.ui.color_equatorial_grid_color, self.ui.bool_equatorial_grid)
        set_enabled_from_checkbox(self.ui.bool_galactic_text, self.ui.bool_galactic_grid)
        set_enabled_from_checkbox(self.ui.color_galactic_grid_color, self.ui.bool_galactic_grid)
        set_enabled_from_checkbox(self.ui.color_constellation_figure_color, self.ui.bool_constellation_figures)
        set_enabled_from_checkbox(self.ui.color_ecliptic_color, self.ui.bool_ecliptic)
        set_enabled_from_checkbox(self.ui.color_precession_chart_color, self.ui.bool_precession_chart)
        set_enabled_from_checkbox(self.ui.valuetext_clock_rate, self.ui.bool_play_time)

        enabled_if_combosel_in(self.ui.color_constellation_boundary_color,
                                self.ui.combosel_constellation_boundaries,
                                ['All'])
        enabled_if_combosel_in(self.ui.color_constellation_selection_color,
                                self.ui.combosel_constellation_boundaries,
                                ['All', 'Selection only'])

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

        show_grid_constellations = self._viewer_state.mode in ['Sky', 'Solar System', 'Milky Way', 'Universe']
        for tab in range(1, self.ui.tab_widget.count()):
            self.ui.tab_widget.setTabEnabled(tab, show_grid_constellations)

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

    def _update_current_time(self, *args):
        try:
            self.ui.label_current_time.setText(f"Current Time: {self._viewer_state.current_time.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        except:
            pass

    def _current_time_pressed(self):
        time_playing = self._viewer_state.play_time
        if time_playing:
            self._viewer_state.play_time = False

        dialog = TimeDialog(initial_datetime=self._viewer_state.current_time)
        result = dialog.exec_()

        if result == QtWidgets.QDialog.Accepted and dialog.datetime is not None:
            print(dialog.datetime)
            self._viewer_state.last_set_time = dialog.datetime

        if time_playing:
            self._viewer_state.play_time = True
