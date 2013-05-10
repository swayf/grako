
start: test

test: clean parser
	PYTHONPATH=../.. \
		python antlr2grako.py grammar/Python.g  \
				> python.ebnf
	PYTHONPATH=../.. \
		python -m grako python.ebnf  \
				2>&1

parser: antlr_parser.py

antlr_parser.py: grammar/antlr.ebnf
	PYTHONPATH=../.. python -m grako -m ANTLR -o $@ \
			   $< 2>&1

clean:
	-@rm -f antlr_parser.py
