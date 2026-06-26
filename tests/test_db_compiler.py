# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# Unit tests verifying S-expression compilation to SQL, Neo4j Cypher, and MongoDB queries.

import pytest
from englisp.compiler import compile_program, compile_sql_expr, compile_cypher_expr, compile_mongodb_expr
from englisp.canonicalizer import parse_sexpr

def test_sql_compilation():
    # 1. Test SQL Assertion
    expr_assert = parse_sexpr("(assert (chased fido cat))")
    sql_assert = compile_sql_expr(expr_assert)
    assert "INSERT INTO chased (subject, object) VALUES ('fido', 'cat');" in sql_assert

    expr_assert_unary = parse_sexpr("(assert (lazy dog))")
    sql_assert_unary = compile_sql_expr(expr_assert_unary)
    assert "INSERT INTO lazy (subject) VALUES ('dog');" in sql_assert_unary

    # 2. Test SQL Query
    expr_query = parse_sexpr("(chased ?x cat)")
    sql_query = compile_sql_expr(expr_query)
    assert "SELECT subject AS x FROM chased WHERE object = 'cat';" in sql_query

    # 3. Test SQL Conjunction Query
    expr_conj = parse_sexpr("(and (chased ?x ?y) (lazy ?x))")
    sql_conj = compile_sql_expr(expr_conj)
    assert "SELECT t0.subject AS x, t0.object AS y FROM chased t0, lazy t1 WHERE t1.subject = t0.subject;" in sql_conj


def test_cypher_compilation():
    # 1. Test Cypher Assertion
    expr_assert = parse_sexpr("(assert (chased fido cat))")
    cypher_assert = compile_cypher_expr(expr_assert)
    assert "MERGE (n0:Entity {id: 'fido'}) MERGE (n1:Entity {id: 'cat'}) CREATE (n0)-[:CHASED]->(n1);" in cypher_assert

    expr_assert_unary = parse_sexpr("(assert (lazy dog))")
    cypher_assert_unary = compile_cypher_expr(expr_assert_unary)
    assert "MERGE (n0:Entity {id: 'dog'}) SET n0.lazy = true;" in cypher_assert_unary

    # 2. Test Cypher Query
    expr_query = parse_sexpr("(chased ?x cat)")
    cypher_query = compile_cypher_expr(expr_query)
    assert "MATCH (x)-[:CHASED]->(n1:Entity {id: 'cat'}) RETURN x.id AS x;" in cypher_query

    # 3. Test Cypher Conjunction Query
    expr_conj = parse_sexpr("(and (chased ?x ?y) (lazy ?x))")
    cypher_conj = compile_cypher_expr(expr_conj)
    assert "MATCH (x)-[:CHASED]->(y), (x:Entity) WHERE x.lazy = true RETURN x.id AS x, y.id AS y;" in cypher_conj


def test_mongodb_compilation():
    # 1. Test MongoDB Assertion
    expr_assert = parse_sexpr("(assert (chased fido cat))")
    mongo_assert = compile_mongodb_expr(expr_assert)
    assert 'db.chased.insertOne({"subject": "fido", "object": "cat"});' in mongo_assert

    expr_assert_unary = parse_sexpr("(assert (lazy dog))")
    mongo_assert_unary = compile_mongodb_expr(expr_assert_unary)
    assert 'db.lazy.insertOne({"subject": "dog"});' in mongo_assert_unary

    # 2. Test MongoDB Query
    expr_query = parse_sexpr("(chased ?x cat)")
    mongo_query = compile_mongodb_expr(expr_query)
    assert 'db.chased.find({"object": "cat"}, {"_id": 0, "x": "$subject"});' in mongo_query

    # 3. Test MongoDB Conjunction Query (Lookup Aggregation)
    expr_conj = parse_sexpr("(and (chased ?x ?y) (lazy ?x))")
    mongo_conj = compile_mongodb_expr(expr_conj)
    assert 'db.chased.aggregate([' in mongo_conj
    assert '$lookup' in mongo_conj
    assert '"from": "lazy"' in mongo_conj


def test_compiler_program_dispatch():
    # Test program-level compilation dispatch
    prog = ["(assert (lazy dog))", "(chased ?x cat)"]
    
    sql_prog = compile_program(prog, "sql")
    assert "INSERT INTO lazy (subject)" in sql_prog
    assert "SELECT subject AS x" in sql_prog

    cypher_prog = compile_program(prog, "cypher")
    assert "MERGE (n0:Entity {id: 'dog'})" in cypher_prog
    assert "MATCH (x)-[:CHASED]->" in cypher_prog

    mongo_prog = compile_program(prog, "mongodb")
    assert 'db.lazy.insertOne' in mongo_prog
    assert 'db.chased.find' in mongo_prog
