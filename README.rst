============
pyxform v0.9
============

.. image:: https://travis-ci.org/XLSForm/pyxform.svg?branch=master
    :target: https://travis-ci.org/XLSForm/pyxform

pyxform is a Python library that makes writing XForms for ODK Collect and enketo
easy by converting XLS(X) spreadsheets into XForms. A new user of pyxform should
look at the documentation `here <https://formhub.org/syntax/>`_ or
`here <http://opendatakit.org/help/form-design/xlsform/>`_. 

XLS(X) documents used as input must follow to the `XLSForm standard <http://xlsform.org/>`_ and the resulting output follows the `ODK XForms <https://github.com/opendatakit/xforms-spec>`_ standard. 

* formhub.org uses the repo here:
https://github.com/modilabs/pyxform

pyxform is a major rewrite of `xls2xform <http://github.com/mvpdev/xls2xform/>`_.

Running pyxform as a Python script:
===========================

1. install xlrd::

    # On ubuntu these terminal commands should do it:

    easy_install pip

    pip install xlrd

2. Run this command::

    python pyxform/xls2xform.py path_to_XLSForm output_path

Installation
============
Installing pyxform from github is easy with pip::

	pip install -e git+https://github.com/INSERT GH USER NAME HERE/pyxform.git@master#egg=pyxform

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
=========
`Changelog <CHANGES.txt>`_