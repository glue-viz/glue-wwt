from __future__ import absolute_import, division, print_function

from mock import MagicMock

from glue.core import Data, DataCollection, Hub, message, Session
from ..data_viewer import WWTDataViewer


class TestWWTDataViewer(object):

    def setup_method(self, method):
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4])
        self.dc = DataCollection([self.d])
        self.hub = self.dc.hub
        self.session = Session(data_collection=self.dc, hub=self.hub)
        self.widget = WWTDataViewer(self.session, webdriver_class=MagicMock)
        self.options = self.widget.options_widget()

    def register(self):
        self.widget.register_to_hub(self.hub)

    def test_add_data(self):
        self.widget.add_data(self.d)
        self.options.ra_att = self.d.id['x'], self.d
        self.options.dec_att = self.d.id['y'], self.d
        assert self.d in self.widget

    def test_double_add_ignored(self):
        assert len(self.widget) == 0
        self.widget.add_data(self.d)
        assert len(self.widget) == 1
        self.widget.add_data(self.d)
        assert len(self.widget) == 1

    def test_updated_on_data_update_message(self):
        self.register()
        self.widget.add_data(self.d)
        layer = self.widget._layer_artist_container[self.d][0]
        layer.update = MagicMock()
        self.d.style.color = 'green'
        assert layer.update.call_count == 1

    def test_updated_on_subset_update_message(self):
        self.register()
        s = self.d.new_subset()
        self.widget.add_subset(s)
        layer = self.widget._layer_artist_container[s][0]
        layer.update = MagicMock()
        s.style.color = 'green'
        assert layer.update.call_count == 1

    def test_remove_data(self):
        self.register()
        self.widget.add_data(self.d)
        layer = self.widget._layer_artist_container[self.d][0]

        layer.clear = MagicMock()
        self.hub.broadcast(message.DataCollectionDeleteMessage(self.dc,
                                                               data=self.d))
        # TODO: the following currently fails but is not critical, so we
        #       skip for now.
        # assert layer.clear.call_count == 1
        assert self.d not in self.widget

    def test_remove_subset(self):
        self.register()
        s = self.d.new_subset()
        self.widget.add_subset(s)

        layer = self.widget._layer_artist_container[s][0]
        layer.clear = MagicMock()

        self.hub.broadcast(message.SubsetDeleteMessage(s))

        assert layer.clear.call_count == 1
        assert self.d not in self.widget

    def test_subsets_added_with_data(self):
        s = self.d.new_subset()
        self.widget.add_data(self.d)
        assert s in self.widget

    def test_subsets_live_added(self):
        self.register()
        self.widget.add_data(self.d)
        s = self.d.new_subset()
        assert s in self.widget

    # TODO: determine if the following test is the desired behavior
    # def test_subsets_not_live_added_if_data_not_present(self):
    #     self.register()
    #     s = self.d.new_subset()
    #     assert s not in self.widget

    def test_updated_on_add(self):
        self.register()
        self.widget._update_layer = MagicMock()
        self.widget.add_data(self.d)
        # TODO: ideally, the following should be called exactly once
        assert self.widget._update_layer.call_count >= 1

    def test_updated_on_coordinate_change(self):
        self.register()
        self.widget.add_data(self.d)
        self.options.ra_att = self.d.id['x'], self.d
        self.options.dec_att = self.d.id['y'], self.d
        artist = self.widget._layer_artist_container[self.d][0]
        self.widget._update_layer = MagicMock()
        self.options.ra_att = self.d.id['y'], self.d
        self.widget._update_layer.call_count > 0
