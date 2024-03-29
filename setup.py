#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup Script for cctl"""

import sys
from os import path
import setuptools
sys.path.insert(0, path.abspath('./src'))
import cctl  # noqa: E402

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='cctl',
    version=cctl.__version__,
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
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'cctl = cctl.__main__:main',
            'cctld = cctld.__main__:main'
        ]
    },
    include_package_data=True,
    install_requires=[
        'pyzmq',
        'pyserial',
        'reactivex',
        'bleak',
        'textual',
        'python-daemon'
    ]
)
