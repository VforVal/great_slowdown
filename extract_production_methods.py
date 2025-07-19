#!/usr/bin/env python3
"""
Extract Production Methods Data using BulkReader
Extracts production method data from Victoria 3 mod files and creates a structured DataFrame
with parent building, production method name, input/output goods, and employment data.
"""

import pandas as pd
from bulk_reader import BulkReader
from typing import Dict, List, Any, Optional
from pathlib import Path

class ProductionMethodExtractor:
    def __init__(self, production_methods_dir: str = "common/production_methods"):
        self.production_methods_dir = Path(production_methods_dir)
        
    def extract_all_data(self) -> pd.DataFrame:
        """Extract data from all production method files."""
        all_data = []
        
        # Get all .txt files in the production methods directory
        txt_files = list(self.production_methods_dir.glob('*.txt'))
        
        for filepath in txt_files:
            if filepath.name != 'production_methods.md':  # Skip markdown file
                data = self.extract_file_data(str(filepath))
                all_data.extend(data)
                print(f"Processed {filepath.name}: {len(data)} production methods")
        
        if not all_data:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Reorder columns for better readability
        column_order = [
            'production_method_name', 'parent_building', 'filepath', 'filename',
            'texture', 'is_default', 'is_hidden_when_unavailable',
            'unlocking_technologies', 'unlocking_principles', 'disallowing_laws',
            'replacement_if_valid', 'required_input_goods'
        ]
        
        # Add input goods columns
        input_cols = [col for col in df.columns if col.startswith('input_')]
        column_order.extend(sorted(input_cols))
        
        # Add output goods columns
        output_cols = [col for col in df.columns if col.startswith('output_')]
        column_order.extend(sorted(output_cols))
        
        # Add employment columns
        employment_cols = [col for col in df.columns if col.startswith('employment_') or col == 'total_employment']
        column_order.extend(sorted(employment_cols))
        
        # Reorder DataFrame
        existing_cols = [col for col in column_order if col in df.columns]
        if existing_cols:
            df = df[existing_cols].copy()
        
        return df
    
    def extract_file_data(self, filepath: str) -> List[Dict]:
        """Extract production method data from a single file."""
        # Use bulk reader to get all data from the file
        reader = BulkReader([{
            'filepath': filepath,
            'recursive': False
        }])
        
        df = reader.read_to_dataframe()
        
        if df.empty:
            return []
        
        # Since the bulk reader doesn't extract production method names,
        # we need to infer them from the file content and structure
        # For now, let's create a single production method entry per file
        # and collect all the data into it
        
        pm_data = {
            'production_method_name': f"pm_{Path(filepath).stem}",  # Use filename as PM name
            'filepath': filepath,
            'filename': Path(filepath).name,
            'parent_building': self._infer_parent_building(filepath, ""),
            'texture': '',
            'is_default': False,
            'is_hidden_when_unavailable': False,
            'unlocking_technologies': '',
            'unlocking_principles': '',
            'disallowing_laws': '',
            'replacement_if_valid': '',
            'required_input_goods': '',
        }
        
        # Process all the extracted data
        for _, row in df.iterrows():
            key = str(row['key'])
            value = row['value']
            
            # Map the extracted keys to our structure
            if key == 'texture':
                pm_data['texture'] = value
            elif key == 'is_default':
                pm_data['is_default'] = value
            elif key == 'is_hidden_when_unavailable':
                pm_data['is_hidden_when_unavailable'] = value
            elif key == 'replacement_if_valid':
                pm_data['replacement_if_valid'] = value
            elif key == 'unlocking_technologies':
                pm_data['unlocking_technologies'] = value
            elif key == 'unlocking_principles':
                pm_data['unlocking_principles'] = value
            elif key == 'disallowing_laws':
                pm_data['disallowing_laws'] = value
            elif key == 'required_input_goods':
                pm_data['required_input_goods'] = value
            elif key.startswith('goods_input_'):
                good_name = key.replace('goods_input_', '').replace('_add', '')
                pm_data[f'input_{good_name}'] = value
            elif key.startswith('goods_output_'):
                good_name = key.replace('goods_output_', '').replace('_add', '')
                pm_data[f'output_{good_name}'] = value
            elif key.startswith('building_employment_'):
                pop_type = key.replace('building_employment_', '').replace('_add', '')
                pm_data[f'employment_{pop_type}'] = value
        
        # Calculate total employment
        total_employment = 0
        for key, value in pm_data.items():
            if key.startswith('employment_') and isinstance(value, (int, float)):
                total_employment += value
        pm_data['total_employment'] = total_employment
        
        return [pm_data]
    
    def _infer_parent_building(self, filepath: str, pm_name: str) -> str:
        """Infer the parent building from the file path and production method name."""
        filename = Path(filepath).name
        
        # Map filename to building type
        building_map = {
            '01_industry.txt': 'industry',
            '02_agro.txt': 'agriculture',
            '03_mines.txt': 'mines',
            '04_plantations.txt': 'plantations',
            '05_military.txt': 'military',
            '06_urban_center.txt': 'urban_center',
            '07_government.txt': 'government',
            '08_monuments.txt': 'monuments',
            '09_misc_resource.txt': 'misc_resource',
            '10_canals.txt': 'canals',
            '11_private_infrastructure.txt': 'private_infrastructure',
            '12_subsistence.txt': 'subsistence',
            '13_construction.txt': 'construction',
            '00_dummy.txt': 'dummy'
        }
        
        return building_map.get(filename, 'unknown')
    
    def save_to_csv(self, output_path: str = "production_methods_data.csv") -> None:
        """Save extracted data to CSV file."""
        df = self.extract_all_data()
        if not df.empty:
            df.to_csv(output_path, index=False)
            print(f"Data saved to {output_path}")
            print(f"Total production methods: {len(df)}")
            print(f"Dataframe shape: {df.shape}")
        else:
            print("No data to save")
    
    def save_to_excel(self, output_path: str = "production_methods_data.xlsx") -> None:
        """Save extracted data to Excel file."""
        df = self.extract_all_data()
        if not df.empty:
            df.to_excel(output_path, index=False)
            print(f"Data saved to {output_path}")
            print(f"Total production methods: {len(df)}")
            print(f"Dataframe shape: {df.shape}")
        else:
            print("No data to save")
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the extracted data."""
        df = self.extract_all_data()
        if df.empty:
            return {}
        
        stats = {
            'total_production_methods': len(df),
            'parent_buildings': df['parent_building'].value_counts().to_dict(),
            'default_methods': df['is_default'].sum(),
            'hidden_methods': df['is_hidden_when_unavailable'].sum(),
            'input_goods_columns': [col for col in df.columns if col.startswith('input_')],
            'output_goods_columns': [col for col in df.columns if col.startswith('output_')],
            'employment_columns': [col for col in df.columns if col.startswith('employment_')],
            'files_processed': df['filename'].nunique()
        }
        
        # Employment statistics
        if 'total_employment' in df.columns:
            stats['employment_stats'] = {
                'min_employment': df['total_employment'].min(),
                'max_employment': df['total_employment'].max(),
                'mean_employment': df['total_employment'].mean(),
                'median_employment': df['total_employment'].median()
            }
        
        return stats

def main():
    """Main function to run the extraction."""
    print("=== Victoria 3 Production Methods Data Extraction ===\n")
    
    # Create extractor
    extractor = ProductionMethodExtractor("common/production_methods")
    
    # Extract data
    print("Extracting production methods data...")
    df = extractor.extract_all_data()
    
    if not df.empty:
        print(f"\nExtraction completed!")
        print(f"Total production methods: {len(df)}")
        print(f"Dataframe shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Show sample data
        print(f"\nSample data:")
        print(df.head())
        
        # Get summary statistics
        stats = extractor.get_summary_stats()
        print(f"\nSummary Statistics:")
        print(f"Parent buildings: {stats['parent_buildings']}")
        print(f"Default methods: {stats['default_methods']}")
        print(f"Hidden methods: {stats['hidden_methods']}")
        print(f"Files processed: {stats['files_processed']}")
        
        if 'employment_stats' in stats:
            emp_stats = stats['employment_stats']
            print(f"Employment range: {emp_stats['min_employment']} to {emp_stats['max_employment']}")
            print(f"Average employment: {emp_stats['mean_employment']:.1f}")
        
        # Save to files
        print(f"\nSaving data...")
        extractor.save_to_csv()
        extractor.save_to_excel()
        
    else:
        print("No data extracted!")

if __name__ == "__main__":
    main() 