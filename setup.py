#!/usr/bin/env python
import os
import sys

from codecs import open

from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', 'r', 'utf-8') as f:
    long_description = f.read()

setup(
    name='pxhelper',
    version='0.1.0',
    description='Pixiv downloader',
    long_description=long_description,
    url='https://github.com/eternal-flame-AD/px_helper',
    author='eternal-flame-AD',
    author_email='ef@eternalflame.cn',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='pixiv',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    package_data={'': ['ffmpeg.exe']},
    include_package_data=True if sys.platform == "win32" else False,
    python_requires=">=3.6",
    install_requires=[
        'beautifulsoup4',
        'html5lib',
        'gevent',
    ],
    entry_points={
        'console_scripts': [
            'pxdown=pxhelper.main:main',
        ],
    },
    project_urls={
        'Source': 'https://github.com/eternal-flame-AD/px_helper',
    },
)
