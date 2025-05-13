from __future__ import absolute_import, division, print_function

import io
import os
import sys

import pytest
from unittest.mock import MagicMock, patch

from qtpy import compat

from glue.core import ComponentLink, Data, message
from glue.core.tests.test_state import clone
from glue_qt.app import GlueApplication

from ..qt_data_viewer import WWTQtViewer
from ...tests.test_utils import create_disabled_message

from ...tests.test_base import BaseTestWWTDataViewer

DATA = os.path.join(os.path.dirname(__file__), 'data')


class WWTQtViewerBlocking(WWTQtViewer):

    def _initialize_wwt(self):
        from pywwt.qt import WWTQtClient
        self._wwt = WWTQtClient(block_until_ready=sys.platform != 'win32')


class TestWWTDataViewer(BaseTestWWTDataViewer):

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
