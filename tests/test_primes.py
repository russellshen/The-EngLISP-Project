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
from englisp import minimizer
from englisp import canonicalizer

def test_prime_decomposition():
    # 1. Test verb decomposition to conceptual primes during minimization
    expr = ["kill", "dog", "cat"]
    minimized = minimizer.minimize_sexpr(expr)
    
    # "kill" should decompose into ["cause", ["become", ["not", "alive"]]]
    # "dog" and "cat" are bare nouns, so they remain as strings in the minimized form
    assert minimized == [["cause", ["become", ["not", "alive"]]], "dog", "cat"]

def test_prime_reconstruction():
    # 2. Test reconstruction of the original verb during expansion
    decomposed = [["cause", ["become", ["not", "alive"]]], "dog", "cat"]
    expanded = minimizer.expand_sexpr(decomposed)
    
    # Should reconstruct "kill" and restore the default determiners
    assert expanded == ["kill", ["dog", "the"], ["cat", "the"]]

def test_primes_roundtrip():
    # 3. Test roundtrip for multiple verbs (kill, break, stop, give)
    verbs_test = [
        (["kill", "dog", "cat"], ["kill", ["dog", "the"], ["cat", "the"]]),
        (["break", "dog", "vase"], ["break", ["dog", "the"], ["vase", "the"]]),
        (["stop", "dog", "car"], ["stop", ["dog", "the"], ["car", "the"]]),
        (["give", "dog", "cat"], ["give", ["dog", "the"], ["cat", "the"]]),
    ]
    
    for original, expected_expanded in verbs_test:
        minimized = minimizer.minimize_sexpr(original)
        expanded = minimizer.expand_sexpr(minimized)
        assert expanded == expected_expanded

def test_primes_hash_cons_sharing():
    # 4. Verify that decomposed prime structures are correctly hash-consed/shared in memory when duplicated
    expr = ["and", ["kill", ["dog", "the", "black"], "cat"], ["kill", ["dog", "the", "black"], "mouse"]]
    minimized = minimizer.minimize_sexpr(expr)
    
    # Structure should contain 'let' since the complex 'dog' is duplicated
    assert minimized[0] == "let"
    bindings = minimized[1]
    body = minimized[2]
    
    # Find the two occurrences of the decomposed 'kill' head in the body
    head1 = body[1][0]
    head2 = body[2][0]
    
    assert head1 == ["cause", ["become", ["not", "alive"]]]
    assert head2 == ["cause", ["become", ["not", "alive"]]]
    
    # Assert they are the exact same list object instance in Python memory (thanks to hash-consing)
    assert head1 is head2
    
    # Verify they serialize using Lisp backreference notation
    s = canonicalizer.sexpr_to_string(minimized)
    assert "#1=(cause (become (not alive)))" in s
    assert "#1#" in s

