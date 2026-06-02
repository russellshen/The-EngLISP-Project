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
import englisp

def test_bidirectional_stages_1_and_2():
    # Stage 1 <-> Stage 2
    text = "The dog chased the cat."
    xbar = englisp.nl_to_xbar(text, lang="en")
    assert xbar.category == "IP"
    
    generated = englisp.xbar_to_nl(xbar, lang="en")
    assert generated == text

def test_bidirectional_stages_2_and_3():
    # Stage 2 <-> Stage 3
    xbar = englisp.nl_to_xbar("The dog chased the cat.", lang="en")
    sexpr = englisp.xbar_to_englisp(xbar, lang="en")
    assert sexpr[0] == "chased"
    
    reconstructed_xbar = englisp.englisp_to_xbar(sexpr, lang="en")
    assert reconstructed_xbar.category == "IP"
    assert englisp.xbar_to_nl(reconstructed_xbar) == "The dog chased the cat."

def test_bidirectional_stages_3_and_4():
    # Stage 3 <-> Stage 4
    sexpr = ["chased", ["dog", "the"], ["cat", "the"]]
    minimized = englisp.englisp_to_minimalist(sexpr)
    assert minimized == ["chased", "dog", "cat"]
    
    expanded = englisp.minimalist_to_englisp(minimized)
    assert expanded == ["chased", ["dog", "the"], ["cat", "the"]]

def test_all_the_way_functions():
    # Stage 1 -> Stage 4
    text = "The dog chased the cat."
    minimized = englisp.nl_to_minimalist(text, lang="en")
    assert minimized == ["chased", "dog", "cat"]
    
    # Stage 4 -> Stage 1
    generated = englisp.minimalist_to_nl(minimized, lang="en")
    assert generated == "The dog chased the cat."

def test_string_helpers():
    sexpr = ["chase", ["dog", "the"], ["cat", "the"]]
    s = englisp.to_string(sexpr)
    assert s == "(chase (dog the) (cat the))"
    
    parsed = englisp.from_string(s)
    assert parsed == sexpr
