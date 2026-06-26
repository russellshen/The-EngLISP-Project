# Module 2: The Four-Stage Pipeline Architecture

This module details the technical structure of EngLISP's transformation pipeline, showing how raw text becomes an executable database statement and back.

---

## The Four Stages of Representation

### Stage 1: Natural Language (NL)
*   **Format**: Raw human-readable text (English, French).
*   **Properties**: Ambiguous, redundant, inflected, and stylistically diverse.
*   **Example**: `"The quick dog chased a cat."`

### Stage 2: X-bar Syntax Tree (Linguistic IR)
*   **Format**: Hierarchical phrase structure.
*   **Properties**: Disambiguated grammatical roles, tense vectors, and gender/number agreement rules parsed via an Earley Chart Parser.
*   **Example**:
    ```text
    IP [tense: past]
    ├── Spec
    │   └── DP
    │       ├── Spec ── Det: the
    │       └── Head ── NP: dog
    └── Head
        └── VP
            ├── Head ── V: chased
            └── Comp
                └── DP
                    ├── Spec ── Det: a
                    └── Head ── NP: cat
    ```

### Stage 3: Canonical EngLISP S-Expression
*   **Format**: Rotated prefix-notation Lisp list.
*   **Properties**: Maps head verbs/relations to the head of lists, with arguments canonicalized to their base-word forms.
*   **Example**: `(chased (dog the) (cat a))`

### Stage 4: MinimaLIST S-Expression (Semantic Core)
*   **Format**: Compressed, minimized semantic code.
*   **Properties**: Eliminates determiners, redundancy, and logical negatives using Kolmogorov-inspired graph reference hash-consing and predicate composition.
*   **Example**: `(chased dog cat)`

---

## Bidirectional Flow

The pipeline is fully symmetric and bidirectional:

1.  **Forward Pipeline (Analysis)**:
    `Natural Language` $\rightarrow$ `X-bar Tree` $\rightarrow$ `EngLISP S-expression` $\rightarrow$ `MinimaLIST`
2.  **Reverse Pipeline (Synthesis)**:
    `MinimaLIST` $\rightarrow$ `EngLISP S-expression` $\rightarrow$ `X-bar Tree` $\rightarrow$ `Natural Language`

This guarantees that any compressed semantic core can be expanded back to grammatically correct, inflected, natural language text in any supported language.
