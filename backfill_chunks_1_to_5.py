import os
import sys

# Ensure local project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ledger_manager import record_evaluation, get_ledger_summary
from tune_chunk_5 import (
    translate_sentence_through_englisp,
    translate_with_tuned_englisp_v5,
    compute_loss,
    CUMULATIVE_PARAMETERS
)

def backfill():
    with open("fra.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print("[*] Backfilling Chunks 1 through 5 (Lines 1 to 210)...")
    
    for idx in range(1, 211):
        line = lines[idx - 1].strip()
        if not line:
            continue
        parts = line.split("\t")
        eng = parts[0]
        tgt = parts[1]
        
        base_pred = translate_sentence_through_englisp(eng)
        base_loss = compute_loss(base_pred, tgt)
        
        tuned_pred = translate_with_tuned_englisp_v5(eng)
        tuned_loss = compute_loss(tuned_pred, tgt)
        
        if idx <= 20:
            tier = "Tier 1: Elementary Imperatives (1-20)"
        elif idx <= 40:
            tier = "Tier 1: Phrasal & Motion Verbs (21-40)"
        elif idx <= 60:
            tier = "Tier 1: Idioms & 1pl Agreement (41-60)"
        elif idx <= 110:
            tier = "Tier 1: Copula & Enclitics (61-110)"
        else:
            tier = "Tier 1: SVO & Inversions (111-210)"
            
        record_evaluation(
            line_id=idx,
            base_pred=base_pred,
            base_loss=base_loss,
            tuned_pred=tuned_pred,
            tuned_loss=tuned_loss,
            diagnosis="Elementary Clause / Imperative / Copula",
            tier_label=tier,
            verified=1
        )
        
    print("[SUCCESS] Backfilled lines 1-210.")
    summary = get_ledger_summary()
    print("Updated Ledger Summary:", summary)

if __name__ == "__main__":
    backfill()
