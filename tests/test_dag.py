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
from englisp import canonicalizer
from englisp import minimizer

def test_dag_parsing():
    # 1. Parse S-expression with DAG backreferences
    s = "(and (chase #1=(dog the) cat) (bite #1# mouse))"
    expr = canonicalizer.parse_sexpr(s)
    
    # Check that they represent the correct structure
    assert expr == ["and", ["chase", ["dog", "the"], "cat"], ["bite", ["dog", "the"], "mouse"]]
    
    # Check that the two occurrences of ["dog", "the"] are the exact same list instance in memory
    assert expr[1][1] is expr[2][1]

def test_dag_serialization():
    # 2. Serialize S-expression with shared list objects
    dog_np = ["dog", "the"]
    expr = ["and", ["chase", dog_np, "cat"], ["bite", dog_np, "mouse"]]
    
    s = canonicalizer.sexpr_to_string(expr)
    assert s == "(and (chase #1=(dog the) cat) (bite #1# mouse))"

def test_hash_cons_integration():
    # 3. Verify hash_cons recursively maps equal nested lists to identical objects
    expr = ["and", ["chase", ["dog", "the"], "cat"], ["bite", ["dog", "the"], "mouse"]]
    consed = minimizer.hash_cons(expr)
    
    # The structure should remain identical
    assert consed == ["and", ["chase", ["dog", "the"], "cat"], ["bite", ["dog", "the"], "mouse"]]
    
    # But now, the duplicates should be memory-shared
    assert consed[1][1] is consed[2][1]
    
    # And serialize with backreferences
    s = canonicalizer.sexpr_to_string(consed)
    assert s == "(and (chase #1=(dog the) cat) (bite #1# mouse))"

def test_dag_roundtrip():
    # 4. End-to-end roundtrip of DAG structure
    original_str = "(and (chase #1=(dog the) cat) (bite #1# mouse))"
    expr = canonicalizer.parse_sexpr(original_str)
    serialized = canonicalizer.sexpr_to_string(expr)
    
    assert serialized == original_str
