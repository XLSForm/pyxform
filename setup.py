from distutils.core import setup

setup(
     name='pyxform',
     version='0.9.8',
     author='modilabs',
     author_email='info@modilabs.org',
     packages=['pyxform', 'pyxform.odk_validate'],
     package_dir={'pyxform': 'pyxform'},
     package_data={
        'pyxform': [
            'odk_validate/java_lib/ODK Validate.jar',
            'odk_validate/java_lib/lonely_java_src/FormValidator.java',
        ],
     },
     url='http://pypi.python.org/pypi/pyxform/',
     description='A Python package to create XForms for ODK Collect.',
     long_description=open('README.rst', 'rt').read(),
     install_requires=[
        'modilabs-python-utils==0.1.5',
    ],
)
