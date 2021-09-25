# -*- coding: utf-8 -*-
"""
pyxform - Python library that converts XLSForms to XForms.
"""
from setuptools import find_packages, setup


setup(
    name="pyxform",
    version="1.6.0",
    author="github.com/xlsform",
    author_email="info@xlsform.org",
    packages=find_packages(),
    package_data={
        "pyxform.validators.odk_validate": ["bin/*.*"],
        "pyxform.tests": [
            "example_xls/*.*",
            "fixtures/strings.ini",
            "bug_example_xls/*.*",
            "test_output/*.*",
            "test_expected_output/*.*",
            "validators/.*",
            "validators/data/*.*",
            "validators/data/.*",
        ],
        "pyxform": ["iana_subtags.txt"],
    },
    url="http://pypi.python.org/pypi/pyxform/",
    description="A Python package to create XForms for ODK Collect.",
    long_description=open("README.rst", "rt").read(),
    install_requires=[
        "xlrd==1.2.0",
        "unicodecsv==0.14.1",
    ],
    entry_points={
        "console_scripts": [
            "xls2xform=pyxform.xls2xform:main_cli",
            "pyxform_validator_update=pyxform.validators.updater:main_cli",
        ]
    },
)
