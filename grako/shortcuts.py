from parsing import * #@UnusedWildImport

tok_ = TokenParser
pat_ = PatternParser
star_ = RepeatParser
plus_ = RepeatOneParser
opt_ = OptionalParser
cut_ = CutParser()
ref_ = RuleRefParser
var_ = NamedParser
grp_ = GroupParser
seq_ = SequenceParser
or_ = ChoiceParser
rule_ = RuleParser
grammar_ = Grammar
