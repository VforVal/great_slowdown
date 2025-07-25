#!/usr/bin/env python3
"""
Functions for loading production method and goods data.
"""

import pandas as pd
import re
from typing import Dict

def load_goods_prices(goods_file_path: str = "common/goods/00_goods.txt") -> Dict[str, float]:
    """Extract goods prices from the goods file."""
    goods_prices = {}
    try:
        with open(goods_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match goods and their costs
        # Matches: good_name = { ... cost = 20 ... }
        goods_pattern = r'(\w+)\s*=\s*\{[^}]*?cost\s*=\s*(\d+)'
        matches = re.findall(goods_pattern, content, re.DOTALL)
        
        for good_name, cost in matches:
            goods_prices[good_name] = float(cost)
        
        print(f"Loaded {len(goods_prices)} goods prices")
        return goods_prices
        
    except Exception as e:
        print(f"Error loading goods prices: {e}")
        return {}

def load_pm_data(pm_csv_path: str = "production_methods.csv") -> pd.DataFrame:
    """Load production methods data from CSV."""
    try:
        pm_data = pd.read_csv(pm_csv_path)
        print(f"Loaded {len(pm_data)} production methods")
        return pm_data
    except Exception as e:
        print(f"Error loading PM data: {e}")
        return pd.DataFrame() 