from setuptools import setup, find_packages
import os

setup(name = 'SpellmanUSB',
    packages = ['SpellmanUSB'],
    package_dir={'SpellmanUSB':'SpellmanUSB'},
    install_requires = ['numpy', 'hidapi'],
    zip_safe = False)
