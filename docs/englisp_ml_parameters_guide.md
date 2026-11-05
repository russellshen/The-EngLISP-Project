# EngLISP as a Parameterized Machine Learning Pipeline
**Formulating Supervised Learning & Translation Optimization (English to French)**

---

## 1. Conceptual Framing: Parameters vs. Hyperparameters

In standard machine learning:
* **Parameters (θ)**: Internal numeric weights, probabilities, or scoring values that are directly adjusted or updated based on data and loss signals.
* **Hyperparameters (γ)**: Structural, architectural, or algorithmic settings configured prior to optimization that govern the behavior of the pipeline, parsing search space, and learning process.

Because EngLISP was built as a deterministic, symbolic linguistic engine, treating it as a supervised learning model requires mapping its symbolic components to **probabilistic, weighted, or neuro-symbolic representations**.

---

## 2. Stage-by-Stage Breakdown

```
[English Text]
      │
      ▼ (Stage 1 ➔ 2: Parsing & POS Tagging)
[English X-Bar Tree]
      │
      ▼ (Stage 2 ➔ 3: Rotation & Synset Grounding)
[Interlingua S-Expression]
      │
      ▼ (Stage 3 ➔ 2: French Realization & Lexical Mapping)
[French X-Bar Tree]
      │
      ▼ (Stage 2 ➔ 1: Surface Generation)
[French Output Text]
```

### A. Stage 1 ➔ 2: English Parsing & Part-of-Speech Tagging
*(Implemented in `englisp/parser.py` via `parse()` and `GRAMMAR`)*

* **Parameters (θ):**
  * **PCFG Rule Probabilities:** In a statistical parser setting, grammar productions carry probabilities $P(\alpha \rightarrow \beta \mid \alpha)$. These weights govern structural ambiguity resolution (such as PP-attachment: attaching a prepositional phrase to a VP vs. an NP) and can be updated from parsing loss.
  * **POS Emission Scores:** For polysemous words that can act as multiple parts of speech (e.g., *"run"* as Verb vs. Noun), tag distribution weights $P(\text{POS} \mid w)$ act as parameters.
* **Hyperparameters (γ):**
  * **Chart / Beam Pruning Width ($K$):** Maximum number of active Earley states or chart edges retained at each token position.
  * **Grammar Depth Limits:** Maximum recursion depth for nested clauses or relative clauses.

---

### B. Stage 2 ➔ 3 & WSD: Canonicalization & Semantic Grounding
*(Implemented in `englisp/canonicalizer.py` and `englisp/graph_db.py` via Lesk Word Sense Disambiguation and BabelNet synset lookups)*

* **Parameters (θ):**
  * **Synset Selection Scoring Weights:** When mapping an English word to a language-neutral Synset ID:
    $$\text{Score}(s) = w_1 \cdot \text{Overlap}(s, \text{context}) + w_2 \cdot \text{PriorFreq}(s) - w_3 \cdot \text{GraphDistance}(s, \text{context\_nodes})$$
    The coefficients $w_1, w_2, w_3$ (and semantic edge weights in `SemanticGraphDB`) act as continuous parameters.
  * **Synset Prior Probabilities:** $P(\text{synset} \mid w_{\text{en}})$, encoding baseline sense frequencies.
* **Hyperparameters (γ):**
  * **Context Window Size ($W$):** Number of surrounding context tokens evaluated for Lesk overlap.
  * **Graph Traversal Depth ($D$):** Maximum hop radius when searching for concept paths in `SemanticGraphDB`.
  * **Similarity Metric:** Choice of semantic distance function (e.g., path length vs. Wu-Palmer vs. embedding cosine similarity).

---

### C. Stage 3 ➔ 4 ➔ 3: Semantic Minimization (MinimaLIST)
*(Implemented in `englisp/minimizer.py` via `minimize_sexpr` and `expand_sexpr`)*

* **Parameters (θ):**
  * **Rewrite Thresholds / Soft Rules:** Currently, rewrites like determiner pruning, double negation elimination, and antonym reductions (`(not happy)` $\rightarrow$ `sad`) are discrete Boolean operations. Each rewrite can be parameterized with an execution probability or confidence threshold $\tau_{\text{rewrite}}$.
* **Hyperparameters (γ):**
  * **Enabled Optimizations:** Binary flags toggling specific rewrite passes (e.g., `prune_determiners=True`, `passive_to_active=False`).
  * **Pass Limit:** Maximum number of iterative minimization passes over the S-expression AST.

---

### D. Stage 3 ➔ 2: French Lexical & Syntactic Realization
*(Implemented in `englisp/canonicalizer.py` via `sexpr_to_xbar` and `englisp/loader.py`)*

This is where the majority of translation discrepancies with Google Translate occur:

* **Parameters (θ):**
  * **Translation Table Probabilities $P(w_{\text{fr}} \mid w_{\text{en}})$:** Currently, `ENGLISH_TO_FRENCH_VOCAB` is a static 1-to-1 lookup. Turning this into a multinomial distribution over possible French equivalents (e.g., English *"leave"* $\rightarrow$ French *\{partir: 0.65, quitter: 0.30, laisser: 0.05\}*) creates the primary parameter set for translation learning.
  * **French Adjective Ordering Weights:** Placing adjectives pre-nominal vs. post-nominal based on `FRENCH_PRE_ADJECTIVES`. Parameterizing this as a classification weight $P(\text{pre} \mid \text{adj})$ per adjective allows learning French syntactic placement from data.
  * **Auxiliary Selection Weights:** Probabilities $P(\text{aux}=\text{"être"} \mid v)$ vs. $P(\text{aux}=\text{"avoir"} \mid v)$ for French compound past tenses.
