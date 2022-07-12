# Don't check timestamps, always build a new version
.PHONY: build

all: test build

# --extra-index-url is set to regular pypi below so dependencies like pyyaml are downloaded from there
release-testpypi: all
	twine upload --repository testpypi dist/*
	@printf '\n%s' 'Now you or others can install it like this: ' \ 
	@printf '%s\n' 'pip install --force-reinstall --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ os2borgerpc-client'

# Prerequisites: Install tox (from pip or your distro), then tox.ini installs what's in requirements-test.txt and runs the test
test:
	tox

# Compile the client to dist/
build:
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal
