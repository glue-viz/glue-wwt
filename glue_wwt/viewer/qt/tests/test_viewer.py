import io
import os
import sys

import pytest

from unittest.mock import patch

from qtpy import compat

from glue_qt.app import GlueApplication

from ..viewer import WWTQtViewer

from ...tests.test_base import BaseTestWWTDataViewer

DATA = os.path.join(os.path.dirname(__file__), 'data')


class WWTQtViewerBlocking(WWTQtViewer):

    def _initialize_wwt(self):
        from pywwt.qt import WWTQtClient
        self._wwt = WWTQtClient(block_until_ready=sys.platform != 'win32')


class TestQtWWTDataViewer(BaseTestWWTDataViewer):

    def _create_new_application(self):
        self.application = GlueApplication()

    def _create_new_viewer(self):
        self.viewer = self.application.new_data_viewer(WWTQtViewerBlocking)

    def test_load_session_back_compat(self):

        # Make sure that old session files continue to work

        app = GlueApplication.restore_session(os.path.join(DATA, 'wwt_simple.glu'))
        viewer_state = app.viewers[0][0].state
        assert viewer_state.lon_att.label == 'a'
        assert viewer_state.lat_att.label == 'b'
        assert viewer_state.frame == 'Galactic'

    def test_load_session_back_compat_pre_split(self):

        # Make sure that old session files from before the Qt/Jupyter split work

        app = GlueApplication.restore_session(os.path.join(DATA, 'wwt_pre_split.glu'))
        assert isinstance(app.viewers[0][0], WWTQtViewer)

    # @pytest.mark.skipif(sys.platform == 'win32', reason="Test causes issues on Windows")
    @pytest.mark.xfail(reason="'asynchronous' keyword unsupported by some JavaScript versions")
    def test_save_tour(self, tmpdir):

        filename = tmpdir.join('mytour.wtt').strpath
        self.viewer.add_data(self.d)
        with patch.object(compat, 'getsavefilename', return_value=(filename, None)):
            self.viewer.toolbar.tools['save'].subtools[1].activate()

        assert os.path.exists(filename)
        with io.open(filename, newline='') as f:
            assert f.read().startswith("<?xml version='1.0' encoding='UTF-8'?>\r\n<FileCabinet")
