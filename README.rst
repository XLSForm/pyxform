pyxform
=======

pyxform is a Python library that makes writing XForms for ODK Collect
easy.

pyxform is a major rewrite of `xls2xform
<http://github.com/mvpdev/xls2xform/>`_. A new user of pyxform should
look at the tutorial spreadsheet in the docs.

Installing from the develop branch of this github repository can be
done with:

pip install -e git+https://github.com/mvpdev/pyxform.git@develop#egg=pyxform

To make sure the install worked out, you can do the following:

cd your-virtual-env-dir/src/pyxform
nosetests
