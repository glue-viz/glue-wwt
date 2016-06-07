from __future__ import absolute_import, division, print_function

def setup():
    from .data_viewer import MyViewer
    from glue.config import qt_client
    qt_client.add(MyViewer)
