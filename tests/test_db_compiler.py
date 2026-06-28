# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license.

import pytest
from englisp.db_compiler import compile_to_sql, compile_to_cypher

def test_sql_compilation():
    # 1. Fact assertion
    sql_assert = compile_to_sql(["chased", "dog", "cat"])
    assert "INSERT INTO facts" in sql_assert
    assert "'chased'" in sql_assert
    assert "'dog'" in sql_assert
    assert "'cat'" in sql_assert
    
    # 2. Logic query
    sql_query = compile_to_sql(["chased", "?who", "cat"])
    assert "SELECT arg1 AS who FROM facts" in sql_query
    assert "predicate = 'chased'" in sql_query
    assert "arg2 = 'cat'" in sql_query

    # 3. Calculation
    sql_math = compile_to_sql(["+", "5", ["*", "2", "3"]])
    assert "SELECT (5 + (2 * 3)) AS calculation_result;" in sql_math

    # 4. Rules
    sql_rule = compile_to_sql(["=>", ["chased", "?x", "?y"], ["scared", "?y"]])
    assert "-- Rule Assertion:" in sql_rule

def test_cypher_compilation():
    # 1. Binary relationship assertion
    cy_assert = compile_to_cypher(["chased", "dog", "cat"])
    assert "MERGE (a:Entity {name: 'dog'})" in cy_assert
    assert "CREATE (a)-[:chased]->(b)" in cy_assert
    
    # 2. Unary property assertion
    cy_unary = compile_to_cypher(["runs", "dog"])
    assert "MERGE (a:Entity {name: 'dog'})-[:IS_A]->(t:Type {name: 'runs'})" in cy_unary

    # 3. Query subject variable
    cy_query = compile_to_cypher(["chased", "?who", "cat"])
    assert "MATCH (who:Entity)-[:chased]->(o:Entity {name: 'cat'}) RETURN who.name AS who;" in cy_query
