# -*- coding: utf-8 -*-
'''
LitePipeline helper: help user to develop LitePipeline's application
'''

from setuptools import setup

from litepipeline_helper.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "litepipeline_helper",
    version = __version__,
    description = "LitePipeline helper: help user to develop LitePipeline's application",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/fiefdx/LitePipeline",
    author = "fiefdx",
    author_email = "fiefdx@163.com",
    packages = [
        'litepipeline_helper',
        'litepipeline_helper.models',
    ],
    include_package_data = True,
    license = "MIT",
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ]
)
