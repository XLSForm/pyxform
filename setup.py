from distutils.core import setup

setup(
    name='pyxform',
    version='0.9.19',
    author='modilabs',
    author_email='info@modilabs.org',
    packages=['pyxform', 'pyxform.odk_validate'],
    package_dir={'pyxform': 'pyxform'},
    package_data={
        'pyxform': [
            'odk_validate/ODK_Validate.jar',
        ],
    },
    url='http://pypi.python.org/pypi/pyxform/',
    description='A Python package to create XForms for ODK Collect.',
    long_description=open('README.rst', 'rt').read(),
    install_requires=[
        'xlrd==0.8.0',
        'lxml==2.3.4',
    ],
)
