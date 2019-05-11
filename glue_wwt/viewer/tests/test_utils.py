from __future__ import absolute_import, division, print_function

import numpy as np
from numpy.testing import assert_allclose

from ..utils import center_fov


def test_center_fov():

    lon = np.array([3, 3])
    lat = np.array([1, 3])

    lon_c, lat_c, fov = center_fov(lon, lat)

    assert_allclose(lon_c, 3)
    assert_allclose(lat_c, 2)
    assert_allclose(fov, 1)


def test_center_fov_non_finite():

    # Make sure non-finite values are ignored

    lon = np.array([3, 3, np.nan, np.inf])
    lat = np.array([1, 3, np.nan, np.inf])

    lon_c, lat_c, fov = center_fov(lon, lat)

    assert_allclose(lon_c, 3)
    assert_allclose(lat_c, 2)
    assert_allclose(fov, 1)
