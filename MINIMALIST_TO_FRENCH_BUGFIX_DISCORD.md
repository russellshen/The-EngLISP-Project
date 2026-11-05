# 🇫🇷 EngLISP Bugfix: MinimaLIST to French Generation & Grammar

> **Summary**: Investigation and resolution of issues when translating from MinimaLIST S-expressions to French natural language on the EngLISP website, which previously leaked English words and produced ungrammatical French phrases.

---

## 🔍 Root Cause Analysis

When synthesizing French natural language from MinimaLIST S-expressions (`MinimaLIST` → `EngLISP S-expr` → `X-bar Tree` → `French Text`), several compounding bugs across noun expansion, pronoun handling, determiner inflection, and subject-verb agreement corrupted the generated sentences:

### 1. 👤 Pronoun Expansion with Default Determiners
* **The Bug**: `expand_sexpr()` in `englisp/minimizer.py` treated every terminal noun as a bare noun requiring a restored determiner (`"the"`).
* **The Cause**: Pronouns (`she`, `i`, `he`, etc.) carry part-of-speech `"N"`. `expand_sexpr()` unconditionally expanded `['she']` and `['i']` into `['she', 'the']` and `['i', 'the']`.
* **Impact**: French synthesis generated:
  * `(has she book)` &rarr; `*Le she a le livre.*`
  * `(am i ...)` &rarr; `*L'i am ...*`

---

### 2. 🏷️ Possessive Modifier Nested Expansion
* **The Bug**: In phrases like `(death her)` within `(am i (to (blame (for (death her)))))`, `expand_sexpr()` treated `"her"` as an independent bare nominal constituent rather than a possessive determiner.
* **The Cause**: `"her"` expanded to `['her', 'the']`, which was then embedded as an extra prepositional modifier inside `death`: `['death', 'the', ['her', 'the']]` (*the death the her*).
* **Impact**: French synthesis produced `*... pour le death l'her*` instead of `pour sa mort`.

---

### 3. 🔢 Missing Plural & Gender Determiner Translation
* **The Bug**: `translate_word_from_pivot()` in `englisp/canonicalizer.py` only accepted a `gender` parameter and had no concept of grammatical `number`.
* **The Cause**: Definite article `"the"` only ever returned `"le"` or `"la"`, completely lacking support for the plural definite article `"les"` or indefinite `"des"`.
* **Impact**: Plural nouns received singular masculine articles (`*Le chiens*`, `*Le fraises*`).

---

### 4. 🔤 Vocabulary Gaps for Pronouns, Prepositions, & Core Verbs
* **The Bug**: `sample_english_to_french_vocab.lson` lacked translations for core pronouns (`she`, `he`, `i`, `they`, `we`), prepositions (`for` &rarr; `pour`, `like` &rarr; `comme`, `to` &rarr; `à`), and common predicates/nouns (`taste` &rarr; `goûte`, `blame` &rarr; `blâmer`, `strawberry` &rarr; `fraise`, `death` &rarr; `mort`).
* **Impact**: Words missing from the French lexicon defaulted back to English words, leaking directly into French sentences.

---

### 5. 🍓 Plural Stemming Failure for `-ies` Nouns
* **The Bug**: `translate_word_from_pivot()` stripped only a trailing `"s"` (`word_lower[:-1]`).
* **The Cause**: For `-ies` plurals such as `"strawberries"`, stripping `"s"` produced `"strawberrie"`, failing dictionary lookups.
* **Impact**: `"strawberries"` was left in English as `*Le strawberries*`.

---

### 6. ⚖️ Hardcoded Singular Subject-Verb Agreement
* **The Bug**: French auxiliary generation in `canonicalizer.py` hardcoded 3rd-person singular (`"3sg"`) and auxiliary `"a"`.
* **The Cause**:
  * Plural subjects (`dogs`, `strawberries`, `they`) received singular verbs and singular auxiliary `"a"` instead of plural auxiliary `"ont"` and plural present verb inflection (`-ent`).
  * 1st-person singular (`i` / `je`) with copula `"am"` fell back to English `"am"` or `"est"` instead of `"suis"`.
