========
pyxform
========

|pypi| |python|

.. |pypi| image:: https://badge.fury.io/py/pyxform.svg
    :target: https://badge.fury.io/py/pyxform

.. |python| image:: https://img.shields.io/badge/python-3.10,3.11,3.12-blue.svg
    :target: https://www.python.org/downloads

``pyxform`` is a Python library that simplifies writing forms for ODK Collect and Enketo by converting spreadsheets that follow the `XLSForm standard <http://xlsform.org/>`_ into `ODK XForms <https://github.com/opendatakit/xforms-spec>`_. The XLSForms format is used in a `number of tools <http://xlsform.org/en/#tools-that-support-xlsforms>`_.

Project status
===============
``pyxform`` is actively maintained by `ODK <https://getodk.org/about/team.html>`_.

Current goals for the project include:

* Enable more complex workflows through sophisticated XPath expressions and `entities <https://getodk.github.io/xforms-spec/entities>`_
* Improve error messages and make troubleshooting easier
* Improve experience, particularly for multi-language forms

``pyxform`` was started at the `Sustainable Engineering Lab at Columbia University <https://qsel.columbia.edu/>`_, and until 2018 was maintained primarily by `Ona <https://ona.io/>`_.

Using ``pyxform``
==================
For user support, please start by posting to `the ODK forum <https://forum.getodk.org/c/support/6>`__ where your question will get the most visibility.

There are 3 main ways that ``pyxform`` is used:

* Through a form server, such as the `pyxform-http service wrapper <https://github.com/getodk/pyxform-http>`_, or `ODK Central <https://docs.getodk.org/getting-started/>`_.
* The command line utility ``xls2xform``, which can be helpful for troubleshooting or as part of a broader form creation pipeline.
* As a library, meaning that another python project imports functionality from ``pyxform``.

Running the latest release of pyxform
-------------------------------------
To convert forms at the command line, the latest official release of pyxform can be installed using `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_::

    pip install pyxform

The ``xls2xform`` command can then be used::

    xls2xform path_to_XLSForm [output_path]

The currently supported Python versions for ``pyxform`` are 3.10, 3.11 and 3.12.

Running pyxform from local source
---------------------------------

Note that you must uninstall any globally installed ``pyxform`` instance in order to use local modules. Please install java 8 or newer version.

From the command line, complete the following. These steps use a `virtualenv <https://docs.python.org/3.10/tutorial/venv.html>`_ to make dependency management easier, and to keep the global site-packages directory clean::

    # Get a copy of the repository.
    mkdir -P ~/repos/pyxform
    cd ~/repos/pyxform
    git clone https://github.com/XLSForm/pyxform.git repo

    # Create and activate a virtual environment for the install.
    /usr/local/bin/python3.10 -m venv venv
    . venv/bin/activate

    # Install the pyxform and it's production dependencies.
    (venv)$ cd repo
    # If this doesn't work, upgrade pip ``pip install --upgrade pip`` and retry.
    (venv)$ pip install -e .
    (venv)$ python pyxform/xls2xform.py --help
    (venv)$ xls2xform --help           # same effect as previous line
    (venv)$ which xls2xform            # ~/repos/pyxform/venv/bin/xls2xform

To leave and return to the virtualenv::

    (venv)$ deactivate                 # leave the venv, scripts not on $PATH
    $ xls2xform --help
    # -bash: xls2xform: command not found
    $ . ~/repos/pyxform/venv/bin/activate     # reactivate the venv
    (venv)$ which xls2xform                   # scripts available on $PATH again
    ~/repos/pyxform/venv/bin/xls2xform

Installing pyxform from remote source
-------------------------------------
``pip`` can install from the GitHub repository. Only do this if you want to install from the master branch, which is likely to have pre-release code. To install the latest release, see above.::

    pip install git+https://github.com/XLSForm/pyxform.git@master#egg=pyxform

You can then run xls2xform from the commandline::

    xls2xform path_to_XLSForm [output_path]

