#!/usr/bin/env python
import re
import sys
import os

from setuptools import setup


with open("README.rst") as fp:
    long_desc = fp.read()

setup(
    name="PsycoSpans",
    version="0.1.1",
    description="Psycopg2 support for the Spans library",
    long_description=long_desc,
    license="MIT",
    author="Andreas Runfalk",
    author_email="andreas@runfalk.se",
    url="https://www.github.com/runfalk/psycospans",
    packages=["psycospans"],
    install_requires=[
        "spans",
    ],
    extras_require={
        "dev": [
            "psycopg2-binary",
            "pytest",
        ],
    },
    classifiers=(
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Database",
        "Topic :: Utilities"
    ),
    zip_safe=False,
)
