#!/usr/bin/env python

from __future__ import print_function

from setuptools import setup, find_packages

entry_points = """
[glue.plugins]
wwt=glue_wwt:setup
"""

with open('glue_wwt/version.py') as infile:
    exec(infile.read())

with open('README.rst') as infile:
    LONG_DESCRIPTION = infile.read()

install_requires = ['numpy',
                    'glue-core>=0.10',
                    'qtpy',
                    'astropy',
                    'matplotlib',
                    'requests']

setup(name='glue-wwt',
      version=__version__,
      description='Glue WorldWide Telescope plugin',
      long_description=LONG_DESCRIPTION,
      url="https://github.com/glue-viz/glue-wwt",
      author='Thomas Robitaille',
      author_email='thomas.robitaille@gmail.com',
      packages = find_packages(),
      package_data = {'glue_wwt.viewer': ['*.ui', '*.html', '*.js', '*.png']},
      install_requires=install_requires,
      entry_points=entry_points
    )
