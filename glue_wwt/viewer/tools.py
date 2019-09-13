from __future__ import absolute_import, division, print_function

import time
from qtpy import compat

from glue.viewers.common.tool import Tool

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

        self.viewer._wwt.render(filename)


SAVE_TOUR_CODE = """
function getViewAsTour() {

  // Get current view as XML and save to the tourxml variable

  wwtlib.WWTControl.singleton.createTour()
  editor = wwtlib.WWTControl.singleton.tourEdit
  editor.addSlide()
  tour = editor.get_tour()
  blb = tour.saveToBlob()

  const reader = new FileReader();

  reader.addEventListener('loadend', (e) => {
  const text = e.srcElement.result;
  tourxml += text;
  });

  // Start reading the blob as text.
  reader.readAsText(blb);

}

getViewAsTour()
"""


@viewer_tool
class SaveTourTool(Tool):

    icon = 'glue_filesave'
    tool_id = 'wwt:savetour'
    action_text = 'Save the view to a tour file'
    tool_tip = 'Save the view to a tour file'

    def activate(self):

        filename, _ = compat.getsavefilename(caption='Save File',
                                             filters='WWT Tour File (*.wtt);;',
                                             selectedfilter='WWT Tour File (*.wtt);;')

        # This indicates that the user cancelled
        if not filename:
            return

        self.viewer._wwt.widget.page.runJavaScript("tourxml = '';", asynchronous=False)
        tourxml = self.viewer._wwt.widget.page.runJavaScript('tourxml;', asynchronous=False)

        self.viewer._wwt.widget.page.runJavaScript(SAVE_TOUR_CODE)

        start = time.time()
        tourxml = None
        while time.time() - start < 10:
            time.sleep(0.1)
            tourxml = self.viewer._wwt.widget.page.runJavaScript('tourxml;', asynchronous=False)
            if tourxml:
                break

        if not tourxml:
            raise Exception("Failed to save tour")

        with open(filename, 'w') as f:
            f.write(tourxml)
