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

from typing import List, Optional, Union, Dict, Any

class XBarNode:
    """
    Represents a node in an X-bar syntactic tree.
    In X-bar theory:
      - A phrase (XP) consists of a Specifier and an X-bar (X').
      - An X-bar (X') consists of a Head (X) and a Complement, or another X-bar and an Adjunct.
      - A Head (X) is a lexical item (terminal) or functional category.
    """
    def __init__(
        self,
        category: str,
        role: str,  # 'phrase', 'bar', 'head', 'specifier', 'complement', 'adjunct', 'terminal'
        label: Optional[str] = None,
        children: Optional[List['XBarNode']] = None
    ):
        self.category = category  # e.g., "NP", "N'", "N", "VP", "V'", "V", "IP", "I'", "I", "Det"
        self.role = role          # Grammatical role of this node relative to its parent
        self.label = label        # Text content (only if leaf/terminal node)
        self.children = children if children is not None else []

    def is_terminal(self) -> bool:
        """Returns True if the node is a terminal leaf (contains text label and no children)."""
        return len(self.children) == 0 and self.label is not None

    def collect_terminals(self) -> List[str]:
        """Recursively collects all terminal leaf labels in order."""
        if self.is_terminal():
            return [self.label]
        
        terminals = []
        for child in self.children:
            terminals.extend(child.collect_terminals())
        return terminals

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the tree into a nested dictionary."""
        data = {
            "category": self.category,
            "role": self.role
        }
        if self.label is not None:
            data["label"] = self.label
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'XBarNode':
        """Deserializes a dictionary into an XBarNode tree."""
        node = cls(
            category=data["category"],
            role=data["role"],
            label=data.get("label"),
            children=[cls.from_dict(c) for c in data.get("children", [])]
        )
        return node

    def pretty_print(self, indent: int = 0) -> str:
        """Returns a formatted string representing the hierarchical structure of the tree."""
        indent_str = "  " * indent
        role_info = f" [{self.role}]" if self.role else ""
        if self.is_terminal():
            return f"{indent_str}{self.category}{role_info}: \"{self.label}\"\n"
        
        output = f"{indent_str}{self.category}{role_info}\n"
        for child in self.children:
            output += child.pretty_print(indent + 1)
        return output

    def __repr__(self) -> str:
        if self.is_terminal():
            return f"XBarNode({self.category}, role={self.role}, label='{self.label}')"
        return f"XBarNode({self.category}, role={self.role}, children_count={len(self.children)})"
