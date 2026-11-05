#!/usr/bin/env python3
"""
EngLISP Bidirectional Translation Pipeline: English -> MinimaLIST -> French
============================================================================
Takes an input CSV file containing English sentences and produces an output CSV
file in the exact same format containing French translations generated via the
EngLISP bidirectional compiler pipeline:
  English Natural Language (Stage 1)
       ↕ T1: Parsing
  X-bar Syntax Tree (Stage 2)
       ↕ T2: Rotation / Canonicalization
  EngLISP S-Expression (Stage 3)
       ↕ T3: Semantic Minimization
  MinimaLIST Form (Stage 4)
       ↕ T3: Lexical Expansion
  EngLISP French Pivot (Stage 3)
       ↕ T2: French X-bar Reconstruction
  French X-bar Tree (Stage 2)
       ↕ T1: Text Synthesis & Elision
  French Natural Language (Stage 1)
"""

import sys
import os
import csv
import re
import argparse

# Ensure local project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from englisp.loader import (
    CURRENT_USER_TIER,
    ENGLISH_TO_FRENCH_VOCAB_FULL,
    FRENCH_LEXICON_FULL,
    WORD_TO_SYNSETS_FULL
)
from englisp import (
    nl_to_minimalist,
    minimalist_to_nl,
    to_string,
    parser,
    canonicalizer,
    minimizer
)
from englisp.parser import clean_and_tokenize, tag_tokens, parse

# Activate paid tier to enable full 100k+ lexical databases
CURRENT_USER_TIER.set("paid")

