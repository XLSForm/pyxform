# -*- coding: utf-8 -*-
"""
pyxform - Python library that converts XLSForms to XForms.
"""
from setuptools import find_packages, setup


setup(
    name="pyxform",
    version="1.8.0",
    author="github.com/xlsform",
    author_email="info@xlsform.org",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "pyxform.validators.odk_validate": ["bin/*.*"],
        "pyxform": ["iana_subtags.txt"],
    },
    url="http://pypi.python.org/pypi/pyxform/",
    description="A Python package to create XForms for ODK Collect.",
    long_description=open("README.rst", "rt").read(),
    python_requires=">=3.7",
    install_requires=[
        "xlrd==2.0.1",
        "openpyxl==3.0.9",
        "defusedxml==0.7.1",
    ],
    entry_points={
        "console_scripts": [
            "xls2xform=pyxform.xls2xform:main_cli",
            "pyxform_validator_update=pyxform.validators.updater:main_cli",
        ]
    },
)
