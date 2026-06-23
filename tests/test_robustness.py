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
from englisp import parser, canonicalizer, minimizer

def test_fuzzy_spellcheck():
    # Typos in English
    text_en = "teh dog chased teh cat."
    tree_en = parser.parse(text_en)
    sexpr_en = canonicalizer.xbar_to_sexpr(tree_en)
    assert canonicalizer.sexpr_to_string(sexpr_en) == "(chased (dog the) (cat the))"

    # Typos in French
    text_fr = "le renard paresux saute."  # "paresux" typo for "paresseux"
    tree_fr = parser.parse(text_fr, lang="fr")
    sexpr_fr = canonicalizer.xbar_to_sexpr(tree_fr, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr_fr) == "(jumps (fox the lazy))"

def test_contraction_expansion():
    # English contraction: "can't"
    text1 = "The dog can't jump."
    tree1 = parser.parse(text1)
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1)
    # Pivot should wrap in "cannot" modal
    assert canonicalizer.sexpr_to_string(sexpr1) == "(cannot (jump (dog the)))"

    # English contraction: "doesn't"
    text2 = "The student doesn't read the book."
    tree2 = parser.parse(text2)
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2)
    assert canonicalizer.sexpr_to_string(sexpr2) == "(doesnt (read (student the) (book the)))"

def test_fragment_parsing_and_generation():
    # 1. Noun Phrase fragment
    text_np = "the modern computer"
    tree_np = parser.parse(text_np)
    assert tree_np.category == "FRAG"
    sexpr_np = canonicalizer.xbar_to_sexpr(tree_np)
    assert canonicalizer.sexpr_to_string(sexpr_np) == "(frag (computer the modern))"
    
    # Roundtrip generation
    xbar_np2 = canonicalizer.sexpr_to_xbar(sexpr_np)
    assert parser.generate(xbar_np2) == "The modern computer."

    # 2. Prepositional Phrase fragment
    text_pp = "in the library"
    tree_pp = parser.parse(text_pp)
    assert tree_pp.category == "FRAG"
    sexpr_pp = canonicalizer.xbar_to_sexpr(tree_pp)
    assert canonicalizer.sexpr_to_string(sexpr_pp) == "(frag (in (library the)))"
    
    # Roundtrip generation
    xbar_pp2 = canonicalizer.sexpr_to_xbar(sexpr_pp)
    assert parser.generate(xbar_pp2) == "In the library."

    # 3. Verb Phrase fragment
    text_vp = "chased the cat"
    tree_vp = parser.parse(text_vp)
    assert tree_vp.category == "FRAG"
    sexpr_vp = canonicalizer.xbar_to_sexpr(tree_vp)
    assert canonicalizer.sexpr_to_string(sexpr_vp) == "(frag (chased _ (cat the)))"
    
    # Roundtrip generation
    xbar_vp2 = canonicalizer.sexpr_to_xbar(sexpr_vp)
    assert parser.generate(xbar_vp2) == "Chased the cat."

def test_fragment_minimization_and_expansion():
    # Test that (frag ...) is bypassed and minimized correctly
    sexpr_np = ["frag", ["computer", "the", "modern"]]
    min_sexpr = minimizer.minimize_sexpr(sexpr_np)
    # The determiner 'the' should be pruned under NP minimization, but 'frag' bypassed
    assert canonicalizer.sexpr_to_string(min_sexpr) == "(frag (computer modern))"

    # Expand back
    exp_sexpr = minimizer.expand_sexpr(min_sexpr)
    assert canonicalizer.sexpr_to_string(exp_sexpr) == "(frag (computer the modern))"

def test_cross_lingual_fragment():
    # French fragment to English pivot to French/English text
    fr_frag = "dans la bibliothèque"
    tree_fr = parser.parse(fr_frag, lang="fr")
    sexpr_fr = canonicalizer.xbar_to_sexpr(tree_fr, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr_fr) == "(frag (in (library the)))"

    # Generate English
    tree_en = canonicalizer.sexpr_to_xbar(sexpr_fr, lang="en")
    assert parser.generate(tree_en, lang="en") == "In the library."

    # Generate French
    tree_fr_gen = canonicalizer.sexpr_to_xbar(sexpr_fr, lang="fr")
    assert parser.generate(tree_fr_gen, lang="fr") == "Dans la bibliothèque."
