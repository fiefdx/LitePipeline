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
        'litepipeline.tool',
        'litepipeline.manager',
        'litepipeline.manager.db',
        'litepipeline.manager.handlers',
        'litepipeline.manager.models',
        'litepipeline.manager.utils',
        'litepipeline.node',
        'litepipeline.node.handlers',
        'litepipeline.node.utils',
        'litepipeline.viewer',
        'litepipeline.viewer.handlers',
        'litepipeline.viewer.utils',
        'litepipeline.viewer.modules',
    ],
    entry_points = {
        'console_scripts': [
            'litepipeline = litepipeline.tool.litepipeline:main',
            'litemanager = litepipeline.manager.manager:main',
            'litenode = litepipeline.node.node:main',
            'liteviewer = litepipeline.viewer.viewer:main',
        ],
    },
    install_requires = [
        "progress >= 1.5",
        "requests >= 2.22.0",
        "tornado",
        "pyYAML",
        "tinydb",
        "sqlalchemy == 1.3.23",
        "docker",
        "tornado_discovery",
        "tea_encrypt",
        "litepipeline_helper >= 0.0.17",
        "litedfs_client >= 0.0.4",
    ],
    extras_require = {
        "dfs": ["litedfs"]
    },
    include_package_data = True,
    license = "MIT",
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ]
)
