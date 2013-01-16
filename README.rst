Grako
=====

.. code :: python

**Grako** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs a memoizing_ PEG_ parser in Python_.

I wrote **Grako** to address the shortcommings I have encountered over the years while working with other parser generation tools:

* To deal with programming languages in which important statement words (can't call them keywords) may be used as identifiers in programs, the parser must be able to lead the lexer. The parser also must lead the lexer to parse languages in which the meaning of input symbols may change with context (context sensitive languages) like Ruby_.

* When ambiguity is the norm in the parsed language, an LL or LR grammar becomes contaminated with miriads of lookaheads (just to make the parser greedy). PEG_ parsers address ambiguity from the onset, and memoization makes backtracking very efficient.

* Semantic actions, like AST creation or transformation, *do not*  belong in the grammar. Semantic actions in the grammar create yet another programming language to deal with when doing parsing and translation: the source language, the grammar language, the semantics language, the generated parser language, and translation's target language. 
  
* Pre-processing (like handling includes, fixed column formats, or Python_'s structure through indentation) belong in well-designed program code, and not in the grammar. 

* It is easy to recruit help on the base programming language (Python_), but, as the grammar language becomes more complex, it becomes increasingly difficult to find who can maintain a grammar. **Grako** grammars are in the spirit of a *Translators and Interpreters 101* course (if something's hard to explain to an university student, it's probably too complicated).

* Generated parsers should be humanly readable and debuggable. Looking at the generated source is sometimes the only way to find problems in a grammar, the semantic actions, or in the parser generator itself. And there's no way to trust generated code that you cannot understand.

* Python_ is a great language for working in language parsing and translation.

.. _EBNF: http://en.wikipedia.org/wiki/Ebnf 
.. _memoizing: http://en.wikipedia.org/wiki/Memoization 
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar 
.. _Python: http://python.org
.. _Ruby: http://www.ruby-lang.org/

The Generated Parsers
=====================

A **Grako** generated parser consists of the following classes:

* A root class derived from ``Parser`` wich implements the parser using one method for each grammar rule. The per-rule methods are named enclosing the rule's name with underscores to emphasize that they should not be tampered with (called, overriden, etc)::
 
    def _myrulename_(self):

* An *abstract* parser class that inherits from the root parser and verifies at runtime that there's a semantic method (see below) for every rule invoked. This class is useful as a parent class when changes are being made to the grammar, as it will throw an exception if there are missing semantic methods.

* An base class with one semantic method per grammar rule. Each method receives the as its single parameter the *Abstract Syntax Tree* (AST) built from the rule invocation.::

    def myrulename(self, ast):
        return ast

The methods in the base parser class return the same AST received as parameter, but derived classes can override the methods to have them return anything you like (like a *Semantic Tree*). You can use the base class as a template for your own parser.
       
The default ASTs are either lists, or dict objects that contain one item for every named element in the original grammar rule. Items can be accessed through the standard dict syntax, ``ast['key']``, or as attributes, ``ast.key``. 

AST entries are single values if only one item was added to a name, or lists if more than one item was added. There's a provision in the grammar syntax to force an entry to be a list even if a single item was added. 


Using the Tool
==============

**Grako** is run from the commandline like this::

    $ python -m grako

The *-h* and *--help* parameters provide full usage information::

        $ python -m grako -h
        usage: grako [-h] [-m name] [-o outfile] [-v] grammar

        Grako (for grammar compiler) takes grammars in a variation of EBNF as input, 
        and outputs a memoizing PEG parser in Python.
        
        positional arguments:
          grammar               The file name of the grammar to generate a parser for

        optional arguments:
          -h, --help            show this help message and exit
          -m name, --name name  An optional name for the grammar. It defaults to the
                                basename of the grammar file's name
          -o outfile, --outfile outfile
                                specify where the output should go (default is stdout)
          -v, --verbose         produce verbose output

        $


Using The Generated Parser
==========================

To use the generated parser, subclass the base or the abstract parser, create an instance of it passing the text to parse, and invoke its ``parse`` method passing the starting rule's name as parameter::

    class MyParser(MyParserBase):
        pass

    parser = MyParser('text to parse')
    result = parser.parse('start')
    print result # pasres() returns an AST by default
    print result.jsons() # the AST can be converted to json

The generated parsers have named arguments to specify whitespace characters, the regular expression for comments, case sensitivity, verbosity, etc. 

The EBNF Grammar Syntax
=======================

**Grako** uses a variant of the standard EBNF_ syntax. A grammar consists of a sequence of one or more rules of the form:

    ``name = expre ;``

If a *name* collides with a Python_ keyword, an underscore (``_``) will be appended to it on the generated parser.

The expressions, in reverse order of precedence, can be:

    ``e1 | e2``
        Match either ``e1`` or ``e2``.

    ``e1 e2`` 
        Match ``e1`` and then match ``e2``.

    ``( e )``
        Grouping. Match ``e``.

    ``[ e ]``
        Optionally match ``e``.

    ``{ e }`` or ``{ e }*``
        Match ``e`` zero or more times.

    ``{ e }+`` or ``{ e }-``
        Match ``e`` one or more times.

    ``&e``
        Positive lookahead. Try parsing ``e``, but do not consume any input.

    ``!e``
        Negative lookahead. Try parsing ``e`` and fail if the parse succeeds. 
        Do not consume any input whichever the outcome.

    ``'text'`` or ``"text"``
        Match the text within the quotation marks.

    ``?/<regexp>/?``
        Match the Python_ regular expression ``<regexp>`` at the current text 
        position. Unlike other expressions, this one does not advance over whitespace or 
        comments. For that, place the ``regexp`` as the only term in its own rule.

    ``rulename``
        Invoke the rule named ``rulename``. To help with lexical aspects of grammars,
        rules with names that begin with an uppercase letter will not advance the 
        input over whitespace and comments.

    ``()``
        The empty expression. Match nothing.

    ``>>``
        The cut expression. After this point, prevent other options from being
        considered even if the current option fails to parse.

    ``name:e``
        Add the result of ``e`` to the AST using ``name`` as key. If more than one item is
        added with the same ``name``, the entry is converted to a list.
    
    ``name+:e``
        Add the result of ``e`` to the AST using ``name`` as key. Force the entry to be 
        a list even if only one element is added.

    ``$``
        The *end of text* symbol. Verify thad the end of the input text has been reached.

    ``(*`` *comment* ``*)``
        Comments may appear anywhere in the text.

When there are no named items in a rule, the AST consists of the return values of elements parsed by the rule, either a single item or a list. This default behavior makes it easier to write simple rules. You will have an AST created for::

    number = ?/[0-9]+/?

without having to write::
    
    number = number:?/[0-9]+/?

When a rule has named elementes, the unnamed ones are excluded from the AST (ignored).

It is also possible to add an AST name to a rule::

    ast_name:rule = expre;

That will make the default AST returned to be a dict with a single item with key ``ast_name`` and the value recovered from the right hand side of the rule.

Whitespace
==========

By default, **Grako** generated parsers skip the usual whitespace charactes (``\t`` ``\v`` ``\n`` ``\r`` and the space character), but you can change that behaviour by passing a ``whitespace`` parameter to your parser::

    parser = MyParser(text, whitespace='\t ')

If you pass no whitespace characters::

    parser = MyParser(text, whitespace='')

then you will have to handle whitespace in your grammar as it's often done in PEG_ parsers.



Case Sensitivity
================

If your language is case insensitive, you can tell your parser so using the ``ignorecase`` parameter::

    parser = MyParser(text, ignorecase=True)

The change will affect both token and pattern matching.


Comments
========

Parsers will skip over comments specified as a regular expression using the ``comments_re`` paramenter::
    
    parser = MyParser(text, comments_re="\(\*.*?\*\)")


Semantic Actions
================

There are no constructs for semantic actions in **Grako** grammars. This is on purpose, as we believe that semantic actions obscure the declarative nature of grammars, and provide for poor modularization from the parser execution perspective.

The overridable per-rule methods in the generated abstract parser provide enough opportunity to do post-processing, checks (like for inadecuate use of keywords), and AST transformation.

For finer-grained control it is enough to declare more rules, as the impact on the parsing times will be minimal.

If pre-processing is required, one can place invocations of empty rules where appropiate::

    myrule = first_part preproc {second_part} ;

    preproc = () ;

The abstract parser will contain a rule of of the form::

    def preproc(self, ast):
        return ast

Warning
=======

The ``grako.model`` package is still under development. It's not usable in it's current state.

License
=======

**Grako** is copyright 2012-2013 by `ResQSoft Inc.`_ and  `Juancarlo Añez`_

.. _`ResQSoft Inc.`:  http://www.resqsoft.com/
.. _ResQSoft:  http://www.resqsoft.com/
.. _`Juancarlo Añez`: mailto:apalala@gmail.com

You may use the tool under the terms of the `GNU General Public License (GPL) version 3`_ as described in the enclosed **LICENSE.txt** file.

.. _`GNU General Public License (GPL) version 3`:  http://www.gnu.org/licenses/gpl.html


Credits
=======

The following must be mentioned as contributors of thoughts, ideas, code, *and funding* to the **Grako** project:

    **Bryan Ford** introduced_ PEG_ (parsing expression grammars) in 2004. 

    Other parser generators like `PEG.js`_ by **David Majda** inspired the work in **Grako**.

    **William Thompson** inspired the use of context managers with his `blog post`_ that I knew about through the invaluable `Python Weekly`_ nesletter, curated by **Rahul Chaudhary**

    **Terence Parr** created ANTLR_, probably the most solid and professional parser generator out there. Ter, *ANTLR* ant the folks on the ANLTR forums helped me shape my ideas about **Grako**.

    **JavaCC** looks like an abandoned project. I'll credit it properly when I have more information.

    **Guido van Rossum** created and has lead the development of the Python_ programming environment for over a decade. A tool like **Grako**, at under two thousand lines of code, would not have been possible without Python_.

    **My students** at UCAB_ inspired me to think about how grammar-based parser generation could be made more approachable.

    **Manuel Rey** led me through another, unfinished thesis project that taught me about what languages (programming languages in particular) are about.

    **Gustavo Lau** was my professor of *Language Theory* at USB_, and he was kind enough to be my tutor in a thesis project on programming languages that was more than I could chew.

    **Grako** would not have been possible without the funding provided by **Thomas Bragg** through ResQSoft_. 
    
.. _`blog post`: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html 
.. _`Python Weekly`: http://www.pythonweekly.com/ 
.. _introduced: http://dl.acm.org/citation.cfm?id=964001.964011
.. _`PEG.js`: http://pegjs.majda.cz/
.. _UCAB: http://www.ucab.edu.ve/
.. _USB: http://www.usb.ve/
.. _ANTLR: http://www.antlr.org/ 

-------------------------

