from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets

from glue.external.echo.qt import autoconnect_callbacks_to_qt
from glue.utils.qt import load_ui, fix_tab_widget_fontsize


class WWTImageStyleEditor(QtWidgets.QWidget):
    def __init__(self, layer_artist):
        super(WWTImageStyleEditor, self).__init__()
        self.ui = load_ui('image_style_editor.ui', self, directory=os.path.dirname(__file__))
