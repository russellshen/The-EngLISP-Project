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
from englisp import parser
from englisp import canonicalizer
from englisp.interpreter import WorldModel, evaluate

def test_english_complex_tenses_bidirectional():
    # 1. Past Perfect Continuous: "had been chasing"
    text1 = "The dog had been chasing the cat."
    tree1 = parser.parse(text1, lang="en")
    
    # Verify the X-bar structure contains multiple auxiliary nodes
    ibar = tree1.children[1]
    aux_labels = [c.label for c in ibar.children if c.category == "I"]
    assert "had" in aux_labels
    assert "been" in aux_labels
    
    # Rotate to S-expression
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1, lang="en")
    assert sexpr1 == ["chase", ["dog", "the"], ["cat", "the"], [-1, -1, "continuous"]]
    
    # Reconstruct and generate text back
    reconstructed_tree = canonicalizer.sexpr_to_xbar(sexpr1, lang="en")
    generated_text = parser.generate(reconstructed_tree, lang="en")
    assert generated_text == "The dog had been chasing the cat."

    # 2. Future Perfect: "will have chased"
    text2 = "The dog will have chased the cat."
    tree2 = parser.parse(text2, lang="en")
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2, lang="en")
    assert sexpr2 == ["chase", ["dog", "the"], ["cat", "the"], [1, -1, "simple"]]
    
    reconstructed_tree2 = canonicalizer.sexpr_to_xbar(sexpr2, lang="en")
    generated_text2 = parser.generate(reconstructed_tree2, lang="en")
    assert generated_text2 == "The dog will have chased the cat."

def test_french_complex_tenses_bidirectional():
    # 1. Past Perfect Continuous: "avait été en train de chasser"
    text1 = "Le chien avait \u00e9t\u00e9 en train de chasser le chat."
    tree1 = parser.parse(text1, lang="fr")
    
    # Verify auxiliaries
    ibar = tree1.children[1]
    aux_labels = [c.label for c in ibar.children if c.category == "I"]
    assert "avait" in aux_labels
    assert "\u00e9t\u00e9" in aux_labels
    assert "en" in aux_labels
    assert "train" in aux_labels
    assert "de" in aux_labels
    
    # Rotate to English pivot S-expression
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1, lang="fr")
    # Should have identical pivot vector as English "had been chasing"
    assert sexpr1 == ["chase", ["dog", "the"], ["cat", "the"], [-1, -1, "continuous"]]
    
    # Reconstruct and generate French text back
    reconstructed_tree = canonicalizer.sexpr_to_xbar(sexpr1, lang="fr")
    generated_text = parser.generate(reconstructed_tree, lang="fr")
    assert generated_text == "Le chien avait \u00e9t\u00e9 en train de chasser le chat."

    # 2. Plus-que-parfait (Past Perfect): "avait chassé"
    text2 = "Le chien avait chass\u00e9 le chat."
    tree2 = parser.parse(text2, lang="fr")
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2, lang="fr")
    assert sexpr2 == ["chase", ["dog", "the"], ["cat", "the"], [-1, -1, "simple"]]
    
    reconstructed_tree2 = canonicalizer.sexpr_to_xbar(sexpr2, lang="fr")
    generated_text2 = parser.generate(reconstructed_tree2, lang="fr")
    assert generated_text2 == "Le chien avait chass\u00e9 le chat."

def test_cross_lingual_tense_translation():
    # Translate English "The dog was chasing the cat" to French "Le chien chassait le chat."
    text_en = "The dog was chasing the cat."
    tree_en = parser.parse(text_en, lang="en")
    sexpr = canonicalizer.xbar_to_sexpr(tree_en, lang="en")
    assert sexpr == ["chase", ["dog", "the"], ["cat", "the"], [-1, 0, "continuous"]]
    
    # Reconstruct in French
    tree_fr = canonicalizer.sexpr_to_xbar(sexpr, lang="fr")
    generated_fr = parser.generate(tree_fr, lang="fr")
    assert generated_fr == "Le chien chassait le chat."
    
    # Symmetrically, translate French "Le chien chassait le chat." back to English
    tree_fr_parsed = parser.parse("Le chien chassait le chat.", lang="fr")
    sexpr_fr = canonicalizer.xbar_to_sexpr(tree_fr_parsed, lang="fr")
    assert sexpr_fr == ["chase", ["dog", "the"], ["cat", "the"], [-1, 0, "continuous"]]
    
    tree_en_reconstructed = canonicalizer.sexpr_to_xbar(sexpr_fr, lang="en")
    generated_en = parser.generate(tree_en_reconstructed, lang="en")
    assert generated_en == "The dog was chasing the cat."

def test_world_model_tense_constraint():
    model = WorldModel()
    
    # Assert a fact in the past perfect: "had chased" -> [-1, -1, "simple"]
    fact_sexpr1 = ["assert", ["chase", ["dog", "the"], ["cat", "the"], [-1, -1, "simple"]]]
    res1 = evaluate(fact_sexpr1, model)
    assert res1["success"] is True
    
    # Assert another fact in present continuous: "is chasing" -> [0, 0, "continuous"]
    fact_sexpr2 = ["assert", ["chase", ["dog", "the"], ["fox", "the"], [0, 0, "continuous"]]]
    res2 = evaluate(fact_sexpr2, model)
    assert res2["success"] is True
    
    # Query with exact matching of tense vectors
    # Does the dog chase the cat in the past perfect?
    query_sexpr1 = ["chase", "dog", "cat", [-1, -1, "simple"]]
    res_query1 = evaluate(query_sexpr1, model)
    assert res_query1["result"] is True
    
    # Does the dog chase the fox in present continuous?
    query_sexpr2 = ["chase", "dog", "fox", [0, 0, "continuous"]]
    res_query2 = evaluate(query_sexpr2, model)
    assert res_query2["result"] is True
    
    # Is the dog chasing the cat in the present continuous?
    query_sexpr3 = ["chase", "dog", "cat", [0, 0, "continuous"]]
    res_query3 = evaluate(query_sexpr3, model)
    assert res_query3["result"] is False
