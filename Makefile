# Compile the client to dist/
all:
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal
