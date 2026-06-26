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

import re
from typing import List, Optional, Tuple, Any
from englisp.xbar import XBarNode
from englisp.loader import (
    LEXICON, FRENCH_LEXICON, GRAMMAR, FRENCH_GRAMMAR, ENGLISH_CONTRACTIONS,
    ORIGINAL_EN_WORDS, ORIGINAL_FR_WORDS, FRENCH_GENDER, MORPHOLOGY_RULES
)

class EngLISPParseError(ValueError):
    def __init__(self, message: str, diagnostics: dict):
        super().__init__(message)
        self.diagnostics = diagnostics

PRONOUN_LEXICON = {
    # English Subject Pronouns
    "he": {"gender": "masculine", "number": "singular", "type": "subject"},
    "she": {"gender": "feminine", "number": "singular", "type": "subject"},
    "it": {"gender": "neuter", "number": "singular", "type": "subject_or_object"},
    "they": {"gender": "neutral", "number": "plural", "type": "subject"},
    # English Object Pronouns
    "him": {"gender": "masculine", "number": "singular", "type": "object"},
    "her": {"gender": "feminine", "number": "singular", "type": "object"},
    "them": {"gender": "neutral", "number": "plural", "type": "object"},
    # English Possessive Pronouns
    "his": {"gender": "masculine", "number": "singular", "type": "possessive"},
    "its": {"gender": "neuter", "number": "singular", "type": "possessive"},
    "their": {"gender": "neutral", "number": "plural", "type": "possessive"},
    
    # French Subject Pronouns
    "il": {"gender": "masculine", "number": "singular", "type": "subject"},
    "elle": {"gender": "feminine", "number": "singular", "type": "subject"},
    "ils": {"gender": "masculine", "number": "plural", "type": "subject"},
    "elles": {"gender": "feminine", "number": "plural", "type": "subject"},
    # French Object/Possessive Pronouns
    "lui": {"gender": "neutral", "number": "singular", "type": "object"},
    "leur": {"gender": "neutral", "number": "plural", "type": "object"},
}


