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

from typing import List, Union, Any, Optional, Tuple
from englisp.xbar import XBarNode
from englisp.parser import tag_tokens
from englisp.loader import (
    LEXICON, FRENCH_LEXICON, FRENCH_TO_ENGLISH_VOCAB, ENGLISH_TO_FRENCH_VOCAB,
    FRENCH_GENDER, FRENCH_ADJ_FEMININE, FRENCH_PRE_ADJECTIVES, TENSE_AUXILIARIES,
    ENGLISH_VERB_FORMS, FRENCH_VERB_FORMS, parse_sexpr, MORPHOLOGY_RULES
)

# A type representing a parsed S-Expression in Python (nested lists of strings)
SExpr = Union[str, List[Any]]

IRREGULAR_FRENCH_VERBS = {
    "être": {"1sg": "suis", "2sg": "es", "3sg": "est", "1pl": "sommes", "2pl": "êtes", "3pl": "sont", "imp": "était", "fut": "sera", "cond": "serait", "pp": "été", "inf": "être", "imp_pres": "sois"},
    "est": {"1sg": "suis", "2sg": "es", "3sg": "est", "1pl": "sommes", "2pl": "êtes", "3pl": "sont", "imp": "était", "fut": "sera", "cond": "serait", "pp": "été", "inf": "être", "imp_pres": "sois"},
    "suis": {"1sg": "suis", "2sg": "es", "3sg": "est", "1pl": "sommes", "2pl": "êtes", "3pl": "sont", "imp": "était", "fut": "sera", "cond": "serait", "pp": "été", "inf": "être", "imp_pres": "sois"},
    "avoir": {"1sg": "ai", "2sg": "as", "3sg": "a", "1pl": "avons", "2pl": "avez", "3pl": "ont", "imp": "avait", "fut": "aura", "cond": "aurait", "pp": "eu", "inf": "avoir", "imp_pres": "aie"},
    "a": {"1sg": "ai", "2sg": "as", "3sg": "a", "1pl": "avons", "2pl": "avez", "3pl": "ont", "imp": "avait", "fut": "aura", "cond": "aurait", "pp": "eu", "inf": "avoir", "imp_pres": "aie"},
    "vouloir": {"1sg": "veux", "2sg": "veux", "3sg": "veut", "1pl": "voulons", "2pl": "voulez", "3pl": "veulent", "imp": "voulait", "fut": "voudra", "cond": "voudrait", "pp": "voulu", "inf": "vouloir"},
    "pouvoir": {"1sg": "peux", "2sg": "peux", "3sg": "peut", "1pl": "pouvons", "2pl": "pouvez", "3pl": "peuvent", "imp": "pouvait", "fut": "pourra", "cond": "pourrait", "pp": "pu", "inf": "pouvoir"},
    "devoir": {"1sg": "dois", "2sg": "dois", "3sg": "doit", "1pl": "devons", "2pl": "devez", "3pl": "doivent", "imp": "devait", "fut": "devra", "cond": "devrait", "pp": "dû", "inf": "devoir"},
    "aller": {"1sg": "vais", "2sg": "vas", "3sg": "va", "1pl": "allons", "2pl": "allez", "3pl": "vont", "imp": "allait", "fut": "ira", "cond": "irait", "pp": "allé", "inf": "aller", "imp_pres": "va"},
    "venir": {"1sg": "viens", "2sg": "viens", "3sg": "vient", "1pl": "venons", "2pl": "venez", "3pl": "viennent", "imp": "venait", "fut": "viendra", "cond": "viendrait", "pp": "venu", "inf": "venir"},
    "faire": {"1sg": "fais", "2sg": "fais", "3sg": "fait", "1pl": "faisons", "2pl": "faites", "3pl": "font", "imp": "faisait", "fut": "fera", "cond": "ferait", "pp": "fait", "inf": "faire"},
    "dire": {"1sg": "dis", "2sg": "dis", "3sg": "dit", "1pl": "disons", "2pl": "dites", "3pl": "disent", "imp": "disait", "fut": "dira", "cond": "dirait", "pp": "dit", "inf": "dire"},
    "voir": {"1sg": "vois", "2sg": "vois", "3sg": "voit", "1pl": "voyons", "2pl": "voyez", "3pl": "voient", "imp": "voyait", "fut": "verra", "cond": "verrait", "pp": "vu", "inf": "voir"},
    "prendre": {"1sg": "prends", "2sg": "prends", "3sg": "prend", "1pl": "prenons", "2pl": "prenez", "3pl": "prennent", "imp": "prenait", "fut": "prendra", "cond": "prendrait", "pp": "pris", "inf": "prendre"},
    "savoir": {"1sg": "sais", "2sg": "sais", "3sg": "sait", "1pl": "savons", "2pl": "savez", "3pl": "savent", "imp": "savait", "fut": "saura", "cond": "saurait", "pp": "su", "inf": "savoir"},
    "dormir": {"1sg": "dors", "2sg": "dors", "3sg": "dort", "1pl": "dormons", "2pl": "dormez", "3pl": "dorment", "imp": "dormait", "fut": "dormira", "cond": "dormirait", "pp": "dormi", "inf": "dormir"},
    "partir": {"1sg": "pars", "2sg": "pars", "3sg": "part", "1pl": "partons", "2pl": "partez", "3pl": "partent", "imp": "partait", "fut": "partira", "cond": "partirait", "pp": "parti", "inf": "partir"},
    "entendre": {"1sg": "entends", "2sg": "entends", "3sg": "entend", "1pl": "entendons", "2pl": "entendez", "3pl": "entendent", "imp": "entendait", "fut": "entendra", "cond": "entendrait", "pp": "entendu", "inf": "entendre", "imp_pres": "entends"},
    "attendre": {"1sg": "attends", "2sg": "attends", "3sg": "attend", "1pl": "attendons", "2pl": "attendez", "3pl": "attendent", "imp": "attendait", "fut": "attendra", "cond": "attendrait", "pp": "attendu", "inf": "attendre", "imp_pres": "attends"},
    "courir": {"1sg": "cours", "2sg": "cours", "3sg": "court", "1pl": "courons", "2pl": "courez", "3pl": "courent", "imp": "courait", "fut": "courra", "cond": "courrait", "pp": "couru", "inf": "courir", "imp_pres": "cours"},
    "aider": {"1sg": "aide", "2sg": "aides", "3sg": "aide", "1pl": "aidons", "2pl": "aidez", "3pl": "aident", "imp": "aidait", "fut": "aidera", "cond": "aiderait", "pp": "aidé", "inf": "aider", "imp_pres": "aide"},
    "appeler": {"1sg": "appelle", "2sg": "appelles", "3sg": "appelle", "1pl": "appelons", "2pl": "appelez", "3pl": "appellent", "imp": "appelait", "fut": "appellera", "cond": "appellerait", "pp": "appelé", "inf": "appeler", "imp_pres": "appelle"},
}

