# Test class which is common to Qt and Jupyter

from __future__ import absolute_import, division, print_function

import os

from unittest.mock import MagicMock

from glue.core import ComponentLink, Data, message
from glue.core.tests.test_state import clone

from .test_utils import create_disabled_message

DATA = os.path.join(os.path.dirname(__file__), 'data')


class BaseTestWWTDataViewer(object):

    def setup_method(self, method):
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4], z=[4, 5, 6])
        self.ra_dec_data = Data(ra=[-10, 0, 10], dec=[0, 10, 20])
        self.bad_data_short = Data(x=[-100, 100], y=[-10, 10])
        self.bad_data_long = Data(x=[-100, -90, -80, 80, 90, 100], y=[-10, -7, -3, 3, 7, 10])
        self._create_new_application()
        self.dc = self.application.data_collection
        self.dc.append(self.d)
        self.dc.append(self.ra_dec_data)
        self.dc.append(self.bad_data_short)
        self.dc.append(self.bad_data_long)
        self.dc.add_link(ComponentLink([self.d.id['x']], self.d.id['y']))
        self.hub = self.dc.hub
        self.session = self.application.session
        self._create_new_viewer()
        self.options = self.viewer.options_widget()

    def teardown_method(self, method):
        self.viewer.close(warn=False)
        self.viewer = None
        self.application.close()
        self.application = None

    def register(self):
        self.viewer.register_to_hub(self.hub)

    def test_add_data(self):
        self.viewer.add_data(self.d)
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']

    def test_center(self):
        self.viewer.add_data(self.d)
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']
        self.viewer.layers[0].center()

    def test_new_subset_group(self):
        # Make sure only the subset for data that is already inside the viewer
        # is added.
        d2 = Data(a=[4, 5, 6])
        self.dc.append(d2)
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1
        self.dc.new_subset_group(subset_state=self.d.id['x'] > 1, label='A')
        assert len(self.viewer.layers) == 2

    def test_double_add_ignored(self):
        assert len(self.viewer.layers) == 0
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 1

    def test_remove_data(self):
        self.register()
        self.viewer.add_data(self.d)
        layer = self.viewer._layer_artist_container[self.d][0]

        layer.clear = MagicMock()
        self.hub.broadcast(message.DataCollectionDeleteMessage(self.dc,
                                                               data=self.d))
        # TODO: the following currently fails but is not critical, so we
        #       skip for now.
        # assert layer.clear.call_count == 1
        assert self.d not in self.viewer._layer_artist_container

    def test_remove_subset(self):
        self.register()
        s = self.d.new_subset()
        self.viewer.add_subset(s)

        layer = self.viewer._layer_artist_container[s][0]
        layer.clear = MagicMock()

        self.hub.broadcast(message.SubsetDeleteMessage(s))

        # assert layer.clear.call_count == 1
        assert s not in self.viewer._layer_artist_container

    def test_subsets_added_with_data(self):
        s = self.d.new_subset()
        self.viewer.add_data(self.d)
        assert s in self.viewer._layer_artist_container

    def test_subsets_live_added(self):
        self.register()
        self.viewer.add_data(self.d)
        s = self.d.new_subset()
        assert s in self.viewer._layer_artist_container

    def test_clone(self):

        self.viewer.add_data(self.d)
        self.viewer.state.layers[0].ra_att = self.d.id['y']
        self.viewer.state.layers[0].dec_att = self.d.id['x']

        application2 = clone(self.application)

        application2.viewers[0][0]

    def test_changing_alt_back_to_none(self):

        # Regression test for a bug which caused an exception to
        # happen when changing the altitude attribute back to None
        self.viewer.add_data(self.d)
        self.viewer.state.mode = 'Milky Way'
        self.viewer.state.lon_att = self.d.id['x']
        self.viewer.state.lat_att = self.d.id['y']
        self.viewer.state.alt_att = self.d.id['z']
        self.viewer.state.alt_unit = 'kpc'
        self.viewer.state.alt_att = None

    def test_remove_layer(self):

        # Make sure that _update_markers doesn't get called after removing a
        # layer. This is a regression test for
        # https://github.com/glue-viz/glue-wwt/issues/54

        self.register()
        self.d.add_subset(self.d.id['x'] > 1)
        self.viewer.add_data(self.d)
        assert len(self.viewer.layers) == 2

        subset_layer = self.viewer.layers[1]

        subset_layer.wwt_client.layers.add_table_layer = MagicMock()

        self.viewer.remove_subset(self.d.subsets[0])
        assert len(self.viewer.layers) == 1
        assert subset_layer.wwt_client.layers.add_table_layer.call_count == 0
        assert subset_layer.wwt_layer is None

    def test_skycoord_exception_message_short(self):
        self.viewer.add_data(self.bad_data_short)
        self.viewer.state.lat_att = self.bad_data_short.id['x']
        layer = self.viewer.layers[-1]
        assert not layer.enabled
        disabled_reason = "Latitude angle(s) must be within -90 deg <= angle <= 90 deg, " \
                          f"got {self.bad_data_short['x']}"
        disabled_message = create_disabled_message(disabled_reason)
        assert layer.disabled_message == disabled_message

    def test_skycoord_exception_message_long(self):
        self.viewer.add_data(self.bad_data_long)
        self.viewer.state.lat_att = self.bad_data_long.id['x']
        layer = self.viewer.layers[-1]
        assert not layer.enabled
        disabled_reason = "Latitude angle(s) must be within -90 deg <= angle <= 90 deg, " \
                          "got -100 deg <= angle <= 100 deg"
        disabled_message = create_disabled_message(disabled_reason)
        assert layer.disabled_message == disabled_message

    def test_guess_ra_dec_columns(self):

        # If the first `Data` that we add has columns that should lend
        # themselves towards guessable RA/Dec components, check that
        # the viewer state attributes get set correctly
        self.viewer.add_data(self.ra_dec_data)
        assert self.viewer.state.lon_att is self.ra_dec_data.id['ra']
        assert self.viewer.state.lat_att is self.ra_dec_data.id['dec']

    def test_no_guess_ra_dec_columns(self):

        # Check that we correctly DON'T guess RA/Dec columns
        self.viewer.add_data(self.d)
        assert self.viewer.state.lon_att is self.d.id['x']
        assert self.viewer.state.lat_att is self.d.id['y']

        # Check that if we add a second `Data` with valid RA/Dec behavior,
        # we don't override the current state
        self.viewer.add_data(self.ra_dec_data)
        assert self.viewer.state.lon_att is self.d.id['x']
        assert self.viewer.state.lat_att is self.d.id['y']

    # TODO: determine if the following test is the desired behavior
    # def test_subsets_not_live_added_if_data_not_present(self):
    #     self.register()
    #     s = self.d.new_subset()
    #     assert s not in self.viewer

    # def test_updated_on_coordinate_change(self):
    #     self.register()
    #     self.viewer.add_data(self.d)
    #     self.viewer.state.layers[0].ra_att = self.d.id['x']
    #     self.viewer.state.layers[0].dec_att = self.d.id['y']
    #     artist = self.viewer._layer_artist_container[self.d][0]
    #     self.viewer._update_layer = MagicMock()
    #     self.viewer.state.layers[0].ra_att = self.d.id['y']
    #     self.viewer._update_layer.call_count > 0
