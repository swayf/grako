
test:
	python -u -m grako.test.bootstrap_tests 2>&1
	python -u -m grako.test.buffering_test  2>&1
