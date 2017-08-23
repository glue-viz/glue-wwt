Glue WorldWide Telescope plugin (experimental)
==============================================

|Travis Status| |AppVeyor Status|

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

.. |Travis Status| image:: https://travis-ci.org/glue-viz/glue-wwt.svg
   :target: https://travis-ci.org/glue-viz/glue-wwt?branch=master
.. |AppVeyor Status| image:: https://ci.appveyor.com/api/projects/status/8cxo7uvxd8avuj7p/branch/master?svg=true
   :target: https://ci.appveyor.com/project/glue-viz/glue-wwt/branch/master