* **Hyperparameters (γ):**
  * **Decoding Strategy:** Greedy 1-best selection vs. Beam Search across candidate French trees.
  * **Grammar Strictness:** Fallback behavior when gender is ambiguous (defaulting to masculine `"M"` vs. conditioning on context).

---

### E. Stage 2 ➔ 1: Surface Generation
*(Implemented in `englisp/parser.py` via `generate()`)*

* **Parameters (θ):**
  * Morphological elision penalty weights (if modeling contractions/elisions probabilistically).
* **Hyperparameters (γ):**
  * Deterministic phonetic/orthographic cleanup flags (handling French elisions like `le/la` $\rightarrow$ `l'`, `de` $\rightarrow$ `d'`).

---

## 3. Supervised Learning Formulation

Given:
* **Input ($x_i$):** English sentence.
* **Target ($y^*_i$):** French sentence produced by Google Translate (the reference baseline).
* **EngLISP Model ($\hat{y}_i = f(x_i; \theta, \gamma)$):** Predicted French sentence.

```
                    ┌─────────────────────────┐
      Input x       │     EngLISP Pipeline    │    Prediction ŷ
 (English sentence) │  f(x; θ_vocab, θ_wsd, …)│  (French output)
───────────────────►│                         ├────────────────► ┌─────────────┐
                    └─────────────────────────┘                  │    Loss     │
                                                                 │ Calculation │◄── Loss L(ŷ, y*)
                    ┌─────────────────────────┐                  │ (BLEU/chrF) │
      Input x       │     Google Translate    │   Reference y*   └──────┬──────┘
───────────────────►│    (Baseline Teacher)   ├────────────────► ┌──────▼──────┐
                    └─────────────────────────┘                  │ Optimization│
                                                                 │(Update θ, γ)│
                                                                 └─────────────┘
```

### Loss Functions $\mathcal{L}(\hat{y}, y^*)$
Because translation outputs are discrete sequences:
1. **Sentence-level Metric Loss:**
   * $\mathcal{L}(\hat{y}, y^*) = 1 - \text{chrF}(\hat{y}, y^*)$ or $1 - \text{BLEU}(\hat{y}, y^*)$
   * *(chrF is generally preferred for French due to inflectional suffixes and rich morphology).*
2. **Semantic Similarity Loss:**
   * $\mathcal{L}(\hat{y}, y^*) = 1 - \text{BERTScore}(\hat{y}, y^*)$
3. **Cross-Entropy Loss (if probabilistic):**
   * If EngLISP computes sequence log-likelihoods over target token derivations:
     $$\mathcal{L}(\theta) = -\sum_{t} \log P(y^*_t \mid y^*_{<t}, x; \theta)$$

---

## 4. Optimization Strategies without Standard Backpropagation

Because EngLISP is primarily symbolic, gradients cannot flow through discrete tree operations without relaxation. Three practical ways to optimize:

1. **Direct Count-Based Estimation (M-Step / Supervised Alignment):**
   * Run word alignment (e.g., using `fast-align` or GIZA++) between English source texts and Google Translate French reference outputs.
   * Directly compute maximum-likelihood translation tables:
     $$P(w_{\text{fr}} \mid w_{\text{en}}) = \frac{\text{Count}(w_{\text{en}}, w_{\text{fr}})}{\text{Count}(w_{\text{en}})}$$
   * Replace the static dictionaries in `englisp/resources/` with these empirical frequency distributions.
2. **Reinforcement Learning / Minimum Risk Training (MRT):**
   * Treat lexical choices, synset selections, and syntactic ordering decisions as actions $a \sim \pi_\theta(a \mid x)$.
   * Use REINFORCE / Policy Gradient with reward $R(\hat{y}, y^*) = \text{chrF}(\hat{y}, y^*)$ to adjust the probabilities $\theta$.
3. **Black-Box / Bayesian Optimization (for Hyperparameters & WSD Weights):**
   * Use Optuna or Ray Tune to tune continuous weights ($w_1, w_2, w_3$ in WSD scoring) and categorical hyperparameters (beam widths, minimization toggles) to directly maximize corpus BLEU/chrF against Google Translate.

---

## 5. Summary Reference Table

| Component | Nature | What Acts as a Parameter ($\theta$) | What Acts as a Hyperparameter ($\gamma$) |
| :--- | :--- | :--- | :--- |
| **Parsing** | Syntactic | PCFG rule probabilities, POS tag emission scores | Beam size $K$, recursion depth limit |
| **WSD & Synsets** | Semantic | Scoring weights ($w_{\text{overlap}}, w_{\text{dist}}$), synset priors | Context window $W$, distance metric choice |
| **MinimaLIST** | AST Rewrite | Soft rewrite execution thresholds per rule | Enabled rewrite passes, iteration pass limit |
| **Translation Vocab** | Lexical | Multilingual mapping weights $P(w_{\text{fr}} \mid w_{\text{en}})$ | Out-of-vocabulary fallback strategy |
| **French Realization** | Morphosyntactic | Adjective pre/post ordering probabilities, auxiliary weights | Strict gender defaults, search beam width |