def inflect_verb(base: str, form_type: str, lang: str) -> str:
    base = base.lower()
    # 1. Database forms lookup
    forms_dict = FRENCH_VERB_FORMS if lang == "fr" else ENGLISH_VERB_FORMS
    if lang == "fr":
        if base in IRREGULAR_FRENCH_VERBS and form_type in IRREGULAR_FRENCH_VERBS[base]:
            return IRREGULAR_FRENCH_VERBS[base][form_type]

    if base in forms_dict:
        forms = forms_dict[base]
        idx_map = {
            "fr": {"3sg": 0, "imp": 1, "fut": 2, "pp": 3, "inf": 4},
            "en": {"3sg": 0, "past": 1, "ing": 2, "pp": 3}
        }[lang]
        if form_type in idx_map:
            return forms[idx_map[form_type]]
        elif lang == "fr" and form_type == "3pl":
            if forms[0].endswith("e"):
                return forms[0] + "nt"
            return forms[0]
        elif lang == "fr" and form_type == "1sg":
            if forms[0].endswith("e"):
                return forms[0]
            elif forms[0].endswith(("t", "d")):
                return forms[0][:-1] + "s"
            return forms[0]
    
    # 2. General morphological rules (parameterized by lang)
    if lang == "en":
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
    elif lang == "fr":
        if base.endswith("er"):
            stem = base[:-2]
        elif base.endswith("e"):
            stem = base[:-1]
        elif base.endswith(("ir", "re")):
            stem = base[:-2]
        else:
            stem = base

        if form_type in ("3sg", "1sg"):
            return (stem + "e") if base.endswith("er") else stem
        elif form_type == "imp_pres":
            if base in ("va", "vas"):
                return "va"
            if base.endswith(("e", "é")):
                return base
            return (stem + "e") if base.endswith("er") else (stem + "s")
        elif form_type == "2sg":
            return (stem + "es") if base.endswith("er") else (stem + "s")
        elif form_type == "1pl":
            return stem + "ons"
        elif form_type == "2pl":
            return stem + "ez"
        elif form_type == "3pl":
            return stem + "ent"
        elif form_type == "pp":
            if base.endswith(("é", "i", "u", "s", "t")):
                return base
            return stem + "é"
        elif form_type == "inf":
            return base if base.endswith(("er", "ir", "re")) else stem + "er"
    return base

FRENCH_FUNCTION_WORDS_TO_ENGLISH = {
    # Subject and object pronouns
    "je": "i", "j'": "i", "moi": "me",
    "tu": "you", "toi": "you",
    "il": "he", "lui": "him",
    "elle": "she",
    "on": "one",
    "nous": "we",
    "vous": "you",
    "ils": "they", "eux": "them",
    "elles": "they",
    # Possessive determiners
    "mon": "my", "ma": "my", "mes": "my",
    "ton": "your", "ta": "your", "tes": "your",
    "son": "his", "sa": "her", "ses": "their",
    "notre": "our", "nos": "our",
    "votre": "your", "vos": "your",
    "leur": "their", "leurs": "their",
    # Prepositions
    "pour": "for",
    "avec": "with",
    "dans": "in",
    "sur": "over",
    "sous": "under",
    "sans": "without",
    "chez": "at",
    "par": "by",
    "vers": "toward",
    "contre": "against",
    "entre": "between",
    "pendant": "during",
    "devant": "before",
    "derrière": "behind",
    "depuis": "since",
    "de": "of", "d'": "of",
    "à": "to", "au": "to", "aux": "to",
    # Auxiliaries / Copula forms / Verbs
    "ont": "have",
    "a": "has",
    "ai": "have",
    "as": "have",
    "avons": "have",
    "avez": "have",
    "avait": "had",
    "avaient": "had",
    "aura": "will have",
    "auront": "will have",
    "eu": "had",
    "avoir": "have",
    "suis": "am",
    "es": "are",
    "est": "is",
    "sommes": "are",
    "êtes": "are",
    "sont": "are",
    "était": "was",
    "étaient": "were",
    "sera": "will be",
    "seront": "will be",
    "été": "been",
    "être": "be",
    # Common verbs
    "dort": "sleeps",
    "dorment": "sleep",
    "dormir": "sleep",
    "va": "goes",
    "vont": "go",
    "aller": "go",
    "fait": "makes",
    "font": "make",
    "faire": "make",
}

