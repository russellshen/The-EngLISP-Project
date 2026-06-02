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
from englisp.xbar import XBarNode
from englisp import parser

def test_tokenize_and_tag():
    text = "The quick brown fox jumped over the lazy dog."
    tokens = parser.clean_and_tokenize(text)
    assert tokens == ["the", "quick", "brown", "fox", "jumped", "over", "the", "lazy", "dog"]
    
    tagged = parser.tag_tokens(tokens)
    assert tagged[0] == ("the", "Det")
    assert tagged[3] == ("fox", "N")
    assert tagged[4] == ("jumped", "V")
    assert tagged[5] == ("over", "P")
    assert tagged[8] == ("dog", "N")

def test_parse_simple_sentence():
    # SVO: The dog chased the cat.
    sentence = "The dog chased the cat."
    tree = parser.parse(sentence)
    
    assert tree.category == "IP"
    assert tree.role == "phrase"
    
    # Check subject NP
    subj = tree.children[0]
    assert subj.category == "NP"
    assert subj.role == "specifier"
    
    # Check verb phrase
    ibar = tree.children[1]
    assert ibar.category == "I'"
    vp = ibar.children[1]
    assert vp.category == "VP"
    
    vbar = vp.children[0]
    assert vbar.category == "V'"
    
    v_head = vbar.children[0]
    assert v_head.category == "V"
    assert v_head.label == "chased"
    
    obj = vbar.children[1]
    assert obj.category == "NP"
    assert obj.role == "complement"

def test_parse_complex_sentence():
    sentence = "The quick brown fox jumped over the lazy dog."
    tree = parser.parse(sentence)
    assert tree.category == "IP"
    
    # Verify terminals ordering matches
    terminals = tree.collect_terminals()
    # Note: parsing injects [pres/past] into I node which is in the terminals list
    assert "fox" in terminals
    assert "jumped" in terminals
    assert "over" in terminals
    assert "dog" in terminals

def test_generate_text():
    sentence = "The dog chased the cat."
    tree = parser.parse(sentence)
    generated = parser.generate(tree)
    assert generated == "The dog chased the cat."

def test_earley_parser_ambiguity():
    # Structural ambiguity: "The dog chased the cat in the library."
    # The PP "in the library" can attach to the NP "the cat" or the VP "chased".
    # score_tree should prefer NP attachment (+10 score), making "in the library"
    # a child of the NP "the cat" (N' post-modifier).
    tree = parser.parse("The dog chased the cat in the library.")
    
    # Verify that the PP is attached to "cat" (inside the NP complement)
    # The structure should be:
    # IP -> NP (subject) + I' -> I + VP -> V' -> V ("chased") + NP (complement: "the cat in the library")
    # Inside "the cat in the library" NP: Det ("the") + N' (bar) -> N'_base -> N'_base + PP
    ibar = tree.children[1]
    vp = ibar.children[1]
    vbar = vp.children[0]
    
    obj_np = vbar.children[1]
    assert obj_np.category == "NP"
    assert obj_np.role == "complement"
    
    # Its children should be Det ("the") and N' (bar)
    assert len(obj_np.children) == 2
    nbar = obj_np.children[1]
    assert nbar.category == "N'"
    
    # Since it has a PP, its children are N'_base ("cat") and PP
    assert nbar.children[0].category == "N'"
    assert nbar.children[1].category == "PP"
    assert nbar.children[1].role == "complement"

