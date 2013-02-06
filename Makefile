
test: grako_test regexp_test

grako_test:
	python -u -m grako.test 2>&1

regexp_test:
	cd examples/regexp; make clean; make