def get_base_verb(verb_word: str, lang: str) -> str:
    verb_word = verb_word.lower()
    if lang == "fr":
        if verb_word in ("ai", "as", "a", "avons", "avez", "ont", "avait", "avaient", "aura", "auront", "eu", "eut", "eurent", "avoir"):
            return "avoir"
        if verb_word in ("suis", "es", "est", "sommes", "êtes", "sont", "était", "étaient", "sera", "seront", "été", "être", "fus", "fut", "furent"):
            return "être"
    # Look up in database verb forms first
    forms_dict = FRENCH_VERB_FORMS if lang == "fr" else ENGLISH_VERB_FORMS
    for base, forms in forms_dict.items():
        if verb_word in forms or verb_word == base:
            return base
    # Fallback to rules in MORPHOLOGY_RULES
    rules = MORPHOLOGY_RULES.get(lang, {}).get("base_rules", [])
    for suffix, replacement in rules:
        if verb_word.endswith(suffix):
            return verb_word[:-len(suffix)] + replacement
    return verb_word

def inflect_english_verb(base: str, form_type: str) -> str:
    return inflect_verb(base, form_type, "en")

def inflect_french_verb(base: str, form_type: str) -> str:
    return inflect_verb(base, form_type, "fr")

def get_english_base_verb(verb_word: str) -> str:
    return get_base_verb(verb_word, "en")

def get_french_base_verb(verb_word: str) -> str:
    return get_base_verb(verb_word, "fr")

def get_pivot_base_verb(verb_word: str, lang: str) -> str:
    verb_word = verb_word.lower()
    if verb_word.startswith("v") and len(verb_word) > 1 and verb_word[1].isdigit():
        return verb_word
    if lang == "fr":
        if verb_word in ("ont", "a", "ai", "as", "avons", "avez", "avait", "avaient", "aura", "auront", "eu", "avoir"):
            return "have"
        if verb_word in ("suis", "es", "est", "sommes", "êtes", "sont", "était", "étaient", "sera", "seront", "été", "être"):
            return "be"
        if verb_word in FRENCH_FUNCTION_WORDS_TO_ENGLISH:
            en_trans = FRENCH_FUNCTION_WORDS_TO_ENGLISH[verb_word]
            return get_base_verb(en_trans, "en")
        fr_base = get_base_verb(verb_word, "fr")
        if fr_base in ("avoir", "a", "ont"):
            return "have"
        if fr_base in ("être", "est", "suis", "sont"):
            return "be"
        if fr_base in FRENCH_FUNCTION_WORDS_TO_ENGLISH:
            en_trans = FRENCH_FUNCTION_WORDS_TO_ENGLISH[fr_base]
            return get_base_verb(en_trans, "en")
        en_present = FRENCH_TO_ENGLISH_VOCAB.get(fr_base, fr_base)
        return get_base_verb(en_present, "en")
    else:
        return get_base_verb(verb_word, "en")

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

def is_plural_nominal(expr: Any) -> bool:
    """Checks whether an expression represents a plural nominal constituent."""
    if isinstance(expr, list) and len(expr) > 0:
        head = expr[0]
    elif isinstance(expr, str):
        head = expr
    else:
        return False
    if not isinstance(head, str):
        return False
    head_lower = head.lower()
    if head_lower in ("they", "we", "ils", "elles", "nous", "strawberries", "dogs", "cats"):
        return True
    if head_lower.endswith("s") and head_lower not in ("this", "its", "his", "us", "yes", "i"):
        return True
    return False

def is_1sg_nominal(expr: Any) -> bool:
    """Checks whether an expression represents a 1st person singular nominal constituent."""
    if isinstance(expr, list) and len(expr) > 0:
        head = expr[0]
    elif isinstance(expr, str):
        head = expr
    else:
        return False
    if not isinstance(head, str):
        return False
    return head.lower() in ("i", "je", "j'", "me", "moi")

def is_2sg_nominal(expr: Any) -> bool:
    """Checks whether an expression represents a 2nd person singular nominal constituent."""
    if isinstance(expr, list) and len(expr) > 0:
        head = expr[0]
    elif isinstance(expr, str):
        head = expr
    else:
        return False
    if not isinstance(head, str):
        return False
    return head.lower() in ("tu", "toi")

def is_1pl_nominal(expr: Any) -> bool:
    """Checks whether an expression represents a 1st person plural nominal constituent."""
    if isinstance(expr, list) and len(expr) > 0:
        head = expr[0]
    elif isinstance(expr, str):
        head = expr
    else:
        return False
    if not isinstance(head, str):
        return False
    return head.lower() in ("we", "nous")

def is_2pl_nominal(expr: Any) -> bool:
    """Checks whether an expression represents a 2nd person plural nominal constituent."""
    if isinstance(expr, list) and len(expr) > 0:
        head = expr[0]
    elif isinstance(expr, str):
        head = expr
    else:
        return False
    if not isinstance(head, str):
        return False
    return head.lower() in ("vous",)

