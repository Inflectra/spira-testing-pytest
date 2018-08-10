"""
Defines the entry point of the extension
"""

from setuptools import setup
import os
import codecs

# Register plugin with pytest
setup(
    name='pytest-spiratest',
    version='1.0.0',
    author='Inflectra Corporation',
    author_email='support@inflectra.com',
    url='http://www.inflectra.com/SpiraTest/Integrations/Unit-Test-Frameworks.aspx',
    description='Exports unit tests as test runs in SpiraTest/Team/Plan',
    py_modules=['pytest_spiratest_integration'],
    classifiers=[
        'Framework :: Pytest',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'pytest11': [
            'pytest-spiratest = pytest_spiratest_integration',
        ],
    },
)
