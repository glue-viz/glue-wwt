import os
from datetime import datetime 

from qtpy.QtWidgets import QDialog

from glue_qt.utils import load_ui

__all__ = ['TimeDialog']


class TimeDialog(QDialog):

    def __init__(self, parent=None):
        super(TimeDialog, self).__init__(parent=parent)

        self.ui = load_ui('time_dialog.ui', self, directory=os.path.dirname(__file__))

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_set_time.clicked.connect(self.accept)

        self.time = None

    def accept(self):
        date = self.ui.date_edit.selectedDate().toPython()
        time = self.ui.time_edit.time().toPython()
        self.time = datetime.combine(date, time)

        super(TimeDialog, self).accept()
