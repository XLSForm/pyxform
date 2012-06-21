from distutils.core import setup

setup(
     name='pyxform',
     version='0.9.6',
     author='modilabs',
     author_email='info@modilabs.org',
     packages=['pyxform', 'pyxform.odk_validate'],
     url='http://pypi.python.org/pypi/pyxform/',
     description='A Python package to create XForms for ODK Collect.',
     long_description=open('README.rst', 'rt').read(),
     install_requires=[
        'modilabs-python-utils==0.1.5',
    ]
)
