help:
	cat Makefile && echo '\n'

clean:
	make clean-pyc
	make clean-build

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

tests:
	    coverage run --source totem --omit '*tests*' -m pytest && coverage report -m
