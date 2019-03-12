from setuptools import setup, find_packages
from os import path

import re

project_root = path.join(path.abspath(path.dirname(__file__)), '..')


def get_version():
    with open(path.join(project_root, 'dataclasses_serialization', '__init__.py'), encoding='utf-8') as init_file:
        return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", init_file.read(), re.M).group(1)


def get_requirements():
    with open(path.join(project_root, 'requirements.txt'), encoding='utf-8') as requirements_file:
        return list(filter(None, requirements_file.read().splitlines()))


def get_long_description():
    with open(path.join(project_root, 'README.md'), encoding='utf-8') as readme_file:
        return readme_file.read()


setup(
    name='dataclasses_serialization',
    version=get_version(),
    packages=find_packages(include=('dataclasses_serialization', 'dataclasses_serialization.*')),
    install_requires=get_requirements(),
    setup_requires=['wheel'],

    author='Robert Wright',
    author_email='madman.bob@hotmail.co.uk',

    description='Serialize/deserialize Python dataclasses to various other data formats',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/madman-bob/python-dataclasses-serialization',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    python_requires='>=3.6'
)
