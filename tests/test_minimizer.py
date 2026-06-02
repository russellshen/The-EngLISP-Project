# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.
#
# For commercial licensing inquiries, please contact:
# Russell Shen (russellshen7@gmail.com)
#
# Licensing terms, scope, and compensation are subject to separate negotiation.

import pytest
from englisp import canonicalizer, minimizer

def test_double_negative_elimination():
    # (not (not happy)) -> happy
    expr1 = ["not", ["not", "happy"]]
    min1 = minimizer.minimize_sexpr(expr1)
    assert min1 == "happy"

def test_negated_adjective_contraction():
    # (not happy) -> sad
    expr1 = ["not", "happy"]
    min1 = minimizer.minimize_sexpr(expr1)
    assert min1 == "sad"

def test_active_voice_normalization():
    # (chased cat (by dog)) -> (chased dog cat)
    expr = ["chased", ["cat", "the"], ["by", ["dog", "the"]]]
    min_expr = minimizer.minimize_sexpr(expr)
    assert min_expr == ["chased", "dog", "cat"]

def test_determiner_pruning_and_compounding():
    # (dog the young) -> puppy
    expr = ["dog", "the", "young"]
    min_expr = minimizer.minimize_sexpr(expr)
    assert min_expr == "puppy"
    
    # (dog the) -> dog
    expr_simple = ["dog", "the"]
    min_expr_simple = minimizer.minimize_sexpr(expr_simple)
    assert min_expr_simple == "dog"

def test_minimizer_roundtrip():
    # Starting S-expression: "(chased (dog the young) (cat the))"
    s_expr_str = "(chased (dog the young) (cat the))"
    sexpr = canonicalizer.parse_sexpr(s_expr_str)
    
    # Minimize: -> "(chased puppy cat)"
    minimized = minimizer.minimize_sexpr(sexpr)
    minimized_str = canonicalizer.sexpr_to_string(minimized)
    assert minimized_str == "(chased puppy cat)"
    
    # Expand: -> "(chased (dog the young) (cat the))"
    expanded = minimizer.expand_sexpr(minimized)
    expanded_str = canonicalizer.sexpr_to_string(expanded)
    assert expanded_str == s_expr_str


def test_argument_canonicalization_sorting():
    # Noun Phrase modifier sorting test:
    # (fox the quick brown) vs (fox the brown quick) should both collapse to (fox brown quick)
    expr1 = ["fox", "the", "quick", "brown"]
    expr2 = ["fox", "the", "brown", "quick"]
    
    min1 = minimizer.minimize_sexpr(expr1)
    min2 = minimizer.minimize_sexpr(expr2)
    
    # After det pruning and sorting (brown < quick): both should be ['fox', 'brown', 'quick']
    assert min1 == ["fox", "brown", "quick"]
    assert min2 == ["fox", "brown", "quick"]
    assert min1 == min2

    # Verb Phrase adjunct sorting test:
    # (chased dog cat quickly (in library)) vs (chased dog cat (in library) quickly)
    v_expr1 = ["chased", "dog", "cat", "quickly", ["in", "library"]]
    v_expr2 = ["chased", "dog", "cat", ["in", "library"], "quickly"]
    
    v_min1 = minimizer.minimize_sexpr(v_expr1)
    v_min2 = minimizer.minimize_sexpr(v_expr2)
    
    # Serialized comparison (in library < quickly): both should collapse to (chased dog cat (in library) quickly)
    assert canonicalizer.sexpr_to_string(v_min1) == "(chased dog cat (in library) quickly)"
    assert canonicalizer.sexpr_to_string(v_min2) == "(chased dog cat (in library) quickly)"
    assert v_min1 == v_min2


def test_passive_voice_with_adjuncts():
    # Passive SVO sentence with adjuncts:
    # (chased (cat the) (by (dog the)) quickly) -> (chased dog cat quickly)
    expr = ["chased", ["cat", "the"], ["by", ["dog", "the"]], "quickly"]
    minimized = minimizer.minimize_sexpr(expr)
    assert minimized == ["chased", "dog", "cat", "quickly"]

def test_let_bindings_minimization_and_expansion():
    # Repeated NP: (dog the quick brown)
    expr = ["and", ["chased", ["dog", "the", "quick", "brown"], ["cat", "the"]], ["barked", ["dog", "the", "quick", "brown"]]]
    minimized = minimizer.minimize_sexpr(expr)
    
    assert minimized[0] == "let"
    assert len(minimized[1]) == 1
    assert minimized[1][0][0] == "d"
    assert minimized[1][0][1] == ["dog", "brown", "quick"]
    assert minimized[2] == ["and", ["chased", "d", "cat"], ["barked", "d"]]
    
    expanded = minimizer.expand_sexpr(minimized)
    assert expanded == ["and", ["chased", ["dog", "the", "brown", "quick"], ["cat", "the"]], ["barked", ["dog", "the", "brown", "quick"]]]

def test_predicate_composition_minimization_and_expansion():
    # Unary predicates sharing same subject:
    expr = ["and", ["barked", "dog"], ["runs", "dog"]]
    minimized = minimizer.minimize_sexpr(expr)
    assert minimized == [["and", "barked", "runs"], "dog"]
    
    expanded = minimizer.expand_sexpr(minimized)
    assert expanded == ["and", ["barked", ["dog", "the"]], ["runs", ["dog", "the"]]]


