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

def test_english_subject_pronoun():
    # Singular neuter pronoun "it" resolving to highest salience match
    text = "The dog chased the cat. It jumped."
    tree = parser.parse(text)
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="en")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    assert sexpr_str == "(and (chased (dog the) (cat the)) (jumped (dog)))"
    
    # Text generation should retain original surface pronoun
    gen_text = parser.generate(tree, lang="en")
    assert gen_text == "The dog chased the cat and it jumped."

def test_english_plural_pronoun():
    # Plural pronoun "they" resolving to plural noun "dogs"
    text = "The dogs chased the cat. They jumped."
    tree = parser.parse(text)
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="en")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    assert sexpr_str == "(and (chased (dogs the) (cat the)) (jumped (dogs)))"
    
    gen_text = parser.generate(tree, lang="en")
    assert gen_text == "The dogs chased the cat and they jumped."

def test_french_subject_pronoun():
    # French grammatical gender agreement:
    # "chien" is masculine, "bibliothèque" is feminine.
    # "Elle" is feminine subject pronoun, so it must resolve to "bibliothèque".
    text = "Le chien a chassé la bibliothèque. Elle a sauté."
    tree = parser.parse(text, lang="fr")
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="fr")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    assert sexpr_str == "(and (chased (dog the) (library the)) (jumped (library)))"
    
    gen_text = parser.generate(tree, lang="fr")
    assert gen_text == "Le chien a chassé la bibliothèque et elle a sauté."

def test_french_plural_pronoun():
    # French plural masculine pronoun "Ils" resolving to "chiens"
    text = "Les chiens ont chassé la bibliothèque. Ils ont sauté."
    tree = parser.parse(text, lang="fr")
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="fr")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    assert sexpr_str == "(and (chased (dogs the) (library the)) (jumped (dogs)))"
    
    gen_text = parser.generate(tree, lang="fr")
    assert gen_text == "Les chiens ont chassé la bibliothèque et ils ont sauté."

def test_high_level_api_roundtrip():
    import englisp
    
    # 1. English roundtrip
    text_en = "The dog chased the cat. It jumped."
    minimized_en = englisp.nl_to_minimalist(text_en, lang="en")
    assert minimized_en == ["and", ["chased", "dog", "cat"], ["jumped", "dog"]]
    
    expanded_nl_en = englisp.minimalist_to_nl(minimized_en, lang="en")
    assert expanded_nl_en == "The dog chased the cat and the dog jumped."

    # 2. French roundtrip
    text_fr = "Le chien a chassé la bibliothèque. Elle a sauté."
    minimized_fr = englisp.nl_to_minimalist(text_fr, lang="fr")
    assert minimized_fr == ["and", ["chased", "dog", "library"], ["jumped", "library"]]
    
    expanded_nl_fr = englisp.minimalist_to_nl(minimized_fr, lang="fr")
    assert expanded_nl_fr == "Le chien a chassé la bibliothèque et la bibliothèque a sauté."
