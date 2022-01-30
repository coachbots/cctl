#!/usr/bin/env python3

"""Installation script for cctl"""

from distutils.core import setup

requirements = [
    'distutils'
    'curses'
]

setup(name='cctl',
      version='0.1.0',
      description='cctl (Coachbot Control) is a small utility for ' +
      'controlling coachbots.',
      author='Marko Vejnovic',
      author_email='contact@markovejnovic.com',
      packages=requirements)
