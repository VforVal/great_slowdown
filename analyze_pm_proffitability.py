#!/usr/bin/env python3
"""
Simple script to extract Victoria 3 production methods data to CSV.
Outputs only the CSV file with minimal console output.
"""

import os
import re
import pandas as pd
from typing import Dict, List, Tuple
import pyradox
from analyze_pm_profitability import PMProfitabilityAnalyzer

def tree_to_dict(node):
    if hasattr(node, 'items'):
        return {str(k): tree_to_dict(v) for k, v in node.items()}
    elif isinstance(node, list):
        return [tree_to_dict(i) for i in node]
    else:
        return node

class PMDataExtractor:
    def __init__(self, directory: str):
        self.directory = directory
        self.file_paths = self._find_files()
        analyzer = PMProfitabilityAnalyzer()
        self.goods_prices = analyzer.load_goods_prices()

    def _find_files(self) -> List[str]:
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith(".txt"):
                    files.append(os.path.join(root, filename))
        return files

    def extract_all_pm_data(self) -> List[Dict]:
        all_pm_data = []
        for filepath in self.file_paths:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            tree = tree_to_dict(pyradox.parse(content))
            filename = os.path.basename(filepath)
            pms = self.get_pms_from_tree(tree)
            for pm_name, pm_data in pms.items():
                if isinstance(pm_data, dict):
                    employment_dict = self.get_employment(pm_data)
                    total_employment = sum(employment_dict.values())
                    inputs, outputs = self.get_goods(pm_data)
                    
                    profit_data = self.calculate_profitability(inputs, outputs, total_employment)

                    data = {
                        "production_method_name": pm_name,
                        "parent_building": self.get_parent_building(pm_data, filename),
                        "filename": filename,
                        "total_employment": total_employment,
                        "inputs": str(inputs),
                        "outputs": str(outputs),
                    }
                    data.update(profit_data)
                    all_pm_data.append(data)
        return all_pm_data

    def calculate_profitability(self, inputs: Dict[str, float], outputs: Dict[str, float], total_employment: int) -> Dict:
        input_cost = sum(self.goods_prices.get(good, 0) * quantity for good, quantity in inputs.items())
        output_revenue = sum(self.goods_prices.get(good, 0) * quantity for good, quantity in outputs.items())
        total_profit = output_revenue - input_cost
        
        profit_per_employee = 0
        if total_employment != 0:
            profit_per_employee = total_profit / total_employment
            
        return {
            "input_cost": input_cost,
            "output_revenue": output_revenue,
            "total_profit": total_profit,
            "profit_per_employee": profit_per_employee,
        }

    def get_pms_from_tree(self, tree) -> Dict:
        pms = {}
        if isinstance(tree, dict):
            for k, v in tree.items():
                if str(k).startswith("pm_"):
                    pms[k] = v
        return pms

    def get_parent_building(self, pm_data: Dict, filename: str) -> str:
        return os.path.splitext(filename)[0].split('_', 1)[-1]

    def get_employment(self, pm_data: Dict) -> Dict[str, int]:
        employment = {}
        if "building_modifiers" in pm_data and isinstance(pm_data["building_modifiers"], dict) and "level_scaled" in pm_data["building_modifiers"]:
            ls = pm_data["building_modifiers"]["level_scaled"]
            if isinstance(ls, dict):
                for k, v in ls.items():
                    if k.startswith("building_employment_") and isinstance(v, (int, float)):
                        employment[k] = v
        return employment

    def get_goods(self, pm_data: Dict) -> Tuple[Dict[str, float], Dict[str, float]]:
        inputs, outputs = {}, {}
        if "building_modifiers" in pm_data and isinstance(pm_data["building_modifiers"], dict) and "workforce_scaled" in pm_data["building_modifiers"]:
            ws = pm_data["building_modifiers"]["workforce_scaled"]
            if isinstance(ws, dict):
                for k, v in ws.items():
                    if k.startswith("goods_input_") and isinstance(v, (int, float)):
                        inputs[self.get_good_name(k)] = float(v)
                    elif k.startswith("goods_output_") and isinstance(v, (int, float)):
                        outputs[self.get_good_name(k)] = float(v)
        return inputs, outputs

    def get_good_name(self, key: str) -> str:
        m = re.match(r"goods_(?:input|output)_(.+)_add", key)
        return m.group(1) if m else key

def main():
    extractor = PMDataExtractor(directory="common/production_methods")
    pm_data = extractor.extract_all_pm_data()
    df = pd.DataFrame(pm_data)
    df.to_csv("production_methods.csv", index=False)
    print("Production methods data extracted to production_methods.csv")

if __name__ == "__main__":
    main() 