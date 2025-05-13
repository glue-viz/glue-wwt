from __future__ import absolute_import, division, print_function

# The following needs to be imported before the application is constructed
try:
    from qtpy.QtWebEngineWidgets import QWebEnginePage  # noqa
except ImportError:
    pass

import importlib.metadata

__version__ = importlib.metadata.version('glue-core')


def setup_qt():
    from .viewer.qt.qt_data_viewer import WWTQtViewer
    from glue.config import qt_client
    qt_client.add(WWTQtViewer)


def setup_jupyter():
    from .viewer.jupyter.jupyter_viewer import WWTJupyterViewer  # noqa
