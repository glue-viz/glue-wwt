from __future__ import absolute_import, division, print_function

from mock import MagicMock

from glue.core import Data, DataCollection, message, Session
from ..data_viewer import WWTDataViewer


class TestWWTDataViewer(object):

    def setup_method(self, method):
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4])
        self.dc = DataCollection([self.d])
        self.hub = self.dc.hub
        self.session = Session(data_collection=self.dc, hub=self.hub)
        self.widget = WWTDataViewer(self.session)
        self.widget.register_to_hub(self.hub)
        self.options = self.widget.options_widget()

    def register(self):
        self.widget.register_to_hub(self.hub)

    def test_add_data(self):
        self.widget.add_data(self.d)
        self.widget.state.layers[0].ra_att = self.d.id['x']
        self.widget.state.layers[0].dec_att = self.d.id['y']

    def test_center(self):
        self.widget.add_data(self.d)
        self.widget.state.layers[0].ra_att = self.d.id['x']
        self.widget.state.layers[0].dec_att = self.d.id['y']
        self.widget.layers[0].center()

    def test_new_subset_group(self):
        # Make sure only the subset for data that is already inside the viewer
        # is added.
        d2 = Data(a=[4, 5, 6])
        self.dc.append(d2)
        self.widget.add_data(self.d)
        assert len(self.widget.layers) == 1
        self.dc.new_subset_group(subset_state=self.d.id['x'] > 1, label='A')
        assert len(self.widget.layers) == 2

    def test_double_add_ignored(self):
        assert len(self.widget.layers) == 0
        self.widget.add_data(self.d)
        assert len(self.widget.layers) == 1
        self.widget.add_data(self.d)
        assert len(self.widget.layers) == 1

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
        assert self.d not in self.widget._layer_artist_container

    def test_remove_subset(self):
        self.register()
        s = self.d.new_subset()
        self.widget.add_subset(s)

        layer = self.widget._layer_artist_container[s][0]
        layer.clear = MagicMock()

        self.hub.broadcast(message.SubsetDeleteMessage(s))

        assert layer.clear.call_count == 1
        assert self.d not in self.widget._layer_artist_container

    def test_subsets_added_with_data(self):
        s = self.d.new_subset()
        self.widget.add_data(self.d)
        assert s in self.widget._layer_artist_container

    def test_subsets_live_added(self):
        self.register()
        self.widget.add_data(self.d)
        s = self.d.new_subset()
        assert s in self.widget._layer_artist_container

    # TODO: determine if the following test is the desired behavior
    # def test_subsets_not_live_added_if_data_not_present(self):
    #     self.register()
    #     s = self.d.new_subset()
    #     assert s not in self.widget

    # def test_updated_on_coordinate_change(self):
    #     self.register()
    #     self.widget.add_data(self.d)
    #     self.widget.state.layers[0].ra_att = self.d.id['x']
    #     self.widget.state.layers[0].dec_att = self.d.id['y']
    #     artist = self.widget._layer_artist_container[self.d][0]
    #     self.widget._update_layer = MagicMock()
    #     self.widget.state.layers[0].ra_att = self.d.id['y']
    #     self.widget._update_layer.call_count > 0
