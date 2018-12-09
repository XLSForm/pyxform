=============
pyxform v0.12
=============

|travis|  |appveyor|

.. |travis| image:: https://travis-ci.org/XLSForm/pyxform.svg?branch=master
    :target: https://travis-ci.org/XLSForm/pyxform

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/XLSForm/pyxform?branch=master&svg=true
    :target: https://ci.appveyor.com/project/ukanga/pyxform

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

    xls2xform path_to_XLSForm output_path

``pyxform`` can be run with either Python 2 or Python 3. Continuous integration runs tests on both Python generations to ensure continued compatibility.

Running pyxform from local source
=================================

Note that you must uninstall any globally installed ``pyxform`` instance in order to use local modules.

From the command line::

    python setup.py develop
    python pyxform/xls2xform.py path_to_XLSForm output_path

Consider using a `virtualenv <http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/>`_ and `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_ to make dependency management easier and keep your global site-packages directory clean::

    pip install virtualenv
    pip install virtualenvwrapper
    mkvirtualenv local_pyxform                     # or whatever you want to name it
    (local_pyxform)$ python setup.py develop       # install the local files
    (local_pyxform)$ python pyxform/xls2xform.py --help
    (local_pyxform)$ xls2xform --help              # same effect as previous line
    (local_pyxform)$ which xls2xform.              # ~/.virtualenvs/local_pyxform/bin/xls2xform

To leave and return to the virtual environment::

    (local_pyxform)$ deactivate                    # leave the virtualenv
    $ xls2xform --help
    # -bash: xls2xform: command not found
    $ workon local_pyxform                         # reactivate the virtualenv
    (local_pyxform)$ which xls2xform               # & we can access the scripts once again
    ~/.virtualenvs/local_pyxform/bin/xls2xform

Installing pyxform from remote source
=====================================
`pip` can install from any GitHub repository::

    pip install git+https://github.com/XLSForm/pyxform.git@master#egg=pyxform

You can then run xls2xform from the commandline::

    xls2xform path_to_XLSForm output_path

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
