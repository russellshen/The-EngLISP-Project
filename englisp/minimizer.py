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

from typing import List, Dict, Any
from englisp.canonicalizer import SExpr
from englisp.parser import LEXICON, tag_tokens
from englisp.ontology import CONCEPTUAL_PRIMES, INVERSE_CONCEPTUAL_PRIMES, to_tuple

# Semantic contraction maps: (Noun, Adj) -> contracted Noun
SEMANTIC_CONTRACTIONS = {
    ("dog", "young"): "puppy",
    ("cat", "young"): "kitten",
    ("town", "large"): "city",
    ("man", "young"): "boy",
    ("woman", "young"): "girl",
    ("house", "small"): "cabin",
}

# Inverse map: contracted Noun -> (Noun, Adj)
SEMANTIC_EXPANSIONS = {v: k for k, v in SEMANTIC_CONTRACTIONS.items()}

# Adjective rewrites: (not + adjective) -> opposite adjective
ADJECTIVE_CONTRACTIONS = {
    "happy": "sad",
    "clean": "dirty",
    "fast": "slow",
    "good": "bad",
    "large": "small",
}

ADJECTIVE_EXPANSIONS = {v: k for k, v in ADJECTIVE_CONTRACTIONS.items()}


def get_pos(word: str) -> str:
    """Helper to check the part of speech of a word."""
    tags = tag_tokens([word])
    return tags[0][1] if tags else "N"


def collect_nps(expr, np_counts):
    if isinstance(expr, list) and len(expr) > 0:
        op = expr[0]
        if isinstance(op, str) and get_pos(op) == "N" and len(expr) > 1:
            from englisp.canonicalizer import sexpr_to_string
            key = sexpr_to_string(expr)
            np_counts[key] = np_counts.get(key, 0) + 1
        for x in expr:
            collect_nps(x, np_counts)

def hash_cons(expr: SExpr, memo: dict = None) -> SExpr:
    """
    Recursively canonicalizes list structures inside the S-expression,
    ensuring that equal sub-lists point to the exact same list instance in memory.
    """
    if memo is None:
        memo = {}
    if isinstance(expr, list):
        consed_children = [hash_cons(x, memo) for x in expr]
        key = tuple(id(x) if isinstance(x, list) else x for x in consed_children)
        if key not in memo:
            memo[key] = consed_children
        return memo[key]
    return expr

