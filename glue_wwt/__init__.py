from __future__ import absolute_import, division, print_function

# The following needs to be imported before the application is constructed
from qtpy.QtWebEngineWidgets import QWebEnginePage  # noqa

from .version import __version__  # noqa


def setup():
    from .viewer.qt_data_viewer import WWTQtViewer
    from glue.config import qt_client
    qt_client.add(WWTQtViewer)
