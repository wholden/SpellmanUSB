from setuptools import setup, find_packages
import os

setup(name = 'SpellmanUSB',
    packages = ['SpellmanUSB'],
    package_dir={'SpellmanUSB':'SpellmanUSB'},
    install_requires = ['numpy','hid'],
    zip_safe = False)
