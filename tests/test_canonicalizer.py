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
#
# Reference the footer section of any of the 4 .md files (README.md, SPECIFICATION.md,
# USE_CASES.md, LEXICAL_STRATEGIES.md) in the project's root directory for full licensing details.
#
# I am the sole original creator of the EngLISP project (around August 2025), and did not rely on
# the resources of any academic institution or private individual to develop it.

import pytest
from englisp import parser, canonicalizer

def test_sexpr_parsing_and_stringifying():
    s = "(chased (dog the) (cat the))"
    expr = canonicalizer.parse_sexpr(s)
    assert expr == ["chased", ["dog", "the"], ["cat", "the"]]
    
    back_to_str = canonicalizer.sexpr_to_string(expr)
    assert back_to_str == s

def test_xbar_to_sexpr_rotation():
    # Parse "The dog chased the cat."
    tree = parser.parse("The dog chased the cat.")
    # Rotate to S-expression
    sexpr = canonicalizer.xbar_to_sexpr(tree)
    # Stringify
    s_expr_str = canonicalizer.sexpr_to_string(sexpr)
    assert s_expr_str == "(chased (dog the) (cat the))"

def test_sexpr_to_xbar_reconstruction():
    s_expr_str = "(chased (dog the) (cat the))"
    sexpr = canonicalizer.parse_sexpr(s_expr_str)
    
    # Reconstruct tree
    reconstructed_tree = canonicalizer.sexpr_to_xbar(sexpr)
    
    # Generate back to text
    text = parser.generate(reconstructed_tree)
    assert text == "The dog chased the cat."

def test_modal_parsing_roundtrip():
    # Let's verify modal helper 'can'
    # "The dog can chase the cat."
    tree = parser.parse("The dog can chase the cat.")
    sexpr = canonicalizer.xbar_to_sexpr(tree)
    s_expr_str = canonicalizer.sexpr_to_string(sexpr)
    assert s_expr_str == "(can (chase (dog the) (cat the)))"
    
    # Back to XBar
    reconstructed = canonicalizer.sexpr_to_xbar(sexpr)
    text = parser.generate(reconstructed)
    assert text == "The dog can chase the cat."

def test_coordination_and_relative_clauses_roundtrip():
    # 1. Coordinate sentences
    s1 = "The dog chased the cat and the fox jumped."
    tree1 = parser.parse(s1)
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1)
    s_expr_str1 = canonicalizer.sexpr_to_string(sexpr1)
    assert s_expr_str1 == "(and (chased (dog the) (cat the)) (jumped (fox the)))"
    
    reconstructed1 = canonicalizer.sexpr_to_xbar(sexpr1)
    text1 = parser.generate(reconstructed1)
    assert text1 == s1

    # 2. Relative clause
    s2 = "The dog that chased the cat jumped."
    tree2 = parser.parse(s2)
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2)
    s_expr_str2 = canonicalizer.sexpr_to_string(sexpr2)
    assert s_expr_str2 == "(jumped (dog the (that (chased _ (cat the)))))"
    
    reconstructed2 = canonicalizer.sexpr_to_xbar(sexpr2)
    text2 = parser.generate(reconstructed2)
    assert text2 == s2