* **Impact**:
  * `*Le chiens a chassé le chat.*` instead of `Les chiens ont chassé le chat.`
  * `*L'i am ...*` instead of `Je suis ...`

---

### 7. 🗣️ Missing French Elision for `je`
* **The Bug**: `englisp/parser.py` handled elision for `le`, `la`, and `de`, but lacked elision for subject pronoun `je` preceding a vowel (`je ai` &rarr; `j'ai`).

---

## 🛠️ Changes Implemented

### 1. `englisp/minimizer.py`
* Added `PRONOUNS_NO_DET` and `POSSESSIVE_DETS` sets.
* Updated `expand_sexpr()` to preserve subject/object pronouns as bare phrases (`['she']`, `['i']`) without injecting `"the"`.
* Ensured possessive pronouns (`my`, `your`, `his`, `her`, `its`, `our`, `their`) are preserved as determiners rather than nested nouns so `(death her)` expands to `['death', 'her']`.
* Suppressed determiner injection for verbal/non-det nominals following prepositions (`blame` in `(to blame ...)`).

### 2. `englisp/canonicalizer.py`
* **Determiner & Pronoun Translation**: Added `number` parameter to `translate_word_from_pivot()` with support for plural determiners (`les`, `des`, `ces`, `mes`, `ses`, `nos`, `leurs`), subject pronouns (`je`, `tu`, `il`, `elle`, `nous`, `ils`), and prepositions (`pour`, `à`, `comme`, `avec`, `dans`, `sur`).
* **Morphological Stemming**: Added `-ies` &rarr; `-y` and `-es` stemming before vocabulary queries.
* **Agreement Logic**: Added `is_plural_nominal()` and `is_1sg_nominal()`. Conjugated French copulas (`am` &rarr; `suis`, plural &rarr; `sont`), regular verbs (plural present &rarr; `-ent`), and auxiliaries (`ont` for plural subjects, `ai` for 1st person, `a` for 3rd singular).
* **Verb Forms**: Added `"3pl"` and `"1sg"` inflection support in `inflect_verb()`.

### 3. `englisp/parser.py`
* Added French elision for subject `je` before vowels/silent h (`re.sub(r"\bje\s+([aeiouyéèàâêîôûhAEIOUYÉÈÀÂÊÎÔÛH])", r"j'\1", sentence)`).

### 4. Vocabulary Resources
* Added translations to `sample_english_to_french_vocab.lson` (`am`, `are`, `blame`, `death`, `for`, `fruit`, `he`, `i`, `like`, `she`, `strawberry`, `strawberries`, `taste`, `they`, `we`, `you`).
* Added gender entries to `sample_french_gender.lson` (`mort`: F, `fraise`/`fraises`: F, `fruit`: M).
* Added conjugation entries to `sample_french_verb_forms.lson` (`goûte`, `blâme`).

### 5. Automated Tests
* Added tests in `tests/test_multilingual.py` covering MinimaLIST to French generation, plural determiners, pronouns, and possessive agreements.

---

## 🧪 Verification Results

| MinimaLIST S-Expression | Output (Before) | Output (Fixed) | Status |
| :--- | :--- | :--- | :---: |
| `(has she book)` | *Le she a le livre.* | **Elle a le livre.** | ✅ |
| `(taste strawberries (like fruit))` | *Le strawberries taste like le fruit.* | **Les fraises goûtent comme le fruit.** | ✅ |
| `(am i (to (blame (for (death her)))))` | *L'i am à le blame for le death l'her.* | **Je suis à blâmer pour sa mort.** | ✅ |
| `(chased dogs cat)` | *Le chiens a chassé le chat.* | **Les chiens ont chassé le chat.** | ✅ |
| `(death her)` | *Le death l'her.* | **Sa mort.** | ✅ |
| `(dogs)` | *Le chiens.* | **Les chiens.** | ✅ |

### Test Suite Status
* **Full test suite**: `106 passed in 8.92s` (0 failures, 0 regressions).
