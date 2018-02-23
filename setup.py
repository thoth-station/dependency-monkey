#!/usr/bin/python3

import os
from setuptools import setup, find_packages

import thoth_dependency_monkey


def get_requirements():
    from pipenv.project import Project
    from pipenv.utils import convert_deps_to_pip

    pfile = Project(chdir=False).parsed_pipfile
    requirements = convert_deps_to_pip(pfile['packages'], r=False)

    return requirements


setup(
    name='thoth_dependency_monkey',
    version=thoth_dependency_monkey.__version__,
    packages=find_packages(),
    package_data={
        'thoth_dependency_monkey': [
            'swagger.yaml'
        ]
    },
    install_requires=get_requirements(),
    author='Christoph Görn',
    author_email='goern@redhat.com',
    description=thoth_dependency_monkey.__description__,
    license='GPL 3.0',
    keywords='thoth dependency monkey API openapi',
    url='https://github.com/goern/thoth-dependency-monkey',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later(GPLv3+)',
    ]
)