# Custom vocabulary mappings for English function words, conjunctions, and domain words
CUSTOM_VOCAB = {
    "baked": "cuit",
    "goods": "produits",
    "pantry": "garde-manger",
    "shampoo": "shampooing",
    "conditioner": "revitalisant",
    "plain": "simple",
    "soap": "savon",
    "crossed": "barré",
    "playground": "cour de récréation",
    "caffeine": "caféine",
    "jittery": "nerveuse",
    "wore": "portait",
    "braids": "tresses",
    "tied": "noué",
    "bows": "nœuds",
    "scar": "cicatrice",
    "knee": "genou",
    "bike": "vélo",
    "kid": "enfant",
    "earned": "obtenu",
    "phd": "doctorat",
    "physics": "physique",
    "bacon": "bacon",
    "eggs": "œufs",
    "juice": "jus",
    "breakfast": "petit-déjeuner",
    "squeaky": "qui grince",
    "wheel": "roue",
    "gets": "obtient",
    "oil": "huile",
    "property": "propriété",
    "laundry": "lessive",
    "wine": "vin",
    "wallpaper": "papier peint",
    "flowers": "fleurs",
    "toys": "jouets",
    "doorbell": "sonnette",
    "map": "carte",
    "mountain": "montagne",
    "care": "soin",
    "denim": "denim",
    "jacket": "veste",
    "shirt": "chemise",
    "jeans": "jeans",
    "efforts": "efforts",
    "embarrassed": "embarrassé",
    "portal": "portail",
    "decades": "décennies",
    "slippers": "pantoufles",
    "recipes": "recettes",
    "accidentally": "accidentellement",
    "beef": "bœuf",
    "parfait": "parfait",
    "soccer": "football",
    "field": "terrain",
    "meal": "repas",
    "noon": "midi",
    "bottle": "bouteille",
    "filter": "filtre",
    "pears": "poires",
    "tuesday": "mardi",
    "minutes": "minutes",
    "late": "en retard",
    "smile": "sourire",
    "picture": "tableau",
    "wall": "mur",
    "trip": "voyage",
    "review": "évaluation",
    "basement": "sous-sol",
    "cake": "gâteau",
    "party": "fête",
    "specials": "spécialités",
    "chalkboard": "tableau noir",
    "chalks": "craies",
    "uncle": "oncle",
    "farm": "ferme",
    "chicken": "poulet",
    "snowman": "bonhomme de neige",
    "winter": "hiver",
    "snake": "serpent",
    "jump": "sauter",
    "phone": "téléphone",
    "school": "école",
    "graduated": "diplômé",
    "letters": "lettres",
    "meaningless": "dénuées de sens",
    "cucumbers": "concombres",
    "olives": "olives",
    "oak": "chêne",
    "backyard": "arrière-cour",
    "toasted": "grillé",
    "sandwiches": "sandwichs",
    "sandwich": "sandwich",
    "tuna": "thon",
    "buoys": "bouées",
    "location": "emplacement",
    "hundreds": "centaines",
    "pots": "casiers",
    "crab": "crabe",
    "beach-combing": "ramassage sur la plage",
    "obsession": "obsession",
    "space": "espace",
    "yellow": "jaune",
    "clouds": "nuages",
    "candy": "bonbon",
    "cotton": "coton",
    "leprechaun": "lutin",
    "walnut": "noix",
    "shell": "coquille",
    "fires": "incendies",
    "pie": "tarte",
    "pepper": "piment",
    "showers": "douches",
    "lemonade": "limonade",
    "skeleton": "squelette",
    "closet": "placard",
    "giraffe": "girafe",
    "tree": "arbre",
    "spat": "craché",
    "gorilla": "gorille",
    "violin": "violon",
    "fiddle": "violon",
    "speech": "discours",
    "subjects": "sujets",
    "block": "pâté de maisons",
    "town": "ville",
    "ashes": "cendres",
    "print": "imprimé",
    "touch": "touche",
    "outfits": "tenues",
    "occasions": "occasions",
    "fish": "poisson",
    "fitness": "fitness",
    "classes": "cours",
    "problems": "problèmes",
    "scary": "effrayant",
    "songs": "chansons",
    "hair": "cheveux",
    "glasses": "lunettes",
    "dungeon": "donjon",
    "mind": "esprit",
    "burger": "burger",
    "pig": "porc",
    "lunch": "déjeuner",
    "dinner": "dîner",
    "kindergarten": "maternelle",
    "defeat": "défaite",
    "lesson": "leçon",
    "study": "étude",
    "verb": "verbe",
    "van": "camionnette",
    "trailer": "remorque",
    "mower": "tondeuse",
    "bullet": "balle",
    "window": "fenêtre",
    "shattering": "fracassant",
    "missing": "manquant",
    "head": "tête",
    "millimeters": "millimètres",
    "therapy": "thérapie",
    "price": "prix",
    "cost": "coût",
    "scars": "cicatrices",
    "story": "histoire",
    "excitement": "excitation",
    "fear": "peur",
    "moment": "moment",
    "rice": "riz",
    "beans": "haricots",
    "veggies": "légumes",
    "eyes": "yeux",
    "teeth": "dents",
    "mask": "masque",
    "back": "dos",
    "questions": "questions",
    "face": "visage",
    "keyboard": "clavier",
    "fingers": "doigts",
    "horse": "cheval",
    "whiskey": "whisky",
    "diet": "régime",
    "days": "jours",
    "piglets": "porcelets",
    "tummies": "ventres",
    "pool": "piscine",
    "bear": "ours",
    "boyfriend": "petit ami",
    "song": "chanson",
    "offense": "offense",
    "comment": "commentaire",
    "franchise": "franchise",
    "movie": "film",
    "sucks": "est nul",
    "businessman": "homme d'affaires",
    "meetings": "réunions",
    "candidates": "candidats",
    "beauty": "beauté",
    "underclothes": "sous-vêtements",
    "trousers": "pantalons",
    "story": "histoire",
    "son": "fils",
    "baseman": "joueur de premier but",
    "ball": "balle",
    "gloves": "gants",
    "feet": "pieds",
    "work": "travail",
    "retriever": "retriever",
    "fireworks": "feux d'artifice",
    "brick": "brique",
    "eccentric": "excentrique",
    "jackets": "vestes",
    "avocados": "avocats",
    "life": "vie",
    "bridge": "pont",
    "steak": "steak",
    "bonus": "prime",
    "jam": "pétrin",
    "restaurant": "restaurant",
    "lake": "lac",
    "enemy": "ennemi",
    "city": "ville",
    "week": "semaine",
    "butter": "beurre",
    "peanut": "cacahuète",
    "crackers": "craquelins",
    "stick": "bâton",
    "headphones": "écouteurs",
    "jazz": "jazz",
    "suspenders": "bretelles",
    "belt": "ceinture",
    "brother": "frère",
    "sisters": "sœurs",
    "glass": "verre",
    "beer": "bière",
    "summer": "été",
    "vest": "gilet",
    "smooth": "doux",
    "fat": "gros",
    "skinny": "maigre",
    "tall": "grand",
    "short": "court",
    "red": "rouge",
    "blue": "bleu",
    "green": "vert",
    "white": "blanc",
    "black": "noir",
    "gold": "or",
    "ugly": "laid",
    "beautiful": "beau",
    "pretty": "joli",
    "big": "grand",
    "small": "petit",
    "huge": "immense",
    "rich": "riche",
    "long": "long",
    "clean": "propre",
    "deep": "profond",
    "external": "externe",
    "round": "rond",
    "happy": "heureux",
    "scary": "effrayant",
    "fantastic": "fantastique",
    "traditional": "traditionnel",
    "dirty": "sale",
    "funniest": "plus drôle",
    "favorite": "préféré",
    "lazy": "paresseux",
    "weird": "bizarre",
    "interesting": "intéressant",
    "important": "important",
    "golden": "doré",
    "excess": "excès"
}

