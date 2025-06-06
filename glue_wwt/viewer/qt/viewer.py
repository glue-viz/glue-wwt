from __future__ import absolute_import, division, print_function

from qtpy import QtCore

from glue_qt.viewers.common.data_viewer import DataViewer

from ..data_viewer import WWTDataViewerBase
from ..image_layer import WWTImageLayerArtist
from ..table_layer import WWTTableLayerArtist
from .options_widget import WWTOptionPanel
from .image_style_editor import WWTImageStyleEditor
from .table_style_editor import WWTTableStyleEditor

# We import the following to register the save tool
from . import tools as wwt_tools  # noqa

__all__ = ['WWTQtViewer']


class WWTQtViewer(WWTDataViewerBase, DataViewer):
    _options_cls = WWTOptionPanel

    _layer_style_widget_cls = {
        WWTImageLayerArtist: WWTImageStyleEditor,
        WWTTableLayerArtist: WWTTableStyleEditor,
    }

    subtools = {'save': ['wwt:save', 'wwt:savetour']}
    tools = ["save", "wwt:refresh_cache"]

    def __init__(self, session, parent=None, state=None):
        DataViewer.__init__(self, session, parent=None, state=state)
        WWTDataViewerBase.__init__(self)

        self.setCentralWidget(self._wwt.widget)
        self.resize(self._wwt.widget.size())
        self.setWindowTitle("Earth/Planet/Sky Viewer (WWT)")

        self.options_widget().setEnabled(False)
        self.layer_view().setEnabled(False)

        self._wwt.widget.page.wwt_ready.connect(self._on_wwt_ready)

        self.set_status('NOTE ON ZOOMING: use the z/x keys to zoom in/out if scrolling does not work')

    def __del__(self):
        self._cleanup_time_timer()

    def _initialize_wwt(self):
        from pywwt.qt import WWTQtClient
        self._wwt = WWTQtClient()

    def closeEvent(self, event):
        self._cleanup_time_timer()
        self._wwt.widget.close()
        return super(WWTQtViewer, self).closeEvent(event)

    def _on_wwt_ready(self):
        self.options_widget().setEnabled(True)
        self.layer_view().setEnabled(True)

    # NOTE: Qt needs to use its own QTimer class instead of threading

    def _setup_time_timer(self):
        self._current_time_timer = QtCore.QTimer()
        self._current_time_timer.setInterval(1000)
        self._current_time_timer.timeout.connect(self._update_time)
        self._current_time_timer.start()

    def _cleanup_time_timer(self):
        if self._current_time_timer is not None:
            self._current_time_timer.stop()
            self._current_time_timer = None
