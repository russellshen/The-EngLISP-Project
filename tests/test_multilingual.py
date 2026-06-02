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
from englisp import parser, canonicalizer

def test_language_detection():
    assert parser.detect_language("The dog chased the cat.") == "en"
    assert parser.detect_language("Le chien a chassé le chat.") == "fr"
    assert parser.detect_language("Le renard paresseux a sauté sur le chien intelligent.") == "fr"
    assert parser.detect_language("The quick brown fox jumped.") == "en"

def test_french_parsing_and_rotation_svo():
    # French simple sentence: "Le chien a chassé le chat."
    text = "Le chien a chassé le chat."
    
    # 1. Parse French text to French X-bar tree
    tree = parser.parse(text, lang="fr")
    assert tree.category == "IP"
    assert tree.children[0].category == "NP"
    
    # Verify the French inflected verb has 'a' as auxiliary inflection
    ibar = tree.children[1]
    i_head = ibar.children[0]
    assert i_head.category == "I"
    assert i_head.label == "a"
    
    # 2. Rotate and translate to English pivot S-expression
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="fr")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    
    # Pivot S-expression should be in standard English concepts
    assert sexpr_str == "(chased (dog the) (cat the))"

def test_french_parsing_with_post_nominal_adjectives():
    # French sentence with post-nominal adjective: "Le renard paresseux court." (The lazy fox runs.)
    text = "Le renard paresseux court."
    
    tree = parser.parse(text, lang="fr")
    assert tree.category == "IP"
    
    # Subject NP
    subj = tree.children[0]
    assert subj.category == "NP"
    
    # In French, "paresseux" is post-nominal, so under N'_base as post-modifier
    # NP -> Det + N' -> N'_base -> N'_base + Adj
    nbar = subj.children[1]
    assert nbar.category == "N'"
    assert nbar.children[0].category == "N'"
    assert nbar.children[1].category == "Adj"
    assert nbar.children[1].label == "paresseux"
    
    # Rotate and translate to English pivot S-expression
    sexpr = canonicalizer.xbar_to_sexpr(tree, lang="fr")
    sexpr_str = canonicalizer.sexpr_to_string(sexpr)
    assert sexpr_str == "(runs (fox the lazy))"

def test_pivot_to_french_generation_with_agreement():
    # Let's start with an English pivot S-expression: "(chased (dog the) (cat the))"
    sexpr = canonicalizer.parse_sexpr("(chased (dog the) (cat the))")
    
    # 1. Reconstruct French X-bar tree
    tree_fr = canonicalizer.sexpr_to_xbar(sexpr, lang="fr")
    
    # 2. Generate French text
    text_fr = parser.generate(tree_fr, lang="fr")
    assert text_fr == "Le chien a chassé le chat."

def test_pivot_to_french_generation_with_feminine_agreement():
    # English pivot: "(transforms (system the modern) (representation the minimal))"
    # English equivalent: "The modern system transforms the minimal representation."
    # French mapping:
    # "system" -> "système" (masculine), "modern" -> "moderne"
    # "representation" -> "représentation" (feminine), "minimal" -> "minimale" (agreed)
    # "transforms" -> "transforme"
    # Output: "Le système moderne transforme la représentation minimale."
    sexpr = canonicalizer.parse_sexpr("(transforms (system the modern) (representation the minimal))")
    
    tree_fr = canonicalizer.sexpr_to_xbar(sexpr, lang="fr")
    text_fr = parser.generate(tree_fr, lang="fr")
    assert text_fr == "Le système moderne transforme la représentation minimale."

def test_french_vowel_elision():
    # Test elision for determiners (le/la -> l') and prepositions (de -> d')
    # "computer" -> "ordinateur" (starts with vowel 'o')
    # "the computer" -> "l'ordinateur"
    # "library" -> "bibliothèque" (F)
    # "transforms the language in the computer" -> "(transforms ... (in (computer the)))"
    # Let's test a simple NP pivot: "(computer the)"
    sexpr1 = canonicalizer.parse_sexpr("(computer the)")
    tree_fr1 = canonicalizer.sexpr_to_xbar(sexpr1, lang="fr")
    text_fr1 = parser.generate(tree_fr1, lang="fr")
    assert text_fr1 == "L'ordinateur."
    
    # Test relative clause translation
    # "The dog that chased the cat jumped."
    # French: "Le chien qui a chassé le chat a sauté."
    # Pivot: "(jumped (dog the (that (chased _ (cat the)))))"
    sexpr2 = canonicalizer.parse_sexpr("(jumped (dog the (that (chased _ (cat the)))))")
    tree_fr2 = canonicalizer.sexpr_to_xbar(sexpr2, lang="fr")
    text_fr2 = parser.generate(tree_fr2, lang="fr")
    assert text_fr2 == "Le chien qui a chassé le chat a sauté."

def test_full_cross_lingual_translation():
    # Translate from French to English
    fr_text = "Le renard paresseux a sauté sur le chien intelligent."
    tree_fr = parser.parse(fr_text, lang="fr")
    sexpr = canonicalizer.xbar_to_sexpr(tree_fr, lang="fr")
    
    # Pivot should match English concept
    assert canonicalizer.sexpr_to_string(sexpr) == "(jumped (fox the lazy) (over (dog the smart)))"
    
    # Reconstruct English and generate
    tree_en = canonicalizer.sexpr_to_xbar(sexpr, lang="en")
    en_text = parser.generate(tree_en, lang="en")
    assert en_text == "The lazy fox jumped over the smart dog."

def test_new_verbs_multilingual():
    # Test "tue" (kills)
    fr_text1 = "Le chien tue le chat."
    tree_fr1 = parser.parse(fr_text1, lang="fr")
    sexpr1 = canonicalizer.xbar_to_sexpr(tree_fr1, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr1) == "(kills (dog the) (cat the))"
    
    tree_en1 = canonicalizer.sexpr_to_xbar(sexpr1, lang="en")
    en_text1 = parser.generate(tree_en1, lang="en")
    assert en_text1 == "The dog kills the cat."

    # Test "brise" (breaks)
    fr_text2 = "Le chien brise le livre."
    tree_fr2 = parser.parse(fr_text2, lang="fr")
    sexpr2 = canonicalizer.xbar_to_sexpr(tree_fr2, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr2) == "(breaks (dog the) (book the))"

    # Test "arrête" (stops)
    fr_text3 = "Le chien arrête le chat."
    tree_fr3 = parser.parse(fr_text3, lang="fr")
    sexpr3 = canonicalizer.xbar_to_sexpr(tree_fr3, lang="fr")
    assert canonicalizer.sexpr_to_string(sexpr3) == "(stops (dog the) (cat the))"
