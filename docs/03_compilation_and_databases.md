# Module 3: Compilation, Databases, & Agent Sandbox

This module explains how EngLISP integrates S-expression structures into native runtime languages, database query engines, and multi-agent simulations.

---

## 1. Native Language Compilation Targets

EngLISP compiles S-expressions directly into standalone, executable code blocks for three Lisp runtimes:

### Common Lisp
*   Uses standard boilerplate hashes to track facts.
*   Declares custom relational predicates using `defun` functions forwarding to hash checks.
*   Handles assertions using `(add-fact "pred" args)`.

### Scheme
*   Maintains fact lookup lists.
*   Declares custom predicates using `define` structures.
*   Handles assertions using `(add-fact! "pred" args)`.

### Clojure / ClojureScript
*   Stores fact data inside a thread-safe STM state atom `(atom #{})`.
*   Uses Clojure vectors `[var val]` for `let` bindings and anonymous closures `(fn [_] ...)` for quantifiers.
*   Handles assertions using `(add-fact! "pred" args)`.

---

## 2. Database Query Compiler Targets

To compile natural language instructions directly into production database statements, EngLISP S-expressions are compiled to:

### SQL Target
*   **Assertions**: Transformed to `INSERT INTO` statements.
*   **Queries**: Transformed to `SELECT ... WHERE ...` statements.
*   **Variable Joins**: Conjunctions like `(and (chased ?x ?y) (lazy ?x))` compile to optimized relational SQL self-joins:
    ```sql
    SELECT t0.subject AS x, t0.object AS y 
    FROM chased t0, lazy t1 
    WHERE t1.subject = t0.subject;
    ```

### Neo4j Cypher Target
*   **Assertions**: Transformed to Graph node `MERGE` and relationship `CREATE` statements.
*   **Queries**: Compiled to graph `MATCH ... RETURN` statements.

### MongoDB Target
*   **Assertions**: Transformed to JSON document `db.collection.insertOne(...)`.
*   **Conjunctions**: Compiled to Mongo aggregation pipelines using `$lookup` and `$project` joins.

---

## 3. Interactive Agent Sandbox

The Interactive Agent Sandbox establishes a reactive multi-agent system executing S-expressions in a shared world database:

1.  **Agent Alice (Observer)**:
    Observes natural language inputs, parses them into EngLISP S-expressions, and asserts them into the shared state database.
2.  **Agent Bob (Reasoner)**:
    Runs logic queries using variables (e.g. `(chased ?who cat)`) to fetch matches from the database.
3.  **Agent Charlie (Inferrer)**:
    Asserts logical inference rules (e.g. `(=> (lazy ?x) (sleeps ?x))`) and runs queries to derive inferred conclusions, asserting new facts to the state.
