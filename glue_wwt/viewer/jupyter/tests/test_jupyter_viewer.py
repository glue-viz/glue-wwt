import os

import pytest

from glue_jupyter.app import JupyterApplication

from ..jupyter_viewer import WWTJupyterViewer

from ...tests.test_base import BaseTestWWTDataViewer

DATA = os.path.join(os.path.dirname(__file__), 'data')


# class WWTJupyterViewerBlocking(WWTJupyterViewer):

#     def _initialize_wwt(self):
#         from pywwt.jupyter import WWTJupyterWidget
#         self._wwt = WWTJupyterWidget(block_until_ready=sys.platform != 'win32')


@pytest.mark.xfail
class TestJupyterWWTDataViewer(BaseTestWWTDataViewer):

    def _create_new_application(self):
        self.application = JupyterApplication()

    def _create_new_viewer(self):
        self.viewer = self.application.new_data_viewer(WWTJupyterViewer)
