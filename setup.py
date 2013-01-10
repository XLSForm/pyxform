# This file is adapted from:
# http://packages.python.org/an_example_pypi_project/setuptools.html

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pyxform",
    version = "0.89",
    author = "Columbia University, Modi Research Group",
    author_email = "andrew.ei.marder@gmail.com",
    description = ("A library for authoring XForms for ODK Collect."),
    license = "BSD",
    keywords = "XForm ODK Collect",
    url = "http://github.com/mvpdev/pyxform",
    packages=['pyxform'],
    long_description=read('README.rst'),
    install_requires=[
        'xlrd==0.8.0',
        ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
    ],
)
