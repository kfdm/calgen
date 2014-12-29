from setuptools import setup

setup(
    name='calgen',
    description='Generate calendar from simple config',
    author='Paul Traylor',
    url='http://github.com/kfdm/calgen/',
    version='0.1',
    packages=['calgen'],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    install_requires=['icalendar', 'python-dateutil'],
    entry_points={
        'console_scripts': [
            'calgen = calgen.cli:main'
        ]
    }
)
