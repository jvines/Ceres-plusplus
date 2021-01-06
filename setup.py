#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()
    
setup(
    name='ceres-plusplus',
    version='0.0.1',
    author='Jose Vines',
    author_email='jose.vines@ug.uchile.cl',
    description='An extension to ceres.',
    long_description=long_description,
    long_description_content='text/markdown',
    url='https://github.com/jvines/Ceres-plusplus',
    packages=find_packages(),
    package_data={'cerespp': ['masks']},
    include_package_data=True,
    classifiers=[
        'Programming Languge :: Python :: 3',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Astronomy"
    ],
    python_requires='>=3.6',
    requires=[
        "numpy", "scipy", "matplotlib", "astropy", "PyAstronomy",
        "tabulate", "tqdm", "argparse", "termcolor"
    ]
)