# EngLISP: A Bidirectional Bridge Between Natural Language and Computation

EngLISP is a structured, bidirectional translation system that bridges the gap between the expressive, ambiguous world of human language and the precise, functional world of computation. 

This repository implements the full four-stage pipeline described in the [EngLISP Technical Specification](SPECIFICATION.md), enabling seamless round-trip conversions between human sentences, X-bar syntactic trees, rotated S-expressions, and compressed MinimaLIST configurations.

---

## Documentation Guides

To dive deeper into the theoretical, practical, and lexical design of the EngLISP engine, explore the following documentation:

*   **[EngLISP Technical Specification](SPECIFICATION.md)**: Defines the formal specifications of the 4-stage translation pipeline, S-expression rotation rules, semantic minimization algorithms, and native Lisp/Scheme compile-time macro expansion.
*   **[Lexical & Disambiguation Strategies](LEXICAL_STRATEGIES.md)**: Explains the scaling strategy for large-scale lexicons, including mapping grammatical terminals to language-neutral Synset IDs (BabelNet/WordNet), context-aware Lesk Word Sense Disambiguation (WSD), and Earley chart parsing rules.
*   **[Use-Cases & Applications Guide](USE_CASES.md)**: Explores downstream deployment scenarios such as neuro-symbolic LLM pipeline injection, zero-redundancy network serialization, multi-agent protocols, exact semantic search indexing, and explainable AI audit trails.

---

## The Four-Stage Pipeline

```
     Stage 1: Natural Language
                 ↕ (Parsing & Generation)
     Stage 2: X-bar Syntax Tree (Linguistic IR)
                 ↕ (Rotation Canonicalization)
     Stage 3: EngLISP S-Expression (Computational IR)
                 ↕ (Semantic Minimization & Expansion)
     Stage 4: MinimaLIST EngLISP (Minimal sufficient form)
```

1. **Stage 1 — Natural Language**: Input English text (e.g., *"The quick brown fox jumped over the lazy dog"*).
2. **Stage 2 — X-bar Tree**: A linguistically faithful syntactic tree encoding structural head-complement-specifier relations.
3. **Stage 3 — EngLISP S-Expression**: A rotated Lisp S-expression putting semantic heads/verbs first at each level, e.g., `(jumped (fox the quick brown) (over (dog the lazy)))`.
4. **Stage 4 — MinimaLIST EngLISP**: A minimized sufficient representation that eliminates redundant surface elements (like default determiners) and simplifies logic (double negation elimination), e.g., `(jumped (fox quick brown) (over (dog lazy)))`.

---

## Pipeline Walkthrough Example

To illustrate the forward and reverse transformations, here is the complete life cycle of the sentence *"The dog can chase the cat."*:

### Forward Pipeline (Stage 1 &rarr; Stage 4)

1. **Stage 1 (Natural Language)**:
   ```
   "The dog can chase the cat."
   ```

2. **Stage 2 (X-bar Syntax Tree)**:
   The sentence is parsed into a hierarchical constituency tree:
   ```
   IP [phrase]
     NP [specifier]
       Det [specifier]: "the"
       N' [bar]
         N [head]: "dog"
     I' [bar]
       I [head]: "can"
       VP [complement]
         V' [bar]
           V [head]: "chase"
           NP [complement]
             Det [specifier]: "the"
             N' [bar]
               N [head]: "cat"
   ```

3. **Stage 3 (EngLISP S-Expression)**:
   The syntax tree is canonicalized and rotated. The inflection head `"can"` wraps the clause, and the main verb `"chase"` is rotated to the front of the inner expression:
   ```lisp
   (can (chase (dog the) (cat the)))
   ```

4. **Stage 4 (MinimaLIST EngLISP)**:
   The S-expression is semantic-compressed. Default determiners (`the`) are pruned to reduce redundancy:
   ```lisp
   (can (chase dog cat))
   ```

---

### Reverse Pipeline (Stage 4 &rarr; Stage 1)

1. **Stage 4 (MinimaLIST)**:
   ```lisp
   (can (chase dog cat))
   ```

2. **Stage 3 (EngLISP S-Expression)**:
   The minimizer expands the bare noun arguments back to their canonical noun phrase lists by reintroducing the default determiner (`the`):
   ```lisp
   (can (chase (dog the) (cat the)))
   ```

3. **Stage 2 (X-bar Tree)**:
   The canonicalizer maps the S-expression back to the hierarchical X-bar syntax tree (identical to the parsed tree shown above).

4. **Stage 1 (Natural Language)**:
   The generator traverses the leaf terminals, handles spacing/capitalization, and synthesizes:
   ```
   "The dog can chase the cat."
   ```

---

## LSON (Lisp Symbolic Object Notation) Data Format

