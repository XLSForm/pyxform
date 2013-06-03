============
pyxform v0.9
============

pyxform is a Python library that makes writing XForms for ODK Collect and enketo
easy by converting XLS(X) spreadsheets into XForms. A new user of pyxform should
look at the documentation `here <https://formhub.org/syntax/>`_ or
`here <http://opendatakit.org/help/form-design/xlsform/>`_.

pyxform is used by `opendatakit.org <http://opendatakit.org>`_ and by `formhub.org <http://formhub.org>`_.

* opendatakit.org uses the repo here:
https://github.com/uw-ictd/pyxform

* formhub.org uses the repo here:
https://github.com/modilabs/pyxform

pyxform is a major rewrite of `xls2xform <http://github.com/mvpdev/xls2xform/>`_. 

Running pyxform as a Python script:
===========================

1. install xlrd.

    #On ubuntu these terminal commands should do it:

    easy_install pip

    pip install xlrd

2. Run this command:

    python pyxform/xls2xform.py path_to_XLSForm output_path

Installation
============
Installing pyxform from github is easy with pip::

	pip install -e git+https://github.com/INSERT GH USER NAME HERE/pyxform.git@master#egg=pyxform

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

Chage Log
=========
(since `v0.89
<https://github.com/modilabs/pyxform/tree/39097db3da789fef9e33a6680df1e912dd29c5db>`_)

- Added support for submission_url and public_key settings.
- Added alternative syntax (\::) for grouping headers.
- Added new example/test spreadsheets: (xlsform_spec_test.xls, calculate.xls, warnings.xls)
- xls_to_dict in xls2json_backends.py now converts everything (including numbers and booleans) to trimmed unicode values.
  (This solves the issue with labels not being able to be numbers).
- Aliases added (see *_alias dictionaries in xls2json.py)
- xls2json code can collect warnings into an array and print them to a file.
- Some errors and warnings have row numbers
- Merged jbeorse's base.xls with modilabs's base.xls into all.xls
- Fixed translations for media and hints
- Added media back in
- Added table-lists
- Automatic none option for select all that apply is off by default.
- Adding json_form_schema.json to document the json format.
  (Perhaps it could be used for validation or form generation at some point).
