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

from typing import List, Set, Tuple, Dict, Any, Union, Optional
from englisp.canonicalizer import SExpr, parse_sexpr
from englisp.parser import tag_tokens

def simplify_argument(arg: SExpr) -> str:
    """
    Simplifies a nested S-expression argument to a flat string representation.
    E.g., "dog" -> "dog"
          ["dog", "the"] -> "dog"
          ["dog", "the", "lazy"] -> "dog"
          ["dog", "the", ["that", ["chased", "_", ...]]] -> "dog"
    """
    if isinstance(arg, str):
        return arg
    elif isinstance(arg, list) and len(arg) > 0:
        # Check for tense vector: [t1, t2, aspect]
        if len(arg) == 3 and isinstance(arg[0], int) and isinstance(arg[1], int) and isinstance(arg[2], str):
            return f"tense_{arg[0]}_{arg[1]}_{arg[2]}"
        # The first element is the head noun/category
        return simplify_argument(arg[0])
    return ""

def unify(query_args: List[str], fact_args: Tuple[str, ...], binding: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Unifies query arguments containing optional logic variables (starting with '?')
    against concrete fact arguments, given a set of current variable bindings.
    Returns the updated bindings dict if unification succeeds, or None if it fails.
    """
    new_binding = binding.copy()
    for q_arg, f_arg in zip(query_args, fact_args):
        if q_arg.startswith("?"):
            # Logic variable
            if q_arg in new_binding:
                # Variable already bound, must match the fact value
                if new_binding[q_arg] != f_arg:
                    return None
            else:
                # Bind variable to the fact value
                new_binding[q_arg] = f_arg
        else:
            # Constant, must match exactly
            if q_arg != f_arg:
                return None
    return new_binding

def has_variables(expr: SExpr) -> bool:
    """Recursively checks if an S-expression contains variables starting with '?'."""
    if isinstance(expr, str):
        return expr.startswith("?")
    elif isinstance(expr, list):
        return any(has_variables(x) for x in expr)
    return False

def to_synset(word: str) -> str:
    from englisp.ontology import disambiguate_sense
    if word.startswith("?") or (word.startswith("rel_") and "_" in word) or word == "_" or word in ("IS_A", "val"):
        return word
    # Disambiguate with empty context (fallback to dictionary lookup)
    return disambiguate_sense(word, [])

def from_synset(word: str) -> str:
    from englisp.ontology import lookup_word
    if word.startswith("?") or (word.startswith("rel_") and "_" in word) or word == "_" or word in ("IS_A", "val"):
        return word
    return lookup_word(word, "en")

class WorldModel:
    """
    A stateful Knowledge Base representing the relational state of the world.
    Under the hood, uses SemanticGraphDB for storing facts as a semantic graph,
    supporting recursive IS_A type inheritance traversals.
    """
    def __init__(self):
        from englisp.graph_db import SemanticGraphDB
        self.db = SemanticGraphDB()
        self.rules: List[Tuple[Any, Any]] = []
        self.proof_steps: List[Dict[str, Any]] = []

    def add_fact(self, predicate: str, args: List[str]):
        """Adds a normalized relation/property fact to the knowledge base."""
        pred_syn = to_synset(predicate)
        args_syn = [to_synset(a) for a in args]
        self.db.add_fact(pred_syn, args_syn)

    def remove_fact(self, predicate: str, args: List[str]):
        """Removes a fact from the knowledge base."""
        pred_syn = to_synset(predicate)
        args_syn = [to_synset(a) for a in args]
        self.db.remove_fact(pred_syn, args_syn)

    def add_rule(self, condition: Any, consequence: Any):
        """Adds a logical inference rule to the knowledge base."""
        rule = (condition, consequence)
        if rule not in self.rules:
            self.rules.append(rule)

    def remove_rule(self, condition: Any, consequence: Any):
        """Removes a logical inference rule from the knowledge base."""
        rule = (condition, consequence)
        if rule in self.rules:
            self.rules.remove(rule)

    def clear(self):
        """Resets the knowledge base."""
        self.db.clear()
        self.rules.clear()
        self.proof_steps.clear()

    def get_all_facts(self) -> List[Tuple[str, ...]]:
        """Returns a sorted list of all facts currently in the knowledge base."""
        raw_facts = self.db.get_all_facts()
        mapped_facts = []
        for fact in raw_facts:
            mapped_pred = from_synset(fact[0])
            mapped_args = [from_synset(a) for a in fact[1:]]
            mapped_facts.append((mapped_pred, *mapped_args))
        return sorted(mapped_facts)

    @property
    def facts(self) -> List[Tuple[str, ...]]:
        """A property to maintain backward compatibility with direct facts attribute accesses."""
        return self.get_all_facts()

def substitute(expr: SExpr, var_map: Dict[str, SExpr]) -> SExpr:
    """Substitutes variables bound in a let-expression inside the body recursively."""
    if isinstance(expr, str):
        return var_map.get(expr, expr)
    elif isinstance(expr, list):
        return [substitute(x, var_map) for x in expr]
    return expr

def resolve_term(t: Any, bindings: Dict[str, str]) -> Any:
    while isinstance(t, str) and t.startswith("?") and t in bindings:
        t = bindings[t]
    return t

def unify_terms(t1: Any, t2: Any, bindings: Dict[str, str]) -> Optional[Dict[str, str]]:
    t1 = resolve_term(t1, bindings)
    t2 = resolve_term(t2, bindings)
    if t1 == t2:
        return bindings
    if isinstance(t1, str) and t1.startswith("?"):
        new_b = bindings.copy()
        new_b[t1] = t2
        return new_b
    if isinstance(t2, str) and t2.startswith("?"):
        new_b = bindings.copy()
        new_b[t2] = t1
        return new_b
    return None

def unify_lists(args1: List[str], args2: List[str], bindings: Dict[str, str]) -> Optional[Dict[str, str]]:
    if len(args1) != len(args2):
        return None
    curr = bindings.copy()
    for a1, a2 in zip(args1, args2):
        res = unify_terms(a1, a2, curr)
        if res is None:
            return None
        curr = res
    return curr

def evaluate_math(expr: Any, model: WorldModel, bindings: Dict[str, str] = None) -> float:
    if bindings is None:
        bindings = {}
    if isinstance(expr, str):
        while expr.startswith("?") and expr in bindings:
            expr = bindings[expr]
        if expr.isdigit():
            return int(expr)
        try:
            return float(expr)
        except ValueError:
            pass
        word_to_num = {
            "one": 1, "un": 1, "two": 2, "deux": 2, "three": 3, "trois": 3,
            "four": 4, "quatre": 4, "five": 5, "cinq": 5, "six": 6, "seven": 7,
            "eight": 8, "nine": 9, "ten": 10, "zero": 0
        }
        if expr.lower() in word_to_num:
            return word_to_num[expr.lower()]
        for fact in model.get_all_facts():
            if fact[0] == "val" and len(fact) == 3 and fact[1] == expr:
                try:
                    return float(fact[2]) if "." in fact[2] else int(fact[2])
                except ValueError:
                    pass
        return 0
    elif isinstance(expr, (int, float)):
        return expr
    elif isinstance(expr, list) and len(expr) > 0:
        op = expr[0]
        if op in ("+", "-", "*", "/"):
            vals = [evaluate_math(arg, model, bindings) for arg in expr[1:]]
            if not vals:
                return 0
            import operator
            op_func = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}[op]
            import functools
            try:
                return functools.reduce(op_func, vals)
            except ZeroDivisionError:
                return float('inf')
        elif len(expr) == 1:
            return evaluate_math(expr[0], model, bindings)
    return 0

def find_instances(type_name: str, model: WorldModel) -> Set[str]:
    """Finds all instances of a type in the WorldModel (explicitly or implicitly via IS_A)."""
    type_syn = to_synset(type_name)
    instances = set()
    import re
    for node_id in model.db.nodes:
        if re.match(r"^[nv]\d+", node_id):
            continue
        if type_syn in model.db.traverse_is_a(node_id):
            instances.add(from_synset(node_id))
    return instances


def evaluate_query_with_bindings(
    expr: SExpr,
    model: WorldModel,
    bindings_list: List[Dict[str, str]],
    visited: Optional[List[Tuple[str, Tuple[str, ...]]]] = None
) -> List[Dict[str, str]]:
    """
    Recursively evaluates a query expression against the WorldModel facts and logical rules,
    carrying forward and filtering a list of current variable bindings.
    Supports backward-chaining logical inference with loop detection.
    """
    if visited is None:
        visited = []

    if not isinstance(expr, list) or len(expr) == 0:
        return []

    op = expr[0]
    
    # Handle composed predicate query evaluation: e.g. ((and barked runs) dog)
    if isinstance(op, list) and len(op) > 0 and op[0] in ("and", "or"):
        if len(expr) == 2:
            arg = expr[1]
            reconstructed = [op[0]]
            for pred in op[1:]:
                reconstructed.append([pred, arg])
            return evaluate_query_with_bindings(reconstructed, model, bindings_list, visited)
        return []

    if not isinstance(op, str):
        return []

    if op == "let":
        bindings = expr[1]
        body = expr[2]
        var_map = {var: val for var, val in bindings}
        substituted_body = substitute(body, var_map)
        return evaluate_query_with_bindings(substituted_body, model, bindings_list, visited)

    elif op == "and":
        current_bindings = bindings_list
        for conjunct in expr[1:]:
            current_bindings = evaluate_query_with_bindings(conjunct, model, current_bindings, visited)
            if not current_bindings:
                return []
        return current_bindings

    elif op == "or":
        results = []
        for disjunct in expr[1:]:
            res = evaluate_query_with_bindings(disjunct, model, bindings_list, visited)
            for b in res:
                if b not in results:
                    results.append(b)
        return results

    elif op == "not":
        results = []
        for b in bindings_list:
            sub_res = evaluate_query_with_bindings(expr[1], model, [b], visited)
            if not sub_res:
                results.append(b)
        return results

    elif op == "for-all":
        if len(expr) < 3:
            return []
        type_name = expr[1]
        body = expr[2]
        instances = find_instances(type_name, model)
        if not instances:
            return []
        results = []
        for b in bindings_list:
            all_hold = True
            for inst in instances:
                sub_body = substitute(body, {"_": inst})
                res = evaluate_query_with_bindings(sub_body, model, [b], visited)
                if not res:
                    all_hold = False
                    break
            if all_hold:
                results.append(b)
        return results

    elif op == "exists":
        if len(expr) < 3:
            return []
        type_name = expr[1]
        body = expr[2]
        instances = find_instances(type_name, model)
        if not instances:
            return []
        results = []
        for b in bindings_list:
            any_hold = False
            for inst in instances:
                sub_body = substitute(body, {"_": inst})
                res = evaluate_query_with_bindings(sub_body, model, [b], visited)
                if res:
                    any_hold = True
                    break
            if any_hold:
                results.append(b)
        return results

    else:
        query_pred = op
        query_args = [simplify_argument(x) for x in expr[1:]]

        query_pred_syn = to_synset(query_pred)
        query_args_syn = [to_synset(a) for a in query_args]

        results = []
        
        # 1. Backward-chaining logic variable query
        for b in bindings_list:
            b_syn = {k: to_synset(v) for k, v in b.items()}
            
            # Resolve current bound arguments in synset space to check for visited loop detection
            resolved_args_syn = tuple(b_syn.get(a, a) for a in query_args_syn)
            goal = (query_pred_syn, resolved_args_syn)
            if goal in visited:
                continue  # recursion loop detected
                
            local_results = []
            
            # (A) Query direct database facts
            import itertools
            unbound_vars = [arg for arg in query_args_syn if arg.startswith("?") and arg not in b_syn]
            if not unbound_vars:
                ground_args_syn = [b_syn.get(arg, arg) for arg in query_args_syn]
                if model.db.query(query_pred_syn, ground_args_syn):
                    local_results.append(b)
                    fact_key = (from_synset(query_pred_syn), *(from_synset(a) for a in ground_args_syn))
                    fact_log = {"type": "fact", "fact": fact_key}
                    if fact_log not in model.proof_steps:
                        model.proof_steps.append(fact_log)
            else:
                db = model.db
                candidates = []
                
                if query_pred_syn.upper() == "IS_A" and len(query_args_syn) == 2:
                    arg0_pattern = b_syn.get(query_args_syn[0], query_args_syn[0])
                    arg1_pattern = b_syn.get(query_args_syn[1], query_args_syn[1])
                    
                    if not arg0_pattern.startswith("?") and arg1_pattern.startswith("?"):
                        for anc in db.traverse_is_a(arg0_pattern):
                            candidates.append((arg0_pattern, anc))
                    elif arg0_pattern.startswith("?") and not arg1_pattern.startswith("?"):
                        descendants = set()
                        queue = [arg1_pattern]
                        while queue:
                            curr = queue.pop(0)
                            if curr not in descendants:
                                descendants.add(curr)
                                if curr in db.in_edges:
                                    for src, rel in db.in_edges[curr]:
                                        if rel.upper() == "IS_A":
                                            queue.append(src)
                        for desc in descendants:
                            candidates.append((desc, arg1_pattern))
                    elif arg0_pattern.startswith("?") and arg1_pattern.startswith("?"):
                        for node in db.nodes:
                            for anc in db.traverse_is_a(node):
                                candidates.append((node, anc))
                                
                elif len(query_args_syn) == 1:
                    arg0_pattern = b_syn.get(query_args_syn[0], query_args_syn[0])
                    if arg0_pattern.startswith("?"):
                        target_nodes = set()
                        for node_id, props in db.nodes.items():
                            if node_id in db.out_edges:
                                for tgt, rel in db.out_edges[node_id]:
                                    if (rel == "property" and tgt == query_pred_syn) or (rel.upper() == "IS_A" and tgt == query_pred_syn):
                                        target_nodes.add(node_id)
                        matching_nodes = set()
                        for target in target_nodes:
                            queue = [target]
                            while queue:
                                curr = queue.pop(0)
                                if curr not in matching_nodes:
                                    matching_nodes.add(curr)
                                    if curr in db.in_edges:
                                        for src, rel in db.in_edges[curr]:
                                            if rel.upper() == "IS_A":
                                                queue.append(src)
                        for node in matching_nodes:
                            candidates.append((node,))
                            
                elif len(query_args_syn) == 2:
                    arg0_pattern = b_syn.get(query_args_syn[0], query_args_syn[0])
                    arg1_pattern = b_syn.get(query_args_syn[1], query_args_syn[1])
                    
                    matching_edges = []
                    for e in db.edges:
                        if e[2] == query_pred_syn:
                            matching_edges.append((e[0], e[1]))
                            
                    for s, t in matching_edges:
                        desc_s = set()
                        queue = [s]
                        while queue:
                            curr = queue.pop(0)
                            if curr not in desc_s:
                                desc_s.add(curr)
                                if curr in db.in_edges:
                                    for src, rel in db.in_edges[curr]:
                                        if rel.upper() == "IS_A":
                                            queue.append(src)
                                            
                        desc_t = set()
                        queue = [t]
                        while queue:
                            curr = queue.pop(0)
                            if curr not in desc_t:
                                desc_t.add(curr)
                                if curr in db.in_edges:
                                    for src, rel in db.in_edges[curr]:
                                        if rel.upper() == "IS_A":
                                            queue.append(src)
                                            
                        for x in desc_s:
                            if not arg0_pattern.startswith("?") and x != arg0_pattern:
                                continue
                            for y in desc_t:
                                if not arg1_pattern.startswith("?") and y != arg1_pattern:
                                    continue
                                candidates.append((x, y))
                                
                else:
                    arg_patterns = [b_syn.get(arg, arg) for arg in query_args_syn]
                    for node_id, props in db.nodes.items():
                        if props.get("type") == "relation" and props.get("pred") == query_pred_syn:
                            rel_args = {}
                            if node_id in db.out_edges:
                                for tgt, rel in db.out_edges[node_id]:
                                    if rel.startswith("arg_"):
                                        try:
                                            idx = int(rel.split("_")[1])
                                            rel_args[idx] = tgt
                                        except ValueError:
                                            pass
                            if len(rel_args) == len(query_args_syn):
                                arg_options = []
                                possible = True
                                for idx, pat in enumerate(arg_patterns):
                                    val = rel_args.get(idx)
                                    desc_val = set()
                                    queue = [val]
                                    while queue:
                                        curr = queue.pop(0)
                                        if curr not in desc_val:
                                            desc_val.add(curr)
                                            if curr in db.in_edges:
                                                for src, rel in db.in_edges[curr]:
                                                    if rel.upper() == "IS_A":
                                                        queue.append(src)
                                    if not pat.startswith("?"):
                                        if pat in desc_val:
                                            arg_options.append([pat])
                                        else:
                                            possible = False
                                            break
                                    else:
                                        arg_options.append(list(desc_val))
                                if possible:
                                    for combo in itertools.product(*arg_options):
                                        candidates.append(combo)
                                        
                for vals in candidates:
                    b_ext_syn = b_syn.copy()
                    b_ext = b.copy()
                    matched = True
                    for arg_pattern, val in zip(query_args_syn, vals):
                        if arg_pattern.startswith("?"):
                            if arg_pattern in b_ext_syn and b_ext_syn[arg_pattern] != val:
                                matched = False
                                break
                            b_ext_syn[arg_pattern] = val
                            b_ext[arg_pattern] = from_synset(val)
                        else:
                            if b_syn.get(arg_pattern, arg_pattern) != val:
                                matched = False
                                break
                    if matched:
                        ground_args_syn = [b_ext_syn.get(arg, arg) for arg in query_args_syn]
                        if b_ext not in local_results:
                            local_results.append(b_ext)
                            fact_key = (from_synset(query_pred_syn), *(from_synset(a) for a in ground_args_syn))
                            fact_log = {"type": "fact", "fact": fact_key}
                            if fact_log not in model.proof_steps:
                                model.proof_steps.append(fact_log)

            # (B) Query logical inference rules (backward-chaining step)
            for rule_cond, rule_conseq in model.rules:
                if not isinstance(rule_conseq, list) or len(rule_conseq) == 0:
                    continue
                conseq_pred = rule_conseq[0]
                conseq_args = [simplify_argument(x) for x in rule_conseq[1:]]
                
                if to_synset(conseq_pred) == query_pred_syn:
                    conseq_args_syn = [to_synset(a) for a in conseq_args]
                    unified_syn = unify_lists(query_args_syn, conseq_args_syn, b_syn)
                    if unified_syn is not None:
                        unified = {k: from_synset(v) for k, v in unified_syn.items()}
                        cond_res = evaluate_query_with_bindings(
                            rule_cond, model, [unified], visited + [goal]
                        )
                        for cr in cond_res:
                            cr_syn = {k: to_synset(v) for k, v in cr.items()}
                            res_b = b.copy()
                            for arg in query_args_syn:
                                if arg.startswith("?"):
                                    res_b[arg] = from_synset(resolve_term(arg, cr_syn))
                            if res_b not in local_results:
                                local_results.append(res_b)
                                conseq_fact_syn = [cr_syn.get(arg, arg) for arg in query_args_syn]
                                conseq_fact = (from_synset(query_pred_syn), *(from_synset(a) for a in conseq_fact_syn))
                                
                                sub_facts = []
                                def gather_sub_facts(c_expr, bindings_dict):
                                    if isinstance(c_expr, list) and len(c_expr) > 0:
                                        if c_expr[0] in ("and", "or"):
                                            for sub in c_expr[1:]:
                                                gather_sub_facts(sub, bindings_dict)
                                        elif c_expr[0] == "not":
                                            pass
                                        else:
                                            p = c_expr[0]
                                            a_list = [bindings_dict.get(simplify_argument(x), simplify_argument(x)) for x in c_expr[1:]]
                                            sub_facts.append((p, *a_list))
                                
                                gather_sub_facts(rule_cond, cr)
                                rule_log = {
                                    "type": "rule",
                                    "rule": (rule_cond, rule_conseq),
                                    "consequence": conseq_fact,
                                    "conditions": sub_facts
                                }
                                if rule_log not in model.proof_steps:
                                    model.proof_steps.append(rule_log)
                                    
            for lr in local_results:
                if lr not in results:
                    results.append(lr)
                    
        return results

def generate_explanation(model: WorldModel, query_expr: SExpr, success: bool) -> str:
    """Generates a human-readable natural language explanation for proof steps."""
    if not success:
        return "Query evaluates to False (no proof found)."
        
    def generate_explanation_clause(fact: Tuple[str, ...]) -> str:
        pred = fact[0].lower()
        templates = {
            "parent": "{1} is a parent of {2}",
            "grandparent": "{1} is a grandparent of {2}",
            "ancestor": "{1} is an ancestor of {2}",
            "has": "{1} has {2}",
            "gives": "{1} gives {2} to {3}",
            "chase": "{1} chases {2}",
            "chased": "{1} chased {2}",
            "bark": "{1} barks",
            "barked": "{1} barked",
            "jumps": "{1} jumps",
            "jumped": "{1} jumped",
            "val": "the value of {1} is {2}"
        }
        if pred in templates:
            template = templates[pred]
            res_str = template
            for idx, val in enumerate(fact):
                res_str = res_str.replace(f"{{{idx}}}", val)
            return res_str

        try:
            from englisp import minimalist_to_nl
            sexpr = list(fact)
            text = minimalist_to_nl(sexpr, lang="en")
            if text.endswith("."):
                text = text[:-1]
            if text and text[0].isupper() and not text.startswith("I "):
                text = text[0].lower() + text[1:]
            return text
        except Exception:
            if len(fact) == 2:
                return f"{fact[1]} is {fact[0]}"
            elif len(fact) == 3:
                return f"{fact[1]} {fact[0]} {fact[2]}"
            return f"{fact[0]}({', '.join(fact[1:])})"

    rule_steps = [step for step in model.proof_steps if step["type"] == "rule"]
    if rule_steps:
        explanations = []
        for step in rule_steps:
            conseq_str = generate_explanation_clause(step["consequence"])
            if conseq_str:
                conseq_str = conseq_str[0].upper() + conseq_str[1:]
            cond_strs = [generate_explanation_clause(cond) for cond in step["conditions"]]
            if cond_strs:
                cond_join = " and ".join(cond_strs)
                explanations.append(f"{conseq_str} because {cond_join}")
            else:
                explanations.append(conseq_str)
        return ". ".join(explanations) + "."
    
    fact_steps = [step for step in model.proof_steps if step["type"] == "fact"]
    if fact_steps:
        fact_strs = []
        for step in fact_steps:
            fact_str = generate_explanation_clause(step["fact"])
            if fact_str:
                fact_str = fact_str[0].upper() + fact_str[1:]
                fact_strs.append(fact_str)
        if fact_strs:
            return "Proved: " + ", ".join(fact_strs) + "."
            
    return "Proved from direct database match."

def evaluate(expr: SExpr, model: WorldModel) -> Dict[str, Any]:
    """
    Evaluates an EngLISP S-expression statement (either an assertion, calculation, or logical query).
    Returns a dictionary of execution results.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return {"error": "Invalid S-expression, expected list."}

    op = expr[0]
    
    # Handle logical rule directly: (=> condition consequence)
    if op == "=>":
        if len(expr) < 3:
            return {"error": "Rule operator => requires condition and consequence arguments."}
        cond = expr[1]
        conseq = expr[2]
        model.add_rule(cond, conseq)
        return {
            "type": "assertion",
            "success": True,
            "rule": expr,
            "message": "Logical rule asserted successfully."
        }

    # Handle top-level let binding in query/assertion
    if op == "let":
        bindings = expr[1]
        body = expr[2]
        var_map = {var: val for var, val in bindings}
        substituted_body = substitute(body, var_map)
        return evaluate(substituted_body, model)

    # Handle arithmetic calculation
    if op in ("+", "-", "*", "/"):
        res_val = evaluate_math(expr, model)
        if isinstance(res_val, float) and res_val.is_integer():
            res_val = int(res_val)
        return {
            "type": "calculation",
            "success": True,
            "result": res_val,
            "message": f"Calculated value: {res_val}."
        }

    if op == "if":
        if len(expr) < 3:
            return {"error": "Conditional requires condition and consequence expressions."}
        cond_expr = expr[1]
        cons_expr = expr[2]
        bindings = evaluate_query_with_bindings(cond_expr, model, [{}])
        if not bindings:
            return {
                "type": "conditional",
                "success": True,
                "triggered": False,
                "message": "Condition not met. Consequence not executed."
            }
        results = []
        for b in bindings:
            sub_cons = substitute(cons_expr, b)
            res = evaluate(sub_cons, model)
            results.append(res)
        return {
            "type": "conditional",
            "success": True,
            "triggered": True,
            "bindings": bindings,
            "consequences": results,
            "message": f"Condition met. Triggered consequence {len(results)} time(s)."
        }

    elif op in ("gives", "donne"):
        if len(expr) < 4:
            return {"error": "gives/donne action requires giver, receiver, and item arguments."}
        giver = simplify_argument(expr[1])
        receiver = simplify_argument(expr[2])
        item = simplify_argument(expr[3])
        model.remove_fact("has", [giver, item])
        model.add_fact("has", [receiver, item])
        return {
            "type": "action",
            "success": True,
            "message": f"Action gives: transferred {item} from {giver} to {receiver}."
        }

    elif op in ("increases", "augmente"):
        if len(expr) < 3:
            return {"error": "increases/augmente action requires item and amount arguments."}
        item = simplify_argument(expr[1])
        amount_expr = expr[2]
        amount_word = "one"
        if isinstance(amount_expr, list) and len(amount_expr) == 2 and amount_expr[0] in ("by", "par"):
            amount_word = simplify_argument(amount_expr[1])
        else:
            amount_word = simplify_argument(amount_expr)
        word_to_num = {"one": 1, "un": 1, "two": 2, "deux": 2, "three": 3, "trois": 3}
        amount = word_to_num.get(amount_word, 1)
        current_val = 0
        to_remove = None
        for fact in model.get_all_facts():
            if fact[0] == "val" and len(fact) == 3 and fact[1] == item:
                current_val = int(fact[2])
                to_remove = fact
                break
        if to_remove:
            model.remove_fact("val", list(to_remove[1:]))
        new_val = current_val + amount
        model.add_fact("val", [item, str(new_val)])
        return {
            "type": "action",
            "success": True,
            "message": f"Action increases: increased {item} value by {amount} to {new_val}."
        }

    elif op in ("decreases", "diminue"):
        if len(expr) < 3:
            return {"error": "decreases/diminue action requires item and amount arguments."}
        item = simplify_argument(expr[1])
        amount_expr = expr[2]
        amount_word = "one"
        if isinstance(amount_expr, list) and len(amount_expr) == 2 and amount_expr[0] in ("by", "par"):
            amount_word = simplify_argument(amount_expr[1])
        else:
            amount_word = simplify_argument(amount_expr)
        word_to_num = {"one": 1, "un": 1, "two": 2, "deux": 2, "three": 3, "trois": 3}
        amount = word_to_num.get(amount_word, 1)
        current_val = 0
        to_remove = None
        for fact in model.get_all_facts():
            if fact[0] == "val" and len(fact) == 3 and fact[1] == item:
                current_val = int(fact[2])
                to_remove = fact
                break
        if to_remove:
            model.remove_fact("val", list(to_remove[1:]))
        new_val = max(0, current_val - amount)
        model.add_fact("val", [item, str(new_val)])
        return {
            "type": "action",
            "success": True,
            "message": f"Action decreases: decreased {item} value by {amount} to {new_val}."
        }

    elif op in ("assert", "tell"):
        if len(expr) < 2:
            return {"error": "Assertion requires a fact/rule argument."}
        fact_expr = expr[1]
        
        # Check if it is a logical rule assertion: e.g. (=> cond conseq)
        is_rule = isinstance(fact_expr, list) and len(fact_expr) == 3 and fact_expr[0] in ("=>", "if")
        if is_rule:
            cond = fact_expr[1]
            conseq = fact_expr[2]
            model.add_rule(cond, conseq)
            return {
                "type": "assertion",
                "success": True,
                "rule": fact_expr,
                "message": "Logical rule asserted successfully."
            }
            
        if not isinstance(fact_expr, list) or len(fact_expr) == 0:
            return {"error": "Assertion target must be a relation expression."}
        
        pred = fact_expr[0]
        if not isinstance(pred, str):
            return {"error": "Predicate name must be a string."}
            
        args = [simplify_argument(x) for x in fact_expr[1:]]
        model.add_fact(pred, args)
        return {
            "type": "assertion",
            "success": True,
            "fact": (pred, *args),
            "message": f"Fact asserted successfully: {pred}({', '.join(args)})"
        }
        
    else:
        # Clear/initialize proof steps
        model.proof_steps.clear()
        
        var_query = has_variables(expr)
        bindings = evaluate_query_with_bindings(expr, model, [{}])
        success = len(bindings) > 0
        explanation = generate_explanation(model, expr, success)
        
        if var_query:
            return {
                "type": "query",
                "variables": True,
                "success": success,
                "bindings": bindings,
                "explanation": explanation,
                "message": f"Query returned {len(bindings)} matching binding(s)." if bindings else "Query returned no matches."
            }
        else:
            return {
                "type": "query",
                "variables": False,
                "success": success,
                "result": success,
                "explanation": explanation,
                "message": "Query evaluates to True." if success else "Query evaluates to False."
            }
