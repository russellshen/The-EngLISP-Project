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
from englisp.interpreter import WorldModel, evaluate, has_variables
from englisp.canonicalizer import parse_sexpr

def test_world_model_assertions():
    model = WorldModel()
    
    # Assert a simple relation
    res1 = evaluate(parse_sexpr("(assert (chased (dog the) (cat the)))"), model)
    assert res1["success"] is True
    assert res1["fact"] == ("chased", "dog", "cat")
    assert ("chased", "dog", "cat") in model.facts

    # Assert a property
    res2 = evaluate(parse_sexpr("(assert (lazy (dog the)))"), model)
    assert res2["success"] is True
    assert res2["fact"] == ("lazy", "dog")
    assert ("lazy", "dog") in model.facts

def test_propositional_queries():
    model = WorldModel()
    model.add_fact("chased", ["dog", "cat"])
    model.add_fact("lazy", ["dog"])

    # Test basic truth query
    res1 = evaluate(parse_sexpr("(chased dog cat)"), model)
    assert res1["result"] is True

    res2 = evaluate(parse_sexpr("(chased cat dog)"), model)
    assert res2["result"] is False

    # Test logical NOT
    res3 = evaluate(parse_sexpr("(not (chased cat dog))"), model)
    assert res3["result"] is True

    res4 = evaluate(parse_sexpr("(not (chased dog cat))"), model)
    assert res4["result"] is False

    # Test logical AND
    res5 = evaluate(parse_sexpr("(and (chased dog cat) (lazy dog))"), model)
    assert res5["result"] is True

    res6 = evaluate(parse_sexpr("(and (chased dog cat) (not (lazy cat)))"), model)
    assert res6["result"] is True

    res7 = evaluate(parse_sexpr("(and (chased dog cat) (lazy cat))"), model)
    assert res7["result"] is False

    # Test logical OR
    res8 = evaluate(parse_sexpr("(or (chased cat dog) (lazy dog))"), model)
    assert res8["result"] is True

    res9 = evaluate(parse_sexpr("(or (chased cat dog) (lazy cat))"), model)
    assert res9["result"] is False

def test_first_order_variables():
    model = WorldModel()
    model.add_fact("chased", ["dog", "cat"])
    model.add_fact("chased", ["fox", "dog"])
    model.add_fact("lazy", ["dog"])

    # Test simple variable query
    res1 = evaluate(parse_sexpr("(chased dog ?x)"), model)
    assert res1["variables"] is True
    assert res1["success"] is True
    assert res1["bindings"] == [{"?x": "cat"}]

    # Test variable query with multiple matches
    res2 = evaluate(parse_sexpr("(chased ?who dog)"), model)
    assert res2["success"] is True
    assert {"?who": "fox"} in res2["bindings"]

    # Test variable query in AND conjunction (joining bindings)
    res3 = evaluate(parse_sexpr("(and (chased ?x ?y) (lazy ?x))"), model)
    assert res3["success"] is True
    # ?x must be dog because dog is lazy, and dog chased cat, so ?x = dog, ?y = cat
    assert res3["bindings"] == [{"?x": "dog", "?y": "cat"}]

    # Test variable query in AND with NOT (filtering bindings)
    res4 = evaluate(parse_sexpr("(and (chased ?x ?y) (not (lazy ?x)))"), model)
    assert res4["success"] is True
    # ?x = fox chased ?y = dog, and fox is NOT lazy, so this matches
    assert res4["bindings"] == [{"?x": "fox", "?y": "dog"}]

def test_interpreter_let_and_composed_predicates():
    model = WorldModel()
    model.add_fact("chased", ["dog", "cat"])
    model.add_fact("lazy", ["dog"])
    model.add_fact("barked", ["dog"])
    model.add_fact("runs", ["dog"])

    # 1. Test let evaluation in assertion
    res1 = evaluate(parse_sexpr("(let ((d dog)) (assert (happy d)))"), model)
    assert res1["success"] is True
    assert ("happy", "dog") in model.facts

    # 2. Test let evaluation in query
    res2 = evaluate(parse_sexpr("(let ((d dog)) (and (chased d ?x) (lazy d)))"), model)
    assert res2["success"] is True
    assert res2["bindings"] == [{"?x": "cat"}]

    # 3. Test composed predicate evaluation
    res3 = evaluate(parse_sexpr("((and barked runs) ?x)"), model)
    assert res3["success"] is True
    assert res3["bindings"] == [{"?x": "dog"}]

