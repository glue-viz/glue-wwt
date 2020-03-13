from __future__ import absolute_import, division, print_function

from glue.viewers.common.qt.data_viewer import DataViewer

from .data_viewer import WWTDataViewerBase
from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist
from .options_widget import WWTOptionPanel
from .image_style_editor import WWTImageStyleEditor
from .table_style_editor import WWTTableStyleEditor

# We import the following to register the save tool
from . import tools  # noqa

__all__ = ['WWTQtViewer']


class WWTQtViewer(WWTDataViewerBase, DataViewer):
    _options_cls = WWTOptionPanel

    _layer_style_widget_cls = {
        WWTImageLayerArtist: WWTImageStyleEditor,
        WWTTableLayerArtist: WWTTableStyleEditor,
    }

    subtools = {'save': ['wwt:save', 'wwt:savetour']}

    def __init__(self, session, parent=None, state=None):
        DataViewer.__init__(self, session, parent=None, state=state)
        WWTDataViewerBase.__init__(self)

        self.setCentralWidget(self._wwt.widget)
        self.resize(self._wwt.widget.size())
        self.setWindowTitle("Earth/Planet/Sky Viewer (WWT)")

        self.options_widget().setEnabled(False)
        self.layer_view().setEnabled(False)

        self._wwt.widget.page.wwt_ready.connect(self._on_wwt_ready)

    def _initialize_wwt(self):
        from pywwt.qt import WWTQtClient
        self._wwt = WWTQtClient()

    def closeEvent(self, event):
        self._wwt.widget.close()
        return super(WWTQtViewer, self).closeEvent(event)

    def _on_wwt_ready(self):
        self.options_widget().setEnabled(True)
        self.layer_view().setEnabled(True)


# To ensure backward compatibility with old session files, we need to add the
# Qt viewer to the data_viewer namespace
from . import data_viewer  # noqa
data_viewer.WWTDataViewer = WWTQtViewer
