===============
pyxform v1.4.0
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

pyxform is a Python library that makes writing forms for ODK Collect and Enketo easy by converting XLSForms (Excel spreadsheets) into ODK XForms. The XLSForms format is used in a `number of tools <http://xlsform.org/en/#tools-that-support-xlsforms>`_.

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

    xls2xform path_to_XLSForm [output_path]

Development
===========
To set up for development/contributing::

    pip install -r requirements.pip

    python setup.py develop

    cd your-virtual-env-dir/src/pyxform

You can run tests with::

    nosetests

Before committing, make sure to format your code using `black`::

    black pyxform

If you are using a copy of black outside your virtualenv, make sure it is the same version as listed in requirements.pip.

Writing tests
-------------
Make sure to include tests for the changes you're working on. When writing new tests you should add them in `pyxform/test_v1` instead of in `pyxform/test` (which contains tests using an older style). Generally, the easiest way to write tests is to extend `PyxformTestCase` which will let you compile example XLSForm and make assertions on the resulting XForm.

Documentation
=============
To check out the documentation for pyxform do the following::

    pip install Sphinx==1.0.7

    cd your-virtual-env-dir/src/pyxform/docs

    make html

Change Log
==========
`Changelog <CHANGES.txt>`_

Releasing pyxform
=================

1. Make sure the version of ODK Validate in the repo is up-to-date::

    pyxform_validator_update odk update ODK-Validate-vx.x.x.jar

2. Run all tests through Validate by setting the default for ``run_odk_validate`` to ``kwargs.get("run_odk_validate", True)`` in ``pyxform/tests_v1/pyxform_test_case.py``.
3. Draft a new GitHub release with the list of merged PRs. Follow the title and description pattern of the previous release.
4. Checkout a release branch from latest upstream master.
5. Update ``CHANGES.txt`` with the text of the draft release.
6. Update ``README.rst``, ``setup.py``, ``pyxform/__init__.py`` with the new release version number.
7. Commit, push the branch, and initiate a pull request. Wait for tests to pass, then merge the PR.
8. In a clean new release only directory, checkout master.
9. Create a new virtualenv in this directory to ensure a clean Python environment::

     mkvirtualenv pyxform-release

10. Install the development and release requirements::

     pip install -r requirements.pip
     pip install wheel twine

11. Cleanup build and dist folders::

     rm -rf build dist pyxform.egg-info

12. Prepare ``sdist`` and ``bdist_wheel`` distributions::

     python setup.py sdist bdist_wheel

13. Publish release to PyPI with ``twine``::

     twine upload dist/pyxform-*-py2.py3-none-any.whl dist/pyxform-*.tar.gz

14. Tag the GitHub release and publish it.
