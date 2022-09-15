# Don't check timestamps, always build a new version
.PHONY: build

all: test build

release-prepare:
	rm -rf dist

# --extra-index-url is set to regular pypi below so dependencies like pyyaml are downloaded from there
release-testpypi: release-prepare all
	@printf '\n%s' "First clean up so we don't upload old packages along with the new one" \
	twine upload --repository testpypi dist/*
	@printf '\n%s' 'Now you or others can install it like this: ' \ 
	@printf '%s\n' 'pip install --force-reinstall --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ os2borgerpc-client'

# Prerequisites: Install tox (from pip or your distro), then tox.ini installs what's in requirements-test.txt and runs the test
test:
	tox

# If tox fails with requirements missing it might be because it keeps a virtualenv around and doesn't automatically
# install things from requirements-test.txt. In that case do this:
test-rebuild:
	tox --recreate -e py3-default

# Compile the client to dist/
build:
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal
