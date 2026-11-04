"""
EngLISP Batch Translation Client
--------------------------------
Client script for running translation on a batch of English sentences 
via the private EngLISP API server.

Usage:
  python batch_translate_client.py
"""

import time
import json
import requests

API_BASE = "https://api.englisp.com"

# Paste the provisioned teammate API key here
API_KEY = "englisp_live_PASTE_YOUR_TEAMMATE_KEY_HERE"

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def translate_sentence(text: str, source_lang: str = "en", target_lang: str = "fr"):
    text = text.strip()
    if not text:
        return None
        
    # Stage 1 (NL) -> Stage 3 (EngLISP S-Expression)
    parse_res = requests.post(
        f"{API_BASE}/api/parse",
        headers=HEADERS,
        json={"text": text, "lang": source_lang}
    )
    if parse_res.status_code != 200:
        return {"error": f"Parse error: {parse_res.text}", "status": "failed"}
        
    parse_data = parse_res.json()
    if not parse_data.get("success"):
        return {"error": parse_data.get("message", "Parse error"), "status": "failed"}
        
    englisp_expr = parse_data["pipeline"]["stage3_englisp"]

    # Stage 3 (EngLISP S-Expression) -> Stage 1 (Target NL)
    gen_res = requests.post(
        f"{API_BASE}/api/generate-from-englisp",
        headers=HEADERS,
        json={"englisp": englisp_expr, "lang": target_lang}
    )
    if gen_res.status_code != 200:
        return {"error": f"Generation error: {gen_res.text}", "status": "failed"}
        
    gen_data = gen_res.json()
    if not gen_data.get("success"):
        return {"error": gen_data.get("message", "Generation error"), "status": "failed"}
        
    translated_nl = gen_data["pipeline"]["stage1_nl"]
    return {
        "original": text,
        "translated": translated_nl,
        "englisp_ir": englisp_expr,
        "status": "ok"
    }

def batch_translate(sentences, output_file="translations.json"):
    print(f"[*] Starting translation of {len(sentences)} sentences...")
    results = []
    
    for i, sent in enumerate(sentences, 1):
        print(f"[{i}/{len(sentences)}] Translating: {sent[:50]}...")
        res = translate_sentence(sent)
        results.append(res)
        time.sleep(0.05) # Polite delay
        
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    success_count = sum(1 for r in results if r and r.get("status") == "ok")
    print(f"\n[DONE] Translated {success_count}/{len(sentences)} sentences successfully.")
    print(f"Saved results to: {output_file}")

if __name__ == "__main__":
    # Example input sentences
    sample_sentences = [
        "The dog chased the cat.",
        "A student reads a book in the library.",
        "The quick brown fox jumped over the lazy dog."
    ]
    batch_translate(sample_sentences)
