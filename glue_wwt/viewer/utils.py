from __future__ import absolute_import, division, print_function

import numpy as np

from astropy import units as u
from astropy.coordinates import angular_separation
from astropy.coordinates.representation import UnitSphericalRepresentation

__all__ = ['center_fov']


def center_fov(lon, lat):

    # We need to filter out any non-finite values
    keep = np.isfinite(lon) & np.isfinite(lat)
    lon, lat = lon[keep], lat[keep]

    lon = u.Quantity(lon, u.deg, copy=False)
    lat = u.Quantity(lat, u.deg, copy=False)

    unit_sph = UnitSphericalRepresentation(lon, lat, copy=False)

    cen = unit_sph.mean()

    sep = angular_separation(lon, lat, cen.lon, cen.lat).to(u.deg).value.max()

    return cen.lon.to(u.deg).value, cen.lat.to(u.deg).value, sep
