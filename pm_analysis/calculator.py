#!/usr/bin/env python3
"""
Core profitability calculation logic for production methods.
"""

import pandas as pd
import ast
from typing import Dict

def calculate_pm_profitability(pm_data: pd.DataFrame, goods_prices: Dict[str, float]) -> pd.DataFrame:
    """Calculate profitability for each production method."""
    if pm_data is None or pm_data.empty:
        print("No PM data loaded!")
        return pd.DataFrame()
    
    if not goods_prices:
        print("No goods prices loaded!")
        return pd.DataFrame()
    
    results = []
    
    for _, row in pm_data.iterrows():
        pm_info = {
            'production_method_name': row['production_method_name'],
            'parent_building': row['parent_building'],
            'filename': row['filename'],
            'total_employment': row['total_employment'],
            'input_cost': 0,
            'output_revenue': 0,
            'total_profit': 0,
            'profit_per_employee': 0,
            'input_goods': {},
            'output_goods': {},
            'missing_input_prices': [],
            'missing_output_prices': []
        }
        
        # Parse inputs and calculate input cost
        try:
            inputs_str = row['inputs']
            inputs = ast.literal_eval(inputs_str) if isinstance(inputs_str, str) and inputs_str != '{}' else {}
            for good, quantity in inputs.items():
                if good in goods_prices:
                    cost = goods_prices[good] * quantity
                    pm_info['input_cost'] += cost
                    pm_info['input_goods'][good] = {
                        'quantity': quantity,
                        'price': goods_prices[good],
                        'total_cost': cost
                    }
                else:
                    pm_info['missing_input_prices'].append(good)
        except (ValueError, SyntaxError):
            pm_info['missing_input_prices'].append('parse_error')
        
        # Parse outputs and calculate output revenue
        try:
            outputs_str = row['outputs']
            outputs = ast.literal_eval(outputs_str) if isinstance(outputs_str, str) and outputs_str != '{}' else {}
            for good, quantity in outputs.items():
                if good in goods_prices:
                    revenue = goods_prices[good] * quantity
                    pm_info['output_revenue'] += revenue
                    pm_info['output_goods'][good] = {
                        'quantity': quantity,
                        'price': goods_prices[good],
                        'total_revenue': revenue
                    }
                else:
                    pm_info['missing_output_prices'].append(good)
        except (ValueError, SyntaxError):
            pm_info['missing_output_prices'].append('parse_error')
        
        # Calculate total profit
        pm_info['total_profit'] = pm_info['output_revenue'] - pm_info['input_cost']
        
        # Calculate profit per employee (avoid division by zero)
        if pm_info['total_employment'] != 0:
            pm_info['profit_per_employee'] = pm_info['total_profit'] / pm_info['total_employment']
        else:
            # If no employment, mark as unknown rather than infinite
            pm_info['profit_per_employee'] = None
            pm_info['employment_status'] = 'no_employment_data'
        
        results.append(pm_info)
    
    return pd.DataFrame(results) 