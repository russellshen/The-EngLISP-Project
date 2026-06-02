# EngLISP: Formal Specification (v1.0)


This document defines the formal specification of the **EngLISP** system, a structured, bidirectional bridge between human natural languages and canonical computational representations.

For a comprehensive analysis of practical applications, commercial strategies, and academic deployment scenarios, see the [EngLISP Use-Cases & Applications Guide](USE_CASES.md).

---

## 1. Overview & Core Philosophy

EngLISP is designed around the principle of **representation-invariance**. Multiple stylistically diverse, redundant, or ambiguous expressions in natural language that carry identical semantic content are progressively normalized, structured, and minimized into a unique, invariant computational representation—and synthesized back into natural language.

The system is defined by a **four-stage pipeline** and **three bidirectional transformations**:

$$\text{Stage 1 (Natural Language)} \xleftrightarrow{\text{T1}} \text{Stage 2 (X-bar Tree)} \xleftrightarrow{\text{T2}} \text{Stage 3 (EngLISP)} \xleftrightarrow{\text{T3}} \text{Stage 4 (MinimaLIST)}$$

Unlike traditional compilers, every stage in this pipeline is fully bidirectional, enabling round-trip computation and natural language generation from logical ASTs.

### 1.1 Core Theoretical Insights & Novelty

EngLISP pioneers three structural paradigms at the intersection of theoretical computer science, computational linguistics, and formal semantics:

1. **The Invertible (Bidirectional) NLP Compiler**: While standard compilers and parsers operate unidirectionally, EngLISP is a fully invertible compiler. Every transformation ($T1$, $T2$, $T3$) has a mathematically defined inverse, meaning syntax analysis and text synthesis are perfectly symmetric. Modifying raw data at Stage 4 dynamically propagates backward to regenerate grammatically valid natural language in English or French.
2. **Isomorphism of Chomskyan Syntax and McCarthy's Lambda Calculus**: Chomsky's generative grammar (X-bar constituency structures) and McCarthy's Lisp (Lambda calculus) have historically existed as separate paradigms in linguistics and computer science. EngLISP establishes a formal isomorphism between them: the tree rotation algorithm ($T2$) rotates specifier-head-complement syntax coordinates directly into function-argument S-expressions, mapping human language structural rules to executable code blocks.
3. **Algorithmic Natural Semantic Metalanguage (NSM) with DAG Pooling**: In formal semantics, Anna Wierzbicka's Natural Semantic Metalanguage (NSM) posits that all human languages share a core set of universal semantic primes (e.g., `cause`, `become`, `exist`, `not`). EngLISP is the first engine to operationalize NSM as an algorithmic compiler optimization: complex lexical items are decomposed into primitive semantic expressions (e.g., `kill` &rarr; `(cause (become (not alive)))`), which are then memory-shared using Directed Acyclic Graph (DAG) hash-consing backreferences (`#1=...` / `#1#`). During synthesis, these primes are reconstructed back into single-token native words.

---

## 2. Stage 1: Natural Language (NL)

* **Definition**: Free-form natural language text.
* **Characteristics**: Stylistically diverse, structurally ambiguous, grammatically redundant, and context-dependent.
* **Role**: The human-facing input interface and generation target.

---

## 3. Transformation 1 (T1): Parsing & Generation

