============
pyxform v0.9
============

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

Running pyxform from local source
=================================

Note that you must uninstall any globally installed `pyxform` instance in order to use local modules.

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
https://github.com/UW-ICTD/pyxform/blob/master/CHANGES.txt
