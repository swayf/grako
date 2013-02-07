
start: test
	PYTHONPATH=../..  python genparser.py -l
	PYTHONPATH=../..  python genparser.py data/valid S0

test: parser
	PYTHONPATH=../..  python test.py 2>&1

parser: parser_base.py
	
parser_base.py: regexp.ebnf
	PYTHONPATH=../.. python -m grako -m Regex -o parser_base.py regexp.ebnf 2>&1

clean:
	rm -f parser_base.py
	rm -f genparser.py
