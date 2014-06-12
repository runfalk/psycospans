#!/usr/bin/env python
import re
import sys
import os

from setuptools import setup

with open("README.rst") as fp:
    long_desc = fp.read()

with open("LICENSE") as fp:
    license = fp.read()

with open("psycospans/__init__.py") as fp:
    version = re.search('__version__\s+=\s+"([^"]+)', fp.read()).group(1)

requirements = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt") as fp:
        requirements = fp.read().split("\n")

setup(
    name="PsycoSpans",
    version=version,
    description="Psycopg2 support for the Spans library",
    long_description=long_desc,
    license=license,
    author="Andreas Runfalk",
    author_email="andreas@runfalk.se",
    url="https://www.github.com/runfalk/psycospans",
    packages=["psycospans"],
    install_requires=requirements,
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Topic :: Database",
        "Topic :: Utilities"
    ),
    zip_safe=False,
    test_suite="psycospans.tests.suite"
)
