from __future__ import absolute_import, division, print_function

__version__ = '0.4.dev0'

# The following needs to be imported before the application is constructed
from qtpy.QtWebEngineWidgets import QWebEnginePage

def setup():
    from .viewer.data_viewer import WWTDataViewer
    from glue.config import qt_client
    qt_client.add(WWTDataViewer)
