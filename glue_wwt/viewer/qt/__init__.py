def setup():
    from .viewer import WWTQtViewer
    from glue.config import qt_client
    qt_client.add(WWTQtViewer)