Development
===========
To set up for development / contributing, first complete the above steps for "Running pyxform from local source". Then repeat the command used to install pyxform, but with ``[dev]`` appended to the end, e.g.::

    pip install -e .[dev]

You can run tests with::

    python -m unittest

Before committing, make sure to format and lint the code using ``ruff``::

    ruff format pyxform tests
    ruff check pyxform tests

If you are using a copy of ``ruff`` outside your virtualenv, make sure it is the same version as listed in ``pyproject.toml``. Use the project configuration for ``ruff`` in ``pyproject.toml``, which occurs automatically if ``ruff`` is run from the project root (where ``pyproject.toml`` is).

Contributions
-------------
We welcome contributions that have a clearly-stated goal and are tightly focused. In general, successful contributions will first be discussed on `the ODK forum <https://forum.getodk.org/>`__ or in an issue. We prefer discussion threads on the ODK forum because ``pyxform`` issues generally involve considerations for other tools and specifications in ODK and its broader ecosystem. Opening up an issue or a pull request directly may be appropriate if there is a clear bug or an issue that only affects ``pyxform`` developers.

Writing tests
-------------
Make sure to include tests for the changes you're working on. When writing new tests you should add them in ``tests`` folder. Add to an existing test module, or create a new test module. Test modules are named after the corresponding source file, or if the tests concern many files then module name is the topic or feature under test.

When creating new test cases, where possible use ``PyxformTestCase`` as a base class instead of ``unittest.TestCase``. The ``PyxformTestCase`` is a toolkit for writing XLSForms as MarkDown tables, compiling example XLSForms, and making assertions on the resulting XForm. This makes code review much easier by putting the XLSForm content inline with the test, instead of in a separate file. A ``unittest.TestCase`` may be used if the new tests do not involve compiling an XLSForm (but most will). Do not add new tests using the old style ``XFormTestCase``.

