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

import os
import re
import unicodedata
from typing import Any, Dict, List, Set, Tuple

def parse_sexpr(s: str) -> Any:
    """Parses a Lisp S-expression string into nested Python lists, supporting DAG #N= and #N# notation."""
    # Preprocess to space-separate `#N=` and `#N#` tokens
    s = re.sub(r'(#\d+=)', r' \1 ', s)
    s = re.sub(r'(#\d+#)', r' \1 ', s)
    # Tokenize preserving quoted strings
    tokens = re.findall(r'\(|\)|"[^"\\]*(?:\\.[^"\\]*)*"|[^\s()]+', s)
    
    labels = {}
    
    def parse_tokens(token_list: List[str], index: int) -> Tuple[Any, int]:
        if index >= len(token_list):
            raise ValueError("Unexpected end of expression")
        
        token = token_list[index]
        if token.startswith('#') and token.endswith('=') and token[1:-1].isdigit():
            lbl_id = int(token[1:-1])
            val, next_idx = parse_tokens(token_list, index + 1)
            labels[lbl_id] = val
            return val, next_idx
        elif token.startswith('#') and token.endswith('#') and token[1:-1].isdigit():
            lbl_id = int(token[1:-1])
            if lbl_id not in labels:
                raise ValueError(f"Undefined backreference: {token}")
            return labels[lbl_id], index + 1
        elif token == '(':
            sub_list = []
            index += 1
            while index < len(token_list) and token_list[index] != ')':
                expr, next_idx = parse_tokens(token_list, index)
                sub_list.append(expr)
                index = next_idx
            if index >= len(token_list):
                raise ValueError("Unmatched open parenthesis")
            return sub_list, index + 1
        elif token == ')':
            raise ValueError("Unexpected close parenthesis")
        else:
            # Strip surrounding double quotes if present
            if token.startswith('"') and token.endswith('"') and len(token) >= 2:
                token = token[1:-1].replace('\\"', '"')
            return token, index + 1

    if not tokens:
        return ""
    
    expr, _ = parse_tokens(tokens, 0)
    return expr