def minimize_sexpr(expr: SExpr) -> SExpr:
    """
    Minimizes an EngLISP S-expression:
      - Applies core rewrites recursively.
      - Applies Entity Scope Bindings (let expressions) for duplicate noun phrases.
      - Applies DAG Hash-Consing.
    """
    min_expr = _minimize_sexpr_recursive(expr)
    
    np_counts = {}
    collect_nps(min_expr, np_counts)
    
    repeated_nps = {k: v for k, v in np_counts.items() if v > 1}
    if not repeated_nps:
        return hash_cons(min_expr)
        
    # Build bindings
    bindings = []
    var_map = {}
    sorted_keys = sorted(repeated_nps.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        from englisp.canonicalizer import parse_sexpr
        np_list = parse_sexpr(key)
        noun_head = np_list[0]
        var_base = noun_head[0].lower() if noun_head else "x"
        var_name = var_base
        counter = 1
        while var_name in var_map.values() or var_name in ("and", "or", "not", "let"):
            var_name = f"{var_base}{counter}"
            counter += 1
            
        var_map[key] = var_name
        bindings.append([var_name, np_list])
        
    def replace_nps(e):
        if isinstance(e, list):
            from englisp.canonicalizer import sexpr_to_string
            key = sexpr_to_string(e)
            if key in var_map:
                return var_map[key]
            return [replace_nps(x) for x in e]
        return e
        
    bound_body = replace_nps(min_expr)
    return hash_cons(["let", bindings, bound_body])

def _minimize_sexpr_recursive(expr: SExpr) -> SExpr:
    if isinstance(expr, str):
        if expr in CONCEPTUAL_PRIMES:
            return CONCEPTUAL_PRIMES[expr]
        return expr

    if not isinstance(expr, list) or len(expr) == 0:
        return expr

    if expr[0] == "frag":
        if len(expr) < 2:
            return expr
        return ["frag", _minimize_sexpr_recursive(expr[1])]

    # Pre-check: Double negation elimination before children minimization
    if len(expr) == 2 and expr[0] == "not":
        arg = expr[1]
        if isinstance(arg, list) and len(arg) == 2 and arg[0] == "not":
            return _minimize_sexpr_recursive(arg[1])

    # 1. Recursively minimize children first
    min_children = [_minimize_sexpr_recursive(x) for x in expr]
    op = min_children[0]

    # Rule: Predicate Composition: (and (barked dog) (runs dog)) -> ((and barked runs) dog)
    if isinstance(op, str) and op in ("and", "or") and len(min_children) >= 3:
        shared_arg = None
        all_unary_relations = True
        for child in min_children[1:]:
            if isinstance(child, list) and len(child) == 2:
                child_op = child[0]
                if isinstance(child_op, str) and child_op not in ("and", "or", "not", "let"):
                    if shared_arg is None:
                        shared_arg = child[1]
                    elif shared_arg != child[1]:
                        all_unary_relations = False
                        break
                else:
                    all_unary_relations = False
                    break
            else:
                all_unary_relations = False
                break
                
        if all_unary_relations and shared_arg is not None:
            composed_op = [op] + [child[0] for child in min_children[1:]]
            return [composed_op, shared_arg]

    # 2. Check if operator is a string (operator)
    if not isinstance(op, str):
        return min_children

    op_pos = get_pos(op)

    # Rule: Adjective negation: (not happy) -> sad
    if op == "not" and len(min_children) == 2:
        arg = min_children[1]
        if isinstance(arg, str) and arg in ADJECTIVE_CONTRACTIONS:
            return ADJECTIVE_CONTRACTIONS[arg]

    # Rule: Active voice normalization (robust with adjuncts)
    if op_pos == "V":
        passive_agent_idx = -1
        for idx, arg in enumerate(min_children[1:], start=1):
            if isinstance(arg, list) and len(arg) == 2 and arg[0] == "by":
                passive_agent_idx = idx
                break
        
        if passive_agent_idx != -1:
            agent = min_children[passive_agent_idx][1]
            patient = min_children[1]
            other_args = [arg for idx, arg in enumerate(min_children[2:], start=2) if idx != passive_agent_idx]
            min_children = [op, agent, patient] + other_args

    # Rule: Noun phrase modifiers minimization & canonical sorting of modifiers
    if op_pos == "N":
        noun = op
        adjs = []
        pps = []
        
        for arg in min_children[1:]:
            if isinstance(arg, str):
                arg_pos = get_pos(arg)
                if arg_pos == "Det":
                    pass # Pruned by default in MinimaLIST
                elif arg_pos == "Adj":
                    adjs.append(arg)
                else:
                    adjs.append(arg)
            elif isinstance(arg, list) and len(arg) > 0:
                first_elem_pos = get_pos(arg[0])
                if first_elem_pos == "P":
                    pps.append(arg)
                else:
                    adjs.append(arg)
            else:
                adjs.append(arg)

        # Apply semantic contraction
        contracted_noun = noun
        remaining_adjs = []
        for adj in adjs:
            adj_str = adj[0] if isinstance(adj, list) and len(adj) > 0 else adj
            if isinstance(adj_str, str) and (noun, adj_str) in SEMANTIC_CONTRACTIONS:
                contracted_noun = SEMANTIC_CONTRACTIONS[(noun, adj_str)]
            else:
                remaining_adjs.append(adj)

        # Enforce canonical sorting for adjectives and PPs
        from englisp.canonicalizer import sexpr_to_string
        remaining_adjs.sort(key=sexpr_to_string)
        pps.sort(key=sexpr_to_string)

        if not remaining_adjs and not pps:
            return contracted_noun
        
        new_np = [contracted_noun]
        new_np.extend(remaining_adjs)
        new_np.extend(pps)
        return new_np

    # Rule: Verb Phrase argument canonicalization & sorting of adjuncts
    if op_pos == "V":
        verb = op
        core_args = []
        adjuncts = []
        
        # First argument is always the subject
        if len(min_children) > 1:
            core_args.append(min_children[1])
            
        # Second argument is the object if it is a core NP (not PP or Adv)
        if len(min_children) > 2:
            arg = min_children[2]
            is_pp = isinstance(arg, list) and len(arg) > 0 and get_pos(arg[0]) == "P"
            is_adv = isinstance(arg, str) and get_pos(arg) == "Adv"
            if not is_pp and not is_adv:
                core_args.append(arg)
                start_adjunct_idx = 3
            else:
                start_adjunct_idx = 2
        else:
            start_adjunct_idx = 2
            
        # Remaining arguments are adjuncts
        from englisp.canonicalizer import sexpr_to_string
        for arg in min_children[start_adjunct_idx:]:
            adjuncts.append(arg)
            
        # Sort adjuncts alphabetically to enforce canonical ordering
        adjuncts.sort(key=sexpr_to_string)
        
        return [verb] + core_args + adjuncts

    return min_children

def replace_vars(expr, var_map):
    if isinstance(expr, str):
        return var_map.get(expr, expr)
    elif isinstance(expr, list):
        return [replace_vars(x, var_map) for x in expr]
    return expr

def expand_sexpr(expr: SExpr, is_head: bool = False) -> SExpr:
    """
    Expands a MinimaLIST EngLISP expression back to full canonical EngLISP form:
      1. Expands let bindings recursively.
      2. Expands composed predicates recursively.
      3. Reintroduces default determiners: dog -> (dog the).
    """
    expr_tuple = to_tuple(expr)
    if expr_tuple in INVERSE_CONCEPTUAL_PRIMES:
        expr = INVERSE_CONCEPTUAL_PRIMES[expr_tuple]

    if isinstance(expr, list) and len(expr) > 0:
        op = expr[0]
        # 1. Handle let bindings expansion
        if op == "let":
            bindings = expr[1]
            body = expr[2]
            var_map = {var: val for var, val in bindings}
            substituted_body = replace_vars(body, var_map)
            return expand_sexpr(substituted_body, is_head=is_head)
            
        # 2. Handle composed predicate expansion
        if isinstance(op, list) and len(op) > 0 and op[0] in ("and", "or"):
            if len(expr) == 2:
                arg = expr[1]
                reconstructed = [op[0]]
                for pred in op[1:]:
                    reconstructed.append([pred, arg])
                return expand_sexpr(reconstructed, is_head=is_head)

        if op == "frag":
            if len(expr) < 2:
                return expr
            return ["frag", expand_sexpr(expr[1], is_head=False)]

    # 1. Base case: single string terminal (often a pruned bare noun)
    if isinstance(expr, str):
        if not is_head:
            pos = get_pos(expr)
            if pos == "N":
                if expr in SEMANTIC_EXPANSIONS:
                    base_noun, adj = SEMANTIC_EXPANSIONS[expr]
                    return [base_noun, "the", adj]
                return [expr, "the"]
        return expr

    if not isinstance(expr, list) or len(expr) == 0:
        return expr

    # 2. Recursively expand children, specifying that the first element is the head
    exp_children = [expand_sexpr(expr[0], is_head=True)] + [expand_sexpr(x, is_head=False) for x in expr[1:]]
    op = exp_children[0]

    if not isinstance(op, str):
        return exp_children

    op_pos = get_pos(op)

    # 3. If it's a noun phrase list, e.g. ['dog', 'quick'] (which was minimized from ['dog', 'the', 'quick'])
    # We should restore the determiner 'the'
    if op_pos == "N":
        noun = op
        det = "the" # Default determiner
        adjs = []
        pps = []

        has_det = False
        for arg in exp_children[1:]:
            if isinstance(arg, str):
                if get_pos(arg) == "Det":
                    det = arg
                    has_det = True
                else:
                    adjs.append(arg)
            else:
                pps.append(arg)

        # Semantic expansion: puppy -> dog + young
        if noun in SEMANTIC_EXPANSIONS:
            base_noun, young_adj = SEMANTIC_EXPANSIONS[noun]
            noun = base_noun
            adjs.append(young_adj)

        # Build expanded NP list
        new_np = [noun, det]
        new_np.extend(adjs)
        new_np.extend(pps)
        return new_np

    return exp_children
