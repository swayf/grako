
test: grako_test examples

grako_test:
	python -u -m grako.test 2>&1

examples: regexp_test antlr_test

regexp_test:
	cd examples/regex; make -s clean; make -s test > /dev/null

antlr_test:
	cd examples/antlr; make -s clean; make -s test > /dev/null
