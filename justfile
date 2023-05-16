# We deliberately don't currently have a release to production target, because this shouldn't be doable accidentally but only after extensive testing

@default:
  @just --list

# Run black linting on the codebase
black:
  black .

# Install dependencies for building the package which is wheel + deps in setup.py
install-deps:
  pip install wheel PyYAML distro requests semver chardet

# All releases are uploaded via the twine command below which uploads anything under dist/, so if you have old versions lying around delete those first
_release-prepare:
  rm --recursive --force dist

# Release to testpypi
release-testpypi: _release-prepare default
  # Important!: First clean up so we don't upload old packages along with the new one
  twine upload --repository testpypi dist/*
  # Now you or others can install it like this:
  # $ sudo pip install --force-reinstall --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ os2borgerpc-client
  # --extra-index-url is set to regular pypi below so dependencies like pyyaml are downloaded from there

# Prerequisites: Install tox (from pip or your distro), then tox.ini installs what's in requirements-test.txt and runs the test
test:
  tox

# If tox fails with requirements missing it might be because it keeps a virtualenv around and doesn't automatically install things from requirements-test.txt. In that case run this
test-rebuild:
  tox --recreate -e py3-default

# Install tox
install-tox:
  sudo pip install tox

# Compile the client to dist/
build: test _release-prepare install-deps
  # Important!: First delete the build directory as this may contain old versions of the files
  # which are then used to build the wheel version of the package
  rm --recursive --force build
  python3 setup.py sdist
  python3 setup.py bdist_wheel --universal
