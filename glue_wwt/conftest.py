from __future__ import absolute_import, division, print_function

import os

# The application has to always be referenced to avoid being shut down, so we
# keep a reference to it here
app = None


def pytest_configure(config):

    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--single-process'

    global app

    # We need to import PyWWT before setting up a QApplication since the
    # WebEngine widgets require this.
    from pywwt.qt import WWTQtClient  # noqa

    from glue.utils.qt import get_qapp
    app = get_qapp()


def pytest_unconfigure(config):
    global app
    app.quit()
    app = None
