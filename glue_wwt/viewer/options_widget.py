from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets
from glue.utils.qt import load_ui
from glue.external.echo.qt import autoconnect_callbacks_to_qt

__all__ = ['WWTOptionPanel']


class WWTOptionPanel(QtWidgets.QWidget):

    def __init__(self, viewer_state, parent=None):

        super(WWTOptionPanel, self).__init__(parent=parent)

        self._viewer_state = viewer_state

        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        connect_kwargs = {'foreground_opacity': dict(value_range=(0, 100))}

        autoconnect_callbacks_to_qt(self._viewer_state, self.ui, connect_kwargs)
