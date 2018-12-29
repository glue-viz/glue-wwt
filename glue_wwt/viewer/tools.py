from __future__ import absolute_import, division, print_function

from qtpy import compat
from glue.viewers.common.qt.tool import Tool
from glue.config import viewer_tool


@viewer_tool
class SaveTool(Tool):

    icon = 'glue_filesave'
    tool_id = 'wwt:save'
    action_text = 'Save the view to a file'
    tool_tip = 'Save the view to a file'

    def activate(self):

        filename, _ = compat.getsavefilename(caption='Save File',
                                             filters='PNG Files (*.png);;'
                                                      'JPEG Files (*.jpeg);;'
                                                      'TIFF Files (*.tiff);;',
                                             selectedfilter='PNG Files (*.png);;')

        # This indicates that the user cancelled
        if not filename:
            return

        self.viewer._wwt_client.render(filename)
