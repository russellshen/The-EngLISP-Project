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

from typing import List, Union, Any, Optional, Tuple
from englisp.xbar import XBarNode
from englisp.parser import tag_tokens
from englisp.loader import (
    LEXICON, FRENCH_LEXICON, FRENCH_TO_ENGLISH_VOCAB, ENGLISH_TO_FRENCH_VOCAB,
    FRENCH_GENDER, FRENCH_ADJ_FEMININE, FRENCH_PRE_ADJECTIVES, TENSE_AUXILIARIES,
    ENGLISH_VERB_FORMS, FRENCH_VERB_FORMS, parse_sexpr
)

# A type representing a parsed S-Expression in Python (nested lists of strings)
SExpr = Union[str, List[Any]]

def inflect_english_verb(base: str, form_type: str) -> str:
    base = base.lower()
    if base in ENGLISH_VERB_FORMS:
        forms = ENGLISH_VERB_FORMS[base]
        idx = {"3sg": 0, "past": 1, "ing": 2, "pp": 3}[form_type]
        return forms[idx]
    if form_type == "3sg":
        if base.endswith(("s", "sh", "ch", "x", "z", "o")):
            return base + "es"
        elif base.endswith("y") and not base.endswith(("ay", "ey", "oy", "uy")):
            return base[:-1] + "ies"
        return base + "s"
    elif form_type in ("past", "pp"):
        if base.endswith("e"):
            return base + "d"
        elif base.endswith("y") and not base.endswith(("ay", "ey", "oy", "uy")):
            return base[:-1] + "ied"
        return base + "ed"
    elif form_type == "ing":
        if base.endswith("e") and not base.endswith(("ee", "oe", "ye")):
            return base[:-1] + "ing"
        return base + "ing"
    return base

def inflect_french_verb(base: str, form_type: str) -> str:
    base = base.lower()
    if base in FRENCH_VERB_FORMS:
        forms = FRENCH_VERB_FORMS[base]
        idx = {"3sg": 0, "imp": 1, "fut": 2, "pp": 3, "inf": 4}[form_type]
        return forms[idx]
    stem = base[:-1] if base.endswith("e") else base
    if form_type == "3sg":
        return stem + "e"
    elif form_type == "imp":
        return stem + "ait"
    elif form_type == "fut":
        return stem + "era"
    elif form_type == "pp":
        return stem + "é"
    elif form_type == "inf":
        return stem + "er"
    return base

def get_english_base_verb(verb_word: str) -> str:
    verb_word = verb_word.lower()
    for base, forms in ENGLISH_VERB_FORMS.items():
        if verb_word in forms or verb_word == base:
            return base
    if verb_word.endswith("ing"):
        return verb_word[:-3]
    if verb_word.endswith("es"):
        return verb_word[:-2]
    if verb_word.endswith("s"):
        return verb_word[:-1]
    if verb_word.endswith("ed"):
        return verb_word[:-2]
    return verb_word

def get_french_base_verb(verb_word: str) -> str:
    verb_word = verb_word.lower()
    for base, forms in FRENCH_VERB_FORMS.items():
        if verb_word in forms or verb_word == base:
            return base
    if verb_word.endswith(("ait", "ais", "aient")):
        return verb_word[:-3] + "e"
    if verb_word.endswith("ant"):
        return verb_word[:-3] + "e"
    if verb_word.endswith("é"):
        return verb_word[:-1] + "e"
    if verb_word.endswith("er"):
        return verb_word[:-2] + "e"
    return verb_word

def get_pivot_base_verb(verb_word: str, lang: str) -> str:
    verb_word = verb_word.lower()
    if verb_word.startswith("v") and len(verb_word) > 1 and verb_word[1].isdigit():
        return verb_word
    if lang == "fr":
        fr_base = get_french_base_verb(verb_word)
        en_present = FRENCH_TO_ENGLISH_VOCAB.get(fr_base, fr_base)
        return get_english_base_verb(en_present)
    else:
        return get_english_base_verb(verb_word)

def get_tense_vector(aux_words: List[str], verb_word: str, lang: str) -> Tuple[int, int, str]:
    aux_words = [a.lower() for a in aux_words]
    verb_word = verb_word.lower()
    if lang == "en":
        is_continuous = verb_word.endswith("ing")
        is_perfect = any(a in aux_words for a in ("has", "have", "had"))
        if "will" in aux_words:
            t1 = 1
        elif any(a in aux_words for a in ("had", "was", "were")):
            t1 = -1
        elif any(a in aux_words for a in ("has", "have", "is", "am", "are")):
            t1 = 0
        else:
            if verb_word.endswith("ed") or verb_word in ("ran", "spoke", "gave", "read", "was", "were", "had"):
                t1 = -1
            else:
                t1 = 0
        t2 = -1 if is_perfect else 0
        aspect = "continuous" if is_continuous else "simple"
        return t1, t2, aspect
    else:
        is_continuous = "en" in aux_words or verb_word.endswith(("ait", "ais", "aient"))
        if "aura" in aux_words or "sera" in aux_words or verb_word.endswith(("ra", "ront")):
            t1 = 1
        elif "avait" in aux_words or "était" in aux_words or verb_word.endswith(("ait", "ais", "aient", "é", "a", "èrent")) or "a" in aux_words or "ont" in aux_words:
            if ("a" in aux_words or "ont" in aux_words) and "été" in aux_words and "en" in aux_words:
                t1 = 0
            elif ("a" in aux_words or "ont" in aux_words) and not ("en" in aux_words or verb_word.endswith("er")):
                t1 = -1
            else:
                t1 = -1
        else:
            t1 = 0
        if "en" in aux_words:
            t2 = -1 if "été" in aux_words and any(a in aux_words for a in ("avait", "aura", "a", "ont")) else 0
        else:
            if "avait" in aux_words or "aura" in aux_words:
                t2 = -1
            else:
                t2 = 0
        aspect = "continuous" if is_continuous else "simple"
        return t1, t2, aspect

