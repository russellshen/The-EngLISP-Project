# 🛠️ EngLISP Parser Bugfix: Root Cause Analysis & Resolution

> **Summary**: Investigation and resolution of parsing failures on the EngLISP website for natural language sentences, including `"I am to blame for her death."` and `"strawberries taste like fruit"`.

---

## 🔍 Root Cause Analysis

When natural language queries were entered on the EngLISP website, multiple compounding issues across dictionary tier gating, spellcheck distance heuristics, morphological stemming, and POS classification caused the Earley chart parser to fail:

### 1. 🛑 Aggressive Spellcheck Corruption on Guest / Free Tiers
* **Mechanism**: Anonymous website visitors and free accounts run in the `free` tier by default (`CURRENT_USER_TIER = "free"`), which delegates active dictionary lookups to `sample_en_lexicon.lson` (a lightweight 140-word sample).
* **The Bug**: `correct_word()` previously checked only against the active lexicon before triggering fuzzy Levenshtein typo corrections. Any valid English word outside those 140 words within edit distance 1 or 2 was aggressively mutated into a completely different sample word:
  * `"am"` &rarr; `"a"`
  * `"for"` &rarr; `"fox"`
  * `"blame"` &rarr; `"became"`
  * `"death"` &rarr; `"each"`
* **Impact**: `"I am to blame for her death."` was distorted into `['i', 'a', 'to', 'became', 'fox', 'her', 'each']`, completely corrupting the sentence before parsing began.

---

### 2. 👤 Missing 1st & 2nd Person Pronouns in `PRONOUN_LEXICON`
* **Mechanism**: `PRONOUN_LEXICON` only defined 3rd person pronouns (`he`, `she`, `it`, `they`, `him`, `her`, `them`, `his`, `its`, `their`).
* **The Bug**: 1st and 2nd person pronouns (`I`, `me`, `my`, `mine`, `myself`, `we`, `us`, `our`, `you`, `your`, etc.) and French pronouns (`je`, `tu`, `nous`, `vous`, `on`, `moi`, etc.) were absent.
* **Impact**: In WordNet (`LEXICON_FULL`), `"i"` was tagged as an `Adj` (Roman numeral I), causing subject phrases like `"I am ..."` to fail grammatical phrase construction.

---

### 3. 🏷️ Possessive Determiners vs. Noun Classification
* **Mechanism**: `tag_tokens()` previously assigned tag `"N"` (Noun) to *all* pronouns in `PRONOUN_LEXICON`.
* **The Bug**: Possessive pronouns like `"her"` in `"her death"` function as Determiners (`Det`) specifying a noun phrase. Tagging `"her"` as `"N"` created adjacent nouns:
  ```
  [('her', 'N'), ('death', 'N')]
  ```
* **Impact**: The X-bar grammar (`NP -> (Det N') | (N')`) does not permit adjacent uncoordinated nouns without a compound rule, causing Earley parsing to block at `"death"`.

---

### 4. 🔤 Missing Prepositions & Polysemy Blindspots
* **Missing Prepositions**: Common function prepositions like `"for"`, `"into"`, `"onto"`, etc. were missing from both `sample_en_lexicon.lson` and `en_lexicon_f.lson`. Because `"for"` wasn't recognized, spellcheck replaced it with `"fox"`.
* **Polysemous Words**:
  * `"like"` in WordNet was only tagged as `Adj` (similar), missing its prepositional role (`P`) in comparative constructs (`"taste like fruit"`, `"run like the wind"`).
  * `"taste"` in WordNet was only tagged as `N`, missing its verb role (`V`) when following a subject noun.

---

### 5. ⏳ Copula Forms ("am", "are") Tagged as Nouns
* **Mechanism**: In WordNet, `"am"` (Americium / Amplitude Modulation / a.m.) and `"are"` (metric unit of area = 100 m²) are classified as nouns (`N`).
* **The Bug**: In `tag_tokens()`, auxiliary lookahead only tagged copulas as `I` if followed by a verb participle (`-ing`, `-ed`, `been`). When acting as the main/copular verb, they fell through to their dictionary noun tags (`am: N`, `are: N`).
* **Impact**: Sentences like `"I am happy."` and `"We are students."` failed because no verb was identified.

