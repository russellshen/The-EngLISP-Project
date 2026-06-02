# EngLISP: Scale-Level Lexical & Disambiguation Strategies


To transition EngLISP from a prototype to a commercial-ready system, we must resolve lexical ambiguity, manage multi-lingual inputs (code-switching), filter inter-lingual homographs (false friends), and scale our syntactic parsing.

This document outlines the proposed strategies for these challenges and explores how theoretical linguists construct X-bar trees.

These strategies support the production-grade deployment of EngLISP across various domains detailed in the [EngLISP Use-Cases & Applications Guide](USE_CASES.md).

---

## 1. Scale-Level Lexical Datasets & Word Signatures

To transition the interlingua to a production-grade system, we have externalized our lexical vocabulary into **LSON database files** under `englisp/resources/`. To prevent startup delay and memory bloat, all dictionaries are **partitioned alphabetically** (by first character) and loaded **lazily on demand** using custom Python wrappers (`LazyPartitionedDict` and `LazySynsets`):

* **English & French Lexicons**: `en_lexicon_<char>.lson` and `fr_lexicon_<char>.lson` store part-of-speech mappings for over 82k English words and 34k French words.
* **Translation Mappings**: `english_to_french_vocab_<char>.lson` and `french_to_english_vocab_<char>.lson` map pivot terms.
* **BabelNet (Multilingual Concept Core)**: Over 92k multilingual synsets are imported from English WordNet and French Open Multilingual WordNet (OMW). They are partitioned by ID prefix (e.g. `synsets_n02.lson`) to keep files lightweight.
* **Word-to-Synset Reverse Index**: Partitioned alphabetically (`word_to_synsets_<char>.lson`) to discover matching synsets instantly.

---

## 2. Resolving Ambiguity within a Single Language (Homonyms)

Words like *"bank"* have identical spellings but completely different meanings (financial bank vs. river bank). We resolve this dynamically using a **Lesk-style Word Sense Disambiguation (WSD)** algorithm:

* **Overlap Metric & Candidate Priority**: We query matching synset IDs from the partitioned reverse index. To select the correct synset, the algorithm calculates overlap between the sentence's context words and each synset's definition/synonym tokens. If the context is empty, the algorithm uses a priority sort key that ranks candidates favoring (1) original hand-coded synset IDs and (2) exact English/French primary word round-trips, ensuring regression-proof consistency.
* **Graph-Based Semantic Distance**: Using the synset IDs, the `SemanticGraphDB` evaluates paths between concepts. If *"bank"* is surrounded by *"water"* and *"river"*, it is resolved to the riverbank synset (`n09214732`), while *"money"* or *"cash"* resolves it to the financial bank synset (`n08420278`).
* **LLM-Assisted Sense Tagging**: During the Parsing phase (T1), we can query a lightweight local LLM to output the correct WordNet/BabelNet sense key alongside the POS tag. This injects context-aware intelligence at the boundary of Stage 1 &rarr; Stage 2.

---

## 3. Language Identification & Code-Switching

When users enter prompts, we must automatically detect the language of the text, even if they mix languages (code-switch) in a single block.

