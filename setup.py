"""
Package configuration for To LLM View.

This module defines the package setup configuration for distribution.
"""

from setuptools import setup, find_packages

from src.info import VERSION

setup(
    name="to-llm-view",
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "to-llm-view = src.main:main",
        ],
    },
)
