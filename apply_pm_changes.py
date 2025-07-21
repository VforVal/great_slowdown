import pandas as pd
import os
from bulk_tools.bulk_editor import BulkEditor
from bulk_tools.bulk_reader import BulkReader
from typing import List, Dict

# Path constants
PM_CHANGES_CSV = "pm_changes.csv"
PROD_METHODS_DIR = "common/production_methods/"

# Helper to round to nearest 5
def round5(x):
    return int(round(x / 5.0) * 5)

def get_pm_goods(pm_data: dict) -> (List[str], List[str]):
    """Return lists of input and output good keys under workforce_scaled for a PM."""
    inputs, outputs = [], []
    try:
        ws = pm_data["building_modifiers"]["workforce_scaled"]
        for k in ws:
            if k.startswith("goods_input_") and k.endswith("_add"):
                inputs.append(k)
            elif k.startswith("goods_output_") and k.endswith("_add"):
                outputs.append(k)
    except Exception:
        pass
    return inputs, outputs

def main():
    # Read changes
    df = pd.read_csv(PM_CHANGES_CSV)
    # Only consider rows with a change
    df = df[(df["updated_input_cost"].notna()) | (df["updated_revenue"].notna())]
    
    # Group by file for efficiency
    file_to_pms: Dict[str, List[dict]] = {}
    for _, row in df.iterrows():
        fname = os.path.join(PROD_METHODS_DIR, str(row["filename"]))
        if fname not in file_to_pms:
            file_to_pms[fname] = []
        file_to_pms[fname].append(row)

    # For each file, load and edit
    for filepath, pm_rows in file_to_pms.items():
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        # Use BulkReader to parse file
        with open(filepath, 'r', encoding='utf-8') as f:
            import pyradox
            tree = pyradox.parse(f.read())
        changed = False
        for row in pm_rows:
            pm_name = row["production_method_name"]
            if pm_name not in tree:
                print(f"PM {pm_name} not found in {filepath}")
                continue
            pm_data = tree[pm_name]
            inputs, outputs = get_pm_goods(pm_data)
            # Edit inputs
            if pd.notna(row["updated_input_cost"]) and len(inputs) > 0:
                orig = float(row["input_cost"])
                new = float(row["updated_input_cost"])
                delta = new - orig
                per_good = round5(delta / len(inputs)) if len(inputs) > 0 else 0
                for k in inputs:
                    old_val = pm_data["building_modifiers"]["workforce_scaled"][k]
                    pm_data["building_modifiers"]["workforce_scaled"][k] = old_val + per_good
                changed = True
            # Edit outputs
            if pd.notna(row["updated_revenue"]) and len(outputs) > 0:
                orig = float(row["output_revenue"])
                new = float(row["updated_revenue"])
                delta = new - orig
                per_good = round5(delta / len(outputs)) if len(outputs) > 0 else 0
                for k in outputs:
                    old_val = pm_data["building_modifiers"]["workforce_scaled"][k]
                    pm_data["building_modifiers"]["workforce_scaled"][k] = old_val + per_good
                changed = True
        # Write back if changed
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(tree))
            print(f"Updated {filepath}")

if __name__ == "__main__":
    main() 