import pyradox
import pandas as pd
from typing import Dict, List, Union, Callable, Optional, Any
import fnmatch
import re
import os
from pathlib import Path

class BulkReader:
    def __init__(self, file_configs: List[Dict]):
        """
        file_configs: List of dicts, each with:
            - 'filepath': str (file or directory path)
            - 'keys': list of str (extract only these keys, anywhere in the tree)
            - 'pattern': str (wildcard or regex pattern for key matching, e.g. '*_add')
            - 'output_columns': list of str (column names for the dataframe)
            - 'extract_func': callable (optional custom extraction function)
            - 'recursive': bool (if filepath is directory, search recursively)
            - 'file_pattern': str (wildcard pattern for files in directory, e.g. '*.txt')
        If both 'keys' and 'pattern' are None/missing/empty, all numeric values will be extracted.
        """
        self.file_configs = file_configs

    def key_matches(self, key: str, keys: Optional[List[str]], pattern: Optional[str]) -> bool:
        """Check if a key matches the specified keys list or pattern."""
        # Convert key to string to handle pyradox.Token types
        key_str = str(key)
        
        if keys:
            return key_str in keys
        if pattern:
            # Support both fnmatch wildcards and regex (if pattern starts with 're:')
            if pattern.startswith('re:'):
                regex = pattern[3:]
                return re.fullmatch(regex, key_str) is not None
            else:
                return fnmatch.fnmatch(key_str, pattern)
        return True  # If no keys/pattern specified, match everything

    def extract_data_from_node(self, node: Any, filepath: str, keys: Optional[List[str]], 
                              pattern: Optional[str], extract_func: Optional[Callable] = None) -> List[Dict]:
        """Extract data from a node recursively."""
        data = []
        
        if hasattr(node, 'items'):
            for k, v in node.items():
                key_str = str(k)
                
                # Check if this key should be extracted
                if self.key_matches(key_str, keys, pattern):
                    if extract_func:
                        extracted = extract_func(key_str, v, filepath)
                        if extracted:
                            data.append(extracted)
                    elif isinstance(v, (int, float)):
                        data.append({
                            'filepath': filepath,
                            'key': key_str,
                            'value': v,
                            'type': type(v).__name__
                        })
                    elif isinstance(v, str):
                        data.append({
                            'filepath': filepath,
                            'key': key_str,
                            'value': v,
                            'type': 'string'
                        })
                
                # Recursively process nested structures
                if isinstance(v, (dict, list)) or hasattr(v, 'items'):
                    data.extend(self.extract_data_from_node(v, filepath, keys, pattern, extract_func))
                    
        elif isinstance(node, list):
            for item in node:
                data.extend(self.extract_data_from_node(item, filepath, keys, pattern, extract_func))
                
        return data

    def get_files_to_process(self, filepath: str, recursive: bool = False, file_pattern: str = "*.txt") -> List[str]:
        """Get list of files to process from a filepath (file or directory)."""
        path = Path(filepath)
        
        if path.is_file():
            return [str(path)]
        elif path.is_dir():
            files = []
            if recursive:
                files = list(path.rglob(file_pattern))
            else:
                files = list(path.glob(file_pattern))
            return [str(f) for f in files]
        else:
            print(f"Warning: {filepath} is not a valid file or directory")
            return []

    def process_file(self, filepath: str, keys: Optional[List[str]], pattern: Optional[str], 
                    extract_func: Optional[Callable] = None) -> List[Dict]:
        """Process a single file and extract data."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = pyradox.parse(f.read())
            
            return self.extract_data_from_node(tree, filepath, keys, pattern, extract_func)
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []

    def read_to_dataframe(self) -> pd.DataFrame:
        """Read all configured files and return a pandas DataFrame."""
        all_data = []
        
        for config in self.file_configs:
            filepath = config['filepath']
            keys = config.get('keys')
            pattern = config.get('pattern')
            extract_func = config.get('extract_func')
            recursive = config.get('recursive', False)
            file_pattern = config.get('file_pattern', "*.txt")
            
            files = self.get_files_to_process(filepath, recursive, file_pattern)
            
            for f in files:
                data = self.process_file(f, keys, pattern, extract_func)
                all_data.extend(data)
                
            print(f"Processed {len(files)} files from {filepath}")
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        
        # Reorder columns to put filepath first
        if 'filepath' in df.columns:
            cols = ['filepath'] + [col for col in df.columns if col != 'filepath']
            df = df[cols]
        
        return df

    def read_to_csv(self, output_path: str, **kwargs) -> None:
        """Read data and save to CSV file."""
        df = self.read_to_dataframe()
        if not df.empty:
            df.to_csv(output_path, index=False, **kwargs)
            print(f"Data saved to {output_path}")
        else:
            print("No data to save")

    def read_to_excel(self, output_path: str, **kwargs) -> None:
        """Read data and save to Excel file."""
        df = self.read_to_dataframe()
        if not df.empty:
            df.to_excel(output_path, index=False, **kwargs)
            print(f"Data saved to {output_path}")
        else:
            print("No data to save")

# Example usage and utility functions
def create_production_method_reader(filepath: str, recursive: bool = True) -> BulkReader:
    """Create a reader specifically for production method files."""
    
    def extract_production_method_data(key: str, value: Any, filepath: str) -> Optional[Dict]:
        """Extract production method specific data."""
        if isinstance(value, (int, float)):
            return {
                'filepath': filepath,
                'key': key,
                'value': value,
                'type': 'numeric'
            }
        elif isinstance(value, str):
            return {
                'filepath': filepath,
                'key': key,
                'value': value,
                'type': 'string'
            }
        return None
    
    config = {
        'filepath': filepath,
        'recursive': recursive,
        'file_pattern': '*.txt',
        'extract_func': extract_production_method_data
    }
    
    return BulkReader([config])

def create_building_reader(filepath: str, recursive: bool = True) -> BulkReader:
    """Create a reader specifically for building files."""
    
    def extract_building_data(key: str, value: Any, filepath: str) -> Optional[Dict]:
        """Extract building specific data."""
        if isinstance(value, (int, float)):
            return {
                'filepath': filepath,
                'key': key,
                'value': value,
                'type': 'numeric'
            }
        elif isinstance(value, str):
            return {
                'filepath': filepath,
                'key': key,
                'value': value,
                'type': 'string'
            }
        return None
    
    config = {
        'filepath': filepath,
        'recursive': recursive,
        'file_pattern': '*.txt',
        'extract_func': extract_building_data
    }
    
    return BulkReader([config])

# Example usage
if __name__ == "__main__":
    # Example 1: Read all production methods
    reader = create_production_method_reader("common/production_methods")
    df = reader.read_to_dataframe()
    print(f"Extracted {len(df)} data points from production methods")
    print(df.head())
    
    # Example 2: Read specific keys from buildings
    building_reader = BulkReader([{
        'filepath': 'common/buildings',
        'keys': ['base_goods_output', 'base_goods_input', 'level'],
        'recursive': True
    }])
    
    building_df = building_reader.read_to_dataframe()
    print(f"Extracted {len(building_df)} building data points")
    print(building_df.head())
    
    # Example 3: Read using pattern matching
    pattern_reader = BulkReader([{
        'filepath': 'common/production_methods',
        'pattern': '*_add',  # All keys ending with '_add'
        'recursive': True
    }])
    
    pattern_df = pattern_reader.read_to_dataframe()
    print(f"Extracted {len(pattern_df)} pattern-matched data points")
    print(pattern_df.head()) 