### 3.1 Forward Direction: Parsing (NL &rarr; X-bar)
T1 maps a flat text string of natural language to a hierarchical X-bar syntax tree.
* **Mechanism**: Syntactic analysis resolves the linear word sequence into a nested hierarchy of constituents conforming to the X-bar schema.
* **The Hybrid Parsing Architecture**: To handle varying degrees of input complexity, the parsing layer uses a hybrid design:
  1. *Deterministic Earley Chart Parser*: A local, offline chart parser executing the Earley algorithm over a Context-Free Grammar (CFG). It processes recursive rules and resolves ambiguity using a syntax-score heuristic (e.g., favoring NP attachment of prepositional/relative clauses over VP attachment). It uses a "clone-on-build" strategy when completing chart states to avoid node mutation side-effects.
  2. *Robust Fallback & Pre-processing*:
     * *Fuzzy Spell-Checking*: Pre-processes words against the active lexicon using Damerau-Levenshtein edit distance. To keep checking fast, the lexicon is alphabetically partitioned, loading only the partitions matching the first two characters of the target word. A priority queue resolves distance ties by favoring the core hand-coded vocabulary.
     * *Contraction Expansion*: Standardizes contractions (e.g., *don't* &rarr; *dont*) before POS tagging.
     * *Fragment Fallback Parser*: If a complete IP sentence parse cannot be established, the engine falls back to parsing the longest valid constituents (NP, VP, PP) and wraps them in a `FRAG` (Fragment) constituent node to ensure partial translation.
  3. *LLM-Assisted Parser*: An optional, extensible parser that leverages an LLM API to translate arbitrary, complex, or grammatically imperfect user sentences directly into their structured X-bar JSON representations.
* **Property**: *Many-to-Many* due to semantic and syntactic ambiguity in natural language. For instance, the sentence *"I saw the man with the telescope"* parses into two distinct X-bar trees depending on PP-attachment (instrument vs. modifier).

### 3.2 Reverse Direction: Text Synthesis (X-bar &rarr; NL)
T1 reconstructs natural language from an X-bar tree.
* **Mechanism**: Recursively traverses the tree, collects terminal leaf labels in linear order, applies morphological inflection rules (e.g., subject-verb tense agreement), and formats capitalization and punctuation.
* **Property**: *One-to-Many* due to stylistic generation choices (e.g., active vs. passive voice, choice of determiners).

---

## 4. Stage 2: X-bar Syntax Tree (Linguistic IR)

* **Definition**: A hierarchical syntax tree conforming to universal generative grammar rules (X-bar schema).
* **Role**: Structural Intermediate Representation (Linguistic IR).
* **Syntax Schema**:
  Every phrase is represented as a phrase node ($XP$), which projects to an intermediate bar node ($X'$) and a head node ($X$):
  $$XP \rightarrow \text{Specifier } X'$$
  $$X' \rightarrow X \text{ Complement}$$
  $$X' \rightarrow X' \text{ Adjunct } \mid \text{Adjunct } X'$$

```
       XP (Phrase Node)
      /  \
 [Spec]   X' (Bar Node)
         /  \
        X    [Complement]
     (Head)
```

---

## 5. Transformation 2 (T2): Canonicalization & Mapping

### 5.1 Forward Direction: Rotation (X-bar &rarr; EngLISP)
T2 eliminates linguistic syntactic artifacts and language-specific word orders, producing an algebraic representation.
* **The Rotation Algorithm**:
  1. Identify the semantic head node ($X$, such as $V$ in $VP$ or $N$ in $NP$) at each phrase level.
  2. Rotate the tree layout so that the head node is positioned as the first element (operator/function) inside a functional parenthetical block.
  3. Recursively map complements and adjuncts as arguments.
* **Property**: *Many-to-One*. Syntactic variations (e.g. word order variations across different human languages) collapse into the same rotated functional S-expression.

### 5.2 Reverse Direction: Reconstructive Grammar (EngLISP &rarr; X-bar)
T2 generates an X-bar tree from a rotated S-expression.
* **Mechanism**: Inspects the Part-of-Speech (POS) of the operator. Maps verb-first expressions to $IP \rightarrow I' \rightarrow VP$ structures, noun-first expressions to $NP \rightarrow N'$ structures, and preposition-first expressions to $PP \rightarrow P'$ structures.

### 5.3 Multilingual Pivot Architecture (French Support)
To establish representation-invariance across languages, the EngLISP rotation mapping acts as an **interlingua pivot**:
* **Language-Specific Grammars**: Parsing translates surface sentences into language-specific X-bar structures (e.g., handling post-nominal adjectives in French, French gender agreement, and clitic splitting).
* **English Semantic Pivot**: During rotation (T2), language-specific constituents are mapped onto a unified English-based pivot S-expression vocabulary using Word Sense Disambiguation and a bilingual synonym dictionary. Both definitions and translation dictionaries are partitioned by alphabetical character and synset ID prefix to support sub-second on-demand resolution without memory bloat. For example, both English *"The cat"* and French *"Le chat"* map to `["cat", "the"]` in the Stage 3 representation.
* **Morphological Synthesis**: During reconstruction, the engine applies target-language synthesis parameters (e.g., generating French gender-agreed adjectives, handling vowel elisions like `le chien` &rarr; `le chien` vs. `le ordinateur` &rarr; `l'ordinateur`, and constructing complex auxiliary chain tenses).

---

## 6. Stage 3: EngLISP (Computational IR)

* **Definition**: A canonical Lisp-style S-expression representing semantic predicate-argument relationships.
* **Role**: Core Computational Intermediate Representation.
* **Formal Syntax (EBNF)**:
  ```ebnf
  S-Expression = Terminal | "(", Operator, { Argument }, ")" ;
  Operator     = Symbol ;
  Argument     = S-Expression ;
  Terminal     = Symbol | String ;
  Symbol       = Character, { Character | Digit | "-" } ;
  ```
* **Language Neutrality**: Symbols in EngLISP (e.g., `chase`, `dog`, `cat`) represent abstract conceptual units (e.g., WordNet synsets or semantic primes), making the representation agnostic to any specific human language.

---

## 7. Transformation 3 (T3): Minimization & Expansion

### 7.1 Forward Direction: Minimization (EngLISP &rarr; MinimaLIST)
T3 reduces the representation to its minimal sufficient form, aiming towards the Kolmogorov complexity limit (the shortest representation that still preserves complete semantic sufficiency).
* **Optimization Criteria**:
  $$\text{Loss} = \text{Length}(\text{Expression}) + \lambda \cdot (1 - \text{SemanticSufficiency})$$
* **Reduction Rules**:
  1. **Logical Pruning**: Eliminates double negatives: `(not (not X))` &rarr; `X`.
  2. **Antonym Contraction**: Collapses negated adjectives to their polar opposite: `(not happy)` &rarr; `sad`.
  3. **Voice Normalization**: Converts passive constructs to active forms: `(chase patient (by agent))` &rarr; `(chase agent patient)`.
  4. **Semantic Compounding**: Replaces modified nouns with compound lexical primitives: `(dog young)` &rarr; `puppy`.
  5. **Syntactic De-noising**: Prunes default articles/determiners `(dog the)` &rarr; `dog`.
  6. **Variable Bindings (Let-reduction)**: Replaces repeating complex semantic phrases with bound local variables.
  7. **Argument Canonicalization (Structural Ordering)**: Enforces uniform positional and sorting rules for tree arguments. Non-core modifiers (adjectives/PPs in Noun Phrases, adverbs/PPs in Verb Phrases) are sorted alphabetically to ensure that different surface syntactic layouts of the same semantic statement collapse into the identical MinimaLIST S-expression (e.g., `(fox quick brown)` and `(fox brown quick)` both resolve to `(fox brown quick)`).

### 7.2 Reverse Direction: Lexical Expansion (MinimaLIST &rarr; EngLISP)
T3 restores default grammatical parameters from the minimized representation.
* **Mechanism**: 
  - Expands base semantic concepts to full forms (e.g. `puppy` &rarr; `(dog the young)`).
  - Restores default grammatical determiners (e.g. bare noun `dog` &rarr; `(dog the)`).

---

## 8. Stage 4: MinimaLIST EngLISP (Minimal Form)

* **Definition**: The shortest feasible EngLISP S-expression that preserves the intended computational role or semantic truth conditions.
* **Role**: The optimized, zero-redundancy data payload suitable for computer-to-computer transmission, database indexing, and execution.
* **Example**:
  - *Natural Language (Stage 1)*: *"The young dog can chase the cat."*
  - *MinimaLIST Form (Stage 4)*: `(can (chase puppy cat))`

---

## 9. Mathematical Necessity of the Pipeline Order

The three transformations must occur in the exact sequence specified. Any other arrangement results in computational intractability or mathematical invalidity:

1. **T1 (Parsing) must occur first**: Raw natural language is a flat, unstructured character string. It has no syntax tree. You cannot rotate or minimize it directly because grammatical relationships (e.g., locating verbs, subjects, or modifiers) are not yet explicitly resolved. X-bar theory resolves this syntactic structure first.
2. **T2 (Canonicalization) must occur second**: X-bar trees retain language-specific word orders and empty structural categories. Rotating them into operator-first S-expressions strips away this surface layout. It is mathematically impossible to run minimization on raw X-bar trees, as the rewrite-rule search space would have to account for every permutation of linguistic syntax. S-expressions collapse syntactic variations into a uniform algebraic format.
3. **T3 (Minimization) must occur third**: Because Stage 3 has collapsed equivalent syntax structures into identical S-expressions, the minimization engine operates on a normalized, low-entropy algebraic representation. This ensures that optimization algorithms can focus purely on semantic/logical compression rather than fighting grammatical syntax variations.

---

## 10. Advanced Kolmogorov Minimization Brainstorm

Approaching the absolute Kolmogorov complexity floor (the shortest code representation that preserves semantic sufficiency) requires advanced structural transformations on the S-expression:

### 10.1 Entity Factoring and Scope Bindings (`let` expressions)
When entities or descriptors are repeated across clauses, the minimizer factors them out using local scope bindings (analogous to compiler Common Subexpression Elimination):
* **Redundant**: `((chase (dog quick brown) cat) (bark (dog quick brown)))`
* **Factored**: `(let ((d (dog quick brown))) (and (chase d cat) (bark d)))`

### 10.2 Predicate Composition (Higher-Order Factoring)
If multiple predicates apply to the same subject, they can be composed rather than repeating the subject argument:
* **Redundant**: `(and (bark dog) (run dog))`
* **Factored**: `((and bark run) dog)`

### 10.3 Conceptual Prime Decomposition
Decomposing complex vocabulary into language-independent semantic primitives (e.g., `kill` &rarr; `(cause (become (not alive)))`). While temporarily longer, this allows the optimizer to recognize and factor out shared semantic primes (like `cause` or `not`) across different verbs, increasing paragraph-wide compression.

### 10.4 Chronological/Tense Vector Coordinates
Verb helper conjugations ("would have been running") are pruned and replaced by relative numeric vectors indicating temporal offset and aspect relative to evaluation speech time $S$:
* **Standard**: `(past-perfect-continuous run dog)`
* **Compressed**: `(run dog [-1, -1, continuous])`

### 10.5 Graph Sharing (DAG Hash-Consing)
Under the hood, S-expressions are compiled as Directed Acyclic Graphs (DAGs) rather than tree lists. If a complex sub-expression is duplicated, the engine uses memory reference pointers or backreferences rather than replicating nodes:
* **Compressed**: `(and (chase #1=(dog quick black) cat) (bite #1# mouse))`

---

## 11. Native Lisp Compilability & Meta-programming

Because EngLISP targets rotated S-expressions as its core computational representation (Stage 3 and 4), it integrates natively with Lisp's **homoiconic** design. EngLISP expressions are not just static data structures—they are valid abstract syntax trees (ASTs) that can be compiled directly into executable code within any standard Lisp environment (Common Lisp, Scheme, Clojure) using **macros**.

### 11.1 The Lisp Reader & Macros
Lisp programs are read as data before they are evaluated. By loading EngLISP S-expressions into a Lisp environment, we can define macro expansion rules that intercept the rotated operators at compile-time, transforming the linguistic structure into executable Lisp code without runtime interpretation overhead.

### 11.2 Compilation Example (Common Lisp)
Given the MinimaLIST expression `(can (chase dog cat))`, we can compile it into standard executable code using Common Lisp macros:

```lisp
;; Define a macro for the modal 'can' to compile capability checks
(defmacro can (action-expr)
  `(if (has-ability-p ',(first action-expr) ,(second action-expr))
       ,(cons (first action-expr) (rest action-expr))
       (error "Capability check failed: ~A cannot ~A" 
              ',(second action-expr) ',(first action-expr))))

;; Define a macro for the verb 'chase' to compile the semantic action
(defmacro chase (subject object)
  `(execute-simulation-chase ,subject ,object))
```

During the Lisp compilation phase, the code compiles as follows:
1. **Source EngLISP S-expression**:
   ```lisp
   (can (chase dog cat))
   ```
2. **Macro Expansion (Compile-Time)**:
   ```lisp
   (if (has-ability-p 'chase dog)
       (execute-simulation-chase dog cat)
       (error "Capability check failed: dog cannot chase"))
   ```
3. **Execution**: The compiler outputs native machine instructions for the expanded Lisp code. This allows modelers to compile natural language prompts directly into high-performance binary programs.

---

## 12. Computational Theory Grounding

To situate EngLISP within theoretical computer science, we examine its representations in relation to the two foundational models of computation:

* **Lisp S-expressions & Lambda Calculus**: The Lisp S-expressions (Stage 3 and 4) function as a thin syntactic wrapper over Alonzo Church's **Lambda Calculus**. Lisp's core operations (lambda abstraction, variable binding, and application) map directly to lambda terms.
* **LLVM IR & Turing Machines**: In contrast, downstream compilation targets such as **LLVM IR** (Intermediate Representation) function as a thin syntactic wrapper over an infinite-register **Turing Machine**. LLVM's Static Single Assignment (SSA) register layout, sequential state updates, and jump transitions mirror the tape-head state machine.
* **Turing Equivalence**: Under the **Church-Turing Thesis**, Lambda Calculus (the functional paradigm) and Turing Machines (the imperative/state paradigm) are computationally equivalent. 

By translating natural language into rotated Lisp S-expressions, EngLISP grounds human communication in the algebraic structure of Lambda Calculus. Because this model is Turing-equivalent to register-based state machines like LLVM IR, EngLISP functions as a universal, mathematically complete interlingua between natural language and any computable system.

---

## 13. S-Expression Interpretation & Logical Inference Engine

To support dynamic execution, evaluation, and querying over stateful world environments, EngLISP features a stateful `WorldModel` interpreter that processes S-expressions directly.

### 13.1 Dynamic Arithmetic Evaluation
The interpreter recursively evaluates nested mathematical expressions using operators (`+`, `-`, `*`, `/`) over numeric literals and English/French text words (e.g., `"ten"` &rarr; `10`, `"deux"` &rarr; `2`). The system dynamically resolves variable symbols against stored entity values in the database (e.g., querying the value `val` of `money` to compute mathematics over state properties).

### 13.2 Backward-Chaining Logical Inference
The interpreter includes a declarative logical inference engine that processes first-order rule unification:
* **Rule Assertion**: Rules are asserted via `(=> condition consequence)` or `(if condition consequence)`.
* **SLD-Resolution Solver**: Queries containing logic variables (e.g., `(grandparent John ?who)`) are solved using a recursive backward-chaining solver that unifies query terms with rule consequences.
* **Cycle & Loop Protection**: Maintains a query call-stack of active goals to instantly detect cyclic or recursive dependencies (e.g., `ancestor(?x, ?y) => ancestor(?y, ?x)`) and terminate execution safely with `False` instead of looping infinitely.

### 13.3 Explainable AI (XAI) Proof Traces
During evaluation, the solver logs all successful factual deductions and rule applications into a proof trace. This trace is automatically converted back into a structured natural language explanation by passing each proven fact back through the Stage 1 natural language generator (e.g., *"John is a grandparent of Bob because John is a parent of Mary and Mary is a parent of Bob."*).

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
