# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.

import pytest
from englisp import interpreter, canonicalizer

def test_arithmetic_calculations():
    model = interpreter.WorldModel()

    # 1. Basic math evaluation
    expr1 = canonicalizer.parse_sexpr("(+ 5 3)")
    res1 = interpreter.evaluate(expr1, model)
    assert res1["success"] is True
    assert res1["result"] == 8

    # 2. Nested math evaluation
    expr2 = canonicalizer.parse_sexpr("(* (+ 2 3) 4)")
    res2 = interpreter.evaluate(expr2, model)
    assert res2["success"] is True
    assert res2["result"] == 20

    # 3. String numeral text math evaluation
    expr3 = canonicalizer.parse_sexpr("(- ten (two))")
    res3 = interpreter.evaluate(expr3, model)
    assert res3["success"] is True
    assert res3["result"] == 8

    # 4. Database value resolution
    model.add_fact("val", ["money", "10"])
    expr4 = canonicalizer.parse_sexpr("(+ money three)")
    res4 = interpreter.evaluate(expr4, model)
    assert res4["success"] is True
    assert res4["result"] == 13

def test_logical_inference():
    model = interpreter.WorldModel()

    # Assert facts
    model.add_fact("parent", ["John", "Mary"])
    model.add_fact("parent", ["Mary", "Bob"])

    # Assert rule: grandparent(?x, ?z) <= parent(?x, ?y) & parent(?y, ?z)
    # E.g. (=> (and (parent ?x ?y) (parent ?y ?z)) (grandparent ?x ?z))
    rule_expr = canonicalizer.parse_sexpr("(assert (=> (and (parent ?x ?y) (parent ?y ?z)) (grandparent ?x ?z)))")
    res_rule = interpreter.evaluate(rule_expr, model)
    assert res_rule["success"] is True

    # Query: is John grandparent of Bob?
    query1 = canonicalizer.parse_sexpr("(grandparent John Bob)")
    res1 = interpreter.evaluate(query1, model)
    assert res1["success"] is True
    assert res1["result"] is True

    # Query with variable: who is John grandparent of?
    query2 = canonicalizer.parse_sexpr("(grandparent John ?who)")
    res2 = interpreter.evaluate(query2, model)
    assert res2["success"] is True
    assert len(res2["bindings"]) == 1
    assert res2["bindings"][0]["?who"].lower() == "bob"

def test_inference_loop_protection():
    model = interpreter.WorldModel()

    # Cyclic rules: ancestor(?x, ?y) => ancestor(?y, ?x)
    rule_expr = canonicalizer.parse_sexpr("(assert (=> (ancestor ?x ?y) (ancestor ?y ?x)))")
    interpreter.evaluate(rule_expr, model)

    # Query: this should terminate instantly via loop detection and return False
    query = canonicalizer.parse_sexpr("(ancestor A B)")
    res = interpreter.evaluate(query, model)
    assert res["success"] is False
    assert res["result"] is False

def test_xai_explanation():
    model = interpreter.WorldModel()

    model.add_fact("parent", ["John", "Mary"])
    model.add_fact("parent", ["Mary", "Bob"])
    rule_expr = canonicalizer.parse_sexpr("(assert (=> (and (parent ?x ?y) (parent ?y ?z)) (grandparent ?x ?z)))")
    interpreter.evaluate(rule_expr, model)

    query = canonicalizer.parse_sexpr("(grandparent John Bob)")
    res = interpreter.evaluate(query, model)
    assert res["success"] is True
    assert "explanation" in res
    
    # Check that it generated a natural explanation trace
    explanation = res["explanation"].lower()
    assert "john" in explanation
    assert "mary" in explanation
    assert "bob" in explanation
    assert "because" in explanation
