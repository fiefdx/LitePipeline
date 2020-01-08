# -*- coding: utf-8 -*-
'''
LitePipeline command line tool
'''

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "litepipeline",
    version = "0.0.2",
    description = "LitePipeline command line tool",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/fiefdx/LitePipeline/tree/master/client",
    author = "fiefdx",
    author_email = "fiefdx@163.com",
    packages = ['litepipeline'],
    entry_points = {
        'console_scripts': ['litepipeline = litepipeline.litepipeline:main']
    },
    install_requires = [
        "requests >= 2.22.0"
    ],
    include_package_data = True,
    license = "MIT",
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ]
)
