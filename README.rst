Experimental Glue WWT plugin
============================

|Build Status| |Build status|

Requirements
------------

Note that this plugin requires `glue <http://glueviz.org/>`__ to be
installed - see `this
page <http://glueviz.org/en/latest/installation.html>`__ for
instructions on installing glue.

Installing
----------

To install the latest stable version of the plugin, you can do:

::

    pip install glue-wwt

or you can install the latest developer version from the git repository
using:

::

    pip install https://github.com/glue-viz/glue-wwt/archive/master.zip

This will auto-register the plugin with Glue. Now simply start up Glue,
open a tabular dataset, drag it onto the main canvas, then select
'WorldWideTelescope (WWT)'.

Testing
-------

To run the tests, do:

::

    py.test glue_wwt

at the root of the repository. This requires the
`pytest <http://pytest.org>`__ module to be installed.

.. |Build Status| image:: https://travis-ci.org/glue-viz/glue-wwt.svg
   :target: https://travis-ci.org/glue-viz/glue-wwt?branch=master
.. |Build status| image:: https://ci.appveyor.com/api/projects/status/8cxo7uvxd8avuj7p/branch/master?svg=true
   :target: https://ci.appveyor.com/project/glue-viz/glue-wwt/branch/master
