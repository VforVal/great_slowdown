import pyradox
from typing import Dict, List, Union, Callable, Optional
import fnmatch
import re

class BulkEditor:
    def __init__(self, file_configs: List[Dict]):
        """
        file_configs: List of dicts, each with:
            - 'filepath': str
            - 'keys': list of str (edit only these keys, anywhere in the tree)
            - 'pattern': str (wildcard or regex pattern for key matching, e.g. '*_add')
            - 'multiplier': float (optional)
            - 'overwrite': int (optional)
        If both 'keys' and 'pattern' are None/missing/empty, nothing will be edited.
        """
        self.file_configs = file_configs

    @staticmethod
    def round10(x: float) -> int:
        return int(round(x / 10.0) * 10)

    def key_matches(self, key: str, keys: Optional[List[str]], pattern: Optional[str]) -> bool:
        if keys:
            return key in keys
        if pattern:
            # Support both fnmatch wildcards and regex (if pattern starts with 're:')
            if pattern.startswith('re:'):
                regex = pattern[3:]
                return re.fullmatch(regex, key) is not None
            else:
                return fnmatch.fnmatch(key, pattern)
        return False

    def traverse_and_edit(self, node, keys: Optional[List[str]], pattern: Optional[str], edit_func: Callable[[str, Union[int, float]], Optional[int]]) -> int:
        edits = 0
        if hasattr(node, 'items'):
            for k, v in node.items():
                if isinstance(v, (dict, list)) or hasattr(v, 'items'):
                    edits += self.traverse_and_edit(v, keys, pattern, edit_func)
                if self.key_matches(str(k), keys, pattern):
                    if isinstance(v, (int, float)):
                        new_val = edit_func(str(k), v)
                        if new_val is not None and new_val != v:
                            node[k] = new_val
                            edits += 1
        elif isinstance(node, list):
            for item in node:
                edits += self.traverse_and_edit(item, keys, pattern, edit_func)
        return edits

    def process_file(self, filepath: str, keys: Optional[List[str]], pattern: Optional[str], multiplier: Optional[float] = None, overwrite: Optional[int] = None) -> int:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = pyradox.parse(f.read())
        def edit_func(key, value):
            if overwrite is not None:
                return self.round10(overwrite)
            elif multiplier is not None:
                return self.round10(value * multiplier)
            return None
        edits = self.traverse_and_edit(tree, keys, pattern, edit_func)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(tree))
        return edits

    def run(self):
        for config in self.file_configs:
            filepath = config['filepath']
            keys = config.get('keys')
            pattern = config.get('pattern')
            multiplier = config.get('multiplier')
            overwrite = config.get('overwrite')
            edits = self.process_file(filepath, keys, pattern, multiplier, overwrite)
            print(f"{filepath}: {edits} edits made.") 