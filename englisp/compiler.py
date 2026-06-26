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

from typing import List, Set, Any, Union, Optional
from englisp.canonicalizer import SExpr, parse_sexpr
from englisp.interpreter import simplify_argument

# Reserved built-in operators that map directly to language constructs or standard library procedures
BUILTINS = {
    "let", "and", "or", "not", "if",
    "for-all", "exists", "gives", "donne",
    "increases", "augmente", "decreases", "diminue",
    "assert", "tell", "val", "by", "par"
}

COMMON_LISP_BOILERPLATE = """;;; ============================================================================
;;; Common Lisp Runtime for EngLISP
;;; ============================================================================

(defparameter *facts* (make-hash-table :test 'equal))

(defun add-fact (pred &rest args)
  (setf (gethash (cons pred args) *facts*) t))

(defun remove-fact (pred &rest args)
  (remhash (cons pred args) *facts*))

(defun query-fact (pred &rest args)
  (if (gethash (cons pred args) *facts*) t nil))

(defun find-instances (type-name)
  (let ((instances nil))
    (maphash (lambda (k v)
               (declare (ignore v))
               (when (and (equal (car k) type-name) (= (length k) 2))
                 (pushnew (cadr k) instances :test 'equal)))
             *facts*)
    (if instances
        instances
        (let ((entities nil))
          (maphash (lambda (k v)
                     (declare (ignore v))
                     (dolist (x (cdr k))
                       (when (equal x type-name)
                         (pushnew type-name entities :test 'equal))))
                   *facts*)
          entities))))

(defun get-number-value (amount-word)
  (cond
    ((or (equal amount-word "one") (equal amount-word "un")) 1)
    ((or (equal amount-word "two") (equal amount-word "deux")) 2)
    ((or (equal amount-word "three") (equal amount-word "trois")) 3)
    (t 1)))

(defun transfer-ownership (giver receiver item)
  (remove-fact "has" giver item)
  (add-fact "has" receiver item)
  (format nil "Action gives: transferred ~A from ~A to ~A." item giver receiver))

(defun increase-value (item amount-word)
  (let* ((amount (get-number-value amount-word))
         (current-val 0))
    (maphash (lambda (k v)
               (declare (ignore v))
               (when (and (equal (car k) "val") (equal (cadr k) item))
                 (setf current-val (parse-integer (caddr k)))
                 (remove-fact "val" item (caddr k))))
             *facts*)
    (let ((new-val (+ current-val amount)))
      (add-fact "val" item (write-to-string new-val))
      (format nil "Action increases: increased ~A value by ~A to ~A." item amount new-val))))

(defun decrease-value (item amount-word)
  (let* ((amount (get-number-value amount-word))
         (current-val 0))
    (maphash (lambda (k v)
               (declare (ignore v))
               (when (and (equal (car k) "val") (equal (cadr k) item))
                 (setf current-val (parse-integer (caddr k)))
                 (remove-fact "val" item (caddr k))))
             *facts*)
    (let ((new-val (max 0 (- current-val amount))))
      (add-fact "val" item (write-to-string new-val))
      (format nil "Action decreases: decreased ~A value by ~A to ~A." item amount new-val))))

(defun for-all (type-name body-fn)
  (let ((instances (find-instances type-name)))
    (if (null instances)
        nil
        (every body-fn instances))))

(defun exists (type-name body-fn)
  (let ((instances (find-instances type-name)))
    (if (null instances)
        nil
        (some body-fn instances))))

(defmacro run-statement (expr text-desc)
  `(let ((res ,expr))
     (format t "~&Evaluating: ~A~%Result: ~S~%~%" ,text-desc res)))
"""