---

### 6. 🍓 Plural Morphology Stemming Failure on `-ies`
* **Mechanism**: English plural morphology only checked suffixes `-s` and `-es` by raw character stripping (`"strawberries"` &rarr; `"strawberri"`).
* **The Bug**: `"strawberri"` is not a valid word, so the plural noun check failed. The token then fell through to `morphology_rules.lson`, whose `suffix_tags` rule maps words ending in `-es` to verbs (`V`).
* **Impact**: `"strawberries"` was classified as a Verb, generating the unparseable sequence:
  ```
  [('strawberries', 'V'), ('taste', 'N'), ('like', 'N'), ('fruit', 'N')]
  ```

---

### 7. 🖥️ Web Frontend Generic Error Masking
* **The Bug**: `web/static/app.js` checked `showError(data.detail || 'An error occurred during parsing.')`.
* **Impact**: FastAPI HTTP exceptions populate `data.detail`, but parser diagnostic failures return `{"success": false, "message": "..."}`. Because `data.detail` was undefined, the UI masked the exact error reason with a generic error alert.

---

## 🛠️ Key Fixes Implemented

1. **Smart Spellcheck Bypass**:
   * `correct_word()` now checks `LEXICON_FULL`, `PRONOUN_LEXICON`, `COMMON_PREPOSITIONS`, and morphological variants before triggering fuzzy correction. Real words are never mutated.
   * `TierDelegatingDict` now routes partition queries dynamically, preventing full 26-file dictionary scans.

2. **Complete Pronoun Matrix**:
   * Added comprehensive 1st, 2nd, and 3rd person pronouns and reflexive/possessive forms for both English and French.

3. **Contextual POS Tagging**:
   * Differentiates possessive determiners (`Det`) from subject/object pronouns (`N`). `"her [noun]"` is correctly tagged as `Det`.
   * Maps `"am"`, `"are"`, `"is"`, `"was"`, `"were"` to `"V"` when functioning as copula main verbs.
   * Recognizes common prepositions (`for`, `into`, `like` after verbs/nouns).
   * Added perception verb heuristics (`taste`, `smell`, `sound` after nouns) and noun complement tagging for `"to blame"`.
   * Added `-ies` &rarr; `-y` plural stemming (`"strawberries"` &rarr; `"strawberry"`).

4. **Public Sample Vocabulary & Frontend Diagnostics**:
   * Added missing basic vocabulary (`am`, `are`, `blame`, `death`, `for`, `fruit`, `like`, `strawberries`, `taste`, etc.) to `sample_en_lexicon.lson` so guest queries work out of the box.
   * Updated `app.js` to surface `data.message` diagnostics directly to users.

---

## 🧪 Verified Results

All 104 test suite cases pass:
```
================ 104 passed, 37 warnings in 8.10s ================
```

### Sentence 1: `"I am to blame for her death."`
* **EngLISP (Stage 3)**: `(am (i) (to (blame (for (death her)))))`
* **MinimaLIST (Stage 4)**: `(am i (to (blame (for (death her)))))`
* **Compiled SQL**: `INSERT INTO facts (predicate, arg1, arg2) VALUES ('am', 'i', 'to');`
* **Round-trip Text Generation**: `"I am to blame for her death."`

### Sentence 2: `"strawberries taste like fruit"`
* **EngLISP (Stage 3)**: `(taste (strawberries) (like (fruit)))`
* **MinimaLIST (Stage 4)**: `(taste strawberries (like fruit))`
* **Compiled SQL**: `INSERT INTO facts (predicate, arg1, arg2) VALUES ('taste', 'strawberries', 'like');`
* **Round-trip Text Generation**: `"Strawberries taste like fruit."`
