#!/usr/bin/env python

from __future__ import print_function

from setuptools import setup, find_packages

entry_points = """
[glue.plugins]
wwt=glue_wwt:setup
"""

try:
    import pypandoc
    LONG_DESCRIPTION = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    with open('README.md') as infile:
        LONG_DESCRIPTION = infile.read()

with open('glue_wwt/version.py') as infile:
    exec(infile.read())

setup(name='glue_wwt',
      version=__version__,
      description='Glue WorldWide Telescope plugin',
      long_description=LONG_DESCRIPTION,
      url="https://github.com/glue-viz/glue-wwt",
      author='',
      author_email='',
      packages = find_packages(),
      package_data = {'glue_wwt.viewer': ['*.ui']},
      entry_points=entry_points
    )
