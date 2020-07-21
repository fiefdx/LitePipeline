# -*- coding: utf-8 -*-
'''
LitePipeline: distributed pipeline system
'''

from setuptools import setup

from litepipeline_pack_tool.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "litepipeline_pack_tool",
    version = __version__,
    description = "LitePipeline: distributed pipeline system",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/fiefdx/LitePipeline",
    author = "fiefdx",
    author_email = "fiefdx@163.com",
    packages = [
        'litepipeline_pack_tool',
    ],
    entry_points = {
        'console_scripts': [
            'litepack = litepipeline_pack_tool.pack:main',
        ],
    },
    install_requires = [
        "progress >= 1.5",
        "requests >= 2.22.0",
        "pyYAML",
        "litepipeline_helper >= 0.0.17",
        "litedfs_client >= 0.0.4",
    ],
    include_package_data = True,
    license = "MIT",
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ]
)
