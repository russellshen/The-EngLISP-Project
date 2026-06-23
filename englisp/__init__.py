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

from englisp.xbar import XBarNode
from englisp.parser import parse, generate, detect_language
from englisp.canonicalizer import xbar_to_sexpr, sexpr_to_xbar, sexpr_to_string, parse_sexpr
from englisp.minimizer import minimize_sexpr, expand_sexpr

__version__ = "1.0.0"

# --- The 8 Top-Level API Functions for Python Developers ---

def nl_to_xbar(text: str, lang: str = "auto") -> XBarNode:
    """
    Stage 1 -> Stage 2: Parses a natural language sentence into an X-bar tree.
    If lang is "auto", the language is automatically detected (English or French).
    """
    if lang == "auto":
        lang = detect_language(text)
    return parse(text, lang=lang)

def xbar_to_nl(node: XBarNode, lang: str = "en") -> str:
    """
    Stage 2 -> Stage 1: Synthesizes a natural language sentence from an X-bar tree.
    """
    return generate(node, lang=lang)

def xbar_to_englisp(node: XBarNode, lang: str = "en") -> list:
    """
    Stage 2 -> Stage 3: Translates an X-bar tree into a canonical rotated EngLISP S-expression list.
    """
    return xbar_to_sexpr(node, lang=lang)

def englisp_to_xbar(sexpr: list, lang: str = "en") -> XBarNode:
    """
    Stage 3 -> Stage 2: Reconstructs an X-bar tree from a rotated EngLISP S-expression list.
    """
    return sexpr_to_xbar(sexpr, lang=lang)

def englisp_to_minimalist(sexpr: list) -> list:
    """
    Stage 3 -> Stage 4: Compresses a canonical EngLISP S-expression list into MinimaLIST form.
    """
    return minimize_sexpr(sexpr)

def minimalist_to_englisp(sexpr: list) -> list:
    """
    Stage 4 -> Stage 3: Expands a MinimaLIST S-expression list back into a full canonical EngLISP S-expression list.
    """
    return expand_sexpr(sexpr)

# --- The 2 "All the Way" Functions ---

def nl_to_minimalist(text: str, lang: str = "auto") -> list:
    """
    Stage 1 -> Stage 4: Transforms natural language directly to a MinimaLIST S-expression list.
    """
    if lang == "auto":
        lang = detect_language(text)
    xbar = nl_to_xbar(text, lang=lang)
    englisp = xbar_to_englisp(xbar, lang=lang)
    return englisp_to_minimalist(englisp)

def minimalist_to_nl(sexpr: list, lang: str = "en") -> str:
    """
    Stage 4 -> Stage 1: Expands a MinimaLIST S-expression list and synthesizes it back into natural language.
    """
    englisp = minimalist_to_englisp(sexpr)
    xbar = englisp_to_xbar(englisp, lang=lang)
    return xbar_to_nl(xbar, lang=lang)

# --- S-expression string serialization/parsing helpers ---

def to_string(sexpr: list) -> str:
    """Serializes an S-expression list to its canonical string representation (with DAG backreferences if shared)."""
    return sexpr_to_string(sexpr)

def from_string(s: str) -> list:
    """Parses a Lisp-style S-expression string (handling DAG reference notation) into a list structure."""
    return parse_sexpr(s)
