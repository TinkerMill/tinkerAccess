#!/usr/bin/env bash

# Note: only non-pull request commits to the master branch will be published to PyPi
if [ "${TRAVIS_BRANCH}" == "master" ] && [ "${TRAVIS_PULL_REQUEST}" == "false" ]; then
    cd "${PYTHON_PACKAGE_SRC}"
    sudo python setup.py sdist
    twine upload -u "${PYPI_USERNAME}" -p "${PYPI_PASSWORD}" --comment "Uploaded by Travis CI" dist/*
fi