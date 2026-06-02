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
from englisp import canonicalizer
from englisp.compiler import compile_sexpr, compile_program, collect_custom_predicates

def test_collect_custom_predicates():
    sexpr = canonicalizer.parse_sexpr("(if (chased (dog the) (cat the)) (jumps (cat the)))")
    preds = collect_custom_predicates(sexpr)
    assert preds == {"chased", "jumps"}

    # Composed predicate
    sexpr2 = canonicalizer.parse_sexpr("((and barked runs) (dog the))")
    preds2 = collect_custom_predicates(sexpr2)
    assert preds2 == {"barked", "runs"}

def test_compile_sexpr_basic():
    sexpr = canonicalizer.parse_sexpr("(chased (dog the) (cat the))")
    cl_code = compile_sexpr(sexpr, target="common-lisp", is_assertion=False)
    assert cl_code == '(chased "dog" "cat")'
    
    cl_assert = compile_sexpr(sexpr, target="common-lisp", is_assertion=True)
    assert cl_assert == '(add-fact "chased" "dog" "cat")'

    scheme_code = compile_sexpr(sexpr, target="scheme", is_assertion=False)
    assert scheme_code == '(chased "dog" "cat")'
    
    scheme_assert = compile_sexpr(sexpr, target="scheme", is_assertion=True)
    assert scheme_assert == '(add-fact! "chased" "dog" "cat")'

def test_compile_builtins():
    # Conditional
    sexpr = canonicalizer.parse_sexpr("(if (chased (dog the) (cat the)) (jumps (cat the)))")
    cl_code = compile_sexpr(sexpr, target="common-lisp")
    assert cl_code == '(if (chased "dog" "cat") (add-fact "jumps" "cat"))'

    # Let binding
    sexpr_let = canonicalizer.parse_sexpr("(let ((d (dog the))) (and (chased d (cat the)) (barked d)))")
    cl_let = compile_sexpr(sexpr_let, target="common-lisp")
    assert cl_let == '(let ((d "dog")) (and (chased d "cat") (barked d)))'

    # Quantifier
    sexpr_quant = canonicalizer.parse_sexpr("(for-all dog (jumps _))")
    cl_quant = compile_sexpr(sexpr_quant, target="common-lisp")
    assert cl_quant == '(for-all "dog" (lambda (_) (jumps _)))'

    # Action / State mutation
    sexpr_gives = canonicalizer.parse_sexpr("(gives (dog the) (cat the) (book the))")
    cl_gives = compile_sexpr(sexpr_gives, target="common-lisp")
    assert cl_gives == '(transfer-ownership "dog" "cat" "book")'

    # Increases action
    sexpr_inc = canonicalizer.parse_sexpr("(increases (money the) (by two))")
    cl_inc = compile_sexpr(sexpr_inc, target="common-lisp")
    assert cl_inc == '(increase-value "money" "two")'

def test_compile_program():
    sentences = [
        "(assert (chased (dog the) (cat the)))",
        "(if (chased (dog the) (cat the)) (jumps (cat the)))",
        "(for-all dog (jumps _))"
    ]
    cl_prog = compile_program(sentences, target="common-lisp")
    
    # Verify boilerplate components exist
    assert "add-fact" in cl_prog
    assert "find-instances" in cl_prog
    assert "run-statement" in cl_prog
    
    # Verify custom predicate definitions
    assert "(defun chased (&rest args)" in cl_prog
    assert "(defun jumps (&rest args)" in cl_prog
    
    # Verify compiled statements wrapped in run-statement
    assert '(run-statement (add-fact "chased" "dog" "cat")' in cl_prog
    assert '(run-statement (if (chased "dog" "cat") (add-fact "jumps" "cat"))' in cl_prog
    assert '(run-statement (for-all "dog" (lambda (_) (jumps _)))' in cl_prog

    # Scheme target test
    scheme_prog = compile_program(sentences, target="scheme")
    assert "add-fact!" in scheme_prog
    assert "(define (chased . args)" in scheme_prog
    assert "(define-syntax run-statement" in scheme_prog
    assert '(run-statement (add-fact! "chased" "dog" "cat")' in scheme_prog
