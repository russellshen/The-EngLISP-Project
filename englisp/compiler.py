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
                    bind_pairs.append(f"({var} {val_code})")
                bind_str = " ".join(bind_pairs)
                body_code = compile_sexpr(body, target, is_assertion, new_bound_vars)
                return f"(let ({bind_str}) {body_code})"

            elif first in ("for-all", "exists"):
                type_name = compile_sexpr(sexpr[1], target, False, bound_vars)
                body = sexpr[2]
                body_code = compile_sexpr(body, target, is_assertion, bound_vars)
                return f"({first} {type_name} (lambda (_) {body_code}))"

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

def compile_program(sentences: List[Union[str, SExpr]], target: str = "common-lisp") -> str:
    """
    Compiles a sequence of EngLISP S-expressions into a fully executable Common Lisp or Scheme program.
    """
    is_cl = target.lower() in ("common-lisp", "cl")
    
    parsed_sentences = []
    for s in sentences:
        if isinstance(s, str):
            parsed_sentences.append(parse_sexpr(s))
        else:
            parsed_sentences.append(s)

    # Collect all custom predicates from the parsed expressions
    custom_preds = set()
    for s in parsed_sentences:
        custom_preds.update(collect_custom_predicates(s))

    sorted_preds = sorted(list(custom_preds))

    code_lines = []
    
    # Add boilerplate header
    if is_cl:
        code_lines.append(COMMON_LISP_BOILERPLATE)
    else:
        code_lines.append(SCHEME_BOILERPLATE)

    code_lines.append("\n;;; ============================================================================")
    code_lines.append(";;; Custom Predicate Function Declarations")
    code_lines.append(";;; ============================================================================")
    
    for pred in sorted_preds:
        if is_cl:
            code_lines.append(f'(defun {pred} (&rest args)')
            code_lines.append(f'  (apply #\'query-fact "{pred}" args))')
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
