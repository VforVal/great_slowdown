#!/usr/bin/env python3
"""
Simple script to extract Victoria 3 production methods data to CSV.
Outputs only the CSV file with minimal console output.
"""

import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any

class SimplePMExtractor:
    def __init__(self, production_methods_dir: str = "common/production_methods"):
        self.production_methods_dir = production_methods_dir
        self.df = None

    def extract_all_data(self) -> pd.DataFrame:
        """Extract all production method data."""
        all_data = []
        
        # Get all production method files
        pm_dir = Path(self.production_methods_dir)
        pm_files = list(pm_dir.glob("*.txt"))
        
        for filepath in pm_files:
            file_data = self.extract_file_data(str(filepath))
            all_data.extend(file_data)
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        
        # Reduce to only the requested columns
        final_columns = [
            'production_method_name',
            'parent_building', 
            'filepath',
            'filename',
            'inputs',
            'outputs',
            'total_employment',
        ]
        df = df[final_columns]
        
        return df

    def extract_file_data(self, filepath: str) -> List[Dict]:
        """Extract production method data from a single file using regex parsing."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all production method blocks
            pm_blocks = self.extract_pm_blocks(content)
            
            all_pms = []
            for pm_name, pm_content in pm_blocks:
                pm_info = self.parse_pm_block(pm_name, pm_content, filepath)
                if pm_info:
                    all_pms.append(pm_info)
            
            print(f"  Extracted {len(all_pms)} PMs from {Path(filepath).name}")
            return all_pms
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []

    def extract_pm_blocks(self, content: str) -> List[tuple]:
        """Extract individual production method blocks from file content."""
        # Pattern to match PM blocks: pm_name = { ... }
        pm_pattern = r'pm_\w+\s*=\s*\{'
        pm_blocks = []
        
        # Find all PM starts
        matches = list(re.finditer(pm_pattern, content))
        
        for i, match in enumerate(matches):
            pm_name = match.group().split('=')[0].strip()
            start_pos = match.start()
            
            # Find the end of this PM block
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract the PM content
            pm_content = content[start_pos:end_pos]
            
            # Find the closing brace for this specific PM
            brace_count = 0
            pm_end = 0
            for j, char in enumerate(pm_content):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        pm_end = j + 1
                        break
            
            if pm_end > 0:
                pm_blocks.append((pm_name, pm_content[:pm_end]))
        
        return pm_blocks

    def parse_pm_block(self, pm_name: str, pm_content: str, filepath: str) -> Dict[str, Any]:
        """Parse a single production method block."""
        pm_info = {
            'production_method_name': pm_name,
            'filepath': filepath,
            'filename': Path(filepath).name,
            'parent_building': self._infer_parent_building(filepath),
            'inputs': {},
            'outputs': {},
            'total_employment': 0
        }
        
        # Extract input goods
        input_pattern = r'goods_input_(\w+)_add\s*=\s*(-?\d+)'
        for match in re.finditer(input_pattern, pm_content):
            good_name = match.group(1)
            value = int(match.group(2))
            pm_info['inputs'][good_name] = value
        
        # Extract output goods
        output_pattern = r'goods_output_(\w+)_add\s*=\s*(-?\d+)'
        for match in re.finditer(output_pattern, pm_content):
            good_name = match.group(1)
            value = int(match.group(2))
            pm_info['outputs'][good_name] = value
        
        # Extract employment
        employment_pattern = r'building_employment_(\w+)_add\s*=\s*(-?\d+)'
        for match in re.finditer(employment_pattern, pm_content):
            pop_type = match.group(1)
            value = int(match.group(2))
            pm_info['total_employment'] += value
        
        return pm_info

    def _infer_parent_building(self, filepath: str) -> str:
        """Infer the parent building from the file path."""
        filename = Path(filepath).name
        
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

    def save_to_csv(self, output_path: str = "production_methods.csv") -> None:
        """Save extracted data to CSV file."""
        df = self.extract_all_data()
        print(f"Extracted DataFrame shape: {df.shape}")
        if not df.empty:
            df.to_csv(output_path, index=False)
            print(f"CSV saved: {output_path} ({len(df)} production methods)")
        else:
            print("No data extracted!")

def main():
    """Main function - extract and save to CSV."""
    extractor = SimplePMExtractor("common/production_methods")
    extractor.save_to_csv("production_methods.csv")

if __name__ == "__main__":
    main() 