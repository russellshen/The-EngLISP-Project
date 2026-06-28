# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license.

from typing import Any, List
from englisp.canonicalizer import SExpr
from englisp.interpreter import simplify_argument, substitute

def compile_to_sql(expr: SExpr) -> str:
    """
    Compiles an EngLISP S-expression into a standard SQL statement.
    Supports:
      - Let bindings: substitutes variables and compiles body.
      - Rule definitions (=> cond cons): returns descriptive SQL comment.
      - Calculations (+ - * /): compiles to SELECT math.
      - Fact assertions (assert/tell (pred args...)): compiles to INSERT statement.
      - Queries (pred args...): compiles to SELECT query with where clauses.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return "-- Empty or invalid expression"

    op = expr[0]

    # Handle Let Bindings
    if op == "let":
        if len(expr) < 3:
            return "-- Invalid let expression"
        bindings = expr[1]
        body = expr[2]
        var_map = {var: val for var, val in bindings}
        substituted_body = substitute(body, var_map)
        return compile_to_sql(substituted_body)

    # Handle Rules
    if op == "=>":
        return f"-- Rule Assertion: IF {expr[1]} THEN {expr[2]}"

    # Handle Calculations
    if op in ("+", "-", "*", "/"):
        def format_math(e: Any) -> str:
            if isinstance(e, list) and len(e) > 0 and e[0] in ("+", "-", "*", "/"):
                sub_op = e[0]
                terms = [format_math(x) for x in e[1:]]
                return f"({f' {sub_op} '.join(terms)})"
            return str(e)
        return f"SELECT {format_math(expr)} AS calculation_result;"

    # Handle Explicit Assertions
    if op in ("assert", "tell"):
        if len(expr) < 2:
            return "-- Empty assertion"
        inner = expr[1]
        if isinstance(inner, list) and len(inner) > 0 and inner[0] == "=>":
            return compile_to_sql(inner)
        
        if not isinstance(inner, list) or len(inner) == 0:
            return "-- Invalid assertion target"
        
        pred = inner[0]
        args = [simplify_argument(x) for x in inner[1:]]
        
        cols = ["predicate"] + [f"arg{i+1}" for i in range(len(args))]
        vals = [f"'{pred}'"] + [f"'{a}'" for a in args]
        return f"INSERT INTO facts ({', '.join(cols)}) VALUES ({', '.join(vals)});"

    # Handle Queries & implicit assertions
    has_vars = False
    for item in expr:
        if isinstance(item, str) and item.startswith("?"):
            has_vars = True
            break
        elif isinstance(item, list):
            for sub in item:
                if isinstance(sub, str) and sub.startswith("?"):
                    has_vars = True

    pred = op
    args = [simplify_argument(x) if not (isinstance(x, str) and x.startswith("?")) else x for x in expr[1:]]

    if has_vars:
        selects = []
        wheres = [f"predicate = '{pred}'"]
        for i, arg in enumerate(args):
            if arg.startswith("?"):
                var_name = arg[1:]
                selects.append(f"arg{i+1} AS {var_name}")
            else:
                wheres.append(f"arg{i+1} = '{arg}'")
        
        select_clause = ", ".join(selects) if selects else "*"
        return f"SELECT {select_clause} FROM facts WHERE {' AND '.join(wheres)};"
    else:
        cols = ["predicate"] + [f"arg{i+1}" for i in range(len(args))]
        vals = [f"'{pred}'"] + [f"'{a}'" for a in args]
        return f"INSERT INTO facts ({', '.join(cols)}) VALUES ({', '.join(vals)});"


def compile_to_cypher(expr: SExpr) -> str:
    """
    Compiles an EngLISP S-expression into a Neo4j Cypher statement.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return "// Empty or invalid expression"

    op = expr[0]

    # Handle Let Bindings
    if op == "let":
        if len(expr) < 3:
            return "// Invalid let expression"
        bindings = expr[1]
        body = expr[2]
        var_map = {var: val for var, val in bindings}
        substituted_body = substitute(body, var_map)
        return compile_to_cypher(substituted_body)

    # Handle Rules
    if op == "=>":
        return f"// Rule: IF {expr[1]} THEN {expr[2]}"

    # Handle Calculations
    if op in ("+", "-", "*", "/"):
        def format_math(e: Any) -> str:
            if isinstance(e, list) and len(e) > 0 and e[0] in ("+", "-", "*", "/"):
                sub_op = e[0]
                terms = [format_math(x) for x in e[1:]]
                return f"({f' {sub_op} '.join(terms)})"
            return str(e)
        return f"RETURN {format_math(expr)} AS calculation_result"

    # Handle Explicit Assertions
    if op in ("assert", "tell"):
        if len(expr) < 2:
            return "// Empty assertion"
        inner = expr[1]
        if isinstance(inner, list) and len(inner) > 0 and inner[0] == "=>":
            return compile_to_cypher(inner)
        if not isinstance(inner, list) or len(inner) == 0:
            return "// Invalid assertion target"
        
        pred = inner[0]
        args = [simplify_argument(x) for x in inner[1:]]
        
        if len(args) == 1:
            return f"MERGE (a:Entity {{name: '{args[0]}'}})-[:IS_A]->(t:Type {{name: '{pred}'}});"
        elif len(args) >= 2:
            return f"MERGE (a:Entity {{name: '{args[0]}'}}) MERGE (b:Entity {{name: '{args[1]}'}}) CREATE (a)-[:{pred}]->(b);"
        return f"CREATE (:Relation {{predicate: '{pred}'}});"

    # Handle Queries & implicit assertions
    has_vars = False
    for item in expr:
        if isinstance(item, str) and item.startswith("?"):
            has_vars = True
            break

    pred = op
    args = [simplify_argument(x) if not (isinstance(x, str) and x.startswith("?")) else x for x in expr[1:]]

    if has_vars:
        if len(args) == 1:
            if args[0].startswith("?"):
                var_name = args[0][1:]
                return f"MATCH (varname:Entity)-[:IS_A]->(t:Type {{name: '{pred}'}}) RETURN varname.name AS {var_name};"
            else:
                return f"MATCH (a:Entity {{name: '{args[0]}'}})-[:IS_A]->(t:Type {{name: '{pred}'}}) RETURN a.name;"
        elif len(args) >= 2:
            sub = args[0]
            obj = args[1]
            if sub.startswith("?") and obj.startswith("?"):
                s_var = sub[1:]
                o_var = obj[1:]
                return f"MATCH ({s_var}:Entity)-[:{pred}]->({o_var}:Entity) RETURN {s_var}.name AS {s_var}, {o_var}.name AS {o_var};"
            elif sub.startswith("?"):
                s_var = sub[1:]
                return f"MATCH ({s_var}:Entity)-[:{pred}]->(o:Entity {{name: '{obj}'}}) RETURN {s_var}.name AS {s_var};"
            elif obj.startswith("?"):
                o_var = obj[1:]
                return f"MATCH (s:Entity {{name: '{sub}'}})-[:{pred}]->({o_var}:Entity) RETURN {o_var}.name AS {o_var};"
            else:
                return f"MATCH (s:Entity {{name: '{sub}'}})-[:{pred}]->(o:Entity {{name: '{obj}'}}) RETURN true;"
        return f"MATCH (r:Relation {{predicate: '{pred}'}}) RETURN r;"
    else:
        if len(args) == 1:
            return f"MERGE (a:Entity {{name: '{args[0]}'}})-[:IS_A]->(t:Type {{name: '{pred}'}});"
        elif len(args) >= 2:
            return f"MERGE (a:Entity {{name: '{args[0]}'}}) MERGE (b:Entity {{name: '{args[1]}'}}) CREATE (a)-[:{pred}]->(b);"
        return f"CREATE (:Relation {{predicate: '{pred}'}});"
