# Defines the entry point of the extension

from setuptools import setup

print("Entry")

setup(
    name = "pytest-spiratest-integration",
    author = "Inflectra Corporation",
    author_email = "support@inflectra.com",
    description = "Exports unit tests as test runs in SpiraTest/Team/Plan",
    # Makes the plugin available to PyTest
    entry_points = {
        "pytest11": ["pytest-spiratest-integration = pytest_spiratest-integration"]
    },
    classifiers = ["Framework :: Pytest"],
)
