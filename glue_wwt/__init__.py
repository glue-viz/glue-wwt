from __future__ import absolute_import, division, print_function

# The following needs to be imported before the application is constructed
try:
    from qtpy.QtWebEngineWidgets import QWebEnginePage  # noqa
except ImportError:
    pass

import importlib.metadata

__version__ = importlib.metadata.version('glue-core')
