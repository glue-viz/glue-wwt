from __future__ import absolute_import, division, print_function

# The following needs to be imported before the application is constructed
try:
    from qtpy.QtWebEngineWidgets import QWebEnginePage  # noqa
except ImportError:
    pass

import importlib.metadata

__version__ = importlib.metadata.version('glue-core')

# Ensure we can read old session files
from glue.core.state import PATH_PATCHES

PATH_PATCHES[
    "glue_wwt.viewer.data_viewer.WWTDataViewer"
] = "glue_wwt.viewer.qt.viewer.WWTQtViewer"

PATH_PATCHES[
    "glue_wwt.viewer.qt_data_viewer.WWTQtViewer"
] = "glue_wwt.viewer.qt.viewer.WWTQtViewer"

del PATH_PATCHES
