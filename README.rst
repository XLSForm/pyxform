pyxform v0.85
=============

pyxform is a Python library that makes writing XForms for ODK Collect
easy.

pyxform is a major rewrite of `xls2xform
<http://github.com/mvpdev/xls2xform/>`_. A new user of pyxform should
look at the tutorial spreadsheet in the docs.

Installing pyxform from github is easy with pip:

pip install -e git+https://github.com/mvpdev/pyxform.git@master#egg=pyxform

Testing
=======
To make sure the install worked out, you can do the following:

pip install nose==1.0.0
cd your-virtual-env-dir/src/pyxform
nosetests

Documentation
=============
To check out the documentation for pyxform do the following:

pip install Sphinx==1.0.7
cd your-virtual-env-dir/src/pyxform/docs
make html
