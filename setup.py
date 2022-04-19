#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup Script for cctl"""

import sys
from os import path
import setuptools

sys.path.insert(0, path.abspath('./src'))
import cctl

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='cctl',
    version=cctl.__VERSION__,
    author='Marko Vejnovic',
    author_email='contact@markovejnovic.com',
    description='Coachbot Control Software',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: Linux',
    ],
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'cctl = cctl.__main__:main'
        ]
    },
    include_package_data=True
)