SCHEME_BOILERPLATE = """;;; ============================================================================
;;; Scheme Runtime for EngLISP
;;; ============================================================================

(define *facts* '())

(define (add-fact! pred . args)
  (set! *facts* (cons (cons pred args) *facts*))
  #t)

(define (remove-fact! pred . args)
  (set! *facts* (filter (lambda (f) (not (equal? f (cons pred args)))) *facts*))
  #t)

(define (query-fact pred . args)
  (if (member (cons pred args) *facts* equal?) #t #f))

(define (find-instances type-name)
  (let ((instances '()))
    (for-each (lambda (f)
                (if (and (equal? (car f) type-name) (= (length f) 2))
                    (if (not (member (cadr f) instances equal?))
                        (set! instances (cons (cadr f) instances)))))
              *facts*)
    (if (not (null? instances))
        (reverse instances)
        (let ((entities '()))
          (for-each (lambda (f)
                      (for-each (lambda (x)
                                  (if (equal? x type-name)
                                      (if (not (member type-name entities equal?))
                                          (set! entities (cons type-name entities)))))
                                (cdr f)))
                    *facts*)
          (reverse entities)))))

(define (get-number-value amount-word)
  (cond
    ((or (equal? amount-word "one") (equal? amount-word "un")) 1)
    ((or (equal? amount-word "two") (equal? amount-word "deux")) 2)
    ((or (equal? amount-word "three") (equal? amount-word "trois")) 3)
    (else 1)))

(define (transfer-ownership giver receiver item)
  (remove-fact! "has" giver item)
  (add-fact! "has" receiver item)
  (string-append "Action gives: transferred " item " from " giver " to " receiver "."))

(define (increase-value item amount-word)
  (let* ((amount (get-number-value amount-word))
         (current-val 0))
    (for-each (lambda (f)
                (if (and (equal? (car f) "val") (equal? (cadr f) item))
                    (begin
                      (set! current-val (string->number (caddr f)))
                      (remove-fact! "val" item (caddr f)))))
              *facts*)
    (let ((new-val (+ current-val amount)))
      (add-fact! "val" item (number->string new-val))
      (string-append "Action increases: increased " item " value by " (number->string amount) " to " (number->string new-val) "."))))

(define (decrease-value item amount-word)
  (let* ((amount (get-number-value amount-word))
         (current-val 0))
    (for-each (lambda (f)
                (if (and (equal? (car f) "val") (equal? (cadr f) item))
                    (begin
                      (set! current-val (string->number (caddr f)))
                      (remove-fact! "val" item (caddr f)))))
              *facts*)
    (let ((new-val (max 0 (- current-val amount))))
      (add-fact! "val" item (number->string new-val))
      (string-append "Action decreases: decreased " item " value by " (number->string amount) " to " (number->string new-val) "."))))

(define (every proc lst)
  (cond
    ((null? lst) #t)
    ((proc (car lst)) (every proc (cdr lst)))
    (else #f)))

(define (some proc lst)
  (cond
    ((null? lst) #f)
    ((proc (car lst)) #t)
    (else (some proc (cdr lst)))))

(define (for-all type-name body-proc)
  (let ((instances (find-instances type-name)))
    (if (null? instances)
        #f
        (every body-proc instances))))

(define (exists type-name body-proc)
  (let ((instances (find-instances type-name)))
    (if (null? instances)
        #f
        (some body-proc instances))))

(define-syntax run-statement
  (syntax-rules ()
    ((_ expr text-desc)
     (let ((res expr))
       (display "Evaluating: ")
       (display text-desc)
       (newline)
       (display "Result: ")
       (write res)
       (newline)
       (newline)))))
"""

CLOJURE_BOILERPLATE = """;;; ============================================================================
;;; Clojure Runtime for EngLISP
;;; ============================================================================

(def facts (atom #{}))

(defn add-fact! [pred & args]
  (swap! facts conj (cons pred args))
  true)

(defn remove-fact! [pred & args]
  (swap! facts disj (cons pred args))
  true)

(defn query-fact [pred & args]
  (contains? @facts (cons pred args)))

(defn find-instances [type-name]
  (let [insts (atom #{})]
    (doseq [f @facts]
      (when (and (= (first f) type-name) (= (count f) 2))
        (swap! insts conj (second f))))
    (if (seq @insts)
      (vec @insts)
      (let [ents (atom #{})]
        (doseq [f @facts]
          (doseq [x (rest f)]
            (when (= x type-name)
              (swap! ents conj type-name))))
        (vec @ents)))))

(defn get-number-value [amount-word]
  (cond
    (or (= amount-word "one") (= amount-word "un")) 1
    (or (= amount-word "two") (= amount-word "deux")) 2
    (or (= amount-word "three") (= amount-word "trois")) 3
    :else 1))

(defn transfer-ownership [giver receiver item]
  (remove-fact! "has" giver item)
  (add-fact! "has" receiver item)
  (str "Action gives: transferred " item " from " giver " to " receiver "."))

(defn increase-value [item amount-word]
  (let [amount (get-number-value amount-word)
        current-val (atom 0)]
    (doseq [f @facts]
      (when (and (= (first f) "val") (= (second f) item))
        (reset! current-val (Integer/parseInt (nth f 2)))
        (remove-fact! "val" item (nth f 2))))
    (let [new-val (+ @current-val amount)]
      (add-fact! "val" item (str new-val))
      (str "Action increases: increased " item " value by " amount " to " new-val "."))))

(defn decrease-value [item amount-word]
  (let [amount (get-number-value amount-word)
        current-val (atom 0)]
    (doseq [f @facts]
      (when (and (= (first f) "val") (= (second f) item))
        (reset! current-val (Integer/parseInt (nth f 2)))
        (remove-fact! "val" item (nth f 2))))
    (let [new-val (max 0 (- @current-val amount))]
      (add-fact! "val" item (str new-val))
      (str "Action decreases: decreased " item " value by " amount " to " new-val "."))))

(defn for-all [type-name body-fn]
  (let [instances (find-instances type-name)]
    (if (empty? instances)
      false
      (every? body-fn instances))))

(defn exists [type-name body-fn]
  (let [instances (find-instances type-name)]
    (if (empty? instances)
      false
      (boolean (some body-fn instances)))))

(defmacro run-statement [expr text-desc]
  `(let [res# ~expr]
     (println "Evaluating:" ~text-desc)
     (println "Result:" (pr-str res#))
     (println)))
"""


def is_entity_phrase(sexpr: SExpr, bound_vars: Set[str]) -> bool:
    """Heuristic to check if an expression represents a noun phrase (entity) vs a predicate call."""
    if isinstance(sexpr, str):
        if sexpr in bound_vars:
            return True
        return False
        
    if isinstance(sexpr, list):
        if len(sexpr) == 0:
            return True
        first = sexpr[0]
        if not isinstance(first, str):
            return False
            
        if first in BUILTINS:
            return False
            
        # Heuristic 1: If any argument is a variable, placeholder, or bound variable,
        # it is a predicate query/call, not a noun phrase.
        for x in sexpr[1:]:
            if isinstance(x, str) and (x.startswith("?") or x == "_" or x in bound_vars):
                return False
            if isinstance(x, list) and len(x) > 0 and isinstance(x[0], str) and x[0].startswith("?"):
                return False
                
        # Heuristic 2: Check POS of the head word
        from englisp.parser import LEXICON, FRENCH_LEXICON
        pos = LEXICON.get(first) or FRENCH_LEXICON.get(first)
        if pos in ("V", "I"):
            return False
            
        # Heuristic 3: Check if it's a known noun or contains determiners
        dets = {"the", "a", "an", "this", "that", "every", "some", "each", "all",
                "le", "la", "les", "l'", "un", "une", "ce", "cette", "mon", "ton", "son"}
        if any(x in dets for x in sexpr[1:]):
            return True
            
        if pos == "N":
            return True
            
        # Heuristic 4: Verb-like suffixes imply a predicate call
        if isinstance(first, str):
            if first.endswith("ed") or first.endswith("es") or first.endswith("s") or first.endswith("ing"):
                return False
                
        return True
    return False

def collect_custom_predicates(sexpr: SExpr) -> Set[str]:
    """Recursively parses the S-expression and collects all non-builtin predicate symbols."""
    preds = set()
    if isinstance(sexpr, list):
        if len(sexpr) > 0:
            op = sexpr[0]
            if isinstance(op, list) and len(op) > 0 and op[0] in ("and", "or"):
                for pred in op[1:]:
                    if isinstance(pred, str) and pred not in BUILTINS:
                        preds.add(pred)
            elif isinstance(op, str) and op not in BUILTINS:
                # Check if it's a predicate vs entity
                # We collect it if it's NOT an entity phrase
                if not is_entity_phrase(sexpr, set()):
                    preds.add(op)
            
            # Recurse through arguments
            for arg in sexpr[1:]:
                preds.update(collect_custom_predicates(arg))
    return preds

def compile_sexpr(sexpr: SExpr, target: str = "common-lisp", is_assertion: bool = False, bound_vars: Optional[Set[str]] = None) -> str:
    """Recursively translates a single EngLISP S-expression to target dialect code."""
    is_cl = target.lower() in ("common-lisp", "cl")
    is_clj = target.lower() in ("clojure", "clj")
    bound_vars = bound_vars or set()
    
    # 1. Handle string terminals
    if isinstance(sexpr, str):
        if sexpr in bound_vars:
            return sexpr  # Bound variables (no quotes)
        if sexpr.startswith("?"):
            return sexpr  # Logic variables as symbols (e.g. ?x)
        if sexpr == "_":
            return "_"    # Quantifier placeholder symbol
        return f'"{sexpr}"'

    # 2. Handle entity phrases (NP structures like (dog the) which simplify to constant strings)
    if is_entity_phrase(sexpr, bound_vars):
        flat_val = simplify_argument(sexpr)
        return f'"{flat_val}"'

    # 3. Handle list expressions
    if isinstance(sexpr, list) and len(sexpr) > 0:
        first = sexpr[0]

        # Composed predicates: ((and barked runs) dog)
        if isinstance(first, list) and len(first) > 0 and first[0] in ("and", "or"):
            if len(sexpr) == 2:
                arg = sexpr[1]
                reconstructed = [first[0]]
                for pred in first[1:]:
                    reconstructed.append([pred, arg])
                return compile_sexpr(reconstructed, target, is_assertion, bound_vars)

        if not isinstance(first, str):
            return "()"

        # Built-in operators
        if first in BUILTINS:
            if first == "if":
                cond = compile_sexpr(sexpr[1], target, False, bound_vars)
                cons = compile_sexpr(sexpr[2], target, True, bound_vars)
                return f"(if {cond} {cons})"

            elif first in ("and", "or"):
                args = [compile_sexpr(x, target, is_assertion, bound_vars) for x in sexpr[1:]]
                return f"({first} {' '.join(args)})"

            elif first == "not":
                arg = compile_sexpr(sexpr[1], target, is_assertion, bound_vars)
                return f"(not {arg})"

            elif first == "let":
                bindings = sexpr[1]
                body = sexpr[2]
                new_bound_vars = bound_vars.copy()
                bind_pairs = []
                for var, val in bindings:
                    new_bound_vars.add(var)
                    val_code = compile_sexpr(val, target, False, bound_vars)
                    if is_clj:
                        bind_pairs.append(f"{var} {val_code}")
                    else:
                        bind_pairs.append(f"({var} {val_code})")
                if is_clj:
                    bind_str = " ".join(bind_pairs)
                    body_code = compile_sexpr(body, target, is_assertion, new_bound_vars)
                    return f"(let [{bind_str}] {body_code})"
                else:
                    bind_str = " ".join(bind_pairs)
                    body_code = compile_sexpr(body, target, is_assertion, new_bound_vars)
                    return f"(let ({bind_str}) {body_code})"

            elif first in ("for-all", "exists"):
                type_name = compile_sexpr(sexpr[1], target, False, bound_vars)
                body = sexpr[2]
                body_code = compile_sexpr(body, target, is_assertion, bound_vars)
                lambda_sym = "fn" if is_clj else "lambda"
                lambda_args = "[_]" if is_clj else "(_)"
                return f"({first} {type_name} ({lambda_sym} {lambda_args} {body_code}))"

            elif first in ("gives", "donne"):
                giver = compile_sexpr(sexpr[1], target, False, bound_vars)
                receiver = compile_sexpr(sexpr[2], target, False, bound_vars)
                item = compile_sexpr(sexpr[3], target, False, bound_vars)
                return f"(transfer-ownership {giver} {receiver} {item})"

            elif first in ("increases", "augmente", "decreases", "diminue"):
                item = compile_sexpr(sexpr[1], target, False, bound_vars)
                amount_expr = sexpr[2]
                amount_word = "one"
                if isinstance(amount_expr, list) and len(amount_expr) == 2 and amount_expr[0] in ("by", "par"):
                    amount_word = simplify_argument(amount_expr[1])
                else:
                    amount_word = simplify_argument(amount_expr)
                amount_code = f'"{amount_word}"'
                func_name = "increase-value" if first in ("increases", "augmente") else "decrease-value"
                return f"({func_name} {item} {amount_code})"

            elif first in ("assert", "tell"):
                return compile_sexpr(sexpr[1], target, True, bound_vars)

        # Custom relational predicates (e.g. chases, jumps)
        else:
            compiled_args = []
            for x in sexpr[1:]:
                # Keep variables/placeholders as symbols, simplify noun phrase lists
                if isinstance(x, str) and (x.startswith("?") or x == "_" or x in bound_vars):
                    compiled_args.append(x)
                elif isinstance(x, list) and len(x) > 0 and isinstance(x[0], str) and x[0].startswith("?"):
                    compiled_args.append(compile_sexpr(x, target, False, bound_vars))
                else:
                    flat_val = simplify_argument(x)
                    compiled_args.append(f'"{flat_val}"')
            
            if is_assertion:
                cl_func = "add-fact" if is_cl else "add-fact!"
                return f"({cl_func} \"{first}\" {' '.join(compiled_args)})"
            else:
                return f"({first} {' '.join(compiled_args)})"

    return "()"

def compile_sql_expr(sexpr: SExpr, is_assertion: bool = False) -> str:
    import json
    if isinstance(sexpr, str):
        return f"'{sexpr}'"
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        return ""
        
    first = sexpr[0]
    if first in ("assert", "tell"):
        return compile_sql_expr(sexpr[1], is_assertion=True)
        
    if first == "and":
        if is_assertion:
            return "\n".join(compile_sql_expr(x, is_assertion=True) for x in sexpr[1:])
        else:
            select_vars = []
            tables = []
            where_clauses = []
            var_sources = {}
            
            for idx, conj in enumerate(sexpr[1:]):
                if not isinstance(conj, list) or len(conj) == 0:
                    continue
                pred = conj[0]
                alias = f"t{idx}"
                tables.append(f"{pred} {alias}")
                
                args = conj[1:]
                for a_idx, arg in enumerate(args):
                    col_name = "subject" if a_idx == 0 else ("object" if a_idx == 1 else f"arg{a_idx}")
                    if isinstance(arg, str) and arg.startswith("?"):
                        if arg not in select_vars:
                            select_vars.append(arg)
                        if arg in var_sources:
                            prev_alias, prev_col = var_sources[arg]
                            where_clauses.append(f"{alias}.{col_name} = {prev_alias}.{prev_col}")
                        else:
                            var_sources[arg] = (alias, col_name)
                    else:
                        flat_val = simplify_argument(arg)
                        where_clauses.append(f"{alias}.{col_name} = '{flat_val}'")
            
            if select_vars:
                sel_cols = ", ".join(f"{var_sources[v][0]}.{var_sources[v][1]} AS {v[1:]}" for v in select_vars)
            else:
                sel_cols = "1"
            
            sql = f"SELECT {sel_cols} FROM {', '.join(tables)}"
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            return sql + ";"
            
    if is_assertion:
        args = [simplify_argument(x) for x in sexpr[1:]]
        if len(args) == 1:
            return f"INSERT INTO {first} (subject) VALUES ('{args[0]}');"
        elif len(args) == 2:
            return f"INSERT INTO {first} (subject, object) VALUES ('{args[0]}', '{args[1]}');"
        else:
            cols = ["subject", "object"] + [f"arg{i}" for i in range(2, len(args))]
            vals = ", ".join(f"'{a}'" for a in args)
            return f"INSERT INTO {first} ({', '.join(cols)}) VALUES ({vals});"
    else:
        args = sexpr[1:]
        select_vars = []
        where_clauses = []
        for a_idx, arg in enumerate(args):
            col_name = "subject" if a_idx == 0 else ("object" if a_idx == 1 else f"arg{a_idx}")
            if isinstance(arg, str) and arg.startswith("?"):
                select_vars.append((col_name, arg[1:]))
            else:
                flat_val = simplify_argument(arg)
                where_clauses.append(f"{col_name} = '{flat_val}'")
                
        if select_vars:
            sel_cols = ", ".join(f"{col} AS {var_name}" for col, var_name in select_vars)
        else:
            sel_cols = "1"
            
        sql = f"SELECT {sel_cols} FROM {first}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"
        return sql + ";"

def compile_cypher_expr(sexpr: SExpr, is_assertion: bool = False) -> str:
    if isinstance(sexpr, str):
        return sexpr
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        return ""
        
    first = sexpr[0]
    if first in ("assert", "tell"):
        return compile_cypher_expr(sexpr[1], is_assertion=True)
        
    if first == "and":
        if is_assertion:
            return "\n".join(compile_cypher_expr(x, is_assertion=True) for x in sexpr[1:])
        else:
            match_patterns = []
            where_clauses = []
            select_vars = []
            
            c_idx = 0
            for conj in sexpr[1:]:
                if not isinstance(conj, list) or len(conj) == 0:
                    continue
                pred = conj[0]
                args = conj[1:]
                
                if len(args) == 1:
                    arg = args[0]
                    if isinstance(arg, str) and arg.startswith("?"):
                        var_name = arg[1:]
                        if var_name not in select_vars:
                            select_vars.append(var_name)
                        match_patterns.append(f"({var_name}:Entity)")
                        where_clauses.append(f"{var_name}.{pred} = true")
                    else:
                        flat_val = simplify_argument(arg)
                        match_patterns.append(f"(n{c_idx}:Entity {{id: '{flat_val}'}})")
                        where_clauses.append(f"n{c_idx}.{pred} = true")
                        c_idx += 1
                elif len(args) == 2:
                    src, tgt = args[0], args[1]
                    src_node = ""
                    if isinstance(src, str) and src.startswith("?"):
                        src_node = src[1:]
                        if src_node not in select_vars:
                            select_vars.append(src_node)
                    else:
                        flat_val = simplify_argument(src)
                        src_node = f"n{c_idx}:Entity {{id: '{flat_val}'}}"
                        c_idx += 1
                        
                    tgt_node = ""
                    if isinstance(tgt, str) and tgt.startswith("?"):
                        tgt_node = tgt[1:]
                        if tgt_node not in select_vars:
                            select_vars.append(tgt_node)
                    else:
                        flat_val = simplify_argument(tgt)
                        tgt_node = f"n{c_idx}:Entity {{id: '{flat_val}'}}"
                        c_idx += 1
                        
                    match_patterns.append(f"({src_node})-[:{pred.upper()}]->({tgt_node})")
                c_idx += 1
                
            match_str = "MATCH " + ", ".join(match_patterns)
            if where_clauses:
                match_str += " WHERE " + " AND ".join(where_clauses)
            if select_vars:
                return match_str + " RETURN " + ", ".join(f"{v}.id AS {v}" for v in select_vars) + ";"
            else:
                return match_str + " RETURN 1;"

    if is_assertion:
        args = [simplify_argument(x) for x in sexpr[1:]]
        if len(args) == 1:
            return f"MERGE (n0:Entity {{id: '{args[0]}'}}) SET n0.{first} = true;"
        elif len(args) == 2:
            return f"MERGE (n0:Entity {{id: '{args[0]}'}}) MERGE (n1:Entity {{id: '{args[1]}'}}) CREATE (n0)-[:{first.upper()}]->(n1);"
        else:
            merges = [f"MERGE (n{i}:Entity {{id: '{a}'}})" for i, a in enumerate(args)]
            create_rel = f"CREATE (r:Relation {{type: '{first}'}})"
            edges = [f"CREATE (r)-[:ARG_{i}]->(n{i})" for i in range(len(args))]
            return " ".join(merges) + " " + create_rel + " " + " ".join(edges) + ";"
    else:
        args = sexpr[1:]
        select_vars = []
        match_patterns = []
        where_clauses = []
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, str) and arg.startswith("?"):
                var_name = arg[1:]
                select_vars.append(var_name)
                match_patterns.append(f"({var_name}:Entity)")
                where_clauses.append(f"{var_name}.{first} = true")
            else:
                flat_val = simplify_argument(arg)
                match_patterns.append(f"(n0:Entity {{id: '{flat_val}'}})")
                where_clauses.append(f"n0.{first} = true")
        elif len(args) == 2:
            src, tgt = args[0], args[1]
            src_node = ""
            if isinstance(src, str) and src.startswith("?"):
                src_node = src[1:]
                select_vars.append(src_node)
            else:
                flat_val = simplify_argument(src)
                src_node = f"n0:Entity {{id: '{flat_val}'}}"
                
            tgt_node = ""
            if isinstance(tgt, str) and tgt.startswith("?"):
                tgt_node = tgt[1:]
                select_vars.append(tgt_node)
            else:
                flat_val = simplify_argument(tgt)
                tgt_node = f"n1:Entity {{id: '{flat_val}'}}"
                
            match_patterns.append(f"({src_node})-[:{first.upper()}]->({tgt_node})")
            
        match_str = "MATCH " + ", ".join(match_patterns)
        if where_clauses:
            match_str += " WHERE " + " AND ".join(where_clauses)
        if select_vars:
            return match_str + " RETURN " + ", ".join(f"{v}.id AS {v}" for v in select_vars) + ";"
        else:
            return match_str + " RETURN 1;"

def compile_mongodb_expr(sexpr: SExpr, is_assertion: bool = False) -> str:
    import json
    if isinstance(sexpr, str):
        return f'"{sexpr}"'
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        return ""
        
    first = sexpr[0]
    if first in ("assert", "tell"):
        return compile_mongodb_expr(sexpr[1], is_assertion=True)
        
    if first == "and":
        if is_assertion:
            return "\n".join(compile_mongodb_expr(x, is_assertion=True) for x in sexpr[1:])
        else:
            match_stages = []
            project_vars = {}
            lookup_stages = []
            
            for idx, conj in enumerate(sexpr[1:]):
                if not isinstance(conj, list) or len(conj) == 0:
                    continue
                pred = conj[0]
                args = conj[1:]
                
                if idx == 0:
                    source_coll = pred
                    match_doc = {}
                    for a_idx, arg in enumerate(args):
                        col = "subject" if a_idx == 0 else ("object" if a_idx == 1 else f"arg{a_idx}")
                        if isinstance(arg, str) and arg.startswith("?"):
                            project_vars[arg[1:]] = f"${col}"
                        else:
                            match_doc[col] = simplify_argument(arg)
                    if match_doc:
                        match_stages.append(f"{{ $match: {json.dumps(match_doc)} }}")
                else:
                    lookup_local = "subject"
                    lookup_foreign = "subject"
                    
                    for a_idx, arg in enumerate(args):
                        col = "subject" if a_idx == 0 else ("object" if a_idx == 1 else f"arg{a_idx}")
                        if isinstance(arg, str) and arg.startswith("?"):
                            var_name = arg[1:]
                            if var_name in project_vars:
                                for pk, pv in project_vars.items():
                                    if pk == var_name:
                                        lookup_local = pv[1:]
                                        break
                                lookup_foreign = col
                            else:
                                project_vars[var_name] = f"$joined_{idx}.{col}"
                                
                    lookup = {
                        "from": pred,
                        "localField": lookup_local,
                        "foreignField": lookup_foreign,
                        "as": f"joined_{idx}"
                    }
                    lookup_stages.append(f"{{ $lookup: {json.dumps(lookup)} }}")
                    lookup_stages.append(f"{{ $match: {{ 'joined_{idx}.0': {{ $exists: true }} }} }}")
            
            project = {k: v for k, v in project_vars.items()}
            project["_id"] = 0
            stages = match_stages + lookup_stages + [f"{{ $project: {json.dumps(project)} }}"]
            return f"db.{source_coll}.aggregate([\n  " + ",\n  ".join(stages) + "\n]);"

    if is_assertion:
        args = [simplify_argument(x) for x in sexpr[1:]]
        doc = {}
        if len(args) == 1:
            doc["subject"] = args[0]
        elif len(args) == 2:
            doc["subject"] = args[0]
            doc["object"] = args[1]
        else:
            doc["subject"] = args[0]
            doc["object"] = args[1]
            for i, a in enumerate(args[2:]):
                doc[f"arg{i+2}"] = a
        return f"db.{first}.insertOne({json.dumps(doc)});"
    else:
        args = sexpr[1:]
        match_doc = {}
        project_doc = {"_id": 0}
        for a_idx, arg in enumerate(args):
            col = "subject" if a_idx == 0 else ("object" if a_idx == 1 else f"arg{a_idx}")
            if isinstance(arg, str) and arg.startswith("?"):
                project_doc[arg[1:]] = f"${col}"
            else:
                match_doc[col] = simplify_argument(arg)
        
        match_str = json.dumps(match_doc)
        project_str = json.dumps(project_doc)
        return f"db.{first}.find({match_str}, {project_str});"

def compile_program(sentences: List[Union[str, SExpr]], target: str = "common-lisp") -> str:
    """
    Compiles a sequence of EngLISP S-expressions into target dialect query code.
    """
    parsed_sentences = []
    for s in sentences:
        if isinstance(s, str):
            parsed_sentences.append(parse_sexpr(s))
        else:
            parsed_sentences.append(s)

    target_lower = target.lower()
    if target_lower == "sql":
        statements = []
        statements.append("-- ============================================================================")
        statements.append("-- SQL Schema & Data Export generated from EngLISP")
        statements.append("-- ============================================================================\n")
        for s in parsed_sentences:
            statements.append(compile_sql_expr(s))
        return "\n".join(statements)
        
    elif target_lower == "cypher":
        statements = []
        statements.append("// ============================================================================")
        statements.append("// Neo4j Cypher Graph Queries generated from EngLISP")
        statements.append("// ============================================================================\n")
        for s in parsed_sentences:
            statements.append(compile_cypher_expr(s))
        return "\n".join(statements)
        
    elif target_lower == "mongodb":
        statements = []
        statements.append("// ============================================================================")
        statements.append("// MongoDB Query Documents generated from EngLISP")
        statements.append("// ============================================================================\n")
        for s in parsed_sentences:
            statements.append(compile_mongodb_expr(s))
        return "\n".join(statements)

    is_cl = target_lower in ("common-lisp", "cl")
    is_clj = target_lower in ("clojure", "clj")
    custom_preds = set()
    for s in parsed_sentences:
        custom_preds.update(collect_custom_predicates(s))

    sorted_preds = sorted(list(custom_preds))
    code_lines = []
    
    if is_cl:
        code_lines.append(COMMON_LISP_BOILERPLATE)
    elif is_clj:
        code_lines.append(CLOJURE_BOILERPLATE)
    else:
        code_lines.append(SCHEME_BOILERPLATE)

    code_lines.append("\n;;; ============================================================================")
    code_lines.append(";;; Custom Predicate Function Declarations")
    code_lines.append(";;; ============================================================================")
    
    for pred in sorted_preds:
        if is_cl:
            code_lines.append(f'(defun {pred} (&rest args)')
            code_lines.append(f'  (apply #\'query-fact "{pred}" args))')
        elif is_clj:
            code_lines.append(f'(defn {pred} [& args]')
            code_lines.append(f'  (apply query-fact "{pred}" args))')
        else:
            code_lines.append(f'(define ({pred} . args)')
            code_lines.append(f'  (apply query-fact "{pred}" args))')
        code_lines.append("")

    code_lines.append("\n;;; ============================================================================")
    code_lines.append(";;; Main Execution block")
    code_lines.append(";;; ============================================================================")
    
    for s in parsed_sentences:
        from englisp.canonicalizer import sexpr_to_string
        expr_str = sexpr_to_string(s)
        compiled_expr = compile_sexpr(s, target, is_assertion=False)
        code_lines.append(f'(run-statement {compiled_expr} "{expr_str}")')

    return "\n".join(code_lines)
