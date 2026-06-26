# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# Unit tests verifying launch improvements, rate limits, 
# logic querying optimization, parser diagnostics, and externalized morphology.

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from englisp import parser, canonicalizer, interpreter
from englisp.loader import MORPHOLOGY_RULES
from englisp.parser import EngLISPParseError
from englisp.interpreter import WorldModel, evaluate_query_with_bindings
from web.server import app

def test_granular_parser_diagnostics():
    # 1. Test spelling corrections and unknown words tracking
    text = "the dog runs bussining"
    with pytest.raises(EngLISPParseError) as exc_info:
        parser.parse(text)
    
    diag = exc_info.value.diagnostics
    assert diag["sentence"] == "the dog runs bussining"
    assert "bussining" in diag["unknown_words"]
    assert diag["furthest_token_index"] == 3 # blocked at bussining
    assert diag["blocked_token"] == "bussining"

def test_slowapi_rate_limiting():
    client = TestClient(app)
    
    # Reset slowapi limiter state
    from web.server import limiter
    limiter.reset()
    
    # 5 requests pass
    for _ in range(5):
        response = client.post("/api/parse", json={"text": "the dog runs"})
        assert response.status_code == 200
        
    # 6th request fails with 429
    response = client.post("/api/parse", json={"text": "the dog runs"})
    assert response.status_code == 429
    assert "Sandbox rate limit exceeded" in response.json()["detail"]

def test_logic_query_edge_matching_efficiency():
    model = WorldModel()
    
    # Add some facts to DB
    model.add_fact("IS_A", ["fido", "dog"])
    model.add_fact("IS_A", ["dog", "canine"])
    model.add_fact("chased", ["fido", "cat"])
    model.add_fact("chased", ["garfield", "mouse"])
    
    # Verify query matching: (chased ?x cat)
    # This should only bind ?x = fido
    query = ["chased", "?x", "cat"]
    bindings = [{}]
    res = evaluate_query_with_bindings(query, model, bindings, [])
    assert len(res) == 1
    assert res[0]["?x"] == "fido"

    # Verify query matching: (chased ?x ?y)
    query_all = ["chased", "?x", "?y"]
    res_all = evaluate_query_with_bindings(query_all, model, [{}], [])
    # Should find 2 matches
    assert len(res_all) == 2
    match_pairs = {(r["?x"], r["?y"]) for r in res_all}
    assert ("fido", "cat") in match_pairs
    assert ("garfield", "mouse") in match_pairs

def test_externalized_morphology_rules():
    # 1. English plural suffixes loaded from LSON
    assert "s" in MORPHOLOGY_RULES["en"]["plural_suffixes"]
    assert "es" in MORPHOLOGY_RULES["en"]["plural_suffixes"]
    
    # 2. English suffix POS tagging rules loaded from LSON
    assert MORPHOLOGY_RULES["en"]["suffix_tags"]["ly"] == "Adv"
    assert MORPHOLOGY_RULES["en"]["suffix_tags"]["ing"] == "V"

    # 3. Base verb rules loaded from LSON
    # "aimer" base verb is "aime"
    base = canonicalizer.get_base_verb("aimer", "fr")
    assert base == "aime"
    
    # 4. Verb inflections using unified inflect_verb
    # English "run" past form
    past_en = canonicalizer.inflect_verb("run", "past", "en")
    assert past_en == "ran" # loaded from English Verb Forms DB
    
    # French "courir" past participle form
    pp_fr = canonicalizer.inflect_verb("court", "pp", "fr")
    assert pp_fr == "couru" # loaded from French Verb Forms DB
