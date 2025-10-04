from setuptools import setup, find_packages

from info import VERSION

setup(
    name="to-llm-view",
    version=VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "to-llm-view = main:main",
        ],
    },
)