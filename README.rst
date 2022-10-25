Glue WorldWide Telescope plugin (experimental)
==============================================

|Actions Status| |Coverage Status|

Requirements
------------

Note that this plugin requires `glue <http://glueviz.org/>`__ to be
installed - see `this
page <http://glueviz.org/en/latest/installation.html>`__ for
instructions on installing glue.

Installing
----------

If you are using conda, you can easily install the
plugin and all the required dependencies with::

    conda install -c glueviz glue-wwt

Alternatively, if you don't use conda, be sure to install the above
dependencies then install the plugin with::

    pip install glue-wwt

In both cases this will auto-register the plugin with Glue.
Now simply start up Glue,
open a tabular dataset, drag it onto the main canvas, then select
'WorldWideTelescope (WWT)'.

Testing
-------

To run the tests, do::

    py.test glue_wwt

at the root of the repository. This requires the
`pytest <http://pytest.org>`__ module to be installed.

.. |Actions Status| image:: https://github.com/glue-viz/glue-wwt/workflows/ci_workflows/badge.svg
    :target: https://github.com/glue-viz/glue-wwt/actions
    :alt: Glue WWT's GitHub Actions CI Status
.. |Coverage Status| image:: https://codecov.io/gh/glue-viz/glue-wwt/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/glue-viz/glue-wwt
    :alt: Glue WWT's Coverage Status