def clean_and_tokenize(text: str) -> List[str]:
    """Cleans punctuation and splits string into tokens, separating French clitics and expanding contractions."""
    text = text.lower()
    for contraction, expansion in ENGLISH_CONTRACTIONS.items():
        text = re.sub(r"\b" + re.escape(contraction) + r"\b", expansion, text)
    # Separate French clitics (l', d', qu', j', m', t', s', n')
    text = re.sub(r"\b(l|d|qu|j|m|t|s|n)'", r"\1' ", text)
    # Remove punctuation except hyphens/apostrophes
    cleaned = re.sub(r"[^\w\s\-\']", "", text)
    tokens = cleaned.split()
    return [t for t in tokens if t not in ("then", "alors")]

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Damerau-Levenshtein edit distance (with transpositions) between s1 and s2."""
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1, lenstr1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, lenstr2 + 1):
        d[(-1, j)] = j + 1
        
    for i in range(lenstr1):
        for j in range(lenstr2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i-1, j)] + 1,      # deletion
                d[(i, j-1)] + 1,      # insertion
                d[(i-1, j-1)] + cost,  # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i-2, j-2)] + cost) # transposition
    return d[(lenstr1 - 1, lenstr2 - 1)]

def correct_word(word: str, lang: str = "en") -> str:
    """Corrects spelling typos against the active lexicon using Levenshtein distance."""
    w_lower = word.lower()
    if w_lower in PRONOUN_LEXICON:
        return word
    lex = FRENCH_LEXICON if lang == "fr" else LEXICON
    # Ignore placeholders, special symbols, numbers
    if word in lex or word == "_" or (word.startswith("[") and word.endswith("]")) or word.isdigit():
        return word
        
    # Plural check bypass
    plural_suffixes = MORPHOLOGY_RULES.get(lang, {}).get("plural_suffixes", ())
    for suffix in plural_suffixes:
        if w_lower.endswith(suffix):
            base = w_lower[:-len(suffix)]
            if base in lex:
                return word
    
    # We only correct alphabetic words of length >= 2
    if len(word) < 2 or not word.replace("-", "").replace("'", "").isalpha():
        return word

    best_word = word
    best_dist = 999
    
    # Load partitions for the first two characters to keep it fast
    if hasattr(lex, "_load_partition_for_word"):
        lex._load_partition_for_word(word[0])
        if len(word) >= 2:
            lex._load_partition_for_word(word[1])
            
    candidates = dict.keys(lex) if hasattr(lex, "_load_partition_for_word") else lex.keys()
    orig_set = ORIGINAL_FR_WORDS if lang == "fr" else ORIGINAL_EN_WORDS
    
    for vocab_word in candidates:
        if vocab_word.endswith("'") and not word.endswith("'"):
            continue
        dist = levenshtein_distance(word, vocab_word)
        if dist < best_dist:
            best_dist = dist
            best_word = vocab_word
        elif dist == best_dist:
            # Prioritize handcoded original words if there is a distance tie
            if vocab_word in orig_set and best_word not in orig_set:
                best_word = vocab_word
            
    # Max allowed distance: 1 for short words (<=4 chars), 2 for longer words
    max_allowed = 1 if len(word) <= 4 else 2
    if best_dist <= max_allowed:
        return best_word
    return word


def tag_tokens(tokens: List[str], lang: str = "en") -> List[Tuple[str, str]]:
    """Tags tokens with POS tags using lexicon, context, and language-specific heuristics."""
    lex = FRENCH_LEXICON if lang == "fr" else LEXICON
    plural_suffixes = MORPHOLOGY_RULES.get(lang, {}).get("plural_suffixes", ())
    tagged = []
    for idx, token in enumerate(tokens):
        t_lower = token.lower()
        if t_lower in PRONOUN_LEXICON:
            tagged.append((token, "N"))
            continue
        # Contextual lookahead for French auxiliaries
        if lang == "fr" and token in ("a", "est", "avait", "aura", "était", "sera", "ont", "avais", "auront", "seront") and idx + 1 < len(tokens):
            next_token = tokens[idx + 1]
            if (next_token in lex and lex[next_token] == "V") or next_token.endswith("é") or next_token.endswith("er") or next_token in ("été", "être", "en") or re.match(r"^v\d+", next_token):
                tagged.append((token, "I"))
                continue

        # Check for French progressive "en train de/d'" helper sequence
        if lang == "fr":
            if token == "en" and idx + 2 < len(tokens) and tokens[idx+1] == "train" and tokens[idx+2] in ("de", "d'"):
                tagged.append((token, "I"))
                continue
            if token == "train" and idx > 0 and tokens[idx-1] == "en" and idx + 1 < len(tokens) and tokens[idx+1] in ("de", "d'"):
                tagged.append((token, "I"))
                continue
            if token in ("de", "d'") and idx > 1 and tokens[idx-2] == "en" and tokens[idx-1] == "train":
                tagged.append((token, "I"))
                continue

        # Contextual lookahead for English auxiliaries
        if lang == "en" and token in ("is", "am", "are", "was", "were", "has", "have", "had") and idx + 1 < len(tokens):
            next_token = tokens[idx + 1]
            if (next_token in lex and lex[next_token] == "V") or next_token.endswith("ing") or next_token.endswith("ed") or next_token in ("been", "be") or re.match(r"^v\d+", next_token):
                tagged.append((token, "I"))
                continue

        # Check for Synset ID pattern matches
        if re.match(r"^n\d+", token):
            tagged.append((token, "N"))
        elif re.match(r"^v\d+", token):
            tagged.append((token, "V"))
        elif token in lex:
            tagged.append((token, lex[token]))
        elif t_lower.endswith(plural_suffixes) and any(
            t_lower[:-len(sfx)] in lex and lex[t_lower[:-len(sfx)]] == "N"
            for sfx in plural_suffixes if t_lower.endswith(sfx)
        ):
            tagged.append((token, "N"))
        elif idx > 0 and tagged[idx - 1][1] == "I":
            # Contextual: word after helper modal is a Verb
            tagged.append((token, "V"))
        else:
            suffix_tags = MORPHOLOGY_RULES.get(lang, {}).get("suffix_tags", {})
            matched_tag = None
            for suffix, tag in suffix_tags.items():
                if lang == "en" and suffix == "s" and len(token) <= 4:
                    continue
                if token.endswith(suffix):
                    matched_tag = tag
                    break
            if matched_tag:
                tagged.append((token, matched_tag))
            else:
                tagged.append((token, "N"))
    return tagged

# GRAMMAR and FRENCH_GRAMMAR are loaded from loader.py

def clone_with_role(node: XBarNode, role: str) -> XBarNode:
    new_node = XBarNode(
        category=node.category,
        role=role,
        label=node.label,
        children=node.children
    )
    if hasattr(node, "synset_id"):
        new_node.synset_id = node.synset_id
    return new_node

def build_xbar_node(lhs: str, children: Tuple[XBarNode, ...]) -> XBarNode:
    if lhs == "AuxChain":
        if not children:
            return XBarNode(category="AuxChain", role="bar")
        elif len(children) == 1:
            i_head = clone_with_role(children[0], "head")
            return XBarNode(category="AuxChain", role="bar", children=[i_head])
        else:
            i_head = clone_with_role(children[0], "head")
            aux_chain = children[1]
            return XBarNode(category="AuxChain", role="bar", children=[i_head] + aux_chain.children)
    elif lhs == "I'":
        aux_chain = children[0]
        vp = clone_with_role(children[1], "complement")
        if not aux_chain.children:
            default_i = XBarNode(category="I", role="head", label="[pres/past]")
            return XBarNode(category="I'", role="bar", children=[default_i, vp])
        else:
            return XBarNode(category="I'", role="bar", children=aux_chain.children + [vp])
    elif lhs == "IP":
        if len(children) == 2:
            if children[0].category == "CP":
                cond_clause = clone_with_role(children[0], "adjunct")
                main_clause = clone_with_role(children[1], "phrase")
                return XBarNode(category="IP", role="phrase", children=[cond_clause, main_clause])
            elif children[1].category == "ConjP":
                ip_left = children[0]
                conjp = clone_with_role(children[1], "adjunct")
                return XBarNode(category="IP", role="phrase", children=[ip_left, conjp])
            else:
                np = clone_with_role(children[0], "specifier")
                i_bar = clone_with_role(children[1], "bar")
                return XBarNode(category="IP", role="phrase", children=[np, i_bar])
    elif lhs == "Conj'_IP":
        conj = clone_with_role(children[0], "head")
        ip = clone_with_role(children[1], "complement")
        return XBarNode(category="Conj'", role="bar", children=[conj, ip])
    elif lhs == "ConjP_IP":
        conj_bar = clone_with_role(children[0], "bar")
        return XBarNode(category="ConjP", role="phrase", children=[conj_bar])
    elif lhs == "V'_base":
        if len(children) == 3:
            v = clone_with_role(children[0], "head")
            np1 = clone_with_role(children[1], "complement")
            np2 = clone_with_role(children[2], "complement")
            return XBarNode(category="V'", role="bar", children=[v, np1, np2])
        elif len(children) == 2:
            v = clone_with_role(children[0], "head")
            np = clone_with_role(children[1], "complement")
            return XBarNode(category="V'", role="bar", children=[v, np])
        else:
            v = clone_with_role(children[0], "head")
            return XBarNode(category="V'", role="bar", children=[v])
    elif lhs == "V'":
        if len(children) == 1:
            return children[0]
        else:
            v_bar = children[0]
            adjunct = clone_with_role(children[1], "adjunct")
            return XBarNode(category="V'", role="bar", children=[v_bar, adjunct])
    elif lhs == "VP":
        v_bar = clone_with_role(children[0], "bar")
        return XBarNode(category="VP", role="phrase", children=[v_bar])
    elif lhs == "P'":
        p = clone_with_role(children[0], "head")
        np = clone_with_role(children[1], "complement")
        return XBarNode(category="P'", role="bar", children=[p, np])
    elif lhs == "PP":
        p_bar = clone_with_role(children[0], "bar")
        return XBarNode(category="PP", role="phrase", children=[p_bar])
    elif lhs == "C'":
        c = clone_with_role(children[0], "head")
        comp = clone_with_role(children[1], "complement")
        return XBarNode(category="C'", role="bar", children=[c, comp])
    elif lhs == "CP":
        c_bar = clone_with_role(children[0], "bar")
        return XBarNode(category="CP", role="phrase", children=[c_bar])
    elif lhs == "NP":
        if len(children) == 2:
            if children[1].category == "ConjP":
                np_left = children[0]
                conjp = clone_with_role(children[1], "adjunct")
                return XBarNode(category="NP", role="phrase", children=[np_left, conjp])
            else:
                det = clone_with_role(children[0], "specifier")
                n_bar = clone_with_role(children[1], "bar")
                return XBarNode(category="NP", role="phrase", children=[det, n_bar])
        else:
            n_bar = clone_with_role(children[0], "bar")
            return XBarNode(category="NP", role="phrase", children=[n_bar])
    elif lhs == "Conj'_NP":
        conj = clone_with_role(children[0], "head")
        np = clone_with_role(children[1], "complement")
        return XBarNode(category="Conj'", role="bar", children=[conj, np])
    elif lhs == "ConjP_NP":
        conj_bar = clone_with_role(children[0], "bar")
        return XBarNode(category="ConjP", role="phrase", children=[conj_bar])
    elif lhs == "N'_base":
        if len(children) == 1:
            n = clone_with_role(children[0], "head")
            return XBarNode(category="N'", role="bar", children=[n])
        else:
            n_bar = children[0]
            role = "complement" if children[1].category == "PP" else "adjunct"
            modifier = clone_with_role(children[1], role)
            return XBarNode(category="N'", role="bar", children=[n_bar, modifier])
    elif lhs == "N'":
        if len(children) == 1:
            return children[0]
        else:
            adj = clone_with_role(children[0], "adjunct")
            n_bar = children[1]
            return XBarNode(category="N'", role="bar", children=[adj, n_bar])
    else:
        raise ValueError(f"Unknown LHS in build_xbar_node: {lhs}")

def score_tree(node: XBarNode) -> int:
    score = 0
    if node.category == "N'":
        for child in node.children:
            if child.category in ("PP", "CP"):
                score += 10
    elif node.category == "V'":
        for child in node.children:
            if child.category in ("PP", "CP"):
                score -= 10
    for child in node.children:
        score += score_tree(child)
    return score

class EarleyState:
    __slots__ = ("lhs", "rhs", "dot", "start", "children")
    def __init__(self, lhs: str, rhs: Tuple[str, ...], dot: int, start: int, children: Tuple[XBarNode, ...]):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.start = start
        self.children = children
    def is_complete(self) -> bool:
        return self.dot == len(self.rhs)
    def next_symbol(self) -> Optional[str]:
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EarleyState):
            return False
        return (self.lhs == other.lhs and
                self.rhs == other.rhs and
                self.dot == other.dot and
                self.start == other.start and
                self.children == other.children)
    def __hash__(self) -> int:
        return hash((self.lhs, self.rhs, self.dot, self.start, self.children))
    def __repr__(self) -> str:
        rhs_str = list(self.rhs)
        rhs_str.insert(self.dot, "*")
        return f"{self.lhs} -> {' '.join(rhs_str)} ({self.start})"

def detect_language(text: str) -> str:
    """Detects whether text is French (fr) or English (en)."""
    tokens = clean_and_tokenize(text)
    fr_count = sum(1 for t in tokens if t in FRENCH_LEXICON)
    en_count = sum(1 for t in tokens if t in LEXICON)
    return "fr" if fr_count > en_count else "en"

def _run_earley(tagged_tokens: List[Tuple[str, str]], root_cat: str, grammar_rules: dict) -> List[XBarNode]:
    """Helper to run the Earley chart parsing algorithm for a specific root category."""
    N = len(tagged_tokens)
    chart_lists = [[] for _ in range(N + 1)]
    chart_sets = [set() for _ in range(N + 1)]

    def add_state(state: EarleyState, index: int):
        if state not in chart_sets[index]:
            chart_sets[index].add(state)
            chart_lists[index].append(state)
            
            if not state.is_complete():
                next_sym = state.next_symbol()
                for completed in chart_lists[index]:
                    if completed.is_complete() and completed.lhs == next_sym and completed.start == index:
                        completed_node = build_xbar_node(completed.lhs, completed.children)
                        new_state = EarleyState(
                            state.lhs,
                            state.rhs,
                            state.dot + 1,
                            state.start,
                            state.children + (completed_node,)
                        )
                        add_state(new_state, index)

    if root_cat in grammar_rules:
        for rhs in grammar_rules[root_cat]:
            add_state(EarleyState(root_cat, rhs, 0, 0, ()), 0)

    for j in range(N + 1):
        state_idx = 0
        while state_idx < len(chart_lists[j]):
            state = chart_lists[j][state_idx]
            state_idx += 1
            
            if not state.is_complete():
                next_sym = state.next_symbol()
                if next_sym in grammar_rules:
                    for rhs in grammar_rules[next_sym]:
                        add_state(EarleyState(next_sym, rhs, 0, j, ()), j)
                else:
                    if j < N:
                        word, tag = tagged_tokens[j]
                        if tag == next_sym:
                            terminal_node = XBarNode(category=tag, role="terminal", label=word)
                            from englisp.ontology import disambiguate_sense
                            context_words = [t[0] for t in tagged_tokens]
                            terminal_node.synset_id = disambiguate_sense(word, context_words)
                            new_state = EarleyState(
                                state.lhs,
                                state.rhs,
                                state.dot + 1,
                                state.start,
                                state.children + (terminal_node,)
                            )
                            add_state(new_state, j + 1)
            else:
                completed_node = build_xbar_node(state.lhs, state.children)
                for parent in chart_lists[state.start]:
                    if not parent.is_complete() and parent.next_symbol() == state.lhs:
                        new_state = EarleyState(
                            parent.lhs,
                            parent.rhs,
                            parent.dot + 1,
                            parent.start,
                            parent.children + (completed_node,)
                        )
                        add_state(new_state, j)

    parses = []
    for state in chart_lists[N]:
        if state.lhs == root_cat and state.start == 0 and state.is_complete():
            tree = build_xbar_node(state.lhs, state.children)
            parses.append(tree)
            
    furthest_scanned_index = 0
    for j in range(N + 1):
        if len(chart_lists[j]) > 0:
            furthest_scanned_index = j
            
    return parses, furthest_scanned_index

class EntityCandidate:
    __slots__ = ("label", "synset_id", "gender", "number", "salience")
    def __init__(self, label: str, synset_id: Optional[str], gender: str, number: str, salience: int):
        self.label = label
        self.synset_id = synset_id
        self.gender = gender
        self.number = number
        self.salience = salience
    def __repr__(self) -> str:
        return f"{self.label}({self.gender},{self.number},sal={self.salience})"

class DiscourseContext:
    def __init__(self):
        self.sentence_history: List[List[EntityCandidate]] = []

def determine_noun_features(word: str, lang: str) -> Tuple[str, str]:
    w_lower = word.lower()
    if w_lower in PRONOUN_LEXICON:
        feat = PRONOUN_LEXICON[w_lower]
        return feat["gender"], feat["number"]
        
    if lang == "fr":
        # French plural check
        number = "plural" if w_lower.endswith(("s", "x")) else "singular"
        # French gender lookup
        from englisp.loader import FRENCH_GENDER
        g = FRENCH_GENDER.get(w_lower, "M")
        gender = "feminine" if g == "F" else "masculine"
        return gender, number
    else:
        # English plural check
        is_plural = w_lower.endswith("s") and w_lower not in ("class", "glass", "chess", "bus", "gas", "mass")
        number = "plural" if is_plural else "singular"
        
        # English gender heuristics
        masculine_nouns = {"man", "boy", "father", "brother", "son", "husband", "gentleman", "king", "prince"}
        feminine_nouns = {"woman", "girl", "mother", "sister", "daughter", "wife", "lady", "queen", "princess"}
        
        if is_plural:
            gender = "neutral"
        elif w_lower in masculine_nouns:
            gender = "masculine"
        elif w_lower in feminine_nouns:
            gender = "feminine"
        else:
            gender = "neuter"
        return gender, number

def find_head_noun(node: XBarNode) -> Optional[XBarNode]:
    if node.category == "N" and node.is_terminal():
        return node
    for child in node.children:
        res = find_head_noun(child)
        if res:
            return res
    return None

def collect_nps(node: XBarNode, parent_category: Optional[str] = None) -> List[Tuple[XBarNode, str]]:
    nps = []
    role_type = "other"
    if node.category == "NP":
        if parent_category == "IP" and node.role == "specifier":
            role_type = "subject"
        elif parent_category == "V'" and node.role == "complement":
            role_type = "object"
        nps.append((node, role_type))
    for child in node.children:
        nps.extend(collect_nps(child, node.category))
    return nps

def matches_gender(p_gender: str, c_gender: str) -> bool:
    if p_gender == "neutral":
        return True
    if p_gender == "neuter":
        return c_gender in ("neuter", "masculine", "feminine")
    return p_gender == c_gender

def matches_number(p_number: str, c_number: str) -> bool:
    return p_number == c_number

def resolve_pronouns_in_tree(node: XBarNode, context: DiscourseContext, lang: str):
    if node.category == "N" and node.is_terminal():
        w_lower = node.label.lower()
        if w_lower in PRONOUN_LEXICON:
            pronoun_feat = PRONOUN_LEXICON[w_lower]
            p_gender = pronoun_feat["gender"]
            p_number = pronoun_feat["number"]
            
            resolved = None
            for sentence_candidates in context.sentence_history:
                sorted_cands = sorted(sentence_candidates, key=lambda c: c.salience, reverse=True)
                for cand in sorted_cands:
                    if matches_gender(p_gender, cand.gender) and matches_number(p_number, cand.number):
                        resolved = cand
                        break
                if resolved:
                    break
                    
            if resolved:
                node.original_label = node.label
                node.label = resolved.label
                node.resolved_label = resolved.label
                node.synset_id = resolved.synset_id

    for child in node.children:
        resolve_pronouns_in_tree(child, context, lang)

def coordinate_trees(trees: List[XBarNode], lang: str) -> XBarNode:
    if not trees:
        raise ValueError("Cannot coordinate empty list of trees")
    if len(trees) == 1:
        return trees[0]
    conj_word = "et" if lang == "fr" else "and"
    current_tree = trees[0]
    for next_tree in trees[1:]:
        conj_head = XBarNode(category="Conj", role="head", label=conj_word)
        comp = clone_with_role(next_tree, "complement")
        conj_bar = XBarNode(category="Conj'", role="bar", children=[conj_head, comp])
        conjp = XBarNode(category="ConjP", role="phrase", children=[conj_bar])
        conjp.role = "adjunct"
        current_tree = XBarNode(
            category="IP",
            role="phrase",
            children=[clone_with_role(current_tree, "phrase"), conjp]
        )
    return current_tree

def parse(text: str, lang: Optional[str] = None) -> XBarNode:
    """Entrypoint to parse natural language to X-bar tree, with fuzzy correction, pronoun resolution, and fragment tolerance."""
    if lang is None:
        lang = detect_language(text)
        
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        raise ValueError("Text cannot be empty.")
        
    context = DiscourseContext()
    parsed_trees = []
    
    for sentence in sentences:
        tokens = clean_and_tokenize(sentence)
        corrected_tokens = []
        spelling_corrections = []
        unknown_words = []
        
        lex = FRENCH_LEXICON if lang == "fr" else LEXICON
        plural_suffixes = MORPHOLOGY_RULES.get(lang, {}).get("plural_suffixes", ())
        
        for t in tokens:
            corr = correct_word(t, lang)
            corrected_tokens.append(corr)
            if corr.lower() != t.lower():
                spelling_corrections.append({"original": t, "corrected": corr})
            
            w_lower = corr.lower()
            is_known = (w_lower in lex) or (w_lower in PRONOUN_LEXICON) or (w_lower == "_") or (w_lower.startswith("[") and w_lower.endswith("]")) or w_lower.isdigit()
            if not is_known:
                for suffix in plural_suffixes:
                    if w_lower.endswith(suffix):
                        base = w_lower[:-len(suffix)]
                        if base in lex:
                            is_known = True
                            break
            if not is_known:
                unknown_words.append(t)
                
        tagged_tokens = tag_tokens(corrected_tokens, lang)
        grammar_rules = FRENCH_GRAMMAR if lang == "fr" else GRAMMAR
        
        # 1. Try parsing as a full sentence (IP)
        parses, furthest_ip = _run_earley(tagged_tokens, "IP", grammar_rules)
        best_parse = None
        furthest_idx = furthest_ip
        
        if parses:
            best_parse = max(parses, key=score_tree)
        else:
            # 2. Fallback to sub-phrases: NP, VP, PP
            for fallback_cat in ("NP", "VP", "PP"):
                parses, furthest_fallback = _run_earley(tagged_tokens, fallback_cat, grammar_rules)
                if furthest_fallback > furthest_idx:
                    furthest_idx = furthest_fallback
                if parses:
                    best_parse = max(parses, key=score_tree)
                    best_parse = XBarNode(category="FRAG", role="phrase", children=[clone_with_role(best_parse, "complement")])
                    break
                    
        if best_parse is None:
            # Construct granular diagnostics payload
            failure_reason = f"Parser blocked at token '{tagged_tokens[furthest_idx][0]}' at position {furthest_idx}" if furthest_idx < len(tagged_tokens) else "Parser reached end of input but could not complete structure"
            diagnostics = {
                "sentence": sentence,
                "tokens": tokens,
                "corrected_tokens": corrected_tokens,
                "spelling_corrections": spelling_corrections,
                "unknown_words": unknown_words,
                "furthest_token_index": furthest_idx,
                "blocked_token": tagged_tokens[furthest_idx][0] if furthest_idx < len(tagged_tokens) else None,
                "failure_reason": failure_reason
            }
            raise EngLISPParseError(
                f"Failed to parse sentence or fragment: '{sentence}' into X-bar structure. {failure_reason}",
                diagnostics
            )
            
        resolve_pronouns_in_tree(best_parse, context, lang)
        parsed_trees.append(best_parse)
        
        # Extract and record entities
        sentence_candidates = []
        nps = collect_nps(best_parse)
        for np_node, role_type in nps:
            h_noun = find_head_noun(np_node)
            if h_noun:
                label = getattr(h_noun, "resolved_label", h_noun.label)
                if label.lower() in PRONOUN_LEXICON:
                    continue
                gender, number = determine_noun_features(label, lang)
                salience = 3 if role_type == "subject" else (2 if role_type == "object" else 1)
                cand = EntityCandidate(label, h_noun.synset_id, gender, number, salience)
                sentence_candidates.append(cand)
        context.sentence_history.insert(0, sentence_candidates)
        
    return coordinate_trees(parsed_trees, lang)


def find_head_verb(node: XBarNode) -> Optional[str]:
    """Recursively finds the head verb word of a VP node."""
    if node.category == "V" and node.is_terminal():
        return node.label
    for child in node.children:
        res = find_head_verb(child)
        if res:
            return res
    return None

def generate(node: XBarNode, lang: str = "en") -> str:
    """Generates natural language text from an X-bar tree, handling French elision."""
    def collect(n: XBarNode, has_inflection: bool) -> List[str]:
        if n.is_terminal():
            from englisp.ontology import lookup_word
            lbl = getattr(n, "original_label", n.label)
            return [lookup_word(lbl, lang)]
        
        current_has_inflection = has_inflection or (n.category in ("IP", "I'"))
        if n.category == "CP":
            current_has_inflection = False
        
        # Check if this is a conditional sentence IP -> CP IP
        if n.category == "IP" and len(n.children) == 2 and n.children[0].category == "CP":
            tokens = []
            tokens.extend(collect(n.children[0], current_has_inflection))
            tokens.append(",")
            tokens.extend(collect(n.children[1], current_has_inflection))
            return tokens
        
        tokens = []
        for child in n.children:
            if child.category == "VP" and not current_has_inflection and lang == "fr":
                head_verb = find_head_verb(child)
                if head_verb:
                    from englisp.ontology import lookup_word
                    head_verb_fr = lookup_word(head_verb, "fr")
                    if head_verb_fr in ("chassé", "sauté"):
                        tokens.append("a")
            tokens.extend(collect(child, current_has_inflection))
        return tokens

    tokens = collect(node, False)
    
    # Filter out syntactic helper markers like [pres/past] and relative empty placeholder "_"
    filtered = [t for t in tokens if not (t.startswith("[") and t.endswith("]")) and t != "_"]
    
    if not filtered:
        return ""
    
    sentence = " ".join(filtered)
    sentence = sentence.replace(" ,", ",")
    
    # Handle French elision (e.g. "le ordinateur" -> "l'ordinateur", "la école" -> "l'école", "de ordinateur" -> "d'ordinateur")
    if lang == "fr":
        # Match 'le' or 'la' followed by any vowel, vowel with accent, or 'h'
        sentence = re.sub(r"\b(le|la)\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"l'\2", sentence)
        # Match 'de' followed by any vowel or 'h'
        sentence = re.sub(r"\bde\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"d'\1", sentence)
        # Note: if there is spaces around the apostrophe like "l' ordinateur" (resulting from clitic separation),
        # remove the space so it renders as a single word "l'ordinateur"
        sentence = re.sub(r"\b(l|d|qu|j|m|t|s|n)'\s+", r"\1'", sentence)

    # Simple capitalization and punctuation spacing
    sentence = sentence[0].upper() + sentence[1:] + "."
    return sentence
