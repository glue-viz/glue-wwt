from __future__ import absolute_import, division, print_function

from glue.viewers.common.qt.data_viewer import DataViewer

from .data_viewer import WWTDataViewerBase
from .options_widget import WWTOptionPanel
from .layer_style_editor import WWTLayerStyleEditor

# We import the following to register the save tool
from . import tools  # noqa

__all__ = ['WWTDataViewer']


class WWTDataViewer(WWTDataViewerBase, DataViewer):
    _options_cls = WWTOptionPanel
    _layer_style_widget_cls = WWTLayerStyleEditor

    subtools = {'save': ['wwt:save']}

    def __init__(self, session, parent=None, state=None):
        DataViewer.__init__(self, session, parent=None, state=None)
        WWTDataViewerBase.__init__(self)

        self.setCentralWidget(self._wwt.widget)
        self.resize(self._wwt.widget.size())
        self.setWindowTitle("WorldWide Telescope")

        self.options_widget().setEnabled(False)
        self.layer_view().setEnabled(False)

        self._wwt.widget.page.wwt_ready.connect(self._on_wwt_ready)

    def _initialize_wwt(self):
        from pywwt.qt import WWTQtClient
        self._wwt = WWTQtClient()

    def closeEvent(self, event):
        self._wwt.widget.close()
        return super(WWTDataViewer, self).closeEvent(event)

    def _on_wwt_ready(self):
        self.options_widget().setEnabled(True)
        self.layer_view().setEnabled(True)
