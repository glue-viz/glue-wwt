from __future__ import absolute_import, division, print_function

from qtpy import compat

from glue.viewers.common.tool import Tool

from glue.config import viewer_tool


@viewer_tool
class SaveImageTool(Tool):

    icon = 'glue_filesave'
    tool_id = 'wwt:save_image'
    action_text = 'Save the view to an image'
    tool_tip = 'Save the view to an image'

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

@viewer_tool
class SaveHtmlTool(Tool):
    
    icon = 'glue_filesave'
    tool_id = 'wwt:save_html'
    action_text = 'Save the view to an interactive figure'
    tool_tip = 'Save the view to an interactive figure'

    def activate(self):

        filename, _ = compat.getsavefilename(caption='Save File',
                                             filters='ZIP Files (*.zip);;',
                                             selectedfilter='ZIP Files (*.zip);;')

        # This indicates that the user cancelled
        if not filename:
            return

        self.viewer._wwt_client.save_as_html_bundle(filename)

    
