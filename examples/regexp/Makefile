
test: parser
	python test.py 2>&1
	python genparser.py -l
	python genparser.py data/valid S0

parser: parser_base.py
	
parser_base.py: regexp.ebnf
	python -m grako -m Regex -o parser_base.py regexp.ebnf 2>&1
