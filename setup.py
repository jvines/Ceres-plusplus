#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()
    
setup(
    name='cerespp',
    version='1.3.1',
    author='Jose Vines',
    author_email='jose.vines@ug.uchile.cl',
    maintainer="Jose Vines",
    maintainer_email="jose.vines@ug.uchile.cl",
    description='An extension to ceres.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/jvines/Ceres-plusplus',
    packages=find_packages(),
    package_data={'cerespp': ['masks']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        "Programming Language :: Python :: 3",
        'Intended Audience :: Science/Research',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy", "scipy", "matplotlib", "astropy", "PyAstronomy", "tqdm",
        "termcolor"
    ],
    entry_points={
        'console_scripts': [
            'cerespp=cerespp.__main__:main',
        ],
    },
)