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
from englisp import parser, canonicalizer, interpreter

def test_conditionals():
    # 1. English conditional parse
    text_en = "If the dog chases the cat, the cat jumps."
    tree_en = parser.parse(text_en)
    assert tree_en.category == "IP"
    
    # Verify conditional structure (left child is CP, right child is IP)
    assert tree_en.children[0].category == "CP"
    assert tree_en.children[1].category == "IP"
    
    sexpr_en = canonicalizer.xbar_to_sexpr(tree_en)
    assert canonicalizer.sexpr_to_string(sexpr_en) == "(if (chases (dog the) (cat the)) (jumps (cat the)))"
    
    # Roundtrip generation
    tree_en_gen = canonicalizer.sexpr_to_xbar(sexpr_en)
    assert parser.generate(tree_en_gen, lang="en") == "If the dog chases the cat, the cat jumps."

    # 2. French conditional parse
    text_fr = "Si le chien chasse le chat, le chat saute."
    tree_fr = parser.parse(text_fr, lang="fr")
    sexpr_fr = canonicalizer.xbar_to_sexpr(tree_fr, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr_fr) == "(if (chases (dog the) (cat the)) (jumps (cat the)))"
    
    # Cross-lingual roundtrip: generate French from English S-expression
    tree_fr_gen = canonicalizer.sexpr_to_xbar(sexpr_en, lang="fr")
    assert parser.generate(tree_fr_gen, lang="fr") == "Si le chien chasse le chat, le chat saute."

def test_quantifiers():
    # 1. English quantifier: Every
    text1 = "Every dog jumps."
    tree1 = parser.parse(text1)
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1)
    assert canonicalizer.sexpr_to_string(sexpr1) == "(for-all dog (jumps _))"
    
    # Reconstruct and generate
    tree1_gen = canonicalizer.sexpr_to_xbar(sexpr1)
    assert parser.generate(tree1_gen) == "Every dog jumps."

    # 2. English quantifier: Some
    text2 = "Some cat runs."
    tree2 = parser.parse(text2)
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2)
    assert canonicalizer.sexpr_to_string(sexpr2) == "(exists cat (runs _))"
    
    # Reconstruct and generate
    tree2_gen = canonicalizer.sexpr_to_xbar(sexpr2)
    assert parser.generate(tree2_gen) == "Some cat runs."

    # 3. French quantifier: Chaque (for-all)
    text3 = "Chaque chien saute."
    tree3 = parser.parse(text3, lang="fr")
    sexpr3 = canonicalizer.xbar_to_sexpr(tree3, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr3) == "(for-all dog (jumps _))"
    
    # Cross-lingual: generate French from English S-expression
    tree3_fr_gen = canonicalizer.sexpr_to_xbar(sexpr1, lang="fr")
    assert parser.generate(tree3_fr_gen, lang="fr") == "Chaque chien saute."

def test_ditransitives_and_state_mutations():
    # 1. Ditransitive verb: "gives"
    text1 = "The dog gives the cat the book."
    tree1 = parser.parse(text1)
    # V'_base should have V + NP + NP
    sexpr1 = canonicalizer.xbar_to_sexpr(tree1)
    assert canonicalizer.sexpr_to_string(sexpr1) == "(gives (dog the) (cat the) (book the))"
    
    # Roundtrip
    tree1_gen = canonicalizer.sexpr_to_xbar(sexpr1)
    assert parser.generate(tree1_gen) == "The dog gives the cat the book."

    # French ditransitive
    text_fr = "Le chien donne le chat le livre."
    tree_fr = parser.parse(text_fr, lang="fr")
    sexpr_fr = canonicalizer.xbar_to_sexpr(tree_fr, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr_fr) == "(gives (dog the) (cat the) (book the))"
    
    # 2. Arithmetic verb: "increases"
    text2 = "The money increases by two."
    tree2 = parser.parse(text2)
    sexpr2 = canonicalizer.xbar_to_sexpr(tree2)
    assert canonicalizer.sexpr_to_string(sexpr2) == "(increases (money the) (by (two)))"
    
    # Roundtrip
    tree2_gen = canonicalizer.sexpr_to_xbar(sexpr2)
    assert parser.generate(tree2_gen) == "The money increases by two."

    # French arithmetic elision test
    text_fr2 = "L'argent augmente par deux."
    tree_fr2 = parser.parse(text_fr2, lang="fr")
    sexpr_fr2 = canonicalizer.xbar_to_sexpr(tree_fr2, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr_fr2) == "(increases (money the) (by (two)))"

def test_interpreter_programming_evaluation():
    model = interpreter.WorldModel()
    
    # Add initial facts: dog(fido), cat(felix), book(b)
    # and fido owns b: has(fido, b)
    model.add_fact("dog", ["fido"])
    model.add_fact("cat", ["felix"])
    model.add_fact("has", ["fido", "b"])
    
    # Verify initial ownership
    assert ("has", "fido", "b") in model.facts
    assert ("has", "felix", "b") not in model.facts
    
    # 1. Evaluate conditional if-statement (triggering action)
    # "If fido has b, fido gives felix b."
    expr = canonicalizer.parse_sexpr("(if (has fido b) (gives fido felix b))")
    res = interpreter.evaluate(expr, model)
    assert res["success"] is True
    assert res["triggered"] is True
    
    # Verify state mutation: ownership transferred
    assert ("has", "fido", "b") not in model.facts
    assert ("has", "felix", "b") in model.facts
    
    # 2. Evaluate for-all query
    # Assert fido jumps, and check if all dogs jump (false initially since fido hasn't jumped)
    q_forall = canonicalizer.parse_sexpr("(for-all dog (jumps _))")
    res_forall1 = interpreter.evaluate(q_forall, model)
    assert res_forall1["result"] is False
    
    # Assert jumps(fido)
    model.add_fact("jumps", ["fido"])
    # Now all dogs (only fido is registered as dog) jump
    res_forall2 = interpreter.evaluate(q_forall, model)
    assert res_forall2["result"] is True
    
    # 3. Evaluate exists query
    # Check if there exists a cat that jumps
    q_exists = canonicalizer.parse_sexpr("(exists cat (jumps _))")
    res_exists1 = interpreter.evaluate(q_exists, model)
    assert res_exists1["result"] is False
    
    # Assert jumps(felix)
    model.add_fact("jumps", ["felix"])
    res_exists2 = interpreter.evaluate(q_exists, model)
    assert res_exists2["result"] is True
    
    # "increases money by two"
    # Initial money val is 0 implicitly
    q_inc = canonicalizer.parse_sexpr("(increases money (by (two)))")
    res_inc = interpreter.evaluate(q_inc, model)
    assert res_inc["success"] is True
    assert ("val", "money", "2") in model.facts
    
    # Increase again by three
    q_inc2 = canonicalizer.parse_sexpr("(increases money (by (three)))")
    interpreter.evaluate(q_inc2, model)
    assert ("val", "money", "5") in model.facts
