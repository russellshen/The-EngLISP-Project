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
from englisp.ontology import disambiguate_sense, lookup_word
from englisp.graph_db import SemanticGraphDB
from englisp import parser
from englisp import interpreter

def test_lesk_wsd():
    # 1. "bank" near "money" should resolve to financial bank (n08420278)
    context_financial = ["the", "bank", "has", "money"]
    synset_financial = disambiguate_sense("bank", context_financial)
    assert synset_financial == "n08420278"

    # 2. "bank" near "river" should resolve to riverbank (n09214732)
    context_river = ["the", "bank", "by", "the", "river"]
    synset_river = disambiguate_sense("bank", context_river)
    assert synset_river == "n09214732"

def test_graph_db_inheritance():
    db = SemanticGraphDB()
    # fido IS_A dog
    db.add_fact("IS_A", ["fido", "dog"])
    # dog IS_A canine
    db.add_fact("IS_A", ["dog", "canine"])
    # canine bark (unary property)
    db.add_fact("bark", ["canine"])

    # Query: does fido bark?
    assert db.query("bark", ["fido"]) is True
    # Query: does fido inherit from canine?
    assert db.query("IS_A", ["fido", "canine"]) is True
    # Query: fido does not inherit from cat
    assert db.query("IS_A", ["fido", "cat"]) is False

def test_multilingual_synsets():
    # English "dog" and French "chien" map to the same n02084079 synset node
    syn_en = disambiguate_sense("dog", [])
    syn_fr = disambiguate_sense("chien", [])
    assert syn_en == "n02084079"
    assert syn_fr == "n02084079"

    # Reverse lookup works for both English and French
    assert lookup_word("n02084079", "en") == "dog"
    assert lookup_word("n02084079", "fr") == "chien"

def test_wsd_during_parsing_and_interpreter_integration():
    # Parse a sentence with "bank" and "money"
    text1 = "the bank has money"
    tree1 = parser.parse(text1)
    
    def find_node_by_label(n, label):
        if n.is_terminal() and n.label == label:
            return n
        for child in n.children:
            res = find_node_by_label(child, label)
            if res:
                return res
        return None
        
    bank_node = find_node_by_label(tree1, "bank")
    assert bank_node is not None
    assert bank_node.synset_id == "n08420278"

    # Now parse a sentence with "bank" and "river"
    text2 = "the bank by the river"
    tree2 = parser.parse(text2)
    bank_node2 = find_node_by_label(tree2, "bank")
    assert bank_node2 is not None
    assert bank_node2.synset_id == "n09214732"
