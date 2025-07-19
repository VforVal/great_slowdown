#!/usr/bin/env python3
"""
Debug script to see what the bulk reader extracts
"""

from bulk_reader import BulkReader
import pandas as pd

def debug_extraction():
    """Debug what the bulk reader extracts."""
    print("=== Debugging Bulk Reader Extraction ===\n")
    
    # Test with a larger file
    test_file = "common/production_methods/01_industry.txt"
    
    reader = BulkReader([{
        'filepath': test_file,
        'recursive': False
    }])
    
    df = reader.read_to_dataframe()
    
    print(f"Dataframe shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    if not df.empty:
        print("\nFirst 20 rows:")
        print(df.head(20))
        
        # Look for production method keys
        pm_keys = df[df['key'].str.startswith('pm_', na=False)]
        print(f"\nProduction method keys found: {len(pm_keys)}")
        if not pm_keys.empty:
            print(pm_keys[['key', 'value']].head())
        
        # Look for goods input/output keys
        goods_keys = df[df['key'].str.contains('goods_', na=False)]
        print(f"\nGoods keys found: {len(goods_keys)}")
        if not goods_keys.empty:
            print(goods_keys[['key', 'value']].head(10))
        
        # Look for employment keys
        employment_keys = df[df['key'].str.contains('employment_', na=False)]
        print(f"\nEmployment keys found: {len(employment_keys)}")
        if not employment_keys.empty:
            print(employment_keys[['key', 'value']].head(10))
    else:
        print("No data extracted!")

if __name__ == "__main__":
    debug_extraction() 