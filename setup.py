"""
Defines the entry point of the extension
"""

import setuptools
import os
import codecs
import io

with io.open("README.md") as readme_file:
    long_description = readme_file.read()

# Register plugin with pytest
setuptools.setup(
    name ='pytest-spiratest',
    version = '1.4.3',
    author = 'Inflectra Corporation',
    author_email ='support@inflectra.com',
    url = 'http://www.inflectra.com/SpiraTest/Integrations/Unit-Test-Frameworks.aspx',
    description = 'Exports unit tests as test runs in Spira (SpiraTest/Team/Plan)',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = setuptools.find_packages(),
    py_modules = ['pytest_spiratest_integration'],
    classifiers = [
        'Framework :: Pytest',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    entry_points = {
        'pytest11': [
            'pytest-spiratest = pytest_spiratest_integration',
        ],
    },
    include_package_data=True,
    package_data={'': ['sample*.py', 'spira.cfg']},
)