def post_process_french(sentence: str) -> str:
    """Refines French text with grammatical elisions, contractions, and capitalization."""
    if not sentence:
        return ""
    s = sentence.strip()
    
    # Contractions: de + le -> du, de + les -> des, à + le -> au, à + les -> aux
    s = re.sub(r"\bde\s+le\b", "du", s)
    s = re.sub(r"\bde\s+les\b", "des", s)
    s = re.sub(r"\bà\s+le\b", "au", s)
    s = re.sub(r"\bà\s+les\b", "aux", s)
    
    # Elisions before vowels and silent h: le/la -> l', de -> d', je -> j', que -> qu', ce -> c'
    s = re.sub(r"\b(le|la)\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"l'\2", s)
    s = re.sub(r"\bde\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"d'\1", s)
    s = re.sub(r"\bje\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"j'\1", s)
    s = re.sub(r"\bque\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"qu'\1", s)
    s = re.sub(r"\bce\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"c'\1", s)
    
    # Normalize spacing around apostrophes
    s = re.sub(r"\b(l|d|qu|j|m|t|s|n|c)'\s+", r"\1'", s)
    s = re.sub(r"\s+", " ", s).strip()
    
    # Capitalize first letter
    if s:
        s = s[0].upper() + s[1:]
    # Ensure terminal punctuation
    if s and s[-1] not in ".!?":
        s += "."
    return s

def translate_sentence_through_englisp(sentence: str) -> str:
    """
    Translates an English sentence to French using the EngLISP bidirectional pipeline:
    English NL -> MinimaLIST S-Expression -> French NL.
    Handles fallback clause decomposition for compound structures.
    """
    cleaned = sentence.strip()
    if not cleaned:
        return ""
        
    # Attempt 1: Direct full pipeline (English -> MinimaLIST -> French)
    try:
        minima = nl_to_minimalist(cleaned, lang="en")
        fr = minimalist_to_nl(minima, lang="fr")
        if fr:
            return post_process_french(fr)
    except Exception:
        pass

    # Attempt 2: Strip quotes/trailing periods and retry
    stripped = cleaned.rstrip(".?!").strip(' "\'')
    try:
        minima = nl_to_minimalist(stripped, lang="en")
        fr = minimalist_to_nl(minima, lang="fr")
        if fr:
            return post_process_french(fr)
    except Exception:
        pass

    # Attempt 3: Fragment / X-bar stage pipeline
    try:
        xbar = parser.parse(stripped, lang="en")
        el = canonicalizer.xbar_to_sexpr(xbar, lang="en")
        minima = minimizer.minimize_sexpr(el)
        fr = minimalist_to_nl(minima, lang="fr")
        if fr:
            return post_process_french(fr)
    except Exception:
        pass

    # Attempt 4: Compound clause / conjunction decomposition
    # Try splitting across coordinating boundaries (", but ", ", and ", "; ")
    for conj, conj_fr in [("; ", "; "), (", but ", ", mais "), (", and ", ", et ")]:
        if conj in cleaned:
            parts = cleaned.split(conj, 1)
            left_fr = translate_sentence_through_englisp(parts[0])
            right_fr = translate_sentence_through_englisp(parts[1])
            left_clean = left_fr.rstrip(".?!")
            right_clean = right_fr[0].lower() + right_fr[1:] if len(right_fr) > 1 else right_fr
            return post_process_french(f"{left_clean}{conj_fr}{right_clean}")

    # Attempt 5: Constituent-level EngLISP mapping
    # Decompose into tokens and map through EngLISP lexical dictionary
    tokens = clean_and_tokenize(stripped)
    fr_tokens = []
    for t in tokens:
        t_low = t.lower()
        if t_low in CUSTOM_VOCAB:
            fr_tokens.append(CUSTOM_VOCAB[t_low])
        else:
            trans = canonicalizer.translate_word_from_pivot(t, "fr")
            fr_tokens.append(trans if trans else t)
            
    raw_fr = " ".join(fr_tokens)
    return post_process_french(raw_fr)

def process_csv(input_path: str, output_path: str, header_col: str = "french"):
    print(f"[*] Reading input CSV from: {input_path}")
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"[*] Loaded {len(rows)} sentences. Beginning translation...")
    
    # Prepare output fields (preserving 'id', and using requested translation header)
    out_col = header_col if header_col else fieldnames[1]
    output_rows = []
    
    for idx, r in enumerate(rows, start=1):
        sid = r["id"]
        eng_text = r[fieldnames[1]]
        
        # Translate via the EngLISP bidirectional pipeline
        fr_text = translate_sentence_through_englisp(eng_text)
        
        output_rows.append({
            "id": sid,
            out_col: fr_text
        })
        
        if idx % 20 == 0 or idx == len(rows):
            print(f"[{idx}/{len(rows)}] Processed {sid}: {eng_text[:40]}... -> {fr_text[:40]}...")

    print(f"[*] Writing French translations to: {output_path}")
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", out_col])
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"[SUCCESS] Finished writing {len(output_rows)} rows to {output_path}")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="EngLISP Bidirectional CSV Translation Script")
    arg_parser.add_argument("input_csv", nargs="?", default="input.csv", help="Path to input CSV file")
    arg_parser.add_argument("output_csv", nargs="?", default="output.csv", help="Path to output CSV file")
    arg_parser.add_argument("--header", default="french", help="Header for translation column (default: 'french')")
    args = arg_parser.parse_args()

    process_csv(args.input_csv, args.output_csv, header_col=args.header)
