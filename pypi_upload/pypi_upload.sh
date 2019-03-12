#!/usr/bin/env bash

# Build distribution
python pypi_upload/setup.py sdist bdist_wheel

# Upload distribution to PyPI
twine upload --config-file pypi_upload/.pypirc dist/*

# Upload distribution to test PyPI
#twine upload --repository testpypi --config-file pypi_upload/.pypirc dist/*

# Tidy up
rm -rf build
rm -rf dist
rm -rf dataclasses_serialization.egg-info
