
test: grako_test regexp_test

grako_test:
	python -u -m grako.test 2>&1

regexp_test:
	cd examples/regex; make -s clean; make -s test > /dev/null