EngLISP S-expressions and MinimaLIST structures are serialized using **LSON**—a data representation format designed to be theoretically superior to JSON:
*   **Boilerplate-Free Syntax**: Strips away JSON's commas, colons, and quote-redundancies, yielding a compact byte footprint.
*   **Native Graph Sharing**: Uses Lisp anchor `#N=` and backreference `#N#` syntax to serialize circular networks and shared memory nodes natively (DAG hash-consing).
*   **Homoiconicity**: Functions simultaneously as structured data and an executable Abstract Syntax Tree (AST).

For a detailed comparison and payload size measurements, see the [EngLISP Use-Cases & Applications Guide](USE_CASES.md#E).

---

## Features

- **Bidirectional Transformations**: Edit any computational S-expression (Stage 3 or 4) and generate the corresponding natural language sentence and syntactic tree.
- **Glassmorphic Web Dashboard**: An interactive, modern dark-mode visual interface to explore the stages in real-time.
- **Dynamic SVG Tree Renderer**: Displays collapsible, color-coded X-bar constituent trees directly in the browser.
- **Minimization Optimizer**: Automatic rewrite rules for:
  - Double negation removal: `(not (not happy))` &rarr; `happy`
  - Negation-to-antonym reduction: `(not happy)` &rarr; `sad`
  - Passive-to-Active voice restructuring: `(was chased by X)` &rarr; `(chased X)`
  - Modifier compound semantic compression: `(dog young)` &rarr; `puppy`
  - Determiner pruning: `(dog the)` &rarr; `dog`

---

## Installation & Setup

Make sure you have **Python 3.13+** installed.

### Option A: Remote Installation (To use EngLISP in your own projects)
You can install EngLISP directly from the remote GitHub repository without cloning it locally. This automatically installs `englisp` and its dependencies in your active Python environment:

```bash
pip install git+https://github.com/russellshen/The-EngLISP-Project.git
```

### Option B: Local Installation (To run the dashboard visualizer or run tests)
1. Clone the repository and navigate to the directory:
   ```bash
   git clone https://github.com/russellshen/The-EngLISP-Project.git
   cd The-EngLISP-Project
   ```
2. Install the package in editable mode along with development dependencies:
    ```bash
    pip install -e .[dev]
    ```

### Lexical Databases & Fallback Samples

*   **Public Fallback Samples**: This repository comes bundled with lightweight fallback sample datasets (`sample_*.lson` files under `englisp/resources/`). These allow the entire parsing, generation, compilation, and interpretation pipeline to compile, run tests, and execute out of the box for testing and sample inputs.
*   **Full Production Database**: The full-scale multilingual database (containing 254 partition files mapping over 100,000 nouns, verbs, adjectives, grammatical genders, and translations linked to BabelNet and WordNet synsets) is kept in a separate private repository to protect the project's data IP and commercial viability.
*   **Requesting Access**: If you are an academic researcher, open-source contributor, or commercial partner interested in utilizing the full-scale dictionaries or licensing the dataset, please reach out directly via the **Commercial Licensing & Contact** section below.

---

## How to Run

To run the interactive web visualizer:

1. Launch the FastAPI server:
   ```bash
   python run.py
   ```
2. Open your browser and navigate to:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

To run the automated test suite:
```bash
python -m pytest
```

---

## Python Developer API

For larger projects, computational pipelines, and non-toy integration, developers can import the `englisp` package directly into their own Python projects.

### Getting Started

To use the API, make sure the `englisp` directory is in your Python path:

```python
import englisp
```

The package exposes **8 core functions** covering all 3 bidirectional pipeline transformations, 2 direct "all-the-way" shortcuts, and **2 S-expression string serialization helpers**.

---

### 1. Bidirectional Stage Transformations (6 Atomic Functions)

#### Stage 1 (NL) &leftrightarrow; Stage 2 (X-bar Tree)
*   **`nl_to_xbar(text: str, lang: str = "auto") -> XBarNode`**
    Parses natural language text into an X-bar tree AST.
    *   `lang`: Supports `"en"`, `"fr"`, or `"auto"` (which detects the language dynamically).
*   **`xbar_to_nl(node: XBarNode, lang: str = "en") -> str`**
    Synthesizes grammatical natural language text from an X-bar tree.

```python
# Parse English (auto-detected)
tree = englisp.nl_to_xbar("The dog chased the cat.", lang="auto")
print(tree.category)  # Output: IP
print(tree.pretty_print())  # Outputs structured text tree

# Generate back
text = englisp.xbar_to_nl(tree, lang="en")
print(text)  # Output: "The dog chased the cat."
```

#### Stage 2 (X-bar Tree) &leftrightarrow; Stage 3 (EngLISP S-Expression)
*   **`xbar_to_englisp(node: XBarNode, lang: str = "en") -> list`**
    Translates an X-bar tree into a canonical, rotated EngLISP S-expression list.
*   **`englisp_to_xbar(sexpr: list, lang: str = "en") -> XBarNode`**
    Reconstructs an X-bar tree from an EngLISP S-expression list.

```python
# Rotate tree to rotated head-first Lisp list
sexpr = englisp.xbar_to_englisp(tree, lang="en")
print(sexpr)  # Output: ['chased', ['dog', 'the'], ['cat', 'the']]

# Reconstruct X-bar tree from list
tree_rebuilt = englisp.englisp_to_xbar(sexpr, lang="en")
```

#### Stage 3 (EngLISP) &leftrightarrow; Stage 4 (MinimaLIST S-Expression)
*   **`englisp_to_minimalist(sexpr: list) -> list`**
    Compresses an EngLISP S-expression list into MinimaLIST form (applying double negation, antonyms, voice shifts, and determiner prunings).
*   **`minimalist_to_englisp(sexpr: list) -> list`**
    Expands a MinimaLIST S-expression back into canonical EngLISP form.

```python
# Compress S-expression list
min_sexpr = englisp.englisp_to_minimalist(sexpr)
print(min_sexpr)  # Output: ['chased', 'dog', 'cat']

# Expand S-expression list back
expanded_sexpr = englisp.minimalist_to_englisp(min_sexpr)
print(expanded_sexpr)  # Output: ['chased', ['dog', 'the'], ['cat', 'the']]
```

---

### 2. Direct "All the Way" Transformations (2 Shortcut Functions)

For quick end-to-end processing without dealing with intermediate X-bar nodes:

#### Stage 1 (NL) &rarr; Stage 4 (MinimaLIST)
*   **`nl_to_minimalist(text: str, lang: str = "auto") -> list`**
    Directly converts natural language text to a minimized MinimaLIST S-expression list.

```python
min_list = englisp.nl_to_minimalist("The dog was not unhappy.", lang="en")
print(min_list)  # Output: ['happy', 'dog'] (pruned det & double negation)
```

#### Stage 4 (MinimaLIST) &rarr; Stage 1 (NL)
*   **`minimalist_to_nl(sexpr: list, lang: str = "en") -> str`**
    Directly expands a MinimaLIST S-expression and generates the corresponding surface sentence.

```python
sentence = englisp.minimalist_to_nl(['chased', 'dog', 'cat'], lang="fr")
print(sentence)  # Output: "Le chien chassait le chat." (Cross-lingual translation!)
```

---

### 3. Serialization Helpers (2 Utility Functions)

Lisp S-expressions are represented as standard nested Python lists in code. To print them or write them to configuration files, serialize them to/from strings:

*   **`to_string(sexpr: list) -> str`**
    Serializes a nested list to a Lisp-style S-expression string. Supports **DAG hash-consing backreferences** (`#1=...` / `#1#`) for shared memory nodes.
*   **`from_string(s: str) -> list`**
    Parses a Lisp S-expression string back into a nested list structure.

```python
# Serialize S-expression list with shared memory sub-expressions (DAG)
dog_ref = ["dog", "the"]
dag_sexpr = ["and", ["chased", dog_ref, "cat"], ["barked", dog_ref]]
print(englisp.to_string(dag_sexpr))
# Output: (and (chased #1=(dog the) cat) (barked #1#))

# Parse S-expression string back to python lists
parsed_list = englisp.from_string("(and (chased #1=(dog the) cat) (barked #1#))")
print(parsed_list)
# Output: ['and', ['chased', ['dog', 'the'], 'cat'], ['barked', ['dog', 'the']]]
```

---

## Code Directory Structure

- `englisp/xbar.py`: Hierarchical X-bar node class modeling syntax tree representations.
- `englisp/parser.py`: Deterministic natural language parser and generator.
- `englisp/canonicalizer.py`: Tree-rotation S-expression translator (rotates heads/verbs to the front).
- `englisp/minimizer.py`: Semantic optimizer applying rewrite and expansion rules for MinimaLIST forms.
- `englisp/interpreter.py`: Stateful S-expression evaluator supporting arithmetic calculations, backward-chaining logical rules, cycle-detection loop protection, and Explainable AI (XAI) proof trails.
- `englisp/compiler.py`: S-expression compiler compiling canonical forms to native Common Lisp and Scheme.
- `englisp/ontology.py`: Graph database mapping and Word Sense Disambiguation (WSD) synset resolution.
- `englisp/graph_db.py`: Semantic graph database tracking entity relationships and `IS_A` type inheritance.
- `englisp/loader.py`: Alphabetically partitioned lazy-loading database driver.
- `web/server.py`: FastAPI server serving the backend API endpoints.
- `web/static/`: Frontend dashboard containing:
  - `index.html`: Clean glassmorphism layout with Outfit and Inter typography.
  - `styles.css`: Dark-indigo themed visual system.
  - `app.js`: Interactive UI logic, API calls, and custom SVG hierarchical tree layout drawer.

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
