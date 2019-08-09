===============
pyxform v0.14.1
===============

|circleci|  |appveyor| |codecov| |black|

.. |circleci| image:: https://circleci.com/gh/XLSForm/pyxform.svg?style=shield&circle-token=:circle-token
    :target: https://circleci.com/gh/XLSForm/pyxform

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/XLSForm/pyxform?branch=master&svg=true
    :target: https://ci.appveyor.com/project/ukanga/pyxform

.. |codecov| image:: https://codecov.io/github/XLSForm/pyxform/branch/master/graph/badge.svg
	:target: https://codecov.io/github/XLSForm/pyxform

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black

pyxform is a Python library that makes writing XForms for ODK Collect and enketo
easy by converting XLS(X) spreadsheets into XForms. It is used as a library in a number of tools including `the ODK online converter <http://opendatakit.org/xiframe/>`_ and `Ona <https://ona.io>`_.

XLS(X) documents used as input must follow to the `XLSForm standard <http://xlsform.org/>`_ and the resulting output follows the `ODK XForms <https://github.com/opendatakit/xforms-spec>`_ standard.

* formhub.org uses the repo here: https://github.com/modilabs/pyxform

pyxform is a major rewrite of `xls2xform <http://github.com/mvpdev/xls2xform/>`_.

Running the latest release of pyxform
=====================================
For those who want to convert forms at the command line, the latest official release of pyxform can be installed using `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_::

    pip install pyxform

The ``xls2xform`` command can then be used::

    xls2xform path_to_XLSForm [output_path]

``pyxform`` can be run with either Python 2 or Python 3. Continuous integration runs tests on both Python generations to ensure continued compatibility.

Running pyxform from local source
=================================

Note that you must uninstall any globally installed ``pyxform`` instance in order to use local modules.
Please install java 8 or newer version.

From the command line::

    python setup.py develop
    python pyxform/xls2xform.py path_to_XLSForm [output_path]

Consider using a development setup as instructed below


Development Setup
=================================
`Pipenv <https://docs.pipenv.org/en/latest/>`_  is used to allow tight control of dependencies.
It is reccommended by `PyPA <https://packaging.python.org/guides/tool-recommendations/>`_

However, since some dependencies are specific to the various versions of python we support, included is a
bash script that will install dependencies based on the version of python detected.

Running this script is as simple as
    
``
pipenv run conditional_install
``

`pyenv <https://github.com/pyenv/pyenv>`_ is a good way to switch through python versions for further testing.

The next step is to install `odk_validate <https://github.com/opendatakit/validate>`_. This can be run via 
`pipenv run pyxform_validator_update odk update ODK-Validate-v1.13.1.jar'`
(if this fails with a json decode error, delete pyxform/validators/bin/installed.json)

You will need to update your validator when odk_validate is updated. The need to do this will come up when tests
that held previously valid forms are getting validation errors.
Also, you can `Check here for new releases <https://github.com/opendatakit/validate/releases>`_.


Installing pyxform from remote source
=====================================
`pip` can install from any GitHub repository::

    pip install git+https://github.com/XLSForm/pyxform.git@master#egg=pyxform

You can then run xls2xform from the commandline::

    xls2xform path_to_XLSForm [output_path]

Testing
=======
To make sure the install worked out, you can do the following::

    pip install nose==1.0.0

    cd your-virtual-env-dir/src/pyxform

    nosetests

Documentation
=============
To check out the documentation for pyxform do the following::

    pip install Sphinx==1.0.7

    cd your-virtual-env-dir/src/pyxform/docs

    make html

Change Log
==========
`Changelog <CHANGES.txt>`_
