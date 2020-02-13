# -*- coding: utf-8 -*-
'''
LitePipeline: distributed pipeline system
'''

from setuptools import setup

from litepipeline.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "litepipeline",
    version = __version__,
    description = "LitePipeline: distributed pipeline system",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/fiefdx/LitePipeline",
    author = "fiefdx",
    author_email = "fiefdx@163.com",
    packages = [
        'litepipeline',
        'litepipeline.client',
        'litepipeline.client.models',
        'litepipeline.manager',
        'litepipeline.manager.db',
        'litepipeline.manager.handlers',
        'litepipeline.manager.models',
        'litepipeline.manager.utils',
        'litepipeline.node',
        'litepipeline.node.handlers',
        'litepipeline.node.utils',
    ],
    entry_points = {
        'console_scripts': [
            'litepipeline = litepipeline.client.litepipeline:main',
            'liteconfig = litepipeline.client.liteconfig:main',
            'litemanager = litepipeline.manager.manager:main',
            'litenode = litepipeline.node.node:main',
        ],
    },
    install_requires = [
        "requests >= 2.22.0",
        "tornado",
        "pyYAML",
        "tinydb",
        "sqlalchemy",
        "tornado_discovery",
    ],
    include_package_data = True,
    license = "MIT",
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ]
)