def translate_word_from_pivot(word: str, target_lang: str, gender: Optional[str] = None) -> str:
    """Translates an English pivot word to the target language (e.g. French)."""
    if target_lang != "fr":
        return word
    word_lower = word.lower()
    
    # Handle Determiners based on gender
    if word_lower in ("the", "a", "an"):
        if gender == "F":
            return "la" if word_lower == "the" else "une"
        else:
            return "le" if word_lower == "the" else "un"
            
    # Check translation vocabulary
    translated = None
    from englisp.loader import LEXICON
    is_verb = (LEXICON.get(word_lower) == "V") or (word_lower.endswith("s") and LEXICON.get(word_lower[:-1]) == "V")
    if not is_verb and word_lower.endswith("s") and word_lower not in ("this", "its", "his", "their", "them", "us", "yes"):
        singular = word_lower[:-1]
        if singular in ENGLISH_TO_FRENCH_VOCAB:
            translated = ENGLISH_TO_FRENCH_VOCAB[singular] + "s"
    if not translated:
        translated = ENGLISH_TO_FRENCH_VOCAB.get(word_lower, word)
    
    # Handle Adjective agreement
    if gender == "F" and translated in FRENCH_ADJ_FEMININE:
        translated = FRENCH_ADJ_FEMININE[translated]
        
    return translated

# parse_sexpr is loaded from loader.py

def sexpr_to_string(expr: SExpr) -> str:
    """Converts a nested Python list representation back to an S-expression string, supporting DAG backreferences."""
    counts = {}
    visited = set()
    
    def count_list_occurrences(e):
        if isinstance(e, list):
            e_id = id(e)
            counts[e_id] = counts.get(e_id, 0) + 1
            if e_id in visited:
                return
            visited.add(e_id)
            for x in e:
                count_list_occurrences(x)
                
    count_list_occurrences(expr)
    
    shared_labels = {}
    defined_labels = set()
    next_label_id = 1
    
    def serialize_helper(e) -> str:
        nonlocal next_label_id
        if isinstance(e, list):
            e_id = id(e)
            if counts.get(e_id, 0) > 1:
                if e_id in defined_labels:
                    label = shared_labels[e_id]
                    return f"#{label}#"
                else:
                    label = next_label_id
                    next_label_id += 1
                    shared_labels[e_id] = label
                    defined_labels.add(e_id)
                    inner = " ".join(serialize_helper(x) for x in e)
                    return f"#{label}=({inner})"
            else:
                inner = " ".join(serialize_helper(x) for x in e)
                return f"({inner})"
        elif isinstance(e, str):
            return e
        else:
            return str(e)
            
    return serialize_helper(expr)