When writing new ``PyxformTestCase`` tests that make content assertions, it is strongly recommended that the ``xml__xpath*`` matchers are used, in particular ``xml__xpath_match``. Most older tests use matchers like ``xml__contains`` and ``xml__excludes``, which are simple string matches of XML snippets against the result XForm. The ``xml__xpath_match`` kwarg accepts an XPath expression and expects 1 match. The main benefits of using XPath are 1) it allows specifying a document location, and 2) it does not require a particular document order for elements or attributes or whitespace output. To take full advantage of 1), the XPath expressions should specify the full document path (e.g. ``/h:html/h:head/x:model``) rather than a search (e.g. ``.//x:model``). To take full advantage of 2), the expression should include element predicates that specify the expected attribute values, e.g. ``/h:html/h:body/x:input[@ref='/trigger-column/a']``. To specify the absence of an element, an expression like the following may be used with ``xml__xpath_match``: ``/h:html[not(descendant::x:input)]``, or alternatively ``xml__xpath_count``: ``.//x:input`` with an expected count of 0 (zero).

Documentation
=============
For developers, ``pyxform`` uses docstrings, type annotations, and test cases. Most modern IDEs can display docstrings and type annotations in a easily navigable format, so no additional docs are compiled (e.g. sphinx). In addition to the user documentation, developers should be familiar with the `ODK XForms Specification https://getodk.github.io/xforms-spec/`.

For users, ``pyxform`` has documentation at the following locations:
* `XLSForm docs <https://xlsform.org/>`_
* `XLSForm template <https://docs.google.com/spreadsheets/d/1v9Bumt3R0vCOGEKQI6ExUf2-8T72-XXp_CbKKTACuko/edit#gid=1052905058>`_
* `ODK Docs <https://docs.getodk.org/>`_

Change Log
==========
`Changelog <CHANGES.txt>`_

Releasing pyxform
=================

1. Make sure the version of ODK Validate in the repo is up-to-date::

    pyxform_validator_update odk update ODK-Validate-vx.x.x.jar

2. Run all tests through Validate by setting the default for ``run_odk_validate`` to ``True`` in ``tests/pyxform_test_case.py``.
3. Draft a new GitHub release with the list of merged PRs. Follow the title and description pattern of the previous release.
4. Checkout a release branch from latest upstream master.
5. Update ``CHANGES.txt`` with the text of the draft release.
6. Update ``pyproject.toml``, ``pyxform/__init__.py`` with the new release version number.
7. Commit, push the branch, and initiate a pull request. Wait for tests to pass, then merge the PR.
8. Tag the release and it will automatically be published

Manually releasing
===================
Releases are now automatic. These instructions are provided for forks or for a future change in process.

1. In a clean new release only directory, check out master.
2. Create a new virtualenv in this directory to ensure a clean Python environment::

     /usr/local/bin/python3.10 -m venv pyxform-release
     . pyxform-release/bin/activate

3. Install the production and packaging requirements::

     pip install -e .
     pip install flit==3.9.0

4. Clean up build and dist folders::

     rm -rf build dist pyxform.egg-info

5. Prepare ``sdist`` and ``bdist_wheel`` distributions, and publish to PyPI::

     flit --debug publish --no-use-vcs

6. Tag the GitHub release and publish it.

Related projects
================

These projects are not vetted or endorsed but are linked here for reference.

**Converters**

*To XLSForm*

* `cueform <https://github.com/freddieptf/cueform>`_ (Go): from CUE
* `md2xlsform <https://github.com/joshuaberetta/md2xlsform>`_ (Python): from MarkDown
* `xlsform <https://github.com/networkearth/xlsform>`_ (Python): from JSON
* `yxf <https://github.com/Sjlver/yxf>`_ (Python): from YAML

*From XLSForm*

* `ODK2Doc <https://github.com/zaeendesouza/ODK2Doc>`_ (R): to Word
* `OdkGraph <https://github.com/jkpr/OdkGraph>`_ (Python): to a graph
* `Pureser <https://github.com/SwissTPH/Pureser>`_ (Swift): to HTML
* `ppp <https://github.com/pmaengineering/ppp>`_ (Python): to HTML, PDF, Word
* `QuestionnaireHTML <https://github.com/hedibmustapha/QuestionnaireHTML>`_ (R): to HTML
* `xlsform-converter <https://github.com/wq/xlsform-converter>`_ (Python): to Django modules
* `xlsform <https://github.com/networkearth/xlsform>`_ (Python): to JSON
* `xlsform2json <https://github.com/owengrant/xlsform2json>`_ (Java): to JSON
* `XLSform2PDF <https://github.com/HEDERA-PLATFORM/XLSform2PDF>`_ (Python): to PDF
* `xlson <https://github.com/opensrp/xlson>`_ (Python): to OpenSRP JSON
* `yxf <https://github.com/Sjlver/yxf>`_ (Python): to YAML

**Management Tools**

* `surveydesignr <https://github.com/williameoswald/surveydesignr>`_ (R): compare XLSForms
* `ipacheckscto <https://github.com/PovertyAction/ipacheckscto>`_ (Stata): check XLSForm for errors or design issues
* `kobocruncher <https://github.com/Edouard-Legoupil/kobocruncher>`_ (R): generate analysis Rmd from XLSForm
* `odkmeta <https://github.com/PovertyAction/odkmeta>`_ (Stata): use XLSForm to import ODK data to Stata
* `odktools <https://github.com/ilri/odktools>`_ (C++): convert pyxform internal data model to MySQL
* `pmix <https://github.com/pmaengineering/pmix>`_ (Python): manage XLSForm authoring
* `pyxform-docker <https://github.com/seadowg/pyxform-docker>`_ (Dockerfile): image for pyxform development
* `xform-test <https://github.com/PMA-2020/xform-test>`_ (Java): test XLSForms
* `xlsformpo <https://github.com/delcroip/xlsformpo>`_ (Python): use .po files for XLSForm translations
* `XlsFormUtil <https://github.com/unhcr-americas/XlsFormUtil>`_ (R): manage XLSForm authoring
