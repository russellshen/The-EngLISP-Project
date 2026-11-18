import sys
import os

from englisp.loader import CURRENT_USER_TIER
CURRENT_USER_TIER.set('paid')

from englisp import nl_to_minimalist, minimalist_to_nl, to_string
from translate_csv import translate_sentence_through_englisp

def run_chunk(start=0, count=20):
    with open('fra.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    chunk = lines[start:start+count]
    results = []
    for idx, line in enumerate(chunk, start=start+1):
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        eng = parts[0]
        tgt_fr = parts[1]
        
        # Method 1: direct nl_to_minimalist -> minimalist_to_nl
        m_str = ""
        gen_direct = ""
        err_direct = None
        try:
            m = nl_to_minimalist(eng, lang="en")
            m_str = to_string(m)
            gen_direct = minimalist_to_nl(m, lang="fr")
        except Exception as e:
            err_direct = str(e)
            
        # Method 2: translate_sentence_through_englisp (with pipeline fallbacks)
        gen_pipeline = ""
        try:
            gen_pipeline = translate_sentence_through_englisp(eng)
        except Exception as e:
            gen_pipeline = f"ERR: {e}"
            
        print(f"[{idx}] EN: {eng}")
        print(f"     Target FR : {tgt_fr}")
        print(f"     MinimaLIST: {m_str if m_str else f'FAIL ({err_direct})'}")
        print(f"     Direct FR : {gen_direct if gen_direct else f'FAIL ({err_direct})'}")
        print(f"     Pipeline  : {gen_pipeline}")
        print("-" * 50)

if __name__ == "__main__":
    run_chunk(0, 20)