def load_lson_file(filename: str) -> Any:
    """Reads and parses an LSON file from the resources directory, ignoring comments."""
    resources_dir = os.path.join(os.path.dirname(__file__), "resources")
    filepath = os.path.join(resources_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strip comments (semicolon to end of line), ignoring semicolons inside double quotes
    lines = []
    for line in content.splitlines():
        inside_quotes = False
        escaped = False
        comment_idx = -1
        for idx, char in enumerate(line):
            if char == '\\' and not escaped:
                escaped = True
                continue
            if char == '"' and not escaped:
                inside_quotes = not inside_quotes
            elif char == ';' and not inside_quotes:
                comment_idx = idx
                break
            escaped = False
        if comment_idx != -1:
            line = line[:comment_idx]
        lines.append(line)
    clean_content = " ".join(lines).strip()
    
    return parse_sexpr(clean_content)

def load_dict(filename: str) -> Dict[str, str]:
    data = load_lson_file(filename)
    return {item[0]: item[1] for item in data}

def load_set(filename: str) -> Set[str]:
    data = load_lson_file(filename)
    return set(data)

def load_grammar(filename: str) -> Dict[str, List[Tuple[str, ...]]]:
    data = load_lson_file(filename)
    grammar = {}
    for entry in data:
        lhs = entry[0]
        rhs_list = []
        for rhs in entry[1:]:
            rhs_list.append(tuple(rhs))
        grammar[lhs] = rhs_list
    return grammar

def load_contractions(filename: str) -> Dict[str, str]:
    data = load_lson_file(filename)
    contractions = {}
    for item in data:
        key = item[0]
        val = item[1]
        if isinstance(val, list):
            contractions[key] = " ".join(val)
        else:
            contractions[key] = val
    return contractions

def load_verb_forms(filename: str) -> Dict[str, Tuple[str, ...]]:
    data = load_lson_file(filename)
    return {item[0]: tuple(item[1]) for item in data}

def load_babelnet(filename: str) -> Dict[str, Dict[str, Any]]:
    data = load_lson_file(filename)
    synsets = {}
    for entry in data:
        synset_id = entry[0]
        synset_data = {}
        for field in entry[1:]:
            field_name = field[0]
            if field_name == "definition":
                synset_data["definition"] = " ".join(flatten_list(field[1]))
            elif field_name == "words":
                words_dict = {}
                for lang_entry in field[1:]:
                    lang = lang_entry[0]
                    word_list = lang_entry[1]
                    words_dict[lang] = word_list
                synset_data["words"] = words_dict
        synsets[synset_id] = synset_data
    return synsets

def load_primes(filename: str) -> Dict[str, List[Any]]:
    data = load_lson_file(filename)
    return {item[0]: item[1] for item in data}

def flatten_list(lst: Any) -> List[str]:
    if isinstance(lst, str):
        return [lst]
    elif isinstance(lst, list):
        res = []
        for item in lst:
            res.extend(flatten_list(item))
        return res
    else:
        return [str(lst)]

# ----------------- Lazy Partitioned Dictionaries -----------------

def get_partition_char(word: str) -> str:
    if not isinstance(word, str) or not word:
        return "other"
    first_char = word[0].lower()
    if not first_char.isalpha():
        return "other"
    normalized = unicodedata.normalize('NFD', first_char)
    ascii_char = "".join(c for c in normalized if c.isascii() and c.isalpha())
    return ascii_char if ascii_char else "other"

import contextvars
CURRENT_USER_TIER = contextvars.ContextVar("CURRENT_USER_TIER", default="free")

class LazyPartitionedDict(dict):
    def __init__(self, lang_prefix: str, pattern: str, load_fn, force_sample: bool = False):
        self.lang_prefix = lang_prefix
        self.pattern = pattern
        self.load_fn = load_fn
        self.force_sample = force_sample
        self.loaded_partitions = set()
        super().__init__()

    def _load_partition_for_word(self, word: str):
        if not isinstance(word, str):
            return
        p = get_partition_char(word)
        if p not in self.loaded_partitions:
            self.loaded_partitions.add(p)
            if self.force_sample:
                fallback_filename = f"sample_{self.lang_prefix}.lson"
                try:
                    part_data = self.load_fn(fallback_filename)
                    self.update(part_data)
                except FileNotFoundError:
                    pass
            else:
                filename = self.pattern.format(prefix=self.lang_prefix, char=p)
                try:
                    part_data = self.load_fn(filename)
                    self.update(part_data)
                except FileNotFoundError:
                    fallback_filename = f"sample_{self.lang_prefix}.lson"
                    try:
                        part_data = self.load_fn(fallback_filename)
                        self.update(part_data)
                    except FileNotFoundError:
                        pass

    def _load_all_partitions(self):
        for char in "abcdefghijklmnopqrstuvwxyz":
            self._load_partition_for_word(char)
        self._load_partition_for_word("other")

    def __contains__(self, key: Any) -> bool:
        self._load_partition_for_word(key)
        return super().__contains__(key)

    def __getitem__(self, key: Any) -> Any:
        self._load_partition_for_word(key)
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        self._load_partition_for_word(key)
        return super().get(key, default)

    def keys(self):
        self._load_all_partitions()
        return super().keys()

    def values(self):
        self._load_all_partitions()
        return super().values()

    def items(self):
        self._load_all_partitions()
        return super().items()

    def __iter__(self):
        self._load_all_partitions()
        return super().__iter__()

    def __len__(self):
        self._load_all_partitions()
        return super().__len__()


class LazySynsets(dict):
    def __init__(self, force_sample: bool = False):
        self.force_sample = force_sample
        self.loaded_partitions = set()
        super().__init__()

    def _load_partition_for_id(self, syn_id: str):
        if not isinstance(syn_id, str) or len(syn_id) < 3:
            return
        prefix = syn_id[:3]
        if prefix not in self.loaded_partitions:
            self.loaded_partitions.add(prefix)
            if self.force_sample:
                try:
                    part_data = load_babelnet("sample_synsets.lson")
                    self.update(part_data)
                except FileNotFoundError:
                    pass
            else:
                filename = f"synsets_{prefix}.lson"
                try:
                    part_data = load_babelnet(filename)
                    self.update(part_data)
                except FileNotFoundError:
                    try:
                        part_data = load_babelnet("sample_synsets.lson")
                        self.update(part_data)
                    except FileNotFoundError:
                        pass

    def __contains__(self, key: Any) -> bool:
        self._load_partition_for_id(key)
        return super().__contains__(key)

    def __getitem__(self, key: Any) -> Any:
        self._load_partition_for_id(key)
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        self._load_partition_for_id(key)
        return super().get(key, default)


class TierDelegatingDict(dict):
    def __init__(self, sample_dict, full_dict):
        self.sample_dict = sample_dict
        self.full_dict = full_dict
    def _get_active(self):
        tier = CURRENT_USER_TIER.get()
        return self.full_dict if tier == "paid" else self.sample_dict
    def __contains__(self, key) -> bool:
        return key in self._get_active()
    def __getitem__(self, key) -> Any:
        return self._get_active()[key]
    def get(self, key, default=None) -> Any:
        return self._get_active().get(key, default)
    def keys(self):
        return self._get_active().keys()
    def values(self):
        return self._get_active().values()
    def items(self):
        return self._get_active().items()
    def __iter__(self):
        return iter(self._get_active())
    def __len__(self):
        return len(self._get_active())


# Lazy loading dictionary structures
LEXICON_SAMPLE = LazyPartitionedDict("en_lexicon", "{prefix}_{char}.lson", load_dict, force_sample=True)
LEXICON_FULL = LazyPartitionedDict("en_lexicon", "{prefix}_{char}.lson", load_dict, force_sample=False)
LEXICON = TierDelegatingDict(LEXICON_SAMPLE, LEXICON_FULL)

FRENCH_LEXICON_SAMPLE = LazyPartitionedDict("fr_lexicon", "{prefix}_{char}.lson", load_dict, force_sample=True)
FRENCH_LEXICON_FULL = LazyPartitionedDict("fr_lexicon", "{prefix}_{char}.lson", load_dict, force_sample=False)
FRENCH_LEXICON = TierDelegatingDict(FRENCH_LEXICON_SAMPLE, FRENCH_LEXICON_FULL)

FRENCH_TO_ENGLISH_VOCAB_SAMPLE = LazyPartitionedDict("french_to_english_vocab", "{prefix}_{char}.lson", load_dict, force_sample=True)
FRENCH_TO_ENGLISH_VOCAB_FULL = LazyPartitionedDict("french_to_english_vocab", "{prefix}_{char}.lson", load_dict, force_sample=False)
FRENCH_TO_ENGLISH_VOCAB = TierDelegatingDict(FRENCH_TO_ENGLISH_VOCAB_SAMPLE, FRENCH_TO_ENGLISH_VOCAB_FULL)

ENGLISH_TO_FRENCH_VOCAB_SAMPLE = LazyPartitionedDict("english_to_french_vocab", "{prefix}_{char}.lson", load_dict, force_sample=True)
ENGLISH_TO_FRENCH_VOCAB_FULL = LazyPartitionedDict("english_to_french_vocab", "{prefix}_{char}.lson", load_dict, force_sample=False)
ENGLISH_TO_FRENCH_VOCAB = TierDelegatingDict(ENGLISH_TO_FRENCH_VOCAB_SAMPLE, ENGLISH_TO_FRENCH_VOCAB_FULL)

FRENCH_GENDER_SAMPLE = LazyPartitionedDict("french_gender", "{prefix}_{char}.lson", load_dict, force_sample=True)
FRENCH_GENDER_FULL = LazyPartitionedDict("french_gender", "{prefix}_{char}.lson", load_dict, force_sample=False)
FRENCH_GENDER = TierDelegatingDict(FRENCH_GENDER_SAMPLE, FRENCH_GENDER_FULL)

ENGLISH_VERB_FORMS_SAMPLE = LazyPartitionedDict("english_verb_forms", "{prefix}_{char}.lson", load_verb_forms, force_sample=True)
ENGLISH_VERB_FORMS_FULL = LazyPartitionedDict("english_verb_forms", "{prefix}_{char}.lson", load_verb_forms, force_sample=False)
ENGLISH_VERB_FORMS = TierDelegatingDict(ENGLISH_VERB_FORMS_SAMPLE, ENGLISH_VERB_FORMS_FULL)

FRENCH_VERB_FORMS_SAMPLE = LazyPartitionedDict("french_verb_forms", "{prefix}_{char}.lson", load_verb_forms, force_sample=True)
FRENCH_VERB_FORMS_FULL = LazyPartitionedDict("french_verb_forms", "{prefix}_{char}.lson", load_verb_forms, force_sample=False)
FRENCH_VERB_FORMS = TierDelegatingDict(FRENCH_VERB_FORMS_SAMPLE, FRENCH_VERB_FORMS_FULL)

WORD_TO_SYNSETS_SAMPLE = LazyPartitionedDict("word_to_synsets", "{prefix}_{char}.lson", load_dict, force_sample=True)
WORD_TO_SYNSETS_FULL = LazyPartitionedDict("word_to_synsets", "{prefix}_{char}.lson", load_dict, force_sample=False)
WORD_TO_SYNSETS = TierDelegatingDict(WORD_TO_SYNSETS_SAMPLE, WORD_TO_SYNSETS_FULL)

# Lazy loading synsets
BABELNET_SYNSETS_SAMPLE = LazySynsets(force_sample=True)
BABELNET_SYNSETS_FULL = LazySynsets(force_sample=False)
BABELNET_SYNSETS = TierDelegatingDict(BABELNET_SYNSETS_SAMPLE, BABELNET_SYNSETS_FULL)

# Flat loading rules (small files, loaded at startup)
GRAMMAR = load_grammar("grammar.lson")
FRENCH_GRAMMAR = load_grammar("french_grammar.lson")
ENGLISH_CONTRACTIONS = load_contractions("english_contractions.lson")
FRENCH_ADJ_FEMININE = load_dict("french_adj_feminine.lson")
FRENCH_PRE_ADJECTIVES = load_set("french_pre_adjectives.lson")
TENSE_AUXILIARIES = load_set("tense_auxiliaries.lson")
STOPWORDS = load_set("stopwords.lson")
CONCEPTUAL_PRIMES = load_primes("conceptual_primes.lson")
ORIGINAL_SYNSETS = load_set("original_synsets.lson")
ORIGINAL_EN_WORDS = load_set("original_en_words.lson")
ORIGINAL_FR_WORDS = load_set("original_fr_words.lson")



def to_tuple(expr):
    if isinstance(expr, list):
        return tuple(to_tuple(x) for x in expr)
    return expr

INVERSE_CONCEPTUAL_PRIMES = {to_tuple(v): k for k, v in CONCEPTUAL_PRIMES.items()}
