 .. -*- restructuredtext -*-

Grako
=====

**Grako** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs memoizing_ PEG_ parsers in Python_. 

**Grako** is *different* from other PEG_ parser generators in that the generated parsers use Python_'s very efficient exception-handling system to backtrack. **Grako** generated parsers simply assert what must be parsed; there are no complicated *if-then-else* sequences for decison making or backtracking. *Possitive and negative lookaheads*, and the *cut* element allow for additional, hand-crafted optimizations at the grammar level.

**Grako**, the runtime support, and the generated parsers have measurably low `Cyclomatic complexity`_.  At less than 2500 likes of Python_, it is possible to study all its source code in a single session. **Grako**'s only dependecies are on the Python_ 2.7/3.x standard libraries. 

.. _`Cyclomatic complexity`: http://en.wikipedia.org/wiki/Cyclomatic_complexity 

**Grako** is feature complete and currently being used over very large grammars to parse and translate hundreds of thousands of lines of legacy_ code. 

.. _KLOC: http://en.wikipedia.org/wiki/KLOC 
.. _legacy: http://en.wikipedia.org/wiki/Legacy_code 


Rationale
---------

**Grako** was created to address recurring problems encountered over decades of working with parser generation tools:

* To deal with programming languages in which important statement words (can't call them keywords) may be used as identifiers in programs, the parser must be able to lead the lexer. The parser must also lead the lexer to parse languages in which the meaning of input symbols may change with context, like Ruby_.

* When ambiguity is the norm in the parsed language (as is the case in several legacy_ ones), an LL or LR grammar becomes contaminated with miriads of lookaheads. PEG_ parsers address ambiguity from the onset. Memoization, and relying on the exception-handling system makes backtracking very efficient.

* Semantic actions, like `Abstract Syntax Tree`_ (AST_) creation or transformation, *do not*  belong in the grammar. Semantic actions in the grammar create yet another programming language to deal with when doing parsing and translation: the source language, the grammar language, the semantics language, the generated parser's language, and translation's target language. 

* Pre-processing (like dealing with includes, fixed column formats, or Python_'s structure through indentation) belong in well-designed program code, and not in the grammar. 

* It is easy to recruit help knowledged about a mainstream programming language (Python_ in this case); it is not so for grammar description languages. As a grammar language becomes more complex, it becomes increasingly difficult to find who can maintain a parser. **Grako** grammars are in the spirit of a *Translators and Interpreters 101* course (if something's hard to explain to an university student, it's probably too complicated).

* Generated parsers should be humanly-readable and debuggable. Looking at the generated source code is sometimes the only way to find problems in a grammar, the semantic actions, or in the parser generator itself. It's inconvenient to trust generated code that you cannot understand.

* Python_ is a great language for working in language parsing and translation.

.. _`Abstract Syntax Tree`: http://en.wikipedia.org/wiki/Abstract_syntax_tree 
.. _`AST`: http://en.wikipedia.org/wiki/Abstract_syntax_tree 
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf 
.. _memoizing: http://en.wikipedia.org/wiki/Memoization 
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar 
.. _Python: http://python.org
.. _Ruby: http://www.ruby-lang.org/

The Generated Parsers
---------------------

A **Grako** generated parser consists of the following classes:

* A root class derived from ``Parser`` which implements the parser using one method for each grammar rule. The per-rule methods are named enclosing the rule's name with underscores to emphasize that they should not be tampered with (called, overriden, etc)::

    def _myrulename_(self):

* An *abstract* parser class that inherits from the root parser and verifies at runtime that there's a semantic method (see below) for every rule invoked. This class is useful as a parent class when changes are being made to the grammar, as it will throw an exception if there are missing semantic methods.

* An base class with one semantic method per grammar rule. Each method receives as its single parameter the `Abstract Syntax Tree`_ (AST_) built from the rule invocation.::

    def myrulename(self, ast):
        return ast

The methods in the base parser class return the same AST_ received as parameter, but derived classes can override the methods to have them return anything (for example, a `Semantic Graph`_). The base class can be used as a template for the final parser.

By default, and AST_ is either a list (for *closures*), or dict-derived object that contains one item for every named element in the grammar rule. Items can be accessed through the standard dict syntax, ``ast['key']``, or as attributes, ``ast.key``. 

AST_ entries are single values if only one item was associated with a name, or lists if more than one item was matched. There's a provision in the grammar syntax (see below) to force an AST_ entry to be a list even if only one element was matched. The value for named elements that were not found during the parse (perhaps because they are optional) is ``None``.

.. _`Semantic Graph`: http://en.wikipedia.org/wiki/Abstract_semantic_graph 
       

Using the Tool
--------------

**Grako** is run from the commandline::

    $ python -m grako

or::

    $ scripts/grako

or just::

    $ grako

if **Grako** was installed using *easy_install* or *pip*.

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
          -t, --trace           produce verbose parsing output

        $



Using the Generated Parser
--------------------------

To use the generated parser, just subclass the base or the abstract parser, create an instance of it, and invoke its ``parse()`` method passing the text to parse and the starting rule's name as parameter::

    class MyParser(MyParserBase):
        pass

    parser = MyParser()
    ast = parser.parse('text to parse', rule_name='start')
    print(ast)
    print(json.dumps(ast, indent=2)) # ASTs are JSON-friendy

This is more or less what happens if you invole the generated parser directly::

    python myparser.py inputfile startrule

The generated parsers constructors accept named arguments to specify whitespace characters, the regular expression for comments, case sensitivity, verbosity, etc. 



The EBNF Grammar Syntax
-----------------------

**Grako** uses a variant of the standard EBNF_ syntax. A grammar consists of a sequence of one or more rules of the form::

    name = expre ;

or::

    name = expre .

Both the semicolon (``;``) and the period (``.``) are accepted as rule definition terminators.

If a *name* collides with a Python_ keyword, an underscore (``_``) will be appended to it on the generated parser.

If you define more than one rule with the same name::
    
    name = expre1 ;
    name = expre2 ;

The result will be equivalent to applying the choice operator to the 
right-hand-side expressions::

    name = expre1 | expre2 ;

Rule names that start with an uppercase character::

   FRAGMENT = ?/[a-z]+/?

*do not* advance over whitespace before begining to parse. This feature becomes handy when defining complex lexical elements, as it allows breaking them into several rules.

The expressions, in reverse order of operator precedence, can be:

    ``e1 | e2``
        Match either ``e1`` or ``e2``.

    ``e1 e2`` 
        Match ``e1`` and then match ``e2``.

    ``e1 , e2`` 
        As above. Match ``e1`` and then match ``e2``.

    ``( e )``
        Grouping. Match ``e``.

    ``[ e ]``
        Optionally match ``e``.

    ``{ e }`` or ``{ e }*``
        Closure. Match ``e`` zero or more times. Note that the AST_ returned for a closure is always a list.

    ``{ e }+`` or ``{ e }-``
        Closure+1. Match ``e`` one or more times.

    ``&e``
        Positive lookahead. Try parsing ``e``, but do not consume any input.

    ``!e``
        Negative lookahead. Try parsing ``e`` and fail if there's a match. Do not consume any input whichever the outcome.

    ``'text'`` or ``"text"``
        Match the token text within the quotation marks. 
        
        **Note that** if *text* is alphanumeric, then Grako will check that the character following the token is not alphanumerc. This is done to prevent tokens like *IN* matching when the text ahead is *INITIALIZE*. This feature can be turned off by passing ``nameguard=False`` to the `Parser` or the `Buffer`, or by using a pattern expression (see below) instead of a token expression.

    ``?/regexp/?``
        Match the Python_ regular expression ``regexp`` at the current text position. Unlike other expressions, this one does not advance over whitespace or comments. For that, place the ``regexp`` as the only term in its own rule.

    ``rulename``
        Invoke the rule named ``rulename``. To help with lexical aspects of grammars, rules with names that begin with an uppercase letter will not advance the input over whitespace or comments.

    ``()``
        The empty expression. Match nothing.

    ``>>``
        The cut expression. After this point, prevent other options from being considered even if the current option fails to parse.

    ``name:e``
        Add the result of ``e`` to the AST_ using ``name`` as key. If more than one item is added with the same ``name``, the entry is converted to a list.
    
    ``name+:e``
        Add the result of ``e`` to the AST_ using ``name`` as key. Force the entry to be a list even if only one element is added.

    ``@e``
        The override operator. Make the AST_ for the complete rule be the AST_ for ``e``. The override operator is useful to recover only part of the right hand side of a rule without the need to name it, and then add a semantic action to recover the interesting part. This is a typical use of the override operator::

        subexp = '(' @expre ')' .

The AST_ returned for the ``subexp`` rule will be the AST_ recovered from invoking ``expre``, without having to write a semantic action.

    ``$``
        The *end of text* symbol. Verify thad the end of the input text has been reached.

    ``(*`` *comment* ``*)``
        Comments may appear anywhere in the text.

When there are no named items in a rule, the AST_ consists of the elements parsed by the rule, either a single item or a list. This default behavior makes it easier to write simple rules. You will have an AST_ created for::

    number = ?/[0-9]+/? .

without having to write::
    
    number = number:?/[0-9]+/?

When a rule has named elementes, the unnamed ones are excluded from the AST_ (they are ignored).

It is also possible to add an AST_ name to a rule::

    name:rule = expre;

That will make the default AST_ returned to be a dict with a single item ``name`` as key, and the AST_ from the right-hand side of the rule as value.


Whitespace
----------

By default, **Grako** generated parsers skip the usual whitespace charactes (whatever Python_ defines as ``string.whitespace``), but you can change that behaviour by passing a ``whitespace`` parameter to your parser. For example::

    parser = MyParser(text, whitespace='\t ')

will not consider end-of-line characters as whitespace.

If you don't define any whitespace characters::

    parser = MyParser(text, whitespace='')

then you will have to handle whitespace in your grammar rules (as it's often done in PEG_ parsers).


Case Sensitivity
----------------

If the source language is case insensitive, you can tell your parser by using the ``ignorecase`` parameter::

    parser = MyParser(text, ignorecase=True)

The change will affect both token and pattern matching.


Comments
--------

Parsers will skip over comments specified as a regular expression using the ``comments_re`` paramenter::
    
    parser = MyParser(text, comments_re="\(\*.*?\*\)")

For more complex comment handling, you can override the ``Parser._eatcomments()`` method.


Semantic Actions
----------------

There are no constructs for semantic actions in **Grako** grammars. This is on purpose, as we believe that semantic actions obscure the declarative nature of grammars and provide for poor modularization from the parser execution perspective.

The overridable, per-rule methods in the generated abstract parser provide enough opportunity to do semantics as a rule post-processing operation, like verifications (like for inadecuate use of keywords), or AST_ transformation.

For finer-grained control it is enough to declare more rules, as the impact on the parsing times will be minimal.

If pre-processing is required at some point, it is enough to place invocations of empty rules where appropiate::

    myrule = first_part preproc {second_part} ;

    preproc = () ;

The abstract parser will contain a rule of of the form::

    def preproc(self, ast):
        return ast


The (lack of) Documentation
---------------------------
**Grako** so lacking in comments and doc-comments for these reasons:

    1. Inline documentation easily goes out of phase with what the code actually does. It is an equivalent and more productive effort to provide out-of-line documentation.

    2. Minimal and understandable code with meaningful identifiers makes comments redundant or unnecesary.

Still, comments are provided for *non-obvious intentions* in the code, and each **Grako** module carries a doc-comment describing its purpose.


Examples
--------

The file ``etc/grako.ebnf`` contains a grammar for the **Grako** EBNF_ language written in the same language. It is used in the *bootstrap* test suite to prove that **Grako** can generate a parser to parse its own language.


License
-------

**Grako** is Copyright 2012-2013 by `ResQSoft Inc.`_ and  `Juancarlo Añez`_

.. _`ResQSoft Inc.`:  http://www.resqsoft.com/
.. _ResQSoft:  http://www.resqsoft.com/
.. _`Juancarlo Añez`: mailto:apalala@gmail.com

You may use the tool under the terms of the `GNU General Public License (GPL) version 3`_ as described in the enclosed **LICENSE.txt** file.

.. _`GNU General Public License (GPL) version 3`:  http://www.gnu.org/licenses/gpl.html

**If your project requires different licensing** please contact 
`info@resqsoft.com`_.

.. _`info@resqsoft.com`: mailto:info@resqsoft.com


Contact
-------

For queries and comments about **Grako**, please use the `Grako Forum`_.

.. _`Grako Forum`:  https://groups.google.com/forum/?fromgroups#!forum/grako


Credits
-------

The following must be mentioned as contributors of thoughts, ideas, code, *and funding* to the **Grako** project:

* **Niklaus Wirth** was the chief designer of the programming languages Euler, Algol W, Pascal, Modula, Modula-2, Oberon, Oberon-2, and Oberon-07. In the last chapter of his 1976 book `Algorithms + Data Structures = Programs`_, Wirth_ creates a top-down, descent parser with recovery for the Pascal_-like, `LL(1)`_ programming language `PL/0`_. The structure of the program is that of a PEG_ parser, though the concept of PEG_ wasn't formalized until 2004.

* **Bryan Ford** introduced_ PEG_ (parsing expression grammars) in 2004. 

* Other parser generators like `PEG.js`_ by **David Majda** inspired the work in **Grako**.

* **William Thompson** inspired the use of context managers with his `blog post`_ that I knew about through the invaluable `Python Weekly`_ nesletter, curated by **Rahul Chaudhary**

* **Terence Parr** created ANTLR_, probably the most solid and professional parser generator out there. Ter, *ANTLR*, and the folks on the *ANLTR* forums helped me shape my ideas about **Grako**.

* **JavaCC** (originally Jack_) looks like an abandoned project. It was the first parser generator I used while teaching.

* **Guido van Rossum** created and has lead the development of the Python_ programming environment for over a decade. A tool like **Grako**, at under three thousand lines of code, would not have been possible without Python_.

* **My students** at UCAB_ inspired me to think about how grammar-based parser generation could be made more approachable.

* **Gustavo Lau** was my professor of *Language Theory* at USB_, and he was kind enough to be my tutor in a thesis project on programming languages that was more than I could chew.

* **Manuel Rey** led me through another, unfinished thesis project that taught me about what languages (spoken languages in general, and programming languages in particular) are about.

* **Grako** would not have been possible without the funding provided by **Thomas Bragg** through ResQSoft_. 

.. _Wirth: http://en.wikipedia.org/wiki/Niklaus_Wirth 
.. _Pascal: http://en.wikipedia.org/wiki/Pascal_(programming_language) 
.. _`PL/0`: http://en.wikipedia.org/wiki/PL/0 
.. _`LL(1)`: http://en.wikipedia.org/wiki/LL(1) 
.. _`Algorithms + Data Structures = Programs`: http://www.amazon.com/Algorithms-Structures-Prentice-Hall-Automatic-Computation/dp/0130224189/ 
.. _`blog post`: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html 
.. _`Python Weekly`: http://www.pythonweekly.com/ 
.. _introduced: http://dl.acm.org/citation.cfm?id=964001.964011
.. _`PEG.js`: http://pegjs.majda.cz/
.. _UCAB: http://www.ucab.edu.ve/
.. _USB: http://www.usb.ve/
.. _ANTLR: http://www.antlr.org/ 
.. _Jack: http://en.wikipedia.org/wiki/Javacc 


Change History
--------------

**1.0rc3** 2013-02-04 
    * Now the text to parse is passed directly to the `parse()` method.
    * Added a *grako* script to invoke the tool directly.
    * An end-to end translation example is provided in the *examples/regexp* project.
    * Tweaked for convenience and clearness while developing the *regexp* example.
    * Many corrections to this *README*.
    * Tested under Python_ 3.3.
    * Final release candidate for 1.0. Only improvements to the documentation will be accepted from now on.

**1.0rc2** 2013-02-02 
    Second release candidate. Made memoization local to each parser instance so the cached information from one parse doesn't stay (as garbage) when parsing multiple (hundreds of) input files.

**1.0rc1** 2013-01-30 
    First release candidate.

