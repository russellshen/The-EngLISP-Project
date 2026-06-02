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

import re
from typing import List, Dict, Set, Optional

# A complete mock database of BabelNet Synsets containing definitions and multilingual synonyms for inflected and base forms
from englisp.loader import (
    BABELNET_SYNSETS, STOPWORDS, CONCEPTUAL_PRIMES, INVERSE_CONCEPTUAL_PRIMES,
    to_tuple, WORD_TO_SYNSETS, ORIGINAL_SYNSETS
)


def clean_gloss_tokens(text: str) -> Set[str]:
    """Tokenizes text, converts to lowercase, and filters out punctuation and stop words."""
    cleaned = re.sub(r"[^\w\s\-]", "", text.lower())
    tokens = cleaned.split()
    return {t for t in tokens if t not in STOPWORDS}

def disambiguate_sense(word: str, context_words: List[str]) -> str:
    """
    Disambiguates the meaning of a word using a Lesk-style overlap algorithm.
    Finds candidates in BABELNET_SYNSETS matching 'word' in synonyms.
    Calculates overlap between context_words and candidate synset definition/synonym tokens.
    Returns the best matching Synset ID, or the word itself as a fallback if not found.
    """
    word_lower = word.lower()
    candidates = []
    
    synset_ids = WORD_TO_SYNSETS.get(word_lower, [])
    for synset_id in synset_ids:
        if synset_id in BABELNET_SYNSETS:
            candidates.append((synset_id, BABELNET_SYNSETS[synset_id]))
                
    if not candidates:
        return word  # Fallback to plain string concept

    # Sort candidates to prioritize original handcoded synsets and exact round-trip lemmas
    def sort_key(item):
        syn_id, data = item
        is_original = syn_id in ORIGINAL_SYNSETS
        is_primary_en = (data["words"].get("en") and data["words"]["en"][0] == word_lower)
        is_primary_fr = (data["words"].get("fr") and data["words"]["fr"][0] == word_lower)
        return (not is_original, not is_primary_en, not is_primary_fr)

    candidates.sort(key=sort_key)
        
    if len(candidates) == 1:
        return candidates[0][0]
        
    # Clean context words
    context_tokens = {w.lower() for w in context_words if w.lower() not in STOPWORDS and w.lower() != word_lower}
    
    best_synset_id = candidates[0][0]
    max_overlap = -1
    
    for synset_id, data in candidates:
        definition_tokens = clean_gloss_tokens(data["definition"])
        
        # Include synonyms in semantic context tokens
        synonym_tokens = set()
        for lang in ("en", "fr"):
            synonym_tokens.update(data["words"].get(lang, []))
            
        semantic_tokens = definition_tokens.union(synonym_tokens)
        
        # Compute intersection
        overlap = len(context_tokens.intersection(semantic_tokens))
        if overlap > max_overlap:
            max_overlap = overlap
            best_synset_id = synset_id
            
    return best_synset_id

def lookup_word(synset_id: str, lang: str = "en") -> str:
    """Looks up the natural language synonym word corresponding to a Synset ID in the target language."""
    if synset_id in BABELNET_SYNSETS:
        words = BABELNET_SYNSETS[synset_id]["words"].get(lang, [])
        if words:
            return words[0]
    return synset_id


# Primes are loaded from loader.py
