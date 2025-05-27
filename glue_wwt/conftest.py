from __future__ import absolute_import, division, print_function

import os

try:
    import qtpy  # noqa
    from glue_qt.utils import get_qapp  # noqa
except ImportError:
    GLUEQT_INSTALLED = False
else:
    GLUEQT_INSTALLED = True

try:
    import glue_jupyter  # noqa
except ImportError:
    GLUEJUPYTER_INSTALLED = False
else:
    GLUEJUPYTER_INSTALLED = True


# The application has to always be referenced to avoid being shut down, so we
# keep a reference to it here
if GLUEQT_INSTALLED:
    app = None


def pytest_configure(config):

    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--single-process'

    if GLUEQT_INSTALLED:

        # We need to import PyWWT before setting up a QApplication since the
        # WebEngine widgets require this.
        from pywwt.qt import WWTQtClient  # noqa

        global app
        app = get_qapp()


def pytest_unconfigure(config):
    if GLUEQT_INSTALLED:
        global app
        if app is not None:
            app.quit()
        app = None


def pytest_ignore_collect(collection_path, path, config):
    if path.isdir():
        if "qt" in collection_path.parts:
            return not GLUEQT_INSTALLED
        if "jupyter" in collection_path.parts:
            return not GLUEJUPYTER_INSTALLED
