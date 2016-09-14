from setuptools import setup, find_packages

setup(
    name='pyxform',
    version='0.9.24',
    author='github.com/xlsform',
    author_email='info@xlsform.org',
    packages=find_packages(),
    package_data={
        'pyxform.odk_validate': [
            'ODK_Validate.jar',
        ],
        'pyxform.tests': [
            'example_xls/*.*',
            'bug_example_xls/*.*',
            'test_output/*.*',
            'test_expected_output/*.*',
        ]
    },
    url='http://pypi.python.org/pypi/pyxform/',
    description='A Python package to create XForms for ODK Collect.',
    long_description=open('README.rst', 'rt').read(),
    install_requires=[
        'xlrd==1.0.0',
        'unicodecsv==0.14.1',
        'formencode',
        'unittest2',
    ],
)
