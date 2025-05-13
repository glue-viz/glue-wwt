from __future__ import absolute_import, division, print_function

from os.path import abspath, dirname, join

from glue.viewers.common.tool import Tool
from glue.config import viewer_tool


@viewer_tool
class RefreshTileCacheTool(Tool):

    icon = abspath(join(dirname(__file__), 'refresh_cache.png'))
    tool_id = 'wwt:refresh_cache'
    action_text = 'Refresh the WWT tile cache'
    tool_tip = 'Refresh the WWT tile cache'

    def activate(self):
        self.viewer._wwt.refresh_tile_cache()