VERBS_EN_TO_FR = {
    "have": "avoir", "has": "a", "had": "eu",
    "am": "suis", "is": "est", "are": "sont", "was": "était", "were": "étaient", "be": "être",
    "sleep": "dormir", "sleeps": "dort", "slept": "dormi",
    "love": "aimer", "loves": "aime", "loved": "aimé",
    "like": "aimer", "likes": "aime", "liked": "aimé",
    "hate": "détester", "hates": "déteste", "hated": "détesté",
    "want": "vouloir", "wants": "veut", "wanted": "voulu",
    "need": "avoir besoin de", "needs": "a besoin de", "needed": "eu besoin de",
    "know": "savoir", "knows": "sait", "knew": "su",
    "see": "voir", "sees": "voit", "saw": "vu",
    "run": "courir", "runs": "court", "ran": "couru",
    "eat": "manger", "eats": "mange", "ate": "mangé",
    "help": "aider", "helps": "aide", "helped": "aidé",
    "call": "appeler", "calls": "appelle", "called": "appelé",
    "stop": "arrêter", "stops": "arrête", "stopped": "arrêté",
    "wait": "attendre", "waits": "attend", "waited": "attendu",
    "fall": "tomber", "falls": "tombe", "fell": "tombé",
    "leave": "partir", "leaves": "part", "left": "parti",
    "go": "aller", "goes": "va", "went": "allé",
    "come": "venir", "comes": "vient", "came": "venu",
    "arrive": "arriver", "arrives": "arrive", "arrived": "arrivé",
    "try": "essayer", "tries": "essaye", "tried": "essayé",
    "win": "gagner", "wins": "gagne", "won": "gagné",
    "lose": "perdre", "loses": "perd", "lost": "perdu",
    "tell": "dire", "tells": "dit", "told": "dit",
    "say": "dire", "says": "dit", "said": "dit",
    "speak": "parler", "speaks": "parle", "spoke": "parlé",
    "talk": "parler", "talks": "parle", "talked": "parlé",
    "listen": "écouter", "listens": "écoute", "listened": "écouté",
    "look": "regarder", "looks": "regarde", "looked": "regardé",
    "read": "lire", "reads": "lit",
    "write": "écrire", "writes": "écrit", "wrote": "écrit",
    "find": "trouver", "finds": "trouve", "found": "trouvé",
    "give": "donner", "gives": "donne", "gave": "donné",
    "take": "prendre", "takes": "prend", "took": "pris",
    "understand": "comprendre", "understands": "comprend", "understood": "compris",
    "remember": "se rappeler", "remembers": "se rappelle", "remembered": "se rappelait",
    "feel": "se sentir", "feels": "se sent", "felt": "s'est senti",
    "become": "devenir", "becomes": "devient", "became": "devenu",
    "buy": "acheter", "buys": "achète", "bought": "acheté",
    "make": "faire", "makes": "fait", "made": "fait",
    "do": "faire", "does": "fait", "did": "fait",
    "quit": "arrêter", "quits": "arrête",
    "smoke": "fumer", "smokes": "fume", "smoked": "fumé",
    "peel": "éplucher", "peels": "épluche", "peeled": "épluché",
}

COMMON_WORDS_EN_TO_FR = {
    "friend": "ami", "friends": "amis",
    "boss": "patron", "brother": "frère", "sister": "sœur",
    "father": "père", "mother": "mère", "family": "famille",
    "doctor": "médecin", "camera": "appareil photo",
    "mathematics": "mathématiques", "math": "maths",
    "heat": "chaleur", "smoking": "fumer", "explanation": "explication",
    "week": "semaine", "month": "mois", "year": "an",
    "fruit": "fruit", "fruits": "fruits",
    "tie": "cravate", "mailbox": "boîte aux lettres",
    "birthday": "anniversaire", "movie": "film",
    "potatoes": "pommes de terre", "carrots": "carottes",
    "tea": "thé", "art": "art", "cpr": "rcp", "ice": "glace",
    "breakfast": "petit-déjeuner", "lunch": "déjeuner", "dinner": "dîner",
    "teacher": "professeur", "teachers": "professeurs",
    "student": "étudiant", "students": "étudiants",
    "school": "école", "library": "bibliothèque", "books": "livres",
    "paper": "papier", "china": "chine", "greece": "grèce",
    "fur": "fourrure", "luster": "splendeur", "wages": "salaire",
    "taxes": "impôts", "tax": "impôt", "opposition": "opposition",
    "bill": "texte de loi", "onions": "oignons", "onion": "oignon",
    "troops": "troupes", "enemy": "ennemi", "uncle": "oncle",
    "ticket": "billet", "tickets": "places de cinéma",
    "word": "mot", "words": "mots", "man": "homme", "men": "hommes",
    "son": "fils", "sons": "fils", "boy": "garçon", "boys": "garçons",
    "calm": "calme", "sad": "triste", "ready": "prêt", "happy": "heureux",
    "once": "une fois que"
}

FRENCH_UNACCUSATIVES = {
    "tomber", "partir", "aller", "venir", "arriver", "entrer", "sortir", 
    "mourir", "naître", "rester", "devenir", "revenir", "monter", "descendre",
    "fall", "leave", "go", "come", "arrive", "enter", "exit", "die", "stay", "become", "return"
}

