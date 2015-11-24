#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

# https://pypi.python.org/pypi?%3Aaction=list_classifiers
setup(
    name='archive-rotator',
    version='0.1.0',
    description="Flexible utility for rotating backup files.",
    long_description=readme + '\n\n' + history,
    author="Max Harper",
    author_email='maxharp3r@gmail.com',
    url='https://github.com/maxharp3r/archive-rotator',
    packages=[
        'archive_rotator',
    ],
    package_dir={'archive_rotator': 'archive_rotator'},
    entry_points={
        'console_scripts': [
            'archive-rotator = archive_rotator.archive_rotator:main',
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT License",
    zip_safe=False,
    keywords='backup rotation',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Archiving :: Backup',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
