#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from setuptools import setup, find_packages

with open('README.rst', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    runtime_requirements = f.read().split('\n')

with open('requirements_dev.txt', 'r', encoding='utf-8') as f:
    dev_requirements = f.read().split('\n')
    setup_requirements = runtime_requirements + dev_requirements
    test_requirements = runtime_requirements + dev_requirements

setup(
    name='jobson_systemtests',
    version='0.1.0',
    license='Apache Software License 2.0',

    keywords='jobson_systemtests',
    description='A CLI utility for system testing a Jobson server',
    long_description=readme,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: Apache Software License 2.0',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
    ],

    author="Adam Kewley",
    author_email='contact@adamkewley.com',

    python_requires='>=3.4',
    install_requires=runtime_requirements,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,

    packages=find_packages(include=['jobson_systemtests']),
    entry_points={
        'console_scripts': [
            'jobson_systemtests=jobson_systemtests.cli:main',
        ],
    },
)