def translate_word_from_pivot(word: str, target_lang: str, gender: Optional[str] = None, number: str = "singular", pos: Optional[str] = None) -> str:
    """Translates an English pivot word to the target language (e.g. French)."""
    if target_lang != "fr":
        return word
    word_lower = word.lower()
    
    # Handle Determiners based on gender and number
    if word_lower in ("the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their"):
        if number == "plural" or word_lower in ("these", "those"):
            if word_lower == "the":
                return "les"
            elif word_lower in ("a", "an"):
                return "des"
            elif word_lower in ("this", "that", "these", "those"):
                return "ces"
            elif word_lower == "my":
                return "mes"
            elif word_lower == "your":
                return "tes"
            elif word_lower in ("his", "her", "its"):
                return "ses"
            elif word_lower == "our":
                return "nos"
            elif word_lower == "their":
                return "leurs"
        else: # singular
            if word_lower == "the":
                return "la" if gender == "F" else "le"
            elif word_lower in ("a", "an"):
                return "une" if gender == "F" else "un"
            elif word_lower in ("this", "that"):
                return "cette" if gender == "F" else "ce"
            elif word_lower == "my":
                return "ma" if gender == "F" else "mon"
            elif word_lower == "your":
                return "ta" if gender == "F" else "ton"
            elif word_lower in ("his", "her", "its"):
                return "sa" if gender == "F" else "son"
            elif word_lower == "our":
                return "notre"
            elif word_lower == "their":
                return "leur"

    # Pronouns
    PRONOUNS_EN_TO_FR = {
        "i": "je",
        "you": "vous",
        "he": "il",
        "she": "elle",
        "it": "il",
        "we": "nous",
        "they": "ils",
        "me": "moi",
        "him": "lui",
        "them": "eux",
        "us": "nous",
    }
    if word_lower in PRONOUNS_EN_TO_FR:
        return PRONOUNS_EN_TO_FR[word_lower]

    # Prepositions
    PREPS_EN_TO_FR = {
        "for": "pour",
        "to": "à",
        "like": "comme",
        "with": "avec",
        "in": "dans",
        "on": "sur",
        "under": "sous",
        "over": "sur",
        "by": "par",
        "about": "environ",
        "from": "de",
        "of": "de",
        "at": "à",
        "between": "entre",
    }
    if word_lower in PREPS_EN_TO_FR:
        return PREPS_EN_TO_FR[word_lower]

    # Check translation vocabulary
    translated = None
    if pos == "V" and word_lower in VERBS_EN_TO_FR:
        translated = VERBS_EN_TO_FR[word_lower]
    elif word_lower in COMMON_WORDS_EN_TO_FR:
        translated = COMMON_WORDS_EN_TO_FR[word_lower]
    elif word_lower in VERBS_EN_TO_FR:
        translated = VERBS_EN_TO_FR[word_lower]

    if not translated:
        from englisp.loader import LEXICON
        is_verb = (LEXICON.get(word_lower) == "V") or (word_lower.endswith("s") and LEXICON.get(word_lower[:-1]) == "V")
        if not is_verb and word_lower.endswith("ies") and len(word_lower) > 3:
            stem_y = word_lower[:-3] + "y"
            if stem_y in ENGLISH_TO_FRENCH_VOCAB:
                translated = ENGLISH_TO_FRENCH_VOCAB[stem_y] + "s"
        elif not is_verb and word_lower.endswith("es") and len(word_lower) > 3:
            stem_e = word_lower[:-2]
            if stem_e in ENGLISH_TO_FRENCH_VOCAB:
                translated = ENGLISH_TO_FRENCH_VOCAB[stem_e] + "s"
        elif not is_verb and word_lower.endswith("s") and word_lower not in ("this", "its", "his", "their", "them", "us", "yes"):
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
            if lbl_lower in FRENCH_FUNCTION_WORDS_TO_ENGLISH:
                return FRENCH_FUNCTION_WORDS_TO_ENGLISH[lbl_lower]
            translated = None
            from englisp.loader import FRENCH_LEXICON
            is_verb = (FRENCH_LEXICON.get(lbl_lower) == "V") or (lbl_lower.endswith("s") and FRENCH_LEXICON.get(lbl_lower[:-1]) == "V")
            if not is_verb and lbl_lower.endswith(("s", "x")) and lbl_lower not in ("les", "des", "ses", "mes", "tes", "nos", "vos", "leurs"):
                singular = lbl_lower[:-1]
                if singular in FRENCH_FUNCTION_WORDS_TO_ENGLISH:
                    translated = FRENCH_FUNCTION_WORDS_TO_ENGLISH[singular] + "s"
                elif singular in FRENCH_TO_ENGLISH_VOCAB:
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
            if len(node.children) == 1 and node.children[0].category == "VP":
                vp_node = node.children[0]
            elif len(node.children) == 1 and node.children[0].category == "I'":
                i_bar = node.children[0]
            else:
                raise ValueError("Invalid IP node: missing I' bar node.")

        # Find I heads and VP complement inside I'
        aux_words = []
        is_negated = False
        if i_bar:
            for child in i_bar.children:
                if child.category == "I":
                    lbl = child.label
                    if lbl and not (lbl.startswith("[") and lbl.endswith("]")):
                        aux_words.append(lbl.lower())
                elif child.category == "Neg" or (child.label and child.label.lower() == "not"):
                    is_negated = True
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
        elif subject_np:
            subj_sexpr = xbar_to_sexpr(subject_np, lang)
        else:
            subj_sexpr = "_"
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

        modals = [w for w in aux_words if w not in TENSE_AUXILIARIES and w not in ("do", "does", "did")]
        if modals:
            modal_pivot = translate_word_from_pivot(modals[0], "en")
            sentence_sexpr = [modal_pivot, sentence_sexpr]
        
        if is_negated:
            sentence_sexpr = ["not", sentence_sexpr]

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
        arg1, arg2 = expr[1], expr[2]
        if isinstance(arg1, str) or (isinstance(arg1, list) and (len(arg1) == 0 or not isinstance(arg1[0], list)) and (isinstance(arg2, list) and len(arg2) > 0 and arg2[-1] == "_")):
            noun_raw = arg1
            body_expr = arg2
        else:
            noun_raw = arg2
            body_expr = arg1
        noun_str = noun_raw[0] if isinstance(noun_raw, list) else noun_raw
        noun_word = translate_word_from_pivot(noun_str, lang)
        
        if op == "for-all":
            det_label = "chaque" if lang == "fr" else "every"
        else:
            det_label = "quelque" if lang == "fr" else "some"
            
        det_head = XBarNode(category="Det", role="specifier", label=det_label)
        noun_head = XBarNode(category="N", role="head", label=noun_word)
        n_bar = XBarNode(category="N'", role="bar", children=[noun_head])
        subject_np = XBarNode(category="NP", role="phrase", children=[det_head, n_bar])
        subject_np.role = "specifier"
        
        if isinstance(body_expr, list) and len(body_expr) > 1 and body_expr[1] == "_":
            body_expr_eval = [body_expr[0], noun_str] + body_expr[2:]
            body_xbar_full = sexpr_to_xbar(body_expr_eval, lang)
            body_vp = None
            for child in body_xbar_full.children:
                if child.category == "I'":
                    for gc in child.children:
                        if gc.category == "VP":
                            body_vp = gc
                            break
            body_xbar = body_vp if body_vp else body_xbar_full
        else:
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

    if op == "not":
        if len(expr) < 2:
            raise ValueError("Negation expression requires a body argument.")
        body_node = sexpr_to_xbar(expr[1], lang)
        if lang == "fr":
            ne_node = XBarNode(category="Adv", role="adjunct", label="ne")
            pas_node = XBarNode(category="Adv", role="adjunct", label="pas")
            i_bar = None
            for child in body_node.children:
                if child.category == "I'" and child.role == "bar":
                    i_bar = child
            if i_bar and len(i_bar.children) > 0:
                first_head = i_bar.children[0]
                if first_head.category == "I" and not (first_head.label and first_head.label.startswith("[") and first_head.label.endswith("]")):
                    i_bar.children = [ne_node, first_head, pas_node] + i_bar.children[1:]
                else:
                    for c in i_bar.children:
                        if c.category == "VP" and len(c.children) > 0 and len(c.children[0].children) > 0:
                            v_bar = c.children[0]
                            v_head = v_bar.children[0]
                            v_bar.children = [ne_node, v_head, pas_node] + v_bar.children[1:]
                            break
        else:
            not_node = XBarNode(category="Adv", role="adjunct", label="not")
            i_bar = None
            for child in body_node.children:
                if child.category == "I'" and child.role == "bar":
                    i_bar = child
            if i_bar:
                i_bar.children.insert(1, not_node)
        return body_node

    # Tag the English operator to determine its role (V = Sentence/IP, N = NP, P = PP, I = Modal Sentence)
    tags = tag_tokens([op])
    op_cat = tags[0][1] if tags else "N"
    if op.lower() in ("can", "could", "should", "would", "might", "may", "must", "will", "shall", "cannot", "doesnt", "dont", "isnt", "hasnt", "havent", "wont", "wouldnt", "shouldnt", "couldnt"):
        op_cat = "I"
    elif op_cat in ("Conj", "C"):
        pass
    elif op_cat == "P" and len(expr) == 2:
        pass
    elif op.lower() in ("in", "on", "at", "to", "from", "with", "for", "by", "under", "over", "between", "like") and len(expr) == 2:
        op_cat = "P"
    elif op.lower() in VERBS_EN_TO_FR:
        op_cat = "V"
    elif len(expr) > 1 and op_cat not in ("Conj", "C", "P", "I"):
        first_arg = expr[1]
        is_pp = isinstance(first_arg, list) and len(first_arg) > 0 and isinstance(first_arg[0], str) and first_arg[0].lower() in ("in", "on", "at", "to", "from", "with", "for", "by", "under", "over", "between", "like")
        if not is_pp and (isinstance(first_arg, list) or (isinstance(first_arg, str) and first_arg.lower() in ("i", "you", "he", "she", "we", "they", "it", "_"))):
            op_cat = "V"

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
        
        if len(expr) == 1:
            subject_expr = "_"
            args = []
        else:
            subject_expr = expr[1]
            args = expr[2:]
        
        is_plural_subj = is_plural_nominal(subject_expr)
        is_1sg_subj = is_1sg_nominal(subject_expr)
        is_2sg_subj = is_2sg_nominal(subject_expr)
        is_1pl_subj = is_1pl_nominal(subject_expr)
        is_2pl_subj = is_2pl_nominal(subject_expr)

        # Check for tense vector at the end of args
        tense_vector = None
        if args and isinstance(args[-1], list) and len(args[-1]) == 3 and isinstance(args[-1][0], int) and isinstance(args[-1][1], int) and isinstance(args[-1][2], str):
            tense_vector = args[-1]
            args = args[:-1]

        # Determine verb_form and aux_list
        if tense_vector:
            t1, t2, aspect = tense_vector
            if lang == "fr":
                verb_fr_base = translate_word_from_pivot(op, "fr", pos="V")
                if t1 == 0 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    if is_1sg_subj:
                        verb_form = inflect_french_verb(verb_fr_base, "1sg")
                    elif is_2sg_subj:
                        verb_form = inflect_french_verb(verb_fr_base, "2sg")
                    elif is_1pl_subj:
                        verb_form = inflect_french_verb(verb_fr_base, "1pl")
                    elif is_2pl_subj:
                        verb_form = inflect_french_verb(verb_fr_base, "2pl")
                    elif is_plural_subj:
                        verb_form = inflect_french_verb(verb_fr_base, "3pl")
                    else:
                        verb_form = inflect_french_verb(verb_fr_base, "3sg")
                elif t1 == -1 and t2 == 0 and aspect == "simple":
                    is_unacc = op.lower() in FRENCH_UNACCUSATIVES or verb_fr_base.lower() in FRENCH_UNACCUSATIVES
                    if is_unacc:
                        aux_list = ["sont"] if is_plural_subj else (["suis"] if is_1sg_subj else (["sommes"] if is_1pl_subj else (["êtes"] if is_2pl_subj else (["es"] if is_2sg_subj else ["est"]))))
                    else:
                        aux_list = ["ont"] if is_plural_subj else (["ai"] if is_1sg_subj else (["avons"] if is_1pl_subj else (["avez"] if is_2pl_subj else (["as"] if is_2sg_subj else ["a"]))))
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == 0 and aspect == "simple":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "fut")
                elif t1 == 0 and t2 == 0 and aspect == "continuous":
                    aux_list = ["sont" if is_plural_subj else ("suis" if is_1sg_subj else "est"), "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == 0 and aspect == "continuous":
                    aux_list = []
                    verb_form = inflect_french_verb(verb_fr_base, "imp")
                elif t1 == 1 and t2 == 0 and aspect == "continuous":
                    aux_list = ["seront" if is_plural_subj else ("serai" if is_1sg_subj else "sera"), "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 0 and t2 == -1 and aspect == "simple":
                    aux_list = ["ont"] if is_plural_subj else (["ai"] if is_1sg_subj else ["a"])
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == -1 and t2 == -1 and aspect == "simple":
                    aux_list = ["avaient"] if is_plural_subj else (["avais"] if is_1sg_subj else ["avait"])
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 1 and t2 == -1 and aspect == "simple":
                    aux_list = ["auront"] if is_plural_subj else (["aurai"] if is_1sg_subj else ["aura"])
                    verb_form = inflect_french_verb(verb_fr_base, "pp")
                elif t1 == 0 and t2 == -1 and aspect == "continuous":
                    aux_list = ["ont" if is_plural_subj else ("ai" if is_1sg_subj else "a"), "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == -1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["avaient" if is_plural_subj else ("avais" if is_1sg_subj else "avait"), "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                elif t1 == 1 and t2 == -1 and aspect == "continuous":
                    aux_list = ["auront" if is_plural_subj else ("aurai" if is_1sg_subj else "aura"), "été", "en", "train", "de"]
                    verb_form = inflect_french_verb(verb_fr_base, "inf")
                else:
                    aux_list = []
                    verb_form = translate_word_from_pivot(op, "fr", pos="V")
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
            verb_form = translate_word_from_pivot(op, lang, pos="V")
            aux_list = []
            if lang == "fr":
                op_low = op.lower()
                is_past_form = op_low in ("fell", "left", "went", "came", "saw", "ate", "made", "bought", "won", "lost", "fixed", "tried", "met", "said", "promised", "slept") or op_low.endswith("ed")
                if is_past_form:
                    is_unacc = op_low in ("fell", "left", "went", "came") or op_low in FRENCH_UNACCUSATIVES or verb_form.lower() in FRENCH_UNACCUSATIVES
                    if is_unacc:
                        aux_list = ["sont"] if is_plural_subj else (["suis"] if is_1sg_subj else (["sommes"] if is_1pl_subj else (["êtes"] if is_2pl_subj else (["es"] if is_2sg_subj else ["est"]))))
                    else:
                        aux_list = ["ont"] if is_plural_subj else (["ai"] if is_1sg_subj else (["avons"] if is_1pl_subj else (["avez"] if is_2pl_subj else (["as"] if is_2sg_subj else ["a"]))))
                    verb_form = inflect_french_verb(verb_form, "pp")
                else:
                    if subject_expr == "_":
                        verb_form = IRREGULAR_FRENCH_VERBS.get(verb_form, {}).get("imp_pres") or inflect_french_verb(verb_form, "imp_pres")
                    elif is_1sg_subj:
                        verb_form = inflect_french_verb(verb_form, "1sg")
                    elif is_2sg_subj:
                        verb_form = inflect_french_verb(verb_form, "2sg")
                    elif is_1pl_subj:
                        verb_form = inflect_french_verb(verb_form, "1pl")
                    elif is_2pl_subj:
                        verb_form = inflect_french_verb(verb_form, "2pl")
                    elif is_plural_subj:
                        verb_form = inflect_french_verb(verb_form, "3pl")
                    else:
                        verb_form = inflect_french_verb(verb_form, "3sg")

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

        # Check for French clitic object movement
        clitic_node = None
        if lang == "fr" and subject_expr != "_":
            FRENCH_PRONOUN_CLITICS = {
                "you": "te", "him": "le", "her": "la", "it": "le", "them": "les", "us": "nous", "me": "me",
                "vous": "vous", "te": "te", "le": "le", "la": "la", "les": "les", "nous": "nous",
                "lui": "le", "elle": "la", "eux": "les", "moi": "me", "toi": "te", "leur": "les"
            }
            clitic_idx = -1
            for i, child in enumerate(vp_children[1:], start=1):
                if child.category == "NP":
                    # An NP with a determiner (e.g. 'le livre') is a full noun phrase, not a clitic pronoun!
                    has_det = any(c.category == "Det" for c in child.children)
                    if has_det:
                        continue
                    head_noun = ""
                    for desc in child.children:
                        if desc.category == "N'" and desc.children:
                            for c in desc.children:
                                if c.category in ("N", "Pron") and c.label:
                                    head_noun = c.label.lower()
                                    break
                    if not head_noun and child.children:
                        for c in child.children:
                            if c.category in ("N", "Pron") and c.label:
                                head_noun = c.label.lower()
                                break
                    if head_noun in FRENCH_PRONOUN_CLITICS:
                        clitic_label = FRENCH_PRONOUN_CLITICS[head_noun]
                        clitic_node = XBarNode(category="Clitic", role="adjunct", label=clitic_label)
                        clitic_idx = i
                        break
            if clitic_idx != -1:
                vp_children.pop(clitic_idx)

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

        if clitic_node:
            if aux_list:
                aux_list.insert(0, clitic_node.label)
            else:
                v_bar.children = [clitic_node] + v_bar.children

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
                i_label = "ont" if is_plural_subj else ("ai" if is_1sg_subj else "a")
            i_children = [XBarNode(category="I", role="head", label=i_label)]
            
        i_bar = XBarNode(category="I'", role="bar", children=i_children + [vp_phrase])

        return XBarNode(category="IP", role="phrase", children=[subject_np, i_bar])

    elif op_cat == "N":
        # Noun operator => translates to NP
        # S-expression format: (noun det adj1 adj2 ... pp_comp ...)
        is_plural = is_plural_nominal(op)
        number = "plural" if is_plural else "singular"
        noun_word = translate_word_from_pivot(op, lang, number=number)
        noun_lookup_word = noun_word
        if noun_word.startswith("n") and len(noun_word) > 1 and noun_word[1].isdigit():
            from englisp.ontology import lookup_word
            noun_lookup_word = lookup_word(noun_word, "fr")
        gender = FRENCH_GENDER.get(noun_lookup_word)
        if not gender and noun_lookup_word.endswith("s"):
            gender = FRENCH_GENDER.get(noun_lookup_word[:-1])
        if not gender:
            gender = "M" if lang == "fr" else None

        from englisp.parser import PRONOUN_LEXICON
        is_pronoun = op.lower() in PRONOUN_LEXICON

        det_node = None
        pre_adjectives = []
        post_adjectives = []
        post_modifiers = []

        DETERMINER_WORDS = ("the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their")

        for arg in expr[1:]:
            if isinstance(arg, str):
                arg_lower = arg.lower()
                if not is_pronoun and arg_lower in DETERMINER_WORDS:
                    det_label = translate_word_from_pivot(arg, lang, gender, number=number)
                    det_node = XBarNode(category="Det", role="specifier", label=det_label)
                else:
                    arg_tags = tag_tokens([arg])
                    arg_cat = arg_tags[0][1] if arg_tags else "N"
                    if not is_pronoun and arg_cat == "Det":
                        det_label = translate_word_from_pivot(arg, lang, gender, number=number)
                        det_node = XBarNode(category="Det", role="specifier", label=det_label)
                    elif arg_cat == "Adj":
                        adj_label = translate_word_from_pivot(arg, lang, gender, number=number)
                        adj_node = XBarNode(category="Adj", role="adjunct", label=adj_label)
                        if lang == "fr" and adj_label not in FRENCH_PRE_ADJECTIVES:
                            post_adjectives.append(adj_node)
                        else:
                            pre_adjectives.append(adj_node)
                    else:
                        adj_label = translate_word_from_pivot(arg, lang, gender, number=number)
                        adj_node = XBarNode(category="Adj", role="adjunct", label=adj_label)
                        if lang == "fr" and adj_label not in FRENCH_PRE_ADJECTIVES:
                            post_adjectives.append(adj_node)
                        else:
                            pre_adjectives.append(adj_node)
            else:
                # Nested list (PP/CP/NP)
                child_xbar = sexpr_to_xbar(arg, lang)
                if child_xbar.category == "PP":
                    child_xbar.role = "complement"
                    post_modifiers.append(child_xbar)
                elif child_xbar.category == "CP":
                    child_xbar.role = "adjunct"
                    post_modifiers.append(child_xbar)
                elif child_xbar.category == "NP" and lang == "fr":
                    de_head = XBarNode(category="P", role="head", label="de")
                    child_xbar.role = "complement"
                    p_bar = XBarNode(category="P'", role="bar", children=[de_head, child_xbar])
                    pp_node = XBarNode(category="PP", role="phrase", children=[p_bar])
                    pp_node.role = "complement"
                    post_modifiers.append(pp_node)
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
        is_infinitive = (
            noun_word.endswith(("er", "ir", "re", "oir")) and
            noun_word not in ("hiver", "mer", "fer", "soir", "espoir", "livre", "lettre", "arbre", "chambre", "cadre", "ordre", "verre", "pierre", "terre")
        )
        np_children = []
        if det_node:
            np_children.append(det_node)
        elif not is_pronoun and not is_infinitive and lang == "fr":
            det_label = "les" if is_plural else ("la" if gender == "F" else "le")
            np_children.append(XBarNode(category="Det", role="specifier", label=det_label))
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