def xbar_to_sexpr(node: XBarNode, lang: str = "en") -> SExpr:
    """
    Translates an X-bar tree into a rotated Lisp S-expression.
    Rotation rules:
      - IP (Sentence): verb-first. If there is a modal/helper I (e.g. 'can'), we wrap:
        (modal (verb subject object ...)). Otherwise: (verb subject object ...)
      - NP (Noun Phrase): noun-first. (noun det adj1 adj2 ... pp_comp ...)
      - PP (Prepositional Phrase): prep-first. (prep np_comp)
    """
    def get_label(n: XBarNode) -> str:
        lbl = getattr(n, "resolved_label", n.label)
        if not lbl:
            return ""
        if lang == "fr":
            lbl_lower = lbl.lower()
            translated = None
            from englisp.loader import FRENCH_LEXICON
            is_verb = (FRENCH_LEXICON.get(lbl_lower) == "V") or (lbl_lower.endswith("s") and FRENCH_LEXICON.get(lbl_lower[:-1]) == "V")
            if not is_verb and lbl_lower.endswith(("s", "x")) and lbl_lower not in ("les", "des", "ses", "mes", "tes", "nos", "vos", "leurs"):
                singular = lbl_lower[:-1]
                if singular in FRENCH_TO_ENGLISH_VOCAB:
                    translated = FRENCH_TO_ENGLISH_VOCAB[singular] + "s"
            if not translated:
                translated = FRENCH_TO_ENGLISH_VOCAB.get(lbl_lower, lbl)
            return translated
        return lbl

    if node.is_terminal():
        return get_label(node)

    if node.category == "FRAG":
        return ["frag", xbar_to_sexpr(node.children[0], lang)]

    # Check for ConjP child first to handle coordination at any phrase level
    conjp_child = None
    other_child = None
    for child in node.children:
        if child.category == "ConjP":
            conjp_child = child
        else:
            other_child = child
            
    if conjp_child and other_child:
        conj_bar = None
        for c in conjp_child.children:
            if c.category == "Conj'" and c.role == "bar":
                conj_bar = c
        if conj_bar:
            conj_head = None
            right_node = None
            for c in conj_bar.children:
                if c.category == "Conj" and c.role == "head":
                    conj_head = c
                elif c.role == "complement":
                    right_node = c
            if conj_head and right_node:
                return [get_label(conj_head), xbar_to_sexpr(other_child, lang), xbar_to_sexpr(right_node, lang)]

    if node.category == "CP":
        c_bar = None
        for child in node.children:
            if child.category == "C'" and child.role == "bar":
                c_bar = child
        if not c_bar:
            raise ValueError("Invalid CP node: missing C' bar node.")
        
        c_head = None
        body_node = None
        for child in c_bar.children:
            if child.category == "C" and child.role == "head":
                c_head = child
            elif child.category in ("VP", "IP") and child.role == "complement":
                body_node = child
                
        if not c_head or not body_node:
            raise ValueError("Invalid C' node: missing C head or body complement.")
            
        c_label = get_label(c_head)
        
        # Extract auxiliaries and VP component
        aux_words = []
        vp_node = None
        
        if body_node.category == "IP":
            i_bar = None
            for child in body_node.children:
                if child.category == "I'" and child.role == "bar":
                    i_bar = child
            if i_bar:
                for child in i_bar.children:
                    if child.category == "I":
                        lbl = child.label
                        if lbl and not (lbl.startswith("[") and lbl.endswith("]")):
                            aux_words.append(lbl.lower())
                    elif child.category == "VP" and child.role == "complement":
                        vp_node = child
        else:
            vp_node = body_node
            
        if not vp_node:
            raise ValueError("Invalid body node: missing VP component.")
            
        v_bar = None
        for child in vp_node.children:
            if child.category == "V'" and child.role == "bar":
                v_bar = child
        if not v_bar:
            raise ValueError("Invalid VP node inside CP: missing V' bar node.")
            
        verb_word = None
        arguments = []
        raw_verb_word = None
        
        def traverse_v_bar(v_node: XBarNode):
            nonlocal verb_word, raw_verb_word
            for child in v_node.children:
                if child.category == "V" and child.role == "head":
                    verb_word = get_label(child)
                    raw_verb_word = child.label
                elif child.category == "V'" and child.role == "bar":
                    traverse_v_bar(child)
                elif child.role in ("complement", "adjunct"):
                    arguments.append(xbar_to_sexpr(child, lang))
                    
        traverse_v_bar(v_bar)
        if not verb_word:
            verb_word = "is"
            raw_verb_word = "is"
            
        pivot_verb = get_pivot_base_verb(raw_verb_word, lang)
        t1, t2, aspect = get_tense_vector(aux_words, raw_verb_word, lang)
        
        modals = [w for w in aux_words if w not in TENSE_AUXILIARIES]
        
        if t2 == 0 and aspect == "simple":
            inner_sexpr = [verb_word, "_"] + arguments
        else:
            inner_sexpr = [pivot_verb, "_"] + arguments + [[t1, t2, aspect]]
            
        if modals:
            modal_pivot = translate_word_from_pivot(modals[0], "en")
            inner_sexpr = [modal_pivot, inner_sexpr]
            
        return [c_label, inner_sexpr]

    if node.category == "IP":
        # Check for conditional structure IP -> CP IP
        cp_cond = None
        ip_main = None
        for child in node.children:
            if child.category == "CP":
                cp_cond = child
            elif child.category == "IP":
                ip_main = child
                
        if cp_cond and ip_main:
            c_bar = None
            for child in cp_cond.children:
                if child.category == "C'" and child.role == "bar":
                    c_bar = child
            if c_bar:
                c_head = None
                antecedent = None
                for child in c_bar.children:
                    if child.category == "C" and child.role == "head":
                        c_head = child
                    elif child.role == "complement":
                        antecedent = child
                if c_head and antecedent:
                    return ["if", xbar_to_sexpr(antecedent, lang), xbar_to_sexpr(ip_main, lang)]

        # Standard IP
        subject_np = None
        i_bar = None
        for child in node.children:
            if child.category == "NP" and child.role == "specifier":
                subject_np = child
            elif child.category == "I'" and child.role == "bar":
                i_bar = child

        if not i_bar:
            raise ValueError("Invalid IP node: missing I' bar node.")

        # Find I heads and VP complement inside I'
        aux_words = []
        vp_node = None
        for child in i_bar.children:
            if child.category == "I":
                lbl = child.label
                if lbl and not (lbl.startswith("[") and lbl.endswith("]")):
                    aux_words.append(lbl.lower())
            elif child.category == "VP" and child.role == "complement":
                vp_node = child

        if not vp_node:
            raise ValueError("Invalid I' node: missing VP complement.")

        # Check if subject NP has a quantifier: Det is "every", "some", "all", "each", etc.
        quantifier = None
        noun_label = None
        if subject_np:
            det_node = None
            n_bar = None
            for child in subject_np.children:
                if child.category == "Det" and child.role == "specifier":
                    det_node = child
                elif child.category == "N'" and child.role == "bar":
                    n_bar = child
            if det_node and det_node.label:
                det_val = get_label(det_node).lower()
                if det_val in ("every", "some", "all", "each", "chaque", "quelque"):
                    quantifier = "for-all" if det_val in ("every", "all", "each", "chaque") else "exists"
            if n_bar:
                def find_noun(n_node):
                    for child in n_node.children:
                        if child.category == "N" and child.role == "head":
                            return get_label(child)
                        elif child.category == "N'" and child.role == "bar":
                            return find_noun(child)
                    return None
                noun_label = find_noun(n_bar)

        if quantifier and noun_label:
            subj_sexpr = "_"
        else:
            subj_sexpr = xbar_to_sexpr(subject_np, lang) if subject_np else ""

        # Canonicalize VP
        v_bar = None
        for child in vp_node.children:
            if child.category == "V'" and child.role == "bar":
                v_bar = child
        
        if not v_bar:
            raise ValueError("Invalid VP node: missing V' bar node.")

        verb_word = None
        arguments = []
        raw_verb_word = None
        
        def traverse_v_bar(v_node: XBarNode):
            nonlocal verb_word, raw_verb_word
            for child in v_node.children:
                if child.category == "V" and child.role == "head":
                    verb_word = get_label(child)
                    raw_verb_word = child.label
                elif child.category == "V'" and child.role == "bar":
                    traverse_v_bar(child)
                elif child.role in ("complement", "adjunct"):
                    arguments.append(xbar_to_sexpr(child, lang))

        traverse_v_bar(v_bar)

        if not verb_word:
            verb_word = "is"
            raw_verb_word = "is"

        pivot_verb = get_pivot_base_verb(raw_verb_word, lang)
        t1, t2, aspect = get_tense_vector(aux_words, raw_verb_word, lang)

        # Build sentence S-expression: (verb subject complements... tense_vector)
        if t2 == 0 and aspect == "simple":
            sentence_sexpr = [verb_word]
            if subj_sexpr:
                sentence_sexpr.append(subj_sexpr)
            sentence_sexpr.extend(arguments)
        else:
            sentence_sexpr = [pivot_verb]
            if subj_sexpr:
                sentence_sexpr.append(subj_sexpr)
            sentence_sexpr.extend(arguments)
            sentence_sexpr.append([t1, t2, aspect])

        modals = [w for w in aux_words if w not in TENSE_AUXILIARIES]
        if modals:
            modal_pivot = translate_word_from_pivot(modals[0], "en")
            sentence_sexpr = [modal_pivot, sentence_sexpr]
        
        if quantifier and noun_label:
            return [quantifier, noun_label, sentence_sexpr]
        
        return sentence_sexpr

    elif node.category == "VP":
        # VP has V' (bar)
        v_bar = None
        for child in node.children:
            if child.category == "V'" and child.role == "bar":
                v_bar = child
        if not v_bar:
            raise ValueError("Invalid VP node: missing V' bar node.")
        
        verb_word = None
        arguments = []
        raw_verb_word = None
        
        def traverse_v_bar(v_node: XBarNode):
            nonlocal verb_word, raw_verb_word
            for child in v_node.children:
                if child.category == "V" and child.role == "head":
                    verb_word = get_label(child)
                    raw_verb_word = child.label
                elif child.category == "V'" and child.role == "bar":
                    traverse_v_bar(child)
                elif child.role in ("complement", "adjunct"):
                    arguments.append(xbar_to_sexpr(child, lang))
                    
        traverse_v_bar(v_bar)
        if not verb_word:
            verb_word = "is"
            raw_verb_word = "is"
            
        pivot_verb = get_pivot_base_verb(raw_verb_word, lang)
        t1, t2, aspect = get_tense_vector([], raw_verb_word, lang)
        
        if t2 == 0 and aspect == "simple":
            return [verb_word, "_"] + arguments
        else:
            return [pivot_verb, "_"] + arguments + [[t1, t2, aspect]]

    elif node.category == "NP":
        # NP has optional Det (specifier) and N' (bar)
        det_word = None
        n_bar = None
        for child in node.children:
            if child.category == "Det" and child.role == "specifier":
                det_word = get_label(child)
            elif child.category == "N'" and child.role == "bar":
                n_bar = child

        if not n_bar:
            raise ValueError("Invalid NP node: missing N' bar node.")

        # Extract head noun, adjectives (adjuncts), and PP complements
        noun_word = None
        adjectives = []
        post_modifiers = []

        def traverse_n_bar(n_node: XBarNode):
            nonlocal noun_word
            for child in n_node.children:
                if child.category == "N" and child.role == "head":
                    noun_word = get_label(child)
                elif child.category == "N'" and child.role == "bar":
                    traverse_n_bar(child)
                elif child.category == "Adj" and child.role == "adjunct":
                    adjectives.append(get_label(child))
                elif child.role in ("complement", "adjunct"):
                    post_modifiers.append(xbar_to_sexpr(child, lang))

        traverse_n_bar(n_bar)

        if not noun_word:
            noun_word = "thing"

        # Build NP S-expression: (noun det adj1 adj2 ... pp_comps...)
        np_sexpr = [noun_word]
        if det_word:
            np_sexpr.append(det_word)
        np_sexpr.extend(adjectives)
        np_sexpr.extend(post_modifiers)

        return np_sexpr

    elif node.category == "PP":
        # PP has P'
        p_bar = None
        for child in node.children:
            if child.category == "P'" and child.role == "bar":
                p_bar = child

        if not p_bar:
            raise ValueError("Invalid PP node: missing P' bar node.")

        # Find head preposition P and complement NP
        p_head = None
        np_comp = None
        for child in p_bar.children:
            if child.category == "P" and child.role == "head":
                p_head = child
            elif child.category == "NP" and child.role == "complement":
                np_comp = child

        prep_word = get_label(p_head) if p_head else "at"
        np_sexpr = xbar_to_sexpr(np_comp, lang) if np_comp else []

        return [prep_word, np_sexpr]

    # Default fallback: recursively canonicalize all children
    if len(node.children) == 1:
        return xbar_to_sexpr(node.children[0], lang)
    return [xbar_to_sexpr(c, lang) for c in node.children]


