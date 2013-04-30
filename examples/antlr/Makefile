
start: test

test: parser
	PYTHONPATH=../.. \
		python antlr2grako.py grammar/Python.g \ #--trace \
				2>&1

parser: antlr_parser.py

antlr_parser.py: grammar/antlr.ebnf
	PYTHONPATH=../.. python -m grako -m ANTLR -o $@  \
			   $< 2>&1

clean:
	-@rm -f antlr_parser.py
