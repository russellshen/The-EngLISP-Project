# 📊 EngLISP Parallel Corpus Dataset Tally & Ledger

**Source Dataset**: `fra.txt` (Tatoeba English-French Corpus)  
**Total Sentence Pairs in Corpus**: **145,437**  
**Database Ledger**: `dataset_tally.sqlite` (SQLite3 relational tracking store)  
**Last Updated**: 2026-11-17 (Local Time)

---

## 📈 High-Level Progress Dashboard

```mermaid
pie title Dataset Processing Status (145,437 Lines)
    "Analyzed & Tuned" : 710
    "Untouched Remaining" : 144727
```

| Metric | Current Count / Value | Percentage of Dataset |
|:---|:---:|:---:|
| **Total Corpus Lines** | `145,437` | 100.00% |
| **Analyzed & Benchmarked** | `710` | **0.49%** |
| **Untouched Remaining** | `144,727` | **99.51%** |
| **Mean Initial (Base) Loss** | `0.6341` | — |
| **Mean Tuned Loss** | `0.1561` | — |
| **Overall Cumulative Loss Reduction** | **75.38%** | — |

---

## 🏛️ Stratified Complexity Architecture (Option B Sampling Matrix)

| Tier | Line Number Range | Avg. Length | Primary Linguistic Focus | Status | Sentences Completed |
|:---:|:---:|:---:|:---|:---:|:---:|
| **Tier 1** | Lines `1` – `210` | 1–3 words | Imperatives, copular SVC, enclitics, basic SVO, inversion questions | **COMPLETED** | **210 / 210** |
| **Tier 2** | Lines `1,001` – `1,100` | 3–5 words | Transitive SVO, French proclitic object clitics, reflexives, locative PPs | **COMPLETED** | **100 / 100** |
| **Tier 3** | Lines `5,001` – `5,100` | 5–7 words | Sentential Negation (*ne...pas*), prepositional predicates, participial adjectives | **COMPLETED** | **100 / 100** |
| **Tier 4** | Lines `20,001` – `20,100` | 8–11 words | Modal auxiliaries (*should/might*), infinitival complements, double clitics, 3sg past | **COMPLETED** | **100 / 100** |
| **Tier 5** | Lines `50,001` – `50,100` | 12–16 words | Past auxiliary inversion (*Did you...?*), polite modals (*Could you...?*), abstract NPs | **COMPLETED** | **100 / 100** |
| **Tier 6** | Lines `100,001` – `100,100` | 17+ words | Multi-clause discourse, passive voice, partitive expressions, complex genitives | **COMPLETED** | **100 / 100** |

---

## 🔬 Tier-by-Tier Evaluation Breakdown

| Tier Level | Line Range | Count | Mean Base Loss | Mean Tuned Loss | Loss Reduction | Core Theoretical Phenomenon Mastered |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Tier 1** | `1` – `210` | 210 | `0.7044` | `0.2846` | **59.59%** | Subjectless imperatives, copular `I'm`, enclitic clitics (`-moi`), inverted questions |
| **Tier 2** | `1,001` – `1,100` | 100 | `0.6072` | `0.2074` | **65.85%** | **French Proclitic Object Placement** (`Je t'aime`, `Je la connais`, `Je l'ai réparé`), reflexive sensation verbs (`Je me sens mal`), verbal idiom `avoir besoin de` |
| **Tier 3** | `5,001` – `5,100` | 100 | `0.6478` | `0.1050` | **83.80%** | **French Discontinuous Negation** (`ne ... pas`), prepositional predicates (`Je suis à Boston`, `au régime`, `en chemin`), physiological states (`avoir faim/confiance`) |
| **Tier 4** | `20,001` – `20,100` | 100 | `0.5221` | `0.0611` | **88.30%** | **Modal Conditionals** (`devrait/pourrait`), **Double Clitics** (`Il me l'a montré`), **Infinitival Complements** (`appris à nager`, `arrêté de parler`), **Transitive Compound Past** |
| **Tier 5** | `50,001` – `50,100` | 100 | `0.6790` | `0.0984` | **85.51%** | **Past Interrogative Inversion** (`Did you close...` $\to$ `As-tu fermé...`), **Polite Modals** (`Could you help...` $\to$ `Pourriez-vous m'aider...`), **Abstract Noun Determiners** (`La corruption`, `Les vaches`) |
| **Tier 6** | `100,001` – `100,100` | 100 | `0.5671` | `0.0385` | **93.21%** | **Multi-Clause Subordination** (`Once you start, you must continue`), **Passive Voice** (`Le papier fut... inventé`), **Genitive Noun Phrases** (`La fourrure de notre chat`), **Partitives & Quantifiers** (`Un cinquième de mon salaire`) |
| **Cumulative** | **`1` – `100,100`** | **710** | **`0.6341`** | **`0.1561`** | **75.38%** | **Comprehensive multi-tier competence spanning all syntactic complexity strata** |

---

## 🗄️ Querying & Verifying the Ledger

The SQLite ledger is indexed and fully up to date:

```bash
# Query current ledger statistics
python -c "import sqlite3; c=sqlite3.connect('dataset_tally.sqlite').cursor(); print('Analyzed:', c.execute('SELECT COUNT(*) FROM sentence_tally WHERE status=\"ANALYZED\"').fetchone()[0]); print('Untouched:', c.execute('SELECT COUNT(*) FROM sentence_tally WHERE status=\"UNTOUCHED\"').fetchone()[0])"
```
