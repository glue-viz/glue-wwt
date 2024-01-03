from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets
from glue_qt.utils import load_ui
from echo.qt import autoconnect_callbacks_to_qt

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

        self.ui.slider_current_time.valueChanged.connect(self._on_slider_changed)

        self._changing_slider_from_time = False

        self._viewer_state.add_callback('mode', self._update_visible_options)
        self._viewer_state.add_callback('frame', self._update_visible_options)
        self._viewer_state.add_callback('current_time', self._update_current_time)
        self._viewer_state.add_callback('layers', self._update_time_bounds)
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
        fraction = (self._viewer_state.current_time - self._viewer_state.min_time) / (self._viewer_state.max_time - self._viewer_state.min_time)
        slider_min = self.ui.slider_current_time.minimum()
        slider_max = self.ui.slider_current_time.maximum()
        value = round(slider_min + fraction * (slider_max - slider_min))
        self._changing_slider_from_time = True
        self.ui.slider_current_time.setValue(value)
        try:
            self.ui.label_current_time.setText(f"Current Time: {self._viewer_state.current_time}")
        except:
            pass

    def _on_slider_changed(self, *args):
        if self._changing_slider_from_time:
            self._changing_slider_from_time = False
            return
        self._viewer_state.play_time = False 
        value = self.ui.slider_current_time.value()
        slider_min = self.ui.slider_current_time.minimum()
        slider_max = self.ui.slider_current_time.maximum()
        fraction = (value - slider_min) / (slider_max - slider_min)
        self._viewer_state.current_time = self._viewer_state.min_time + fraction * (self._viewer_state.max_time - self._viewer_state.min_time)

    def _update_time_bounds(self, *args):
        min_time = self._viewer_state.min_time
        max_time = self._viewer_state.max_time
        for layer_state in self._viewer_state.layers:
            if layer_state.time_att is not None:
                min_time = min(min_time, min(layer_state.layer[layer_state.time_att]))
                max_time = max(max_time, max(layer_state.layer[layer_state.time_att]))

        self._viewer_state.min_time = min_time
        self._viewer_state.max_time = max_time


