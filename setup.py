#!/usr/bin/python3

import os
from setuptools import setup, find_packages


def get_requirements():
    from pipenv.project import Project
    from pipenv.utils import convert_deps_to_pip

    pfile = Project(chdir=False).parsed_pipfile
    requirements = convert_deps_to_pip(pfile['packages'], r=False)

    return requirements


setup(
    name='thoth_dependency_monkey',
    version='0.1.0-dev',
    packages=find_packages(),
    package_data={
        'thoth_dependency_monkey': [
            'swagger.yaml'
        ]
    },
    install_requires=get_requirements(),
    include_package_data=True,
    author='Christoph Görn',
    author_email='goern@redhat.com',
    maintainer='Christoph Görn',
    maintainer_email='goern@redhat.com',
    description='Thoth Dependency Monkey API',
    license='GPL 3.0',
    keywords='thoth dependency monkey API',
    url='https://github.com/goern/thoth-dependency-monkey',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Intended Audience :: Developers",
    ]
)