* **Character N-gram Models (Block Detection)**: For block-level text, we use fast, lightweight classifiers (like Meta's `fastText` or `langdetect`). These analyze character n-grams (sub-word patterns) and identify the language with >99% accuracy in milliseconds.
* **Token-Level POS Tagging (Code-Switching)**: If a user mixes languages (e.g., *"The chat [French for cat] sleeps on the table"*), block detection is insufficient. 
  * We run the tokens through a multilingual POS tagger.
  * The tagger evaluates which language's lexical database and morpho-syntactic rules the token satisfies best. 
  * Once resolved, BabelNet translates the French word *"chat"* and English word *"cat"* to the same underlying concept ID, merging them into a unified EngLISP expression.

---

## 4. Inter-lingual Homographs (False Friends)

Short strings of characters can mean one thing in one language and something entirely different in another (e.g., *"gift"* means "present" in English but "poison" in German; *"chat"* means "talk" in English but "cat" in French).

We resolve this using two methods:
* **Syntactic Agreement Markers**: We evaluate the surrounding syntactic context in the X-bar tree. If *"chat"* is preceded by the French masculine determiner *"le"* (*"le chat"*), the syntactic parser instantly flags it as a French Noun, resolving the ambiguity.
* **POS Transition Probabilities**: Using Hidden Markov Models (HMM) or transformer-based sequence taggers, we calculate the probability of word sequences. The sequence *"a gift for you"* has a near-zero transition probability in German syntax but a near-100% probability in English, allowing the tagger to flag *"gift"* as English.

---

## 5. Linguistic Strategies for X-bar Tree Construction

To automate the parsing of natural language into X-bar trees at scale, we study how syntax-specializing linguists construct these trees. Linguists determine tree structure using **Constituency Tests**:

### 5.1 Constituency Tests
Linguists prove that a group of words forms a single node (XP) in the tree using three core tests:
1. **The Substitution Test (Pro-Form replacement)**: If a sequence of words can be replaced by a single pronoun (like *"it"*, *"them"*, *"there"*, or *"do so"*), it is a constituent.
   * *Example*: *"The student read [a very long book in the library]."* &rarr; *"The student read [it]."* Proves the bracketed phrase is an NP.
2. **The Movement Test (Clefting)**: If a phrase can be moved to the front of a sentence (clefted) and remain grammatical, it is a single constituent.
   * *Example*: *"The student read a book [in the library]."* &rarr; *"[In the library], the student read a book."* Proves *"in the library"* is a PP.
3. **The Coordination Test**: Only constituents of the same category can be conjoined by *"and"* or *"or"*.
   * *Example*: *"The student read [a book] and [a magazine]."* (NP + NP - valid).

### 5.2 Computational Pipeline Translation
At scale, we convert these linguistic tests into algorithms:
* **Dependency-to-Constituency Mapping**: Dependency parsers (which identify binary head-modifier links like `nsubj`, `dobj`) are computationally easier to run at scale than constituency parsers. 
* **The Strategy**: We run a fast dependency parser first, and then apply a deterministic converter to map those dependency links into their equivalent X-bar structures. For example, a `dobj` (direct object) dependency is mapped directly to a sister node of $V$ under $V'$, satisfying the X-bar complement schema.

---

## License, Copyright, & Feedback

[![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

Copyright © 2026 Russell Shen. All rights reserved.

This project and its documentation are licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.

### License Clarification & Terms

Under the CC BY-NC-ND 4.0 license, you are free to download, copy, and share this codebase for personal, academic, or non-commercial study, subject to the following strict conditions:

1. **Attribution (BY)**: You must give appropriate credit to the author (**Russell Shen**), provide a link to this license, and indicate if any modifications were made. You must do so in a reasonable manner, but not in any way that suggests endorsement.
2. **Non-Commercial (NC)**: You may not use the material for commercial purposes. This explicitly prohibits using this software, its algorithms, data files, or documentation in any commercial products, revenue-generating activities, paid API services, or closed-source corporate projects.
3. **No Derivatives (ND)**: If you remix, transform, or build upon this material, you are permitted to do so only for private, personal use. You **may not distribute** any modified or derived versions of the code, specifications, or datasets to the public or any third party.

### Support & Sponsorship

If you find the EngLISP project useful and want to support its ongoing development, optimization, and research, please consider sponsoring:

* **GitHub Sponsors**: [Sponsor Russell Shen on GitHub](https://github.com/sponsors/russellshen)

Your support helps maintain the public code, keep the hosted playground running, and fund future multi-lingual expansions.

### Questions, Suggestions, & Feedback

If you have honest, good-faith questions, suggestions, or ideas about the EngLISP project or the LSON specification, please feel free to reach out. I welcome community feedback, academic inquiries, and theoretical discussions.

### Commercial Licensing & Contact

Any use outside the narrow scope of the CC BY-NC-ND 4.0 license is strictly prohibited without a separate commercial agreement. Parties interested in commercial deployment, proprietary closed-source integration, SaaS hosting, or distributing modified versions, or who have general feedback and inquiries, may contact the author directly:

* **Russell Shen**
* 📧 [russellshen7@gmail.com](mailto:russellshen7@gmail.com)

*Licensing terms, scope, and compensation are subject to separate negotiation and are granted only by explicit written agreement.*
