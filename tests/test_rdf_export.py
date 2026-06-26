# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# Unit tests verifying S-expression World State export to RDF Turtle format.

import pytest
from fastapi.testclient import TestClient
from englisp.interpreter import WorldModel
from web.server import app, world_model

client = TestClient(app)

def test_turtle_export_serialization():
    # Create an isolated world model and populate it
    model = WorldModel()
    model.add_fact("lazy", ["dog"])
    model.add_fact("chased", ["fido", "cat"])
    model.add_fact("gives", ["alice", "bob", "book"])

    facts = model.get_all_facts()
    
    # Run the serialization logic similar to endpoint
    lines = []
    lines.append("@prefix : <http://englisp.org/schema#> .")
    lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    lines.append("")
    
    for idx, fact in enumerate(facts):
        pred = fact[0]
        args = fact[1:]
        
        def fmt_res(val):
            val_str = str(val).strip()
            if val_str.isalnum():
                return f":{val_str}"
            escaped = val_str.replace('"', '\\"')
            return f'"{escaped}"'
            
        if len(args) == 1:
            subj = fmt_res(args[0])
            lines.append(f"{subj} a :{pred} .")
        elif len(args) == 2:
            subj = fmt_res(args[0])
            obj = fmt_res(args[1])
            lines.append(f"{subj} :{pred} {obj} .")
        else:
            rel_uri = f":relation_{idx}"
            lines.append(f"{rel_uri} a :Relation ;")
            lines.append(f"    :type :{pred} ;")
            for i, arg in enumerate(args):
                val = fmt_res(arg)
                lines.append(f"    :arg{i} {val} ;")
            if lines:
                lines[-1] = lines[-1].rstrip(" ;") + " ."
                
    turtle_content = "\n".join(lines)
    
    # Assert prefixes
    assert "@prefix : <http://englisp.org/schema#> ." in turtle_content
    assert "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ." in turtle_content
    
    # Assert facts
    assert ":dog a :lazy ." in turtle_content
    assert ":fido :chased :cat ." in turtle_content
    assert "a :Relation ;" in turtle_content
    assert "    :type :gives ;" in turtle_content
    assert "    :arg0 :alice ;" in turtle_content
    assert "    :arg1 :bob ;" in turtle_content
    assert "    :arg2 :book ." in turtle_content


def test_rdf_export_endpoint():
    # Reset and populate global world model
    world_model.clear()
    world_model.add_fact("lazy", ["fox"])
    world_model.add_fact("chased", ["dog", "rabbit"])

    response = client.get("/api/world/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/turtle; charset=utf-8"
    
    turtle_text = response.text
    assert ":fox a :lazy ." in turtle_text
    assert ":dog :chased :rabbit ." in turtle_text
