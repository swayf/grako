
test: parser
	python test.py 2>&1

parser: parser_base.py
	
parser_base.py: regexp.ebnf
	python -m grako -m Regex -o parser_base.py regexp.ebnf 2>&1
