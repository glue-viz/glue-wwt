from __future__ import absolute_import, division, print_function

__version__ = "0.0.dev"


def setup():
    from .viewer.data_viewer import WWTDataViewer
    from glue.config import qt_client
    qt_client.add(WWTDataViewer)
