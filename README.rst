=============
pmaxform v1.0
=============

pmaxform is an improved version of pyxform `https://github.com/XLSForm/pyxform`


============
Form Linking
============

First, all variables that you want to link must be placed inside a repeat,
perhaps a household roster. You can generate those variables outside of a
repeat, but then inside the repeat, have a calculate statement that has that
outside variable as the calculation.

Second, inside the repeat, you also need a calculate variable that will
calculate a form name for the child form. It should have a relevant statement
that reflects your inclusion criteria.

In the settings tab, use the setting "xml_root" to set the XML root of the
instance in the XForm. If it is not defined, then by default, the XML root is
the file name.

Next, in the parent xlsform, you need to include columns "save_instance" and
"save_form". For the values you want linked, add under "save_instance" the
xpath in the child form to which you want the value saved. For a hint, look at
the "bind" tag in the child form and copy the "nodeset" value. For the
calculated instance name, under the "save_form" enter the form_id of the child
form.



======================
Previous documentation
======================

.. image:: https://travis-ci.org/XLSForm/pyxform.svg?branch=master
    :target: https://travis-ci.org/XLSForm/pyxform

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

Change Log
=========
https://github.com/UW-ICTD/pyxform/blob/master/CHANGES.txt
