#!/usr/bin/env python3
"""
Test the bulk reader with a single production method file
"""

from bulk_tools.bulk_reader import BulkReader

def test_single_file():
    """Test bulk reader with a single file."""
    print("=== Testing Bulk Reader with Single File ===\n")
    
    # Test with the dummy file
    config = {
        'filepath': 'common/production_methods/00_dummy.txt',
        'recursive': False
    }
    
    reader = BulkReader([config])
    
    print("Reading data...")
    df = reader.read_to_dataframe()
    
    print(f"Dataframe shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    if not df.empty:
        print("\nData found:")
        print(df.head())
    else:
        print("\nNo data extracted!")
    
    return len(df) > 0

if __name__ == "__main__":
    test_single_file() 