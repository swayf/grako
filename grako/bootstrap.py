# coding: utf-8
from collections import OrderedDict
from shortcuts import * #@UnusedWildImport

__all__ = ['WHITESPACE', 'grako_parser']

WHITESPACE = u' \t\v\f\u00a0\r\n\u2028\u2029'

def grako_parser():
    word = rule_('word', pat_(r'[A-Za-z0-9_]+'))
    token = rule_('token', pat_(r'(?:' + r"'(?:[^']|\')*?'" + '|' + r'"(?:[^"]|\")*?"' + ')'))
    pattern = rule_('pattern', pat_(r"/(?:(?!/)|\/)*?/"))
    cut = rule_('cut', tok_('!'))

    subexpre = rule_('subexpre', seq_(tok_('('), cut_, ref_('expre'), tok_(')'), cut_))

    atom = or_(
               ref_('subexpre'),
               ref_('cut'),
               ref_('word'),
               ref_('token'),
               ref_('pattern')
               )

    varname = seq_(seq_(var_('id', ref_('word')), tok_(':'), cut_))
    named = rule_('named',
                or_(
                    var_('named',
                         seq_(varname,
                              var_('value', ref_('atom'))
                              )
                         ),
                    ref_('atom')
                    )
                )

    star = rule_('star', seq_(var_('star', ref_('named')), tok_('*'), cut_))
    plus = rule_('plus', seq_(var_('plus', ref_('named')), tok_('+'), cut_))
    opt = rule_('opt', seq_(var_('opt', ref_('named')), tok_('?'), cut_))

    element = rule_('element', or_(ref_('star'), ref_('plus'), ref_('opt'), ref_('named')))

    sequence = rule_('sequence', star_(ref_('element')))
    choice_tail = plus_(seq_(tok_('|'), cut_, ref_('sequence')))

    choice = or_(
                 var_('or',
                      seq_(
                           ref_('sequence'),
                           choice_tail
                           )
                      ),
                 ref_('sequence')
                 )


    expre = rule_('choice', choice)

    baserule = seq_(
                    var_('name',
                         ref_('word')
                         ),
                    tok_('='),
                    var_('expre', ref_('expre'))
                    )
    rule = rule_('rule',
                  seq_(
                       opt_(varname),
                       baserule,
                       tok_('¶')
                    )
                 )
    grammar = plus_(rule)

    rules = OrderedDict()
    rules.update(rule=rule)
    rules.update(expre=expre)
    rules.update(sequence=sequence)
    rules.update(element=element)
    rules.update(star=star)
    rules.update(plus=plus)
    rules.update(opt=opt)
    rules.update(named=named)
    rules.update(atom=atom)
    rules.update(subexpre=subexpre)
    rules.update(cut=cut)
    rules.update(word=word)
    rules.update(token=token)
    rules.update(pattern=pattern)
    return grammar_(grammar, rules)