def sexpr_to_xbar(expr: SExpr, lang: str = "en") -> XBarNode:
    """
    Translates a rotated Lisp S-expression back into an X-bar tree,
    with support for target language translation and syntactic ordering.
    """
    # Base Case: string terminal
    if isinstance(expr, str):
        # Translate leaf word from English pivot to target language
        translated = translate_word_from_pivot(expr, lang)
        
        # We can figure out its category by POS tag or context
        tags = tag_tokens([expr]) # Eng pivot tagging
        cat = tags[0][1] if tags else "N"
        role = "terminal"
        # If it represents a bare noun, we should promote it to NP to make it grammatically valid!
        if cat == "N":
            noun_node = XBarNode(category="N", role="head", label=translated)
            n_bar = XBarNode(category="N'", role="bar", children=[noun_node])
            return XBarNode(category="NP", role="phrase", children=[n_bar])
        return XBarNode(category=cat, role=role, label=translated)

    if not isinstance(expr, list) or len(expr) == 0:
        raise ValueError("Cannot translate empty or non-list expression to X-bar.")

    op = expr[0]
    if not isinstance(op, str):
        raise ValueError("Invalid S-expression: operator must be a string identifier.")

    if op == "frag":
        if len(expr) < 2:
            raise ValueError("Fragment expression requires an inner phrase expression.")
        inner_xbar = sexpr_to_xbar(expr[1], lang)
        inner_xbar.role = "complement"
        return XBarNode(category="FRAG", role="phrase", children=[inner_xbar])

    if op == "if":
        if len(expr) < 3:
            raise ValueError("Conditional expression requires condition and consequence arguments.")
        cond_node = sexpr_to_xbar(expr[1], lang)
        cons_node = sexpr_to_xbar(expr[2], lang)
        c_label = "si" if lang == "fr" else "if"
        c_head = XBarNode(category="C", role="head", label=c_label)
        cond_node.role = "complement"
        c_bar = XBarNode(category="C'", role="bar", children=[c_head, cond_node])
        cp_node = XBarNode(category="CP", role="phrase", children=[c_bar])
        cp_node.role = "adjunct"
        cons_node.role = "phrase"
        return XBarNode(category="IP", role="phrase", children=[cp_node, cons_node])

    if op in ("for-all", "exists"):
        if len(expr) < 3:
            raise ValueError(f"Quantifier expression '{op}' requires type and body arguments.")
        noun_word = translate_word_from_pivot(expr[1], lang)
        body_expr = expr[2]
        
        if op == "for-all":
            det_label = "chaque" if lang == "fr" else "every"
        else:
            det_label = "quelque" if lang == "fr" else "some"
            
        det_head = XBarNode(category="Det", role="specifier", label=det_label)
        noun_head = XBarNode(category="N", role="head", label=noun_word)
        n_bar = XBarNode(category="N'", role="bar", children=[noun_head])
        subject_np = XBarNode(category="NP", role="phrase", children=[det_head, n_bar])
        subject_np.role = "specifier"
        
        body_xbar = sexpr_to_xbar(body_expr, lang)
        body_xbar.role = "complement"
        
        i_label = "[pres/past]"
        if lang == "fr":
            from englisp.parser import find_head_verb
            head_verb = find_head_verb(body_xbar)
            if head_verb:
                from englisp.ontology import lookup_word
                head_verb_fr = lookup_word(head_verb, "fr")
                if head_verb_fr in ("chassé", "sauté"):
                    i_label = "a"
                
        i_head = XBarNode(category="I", role="head", label=i_label)
        i_bar = XBarNode(category="I'", role="bar", children=[i_head, body_xbar])
        
        return XBarNode(category="IP", role="phrase", children=[subject_np, i_bar])

    # Tag the English operator to determine its role (V = Sentence/IP, N = NP, P = PP, I = Modal Sentence)
    tags = tag_tokens([op])
    op_cat = tags[0][1] if tags else "N"

    if op_cat == "Conj":
        # Coordinate structure: ["and", left_expr, right_expr]
        if len(expr) < 3:
            raise ValueError(f"Conjunction expression '{op}' requires left and right arguments.")
        left_expr = expr[1]
        right_expr = expr[2]
        
        left_node = sexpr_to_xbar(left_expr, lang)
        right_node = sexpr_to_xbar(right_expr, lang)
        
        category = left_node.category
        conj_word = translate_word_from_pivot(op, lang)
        
        conj_head = XBarNode(category="Conj", role="head", label=conj_word)
        right_node.role = "complement"
        conj_bar = XBarNode(category="Conj'", role="bar", children=[conj_head, right_node])
        
        conjp_node = XBarNode(category="ConjP", role="phrase", children=[conj_bar])
        conjp_node.role = "adjunct"
        
        left_node.role = "phrase"
        
        return XBarNode(category=category, role="phrase", children=[left_node, conjp_node])

    elif op_cat == "C":
        # Complementizer / Relative Clause: ["that", ["chased", "_", ["cat", "the"]]]
        if len(expr) < 2:
            raise ValueError(f"Complementizer expression '{op}' requires a verb phrase argument.")
        
        c_word = "qui" if (lang == "fr" and op.lower() in ("that", "who", "which")) else translate_word_from_pivot(op, lang)
        vp_expr = expr[1]
        
        if not isinstance(vp_expr, list) or len(vp_expr) == 0:
            raise ValueError(f"Complementizer complement must be a non-empty verb phrase expression, got: {vp_expr}")

        # Check for modal wrapper
        modal_word = None
        if len(vp_expr) == 2 and isinstance(vp_expr[0], str) and vp_expr[0] not in ("for-all", "exists", "if", "and", "or", "not", "frag"):
            tags = tag_tokens([vp_expr[0]])
            if tags and tags[0][1] == "I":
                modal_word = translate_word_from_pivot(vp_expr[0], lang)
                vp_expr = vp_expr[1]

        verb_base = vp_expr[0]
        vp_args = vp_expr[2:] if (len(vp_expr) > 1 and vp_expr[1] == "_") else vp_expr[1:]
        
        # Check for tense vector at the end of vp_args
        tense_vector = None
        if vp_args and isinstance(vp_args[-1], list) and len(vp_args[-1]) == 3 and isinstance(vp_args[-1][0], int) and isinstance(vp_args[-1][1], int) and isinstance(vp_args[-1][2], str):
            tense_vector = vp_args[-1]
            vp_args = vp_args[:-1]

        # Determine verb_form and aux_list
        if tense_vector:
            t1, t2, aspect = tense_vector
            if lang == "fr":
                verb_fr_base = translate_word_from_pivot(verb_base, "fr")
                if t1 == 0 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "3sg")
                elif t1 == -1 and t2 == 0 and aspect == "simple":
                    aux_list = ["a"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "fut")
                elif t1 == 0 and t2 == 0 and aspect == "continuous":
                    aux_list = ["est", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == 0 and aspect == "continuous":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "imp")
                elif t1 == 1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["sera", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 0 and t2 == -1 and aspect == "simple":
                    aux_list = ["a"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == -1 and t2 == -1 and aspect == "simple":
                    aux_list = ["avait"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == -1 and aspect == "simple":
                    aux_list = ["aura"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 0 and t2 == -1 and aspect == "continuous":
                    aux_list = ["a", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["avait", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["aura", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                else:
                    aux_list = []
                    verb_form = translate_word_from_pivot(verb_base, "fr")
                if aux_list and aux_list[-1] == "de" and verb_form and verb_form.lower()[0] in "aeiouyéèàâêîôû":
                    aux_list[-1] = "d'"
            else:
                verb_en_base = verb_base
                if t1 == 0 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_english_verb(verb_en_base, "3sg")
                elif t1 == -1 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_english_verb(verb_en_base, "past")
                elif t1 == 1 and t2 == 0 and aspect == "simple":
                    aux_list = ["will"]
                    verb_form = verb_en_base
                elif t1 == 0 and t2 == 0 and aspect == "continuous":
                    aux_list = ["is"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == -1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["was"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["will", "be"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 0 and t2 == -1 and aspect == "simple":
                    aux_list = ["has"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == -1 and t2 == -1 and aspect == "simple":
                    aux_list = ["had"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == 1 and t2 == -1 and aspect == "simple":
                    aux_list = ["will", "have"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == 0 and t2 == -1 and aspect == "continuous":
                    aux_list = ["has", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == -1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["had", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["will", "have", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                else:
                    aux_list = []
                    verb_form = verb_base
        else:
            verb_form = translate_word_from_pivot(verb_base, lang)
            aux_list = []

        if modal_word:
            aux_list.insert(0, modal_word)

        # Reconstruct VP, ignoring the subject "_" if it is at index 1
        v_head = XBarNode(category="V", role="head", label=verb_form)
        vp_children = [v_head]
        for arg_expr in vp_args:
            arg_node = sexpr_to_xbar(arg_expr, lang)
            vp_children.append(arg_node)
            
        first_np_idx = -1
        for i, child in enumerate(vp_children[1:], start=1):
            if child.category == "NP":
                child.role = "complement"
                first_np_idx = i
                break
                
        if first_np_idx != -1:
            core_v_bar_children = [v_head, vp_children[first_np_idx]]
            v_bar = XBarNode(category="V'", role="bar", children=core_v_bar_children)
        else:
            v_bar = XBarNode(category="V'", role="bar", children=[v_head])
            
        for i, child in enumerate(vp_children[1:], start=1):
            if i == first_np_idx:
                continue
            if child.category == "PP":
                child.role = "adjunct"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
            elif child.category == "Adv":
                child.role = "adjunct"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
            else:
                child.role = "complement"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
                
        vp_phrase = XBarNode(category="VP", role="phrase", children=[v_bar])
        vp_phrase.role = "complement"
        
        c_head = XBarNode(category="C", role="head", label=c_word)
        
        if aux_list:
            # CP -> C' -> C IP (with empty/bound subject '_')
            subj_head = XBarNode(category="N", role="head", label="_")
            subj_nbar = XBarNode(category="N'", role="bar", children=[subj_head])
            subject_np = XBarNode(category="NP", role="specifier", children=[subj_nbar])
            subject_np.role = "specifier"
            
            i_children = [XBarNode(category="I", role="head", label=aux) for aux in aux_list]
            i_bar = XBarNode(category="I'", role="bar", children=i_children + [vp_phrase])
            ip_node = XBarNode(category="IP", role="phrase", children=[subject_np, i_bar])
            ip_node.role = "complement"
            
            c_bar = XBarNode(category="C'", role="bar", children=[c_head, ip_node])
        else:
            c_bar = XBarNode(category="C'", role="bar", children=[c_head, vp_phrase])
            
        return XBarNode(category="CP", role="phrase", children=[c_bar])

    elif op_cat == "I":
        # Modal/Inflection phrase wrapper: e.g., (can (chase (dog the) (cat the)))
        if len(expr) < 2:
            raise ValueError(f"Modal expression '{op}' requires a sentence body argument.")
        
        modal_word = translate_word_from_pivot(op, lang)
        body_expr = expr[1]

        # Parse body expression which is verb-first (like `(chase (dog the) (cat the))`)
        body_xbar = sexpr_to_xbar(body_expr, lang) # This will create an IP
        
        i_bar = None
        for child in body_xbar.children:
            if child.category == "I'" and child.role == "bar":
                i_bar = child
        
        if i_bar:
            modal_node = XBarNode(category="I", role="head", label=modal_word)
            if len(i_bar.children) > 1 and i_bar.children[0].label == "[pres/past]":
                i_bar.children = [modal_node] + i_bar.children[1:]
            else:
                new_children = [child for child in i_bar.children if child.label != "[pres/past]"]
                i_bar.children = [modal_node] + new_children
        
        return body_xbar

    elif op_cat == "V":
        # Verb operator => translates to IP (Sentence)
        # S-expression format: (verb subject complements/adjuncts...)
        
        if len(expr) < 2:
            raise ValueError(f"Verb expression '{op}' requires at least a subject argument.")
        
        subject_expr = expr[1]
        args = expr[2:]
        
        # Check for tense vector at the end of args
        tense_vector = None
        if args and isinstance(args[-1], list) and len(args[-1]) == 3 and isinstance(args[-1][0], int) and isinstance(args[-1][1], int) and isinstance(args[-1][2], str):
            tense_vector = args[-1]
            args = args[:-1]

        # Determine verb_form and aux_list
        if tense_vector:
            t1, t2, aspect = tense_vector
            if lang == "fr":
                verb_fr_base = translate_word_from_pivot(op, "fr")
                if t1 == 0 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "3sg")
                elif t1 == -1 and t2 == 0 and aspect == "simple":
                    aux_list = ["a"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "fut")
                elif t1 == 0 and t2 == 0 and aspect == "continuous":
                    aux_list = ["est", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == 0 and aspect == "continuous":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "imp")
                elif t1 == 1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["sera", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 0 and t2 == -1 and aspect == "simple":
                    aux_list = ["a"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == -1 and t2 == -1 and aspect == "simple":
                    aux_list = ["avait"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == -1 and aspect == "simple":
                    aux_list = ["aura"]
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 0 and t2 == -1 and aspect == "continuous":
                    aux_list = ["a", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["avait", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["aura", "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                else:
                    aux_list = []
                    verb_form = translate_word_from_pivot(op, "fr")
                if aux_list and aux_list[-1] == "de" and verb_form and verb_form.lower()[0] in "aeiouyéèàâêîôû":
                    aux_list[-1] = "d'"
            else:
                verb_en_base = op
                if t1 == 0 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_english_verb(verb_en_base, "3sg")
                elif t1 == -1 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_english_verb(verb_en_base, "past")
                elif t1 == 1 and t2 == 0 and aspect == "simple":
                    aux_list = ["will"]
                    verb_form = verb_en_base
                elif t1 == 0 and t2 == 0 and aspect == "continuous":
                    aux_list = ["is"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == -1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["was"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["will", "be"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 0 and t2 == -1 and aspect == "simple":
                    aux_list = ["has"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == -1 and t2 == -1 and aspect == "simple":
                    aux_list = ["had"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == 1 and t2 == -1 and aspect == "simple":
                    aux_list = ["will", "have"]
                    verb_form = inflect_english_verb(verb_en_base, "pp")
                elif t1 == 0 and t2 == -1 and aspect == "continuous":
                    aux_list = ["has", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == -1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["had", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                elif t1 == 1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["will", "have", "been"]
                    verb_form = inflect_english_verb(verb_en_base, "ing")
                else:
                    aux_list = []
                    verb_form = op
        else:
            verb_form = translate_word_from_pivot(op, lang)
            aux_list = []

        if subject_expr == "_":
            v_head = XBarNode(category="V", role="head", label=verb_form)
            vp_children = [v_head]
            for arg_expr in args:
                arg_node = sexpr_to_xbar(arg_expr, lang)
                vp_children.append(arg_node)
            first_np_idx = -1
            for i, child in enumerate(vp_children[1:], start=1):
                if child.category == "NP":
                    child.role = "complement"
                    first_np_idx = i
                    break
            if first_np_idx != -1:
                core_v_bar_children = [v_head, vp_children[first_np_idx]]
                v_bar = XBarNode(category="V'", role="bar", children=core_v_bar_children)
            else:
                v_bar = XBarNode(category="V'", role="bar", children=[v_head])
            for i, child in enumerate(vp_children[1:], start=1):
                if i == first_np_idx:
                    continue
                if child.category in ("PP", "Adv"):
                    child.role = "adjunct"
                    v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
                else:
                    child.role = "complement"
                    v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
            return XBarNode(category="VP", role="phrase", children=[v_bar])

        subject_np = sexpr_to_xbar(subject_expr, lang)
        subject_np.role = "specifier"

        # Reconstruct VP:
        v_head = XBarNode(category="V", role="head", label=verb_form)
        vp_children = [v_head]

        for arg_expr in args:
            arg_node = sexpr_to_xbar(arg_expr, lang)
            vp_children.append(arg_node)

        # Reconstruct V' bar
        first_np_idx = -1
        for i, child in enumerate(vp_children[1:], start=1):
            if child.category == "NP":
                child.role = "complement"
                first_np_idx = i
                break
        
        if first_np_idx != -1:
            core_v_bar_children = [v_head, vp_children[first_np_idx]]
            v_bar = XBarNode(category="V'", role="bar", children=core_v_bar_children)
        else:
            v_bar = XBarNode(category="V'", role="bar", children=[v_head])

        # Add remaining arguments as adjuncts or complements wrapping V'
        for i, child in enumerate(vp_children[1:], start=1):
            if i == first_np_idx:
                continue
            if child.category == "PP":
                child.role = "adjunct"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
            elif child.category == "Adv":
                child.role = "adjunct"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])
            else:
                child.role = "complement"
                v_bar = XBarNode(category="V'", role="bar", children=[v_bar, child])

        vp_phrase = XBarNode(category="VP", role="phrase", children=[v_bar])
        vp_phrase.role = "complement"

        # Reconstruct I' and IP
        if aux_list:
            i_children = [XBarNode(category="I", role="head", label=aux) for aux in aux_list]
        else:
            # Fallback helper for default passé composé
            i_label = "[pres/past]"
            verb_word_fr = verb_form
            if verb_form.startswith("v") and len(verb_form) > 1 and verb_form[1].isdigit():
                from englisp.ontology import lookup_word
                verb_word_fr = lookup_word(verb_form, "fr")
            if lang == "fr" and verb_word_fr in ("chassé", "sauté"):
                i_label = "a"
            i_children = [XBarNode(category="I", role="head", label=i_label)]
            
        i_bar = XBarNode(category="I'", role="bar", children=i_children + [vp_phrase])

        return XBarNode(category="IP", role="phrase", children=[subject_np, i_bar])

    elif op_cat == "N":
        # Noun operator => translates to NP
        # S-expression format: (noun det adj1 adj2 ... pp_comp ...)
        noun_word = translate_word_from_pivot(op, lang)
        noun_lookup_word = noun_word
        if noun_word.startswith("n") and len(noun_word) > 1 and noun_word[1].isdigit():
            from englisp.ontology import lookup_word
            noun_lookup_word = lookup_word(noun_word, "fr")
        gender = FRENCH_GENDER.get(noun_lookup_word, "M") if lang == "fr" else None

        det_node = None
        pre_adjectives = []
        post_adjectives = []
        post_modifiers = []

        for arg in expr[1:]:
            if isinstance(arg, str):
                if arg in ("the", "a", "an", "this", "that", "my", "your"):
                    det_label = translate_word_from_pivot(arg, lang, gender)
                    det_node = XBarNode(category="Det", role="specifier", label=det_label)
                else:
                    arg_tags = tag_tokens([arg])
                    arg_cat = arg_tags[0][1] if arg_tags else "N"
                    if arg_cat == "Det":
                        det_label = translate_word_from_pivot(arg, lang, gender)
                        det_node = XBarNode(category="Det", role="specifier", label=det_label)
                    elif arg_cat == "Adj":
                        adj_label = translate_word_from_pivot(arg, lang, gender)
                        adj_node = XBarNode(category="Adj", role="adjunct", label=adj_label)
                        if lang == "fr" and adj_label not in FRENCH_PRE_ADJECTIVES:
                            post_adjectives.append(adj_node)
                        else:
                            pre_adjectives.append(adj_node)
                    else:
                        adj_label = translate_word_from_pivot(arg, lang, gender)
                        adj_node = XBarNode(category="Adj", role="adjunct", label=adj_label)
                        if lang == "fr" and adj_label not in FRENCH_PRE_ADJECTIVES:
                            post_adjectives.append(adj_node)
                        else:
                            pre_adjectives.append(adj_node)
            else:
                # Nested list (PP/CP)
                child_xbar = sexpr_to_xbar(arg, lang)
                if child_xbar.category == "PP":
                    child_xbar.role = "complement"
                    post_modifiers.append(child_xbar)
                elif child_xbar.category == "CP":
                    child_xbar.role = "adjunct"
                    post_modifiers.append(child_xbar)
                else:
                    child_xbar.role = "adjunct"
                    post_modifiers.append(child_xbar)

        # Build N' starting with the noun head
        noun_head = XBarNode(category="N", role="head", label=noun_word)
        n_bar = XBarNode(category="N'", role="bar", children=[noun_head])

        # Attach French post-nominal adjectives
        for adj in post_adjectives:
            adj.role = "adjunct"
            n_bar = XBarNode(category="N'", role="bar", children=[n_bar, adj])

        # Attach post modifiers (PPs/CPs)
        for pm in post_modifiers:
            n_bar = XBarNode(category="N'", role="bar", children=[n_bar, pm])

        # Attach pre-nominal adjectives (nesting from right to left)
        for adj in reversed(pre_adjectives):
            adj.role = "adjunct"
            n_bar = XBarNode(category="N'", role="bar", children=[adj, n_bar])

        # NP Phrase node
        np_children = []
        if det_node:
            np_children.append(det_node)
        np_children.append(n_bar)

        return XBarNode(category="NP", role="phrase", children=np_children)

    elif op_cat == "P":
        # Preposition operator => translates to PP
        # S-expression format: (prep np_comp)
        prep_word = translate_word_from_pivot(op, lang)
        p_head = XBarNode(category="P", role="head", label=prep_word)

        if len(expr) < 2:
            raise ValueError(f"Preposition expression '{op}' requires an NP complement.")

        np_comp_expr = expr[1]
        np_comp = sexpr_to_xbar(np_comp_expr, lang)
        np_comp.role = "complement"

        p_bar = XBarNode(category="P'", role="bar", children=[p_head, np_comp])
        return XBarNode(category="PP", role="phrase", children=[p_bar])

    else:
        # Generic fallback
        generic_head = XBarNode(category=op_cat, role="head", label=translate_word_from_pivot(op, lang))
        children = [generic_head]
        for arg in expr[1:]:
            children.append(sexpr_to_xbar(arg, lang))
        return XBarNode(category=f"{op_cat}P", role="phrase", children=children)
