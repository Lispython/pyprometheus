#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus
~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython <lispython@users.noreply.github.com>.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import re
import sys
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('pyprometheus/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).groups()[0]))

install_require = []
tests_require = [x.strip() for x in open("tests_requirements.txt").readlines() if (x.strip() and not x.strip().startswith('#'))]


def read_description():
    try:
        with open("README.rst", 'r') as f:
            return f.read()
    except Exception:
        return __doc__

class PyTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='pyprometheus',
    version=version,
    author='Alexandr Lispython',
    author_email='lispython@users.noreply.github.com',
    url='https://github.com/Lispython/pyprometheus',
    description='Prometheus python client and instrumentation library',
    long_description=read_description(),
    packages=find_packages(exclude=("tests", "tests.*",)),
    zip_safe=False,
    extras_require={
        'tests': tests_require,
    },
    license='BSD',
    tests_require=tests_require,
    install_requires=install_require,
    cmdclass={'test': PyTest},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pyprometheus = pyprometheus.scripts:main',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',

        'Topic :: Software Development',
        'Topic :: System :: Monitoring',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking :: Monitoring'
    ],
)
