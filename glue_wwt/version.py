from __future__ import absolute_import, division, print_function

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution('glue-wwt').version
except DistributionNotFound:
    __version__ = 'undefined'
