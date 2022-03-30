# Compile the client to dist/
all: test
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal

release-testpypi: all
	twine upload --repository testpypi dist/*
	@printf '\n%s' 'Now you or others can install it like this: ' \ 
	@printf '%s\n' 'pip --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple os2borgerpc-client'

# Prerequisites: Install tox (from pip or your distro), then tox.ini installs what's in requirements-test.txt and runs the test
test:
	tox
