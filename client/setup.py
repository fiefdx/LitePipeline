# -*- coding: utf-8 -*-
'''
LitePipeline command line tool
'''

from setuptools import setup

setup(
    name = "litepipeline",
    version = "0.0.2",
    author = "fiefdx",
    author_email = "fiefdx@163.com",
    packages = ['litepipeline'],
    entry_points = {
        'console_scripts': ['litepipeline = litepipeline.litepipeline:main']
    },
    include_package_data = True,
    install_requires = [
        "requests >= 2.22.0"
    ]
)
