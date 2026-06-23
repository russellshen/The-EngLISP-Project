# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.
#
# For commercial licensing inquiries, please contact:
# Russell Shen (russellshen7@gmail.com)
#
# Licensing terms, scope, and compensation are subject to separate negotiation.
#
# Reference the footer section of any of the 4 .md files (README.md, SPECIFICATION.md,
# USE_CASES.md, LEXICAL_STRATEGIES.md) in the project's root directory for full licensing details.
#
# I am the sole original creator of the EngLISP project (around August 2025), and did not rely on
# the resources of any academic institution or private individual to develop it.

import uuid
from typing import List, Dict, Set, Tuple, Any

class SemanticGraphDB:
    """
    A relational Semantic Graph Database representing entities as nodes and relationships as edges.
    Supports recursive IS_A type inheritance traversals and semantic queries.
    """
    def __init__(self):
        # node_id -> dict of properties
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # list of tuples: (source_node_id, target_node_id, relation_type)
        self.edges: List[Tuple[str, str, str]] = []

    def clear(self):
        """Clears all nodes and edges from the database."""
        self.nodes.clear()
        self.edges.clear()

    def add_node(self, node_id: str, properties: Dict[str, Any] = None):
        """Adds a node with optional properties to the graph."""
        if node_id not in self.nodes:
            self.nodes[node_id] = {}
        if properties:
            self.nodes[node_id].update(properties)

    def add_edge(self, source: str, target: str, rel_type: str):
        """Adds a directed edge between source and target with a relationship type."""
        self.add_node(source)
        self.add_node(target)
        edge = (source, target, rel_type)
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, source: str, target: str, rel_type: str):
        """Removes a specific edge from the graph."""
        edge = (source, target, rel_type)
        if edge in self.edges:
            self.edges.remove(edge)

    def traverse_is_a(self, node_id: str) -> Set[str]:
        """
        Recursively traverses IS_A relationships from the node to find all inherited types/concepts.
        E.g., fido -> dog -> canine -> animal.
        """
        visited = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                # Add all target concepts connected via IS_A edges
                for src, tgt, rel in self.edges:
                    if src == curr and rel.upper() == "IS_A":
                        queue.append(tgt)
        return visited

    def add_fact(self, pred: str, args: List[str]):
        """Asserts a semantic fact (unary, binary, or ternary+) into the graph database."""
        if not args:
            return
            
        # Unary relation: e.g. ("lazy", "dog")
        if len(args) == 1:
            # If pred is a noun synset, treat as type classification (IS_A)
            if pred.startswith("n") and len(pred) > 1 and pred[1].isdigit():
                self.add_edge(args[0], pred, "IS_A")
            else:
                self.add_edge(args[0], pred, "property")
            
        # Binary relation: e.g. ("chased", "dog", "cat") -> add direct relation edge
        elif len(args) == 2:
            if pred.upper() == "IS_A":
                self.add_edge(args[0], args[1], "IS_A")
            else:
                self.add_edge(args[0], args[1], pred)
                
        # Ternary or higher arity: e.g. ("gives", "dog", "cat", "book") -> construct relation node
        else:
            rel_id = f"rel_{pred}_{uuid.uuid4().hex[:8]}"
            self.add_node(rel_id, {"type": "relation", "pred": pred})
            for idx, arg in enumerate(args):
                self.add_edge(rel_id, arg, f"arg_{idx}")

    def remove_fact(self, pred: str, args: List[str]):
        """Removes a semantic fact (unary, binary, or ternary+) from the graph database."""
        if not args:
            return

        if len(args) == 1:
            if pred.startswith("n") and len(pred) > 1 and pred[1].isdigit():
                self.remove_edge(args[0], pred, "IS_A")
            else:
                self.remove_edge(args[0], pred, "property")
        elif len(args) == 2:
            if pred.upper() == "IS_A":
                self.remove_edge(args[0], args[1], "IS_A")
            else:
                self.remove_edge(args[0], args[1], pred)
        else:
            # Find hypernode
            to_remove_node = None
            for node_id, props in list(self.nodes.items()):
                if props.get("type") == "relation" and props.get("pred") == pred:
                    # check if args match
                    rel_args = {}
                    for src, tgt, rel in self.edges:
                        if src == node_id and rel.startswith("arg_"):
                            try:
                                idx = int(rel.split("_")[1])
                                rel_args[idx] = tgt
                            except ValueError:
                                pass
                    matched = True
                    if len(rel_args) == len(args):
                        for idx, arg in enumerate(args):
                            if rel_args.get(idx) != arg:
                                matched = False
                                break
                    else:
                        matched = False
                    if matched:
                        to_remove_node = node_id
                        break
            if to_remove_node:
                # remove node
                del self.nodes[to_remove_node]
                # remove edges
                self.edges = [e for e in self.edges if e[0] != to_remove_node]


    def query(self, pred: str, args: List[str]) -> bool:
        """
        Checks if a predicate fact holds, taking into account IS_A inheritance.
        """
        if not args:
            return False

        # 1. IS_A relation check: args[1] must be in the type inheritance path of args[0]
        if pred.upper() == "IS_A" and len(args) == 2:
            return args[1] in self.traverse_is_a(args[0])

        # Traverse type hierarchies for all arguments
        ancestors_list = [self.traverse_is_a(arg) for arg in args]

        # 2. Unary property query: check if the property holds for any ancestor node
        if len(args) == 1:
            if pred in ancestors_list[0]:
                return True
            for anc in ancestors_list[0]:
                for src, tgt, rel in self.edges:
                    if src == anc and rel == "property" and tgt == pred:
                        return True
            return False

        # 3. Binary relation query: check if relation exists between any pair of ancestors
        elif len(args) == 2:
            for anc1 in ancestors_list[0]:
                for anc2 in ancestors_list[1]:
                    for src, tgt, rel in self.edges:
                        if src == anc1 and tgt == anc2 and rel == pred:
                            return True
            return False

        # 4. Ternary or higher arity query: match against relation hypernodes
        else:
            for node_id, props in self.nodes.items():
                if props.get("type") == "relation" and props.get("pred") == pred:
                    # Gather linked arguments of the hypernode
                    rel_args = {}
                    for src, tgt, rel in self.edges:
                        if src == node_id and rel.startswith("arg_"):
                            try:
                                idx = int(rel.split("_")[1])
                                rel_args[idx] = tgt
                            except ValueError:
                                pass
                    if len(rel_args) == len(args):
                        matches = True
                        for idx, anc_set in enumerate(ancestors_list):
                            val = rel_args.get(idx)
                            # The relation node argument must either be in the ancestor set of the query argument
                            # or be an ancestor of the query argument.
                            if val not in anc_set and not any(v in self.traverse_is_a(args[idx]) for v in self.traverse_is_a(val)):
                                matches = False
                                break
                        if matches:
                            return True
            return False

    def get_all_facts(self) -> List[Tuple[str, ...]]:
        """Reconstructs and returns all normalized tuple facts stored in the graph database."""
        facts = set()
        
        # Unary facts from properties
        for src, tgt, rel in self.edges:
            if rel == "property":
                facts.add((tgt, src))
            elif rel != "IS_A" and not src.startswith("rel_"):
                facts.add((rel, src, tgt))
            elif rel.upper() == "IS_A":
                facts.add(("IS_A", src, tgt))
                facts.add((tgt, src))

        # Ternary facts from hypernodes
        for node_id, props in self.nodes.items():
            if props.get("type") == "relation":
                pred = props["pred"]
                args_map = {}
                for src, tgt, rel in self.edges:
                    if src == node_id and rel.startswith("arg_"):
                        try:
                            idx = int(rel.split("_")[1])
                            args_map[idx] = tgt
                        except ValueError:
                            pass
                args = [args_map[i] for i in sorted(args_map.keys())]
                facts.add((pred, *args))

        return sorted(list(facts))
