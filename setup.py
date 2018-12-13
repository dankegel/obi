#!/usr/bin/env python
'''
obi
'''
from setuptools import setup

setup(
    name='oblong-obi',
    packages=['obi', 'obi.task'],
    entry_points={
        'console_scripts': ['obi=obi.obi:main']
    },
    include_package_data=True,
    version="3.4.8",
    description="g-speak project generator",
    long_description=open('README.md', 'rt').read(),
    author="Justin Shrake",
    author_email="jshrake@oblong.com",
    url="https://github.com/Oblong/obi",
    download_url="https://github.com/Oblong/obi",
    keywords=["g-speak", "greenhouse"],
    install_requires=[
        'docopt==0.6.2',
        'fabric==1.10.3',
        'jinja2==2.8',
        'pyyaml==3.11'
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    data_files=[
        ('man/man1', ['obi.1']),
    ],
    package_data={'': ['README.md']}
)
