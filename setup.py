#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'Click>=8.0',
]

setup(
    name='aura-odoo-maintainer',
    version='0.1.0',
    description="CLI tool to manage Odoo instances",
    long_description=readme,
    author="Jan-Phillip Oesterling",
    author_email='jpo@hav.media',
    url='https://github.com/havmedia/aura-odoo-maintainer',
    packages=find_packages(include=['src']),
    entry_points={
        'console_scripts': [
            'aura-odoo-maintainer=src.main:cli'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='aura-odoo-maintainer',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.12',
    ]
)