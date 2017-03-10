# Neutrino Framework
#
# Copyright (c) 2016-2017, Christiaan Frans Rademan
# All rights reserved.
#
# LICENSE: (BSD3-Clause)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENTSHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import os

try:
    from setuptools import setup
    from setuptools import find_packages
except Exception as e:
    print("Requires 'setuptools'")
    print(" pip install setuptools")
    exit()

config = {
    "name": "nfw",
    "author": "Christiaan Frans Rademan",
    "author_email": "christiaan.rademan@gmail.com",
    "description": "Neutrino Framework - WSGI Applications",
    "license": "BSD 3-Clause",
    "keywords": "web development and restapi framework",
    "url": "http://neutrino.fwiw.co.za",
    "packages": find_packages(),
    "scripts": [
        'neutrino.py'
        ],
    "include_package_data": True,
    "package_data": {'': ['requirements.txt']},
    "classifiers": [
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Environment :: Other Environment",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7"
        ]
    }

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as x:
    readme = x.read()

version_py = os.path.join(os.path.dirname(__file__), 'nfw/version.py')
if os.path.isfile(version_py):
    with open(version_py, 'r') as fh:
        version_git = open(version_py).read()
        version_git = version_git.strip()
        version_git = version_git.split('=')[-1]
        version_git = version_git.replace('\'', '')
else:
    version_git = '0.0.0'

if os.path.exists(os.path.join(os.path.dirname(__file__),                           
                               'requirements.txt')):
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as x:
        requirements = x.read().splitlines()
else:
    requirements = []


setup(
    install_requires=requirements,
    long_description=readme,
    version=version_git,
    **config
)
