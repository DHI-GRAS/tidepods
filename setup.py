from setuptools import setup, find_packages

setup(
    name='tidepods',
    version='1.0',
    description='Generate pfs file for input to MIKE',
    author='Mike Rosca',
    author_email='vlro@dhigroup.com',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        tidepods=tidepods.cli:cli
    '''
)