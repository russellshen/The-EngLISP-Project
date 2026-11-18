#!/usr/bin/env python3
"""
EngLISP Bidirectional Translation Pipeline: English -> MinimaLIST -> French
============================================================================
Translates an input CSV file containing natural language sentences into
French translations generated via the unified EngLISP bidirectional pipeline:
  English Natural Language (Stage 1)
       ↕ T1: Parsing
  X-bar Syntax Tree (Stage 2)
       ↕ T2: Rotation / Canonicalization
  EngLISP S-Expression (Stage 3)
       ↕ T3: Semantic Minimization
  MinimaLIST Canonical Form (Stage 4, Language-Independent Interlingua)
       ↕ T3: Lexical Expansion (Target: French)
  EngLISP S-Expression (Stage 3)
       ↕ T2: French X-bar Reconstruction
  French X-bar Tree (Stage 2)
       ↕ T1: Text Synthesis & Elision
  French Natural Language (Stage 1)
"""

import sys
import os
import csv
import argparse

# Ensure local project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from englisp.loader import CURRENT_USER_TIER
from englisp import nl_to_minimalist, minimalist_to_nl

# Activate paid tier to enable full 100k+ lexical databases
CURRENT_USER_TIER.set("paid")


def translate_sentence_through_englisp(sentence: str, target_lang: str = "fr") -> str:
    """
    Translates natural language text using the unified EngLISP bidirectional pipeline:
      1. Forward: NL -> Language-independent MinimaLIST IR
      2. Reverse: MinimaLIST IR -> Target Language NL (parameterized by target_lang)
    """
    cleaned = sentence.strip()
    if not cleaned:
        return ""
    
    # Forward operation: NL -> Canonical MinimaLIST (Language-independent interlingua)
    minima = nl_to_minimalist(cleaned)
    
    # Reverse operation: Canonical MinimaLIST -> Target Language NL
    translated = minimalist_to_nl(minima, lang=target_lang)
    
    # Ensure capitalization and terminal punctuation
    if translated:
        translated = translated[0].upper() + translated[1:]
        if translated[-1] not in ".!?":
            translated += "."
    return translated


def process_csv(input_path: str, output_path: str, header_col: str = "french", target_lang: str = "fr"):
    print(f"[*] Reading input CSV from: {input_path}")
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"[*] Loaded {len(rows)} sentences. Beginning translation...")
    
    out_col = header_col if header_col else fieldnames[1]
    output_rows = []
    
    for idx, r in enumerate(rows, start=1):
        sid = r["id"]
        src_text = r[fieldnames[1]]
        
        try:
            translated_text = translate_sentence_through_englisp(src_text, target_lang=target_lang)
        except Exception as e:
            translated_text = f"ERROR: {e}"
        
        output_rows.append({
            "id": sid,
            out_col: translated_text
        })
        
        if idx % 20 == 0 or idx == len(rows):
            print(f"[{idx}/{len(rows)}] Processed {sid}: {src_text[:40]}... -> {translated_text[:40]}...")

    print(f"[*] Writing translations to: {output_path}")
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
    arg_parser.add_argument("--lang", default="fr", help="Target language for expansion (default: 'fr')")
    args = arg_parser.parse_args()

    process_csv(args.input_csv, args.output_csv, header_col=args.header, target_lang=args.lang)
