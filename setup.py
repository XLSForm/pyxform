from distutils.core import setup

setup(
    name='pmaxform',
    version='1.0.1',
    author='James K. Pringle',
    author_email='jpringle@jhu.edu',
    packages=['pmaxform', 'pmaxform.odk_validate'],
    package_dir={'pmaxform': 'pmaxform'},
    package_data={
        'pmaxform': [
            'odk_validate/ODK_Validate.jar',
        ],
    },
    url='https://github.com/jkpr/pmaxform',
    description='A Python package to create XForms for ODK Collect.',
    long_description=open('README.rst', 'rt').read(),
    install_requires=[
        'xlrd==0.8.0',
        'lxml==3.4.4',
    ],
)
