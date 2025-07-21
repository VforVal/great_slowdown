import pandas as pd
import os
import re
from bulk_tools.bulk_editor import BulkEditor
from bulk_tools.bulk_reader import BulkReader
from typing import List, Dict, Tuple, Any

# Path constants
PM_CHANGES_CSV = "pm_changes.csv"
PROD_METHODS_DIR = "common/production_methods/"
GOODS_FILE = "common/goods/00_goods.txt"

# Helper to round to nearest 5
def round5(x):
    return int(round(x / 5.0) * 5)

def parse_goods_prices(goods_file: str) -> Dict[str, float]:
    """Parse goods prices from the goods file."""
    prices = {}
    with open(goods_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Pattern: good_name = { ... cost = 20 ... }
    pattern = r"(\w+)\s*=\s*\{[^}]*?cost\s*=\s*(\d+)"
    for match in re.finditer(pattern, content, re.DOTALL):
        good, price = match.groups()
        prices[good] = float(price)
    return prices

def get_pm_goods(pm_data: dict) -> Tuple[List[str], List[str]]:
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

def get_good_from_key(key: str) -> str:
    # goods_input_grain_add -> grain
    m = re.match(r"goods_(?:input|output)_(.+)_add", key)
    return m.group(1) if m else key

def tree_to_dict(obj):
    # Recursively convert pyradox.Tree or similar to dict
    if hasattr(obj, 'items') and not isinstance(obj, dict):
        return {str(k): tree_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {str(k): tree_to_dict(v) for k, v in obj.items()}
    else:
        return obj

def main():
    # Read changes
    df = pd.read_csv(PM_CHANGES_CSV)
    df = df[(df["updated_input_cost"].notna()) | (df["updated_revenue"].notna())]
    # Parse good prices
    good_prices = parse_goods_prices(GOODS_FILE)
    # Group by file for efficiency
    file_to_pms: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in df.iterrows():
        fname = os.path.join(PROD_METHODS_DIR, str(row["filename"]))
        if fname not in file_to_pms:
            file_to_pms[fname] = []
        file_to_pms[fname].append(row.to_dict())
    # For each file, load and edit
    for filepath, pm_rows in file_to_pms.items():
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            import pyradox
            tree = pyradox.parse(f.read())
        lines = open(filepath, 'r', encoding='utf-8').readlines()
        changed = False
        tree_dict = tree_to_dict(tree)
        for row in pm_rows:
            pm_name = str(row["production_method_name"])
            # Robust PM lookup
            pm_key = None
            for k in tree_dict:
                if isinstance(k, str) and k == pm_name:
                    pm_key = k
                    break
            if pm_key is None:
                print(f"PM {pm_name} not found in {filepath}")
                continue
            pm_data = tree_dict[pm_key]
            # Convert pm_data to dict if it's a pyradox.Tree
            if not isinstance(pm_data, dict):
                print(f"PM {pm_name} data is not a dict in {filepath}")
                continue
            inputs, outputs = get_pm_goods(pm_data)
            # Edit inputs
            if pd.notna(row["updated_input_cost"]) and len(inputs) > 0:
                orig = float(row["input_cost"])
                new = float(row["updated_input_cost"])
                delta = new - orig
                per_good_money = delta / len(inputs) if len(inputs) > 0 else 0
                ws = pm_data.get("building_modifiers", {})
                if not isinstance(ws, dict):
                    continue
                ws = ws.get("workforce_scaled", {})
                if not isinstance(ws, dict):
                    continue
                for k in inputs:
                    good = get_good_from_key(k)
                    price = good_prices.get(good, 1)
                    quantity_delta = round5(per_good_money / price)
                    # Defensive: check nested dicts
                    old_val = ws.get(k)
                    if not (isinstance(k, str) and isinstance(old_val, (int, float))):
                        continue
                    new_val = old_val + quantity_delta
                    ws[k] = new_val
                    # Add comment in file lines
                    for i, line in enumerate(lines):
                        if re.match(rf"\s*{re.escape(k)}\s*=\s*{old_val}", line):
                            comment = f"# price={price}, total_input={new}"
                            lines[i] = re.sub(r"(#.*)?$", f" {comment}\n", line)
                            break
                    changed = True
            # Edit outputs
            if pd.notna(row["updated_revenue"]) and len(outputs) > 0:
                orig = float(row["output_revenue"])
                new = float(row["updated_revenue"])
                delta = new - orig
                per_good_money = delta / len(outputs) if len(outputs) > 0 else 0
                ws = pm_data.get("building_modifiers", {})
                if not isinstance(ws, dict):
                    continue
                ws = ws.get("workforce_scaled", {})
                if not isinstance(ws, dict):
                    continue
                for k in outputs:
                    good = get_good_from_key(k)
                    price = good_prices.get(good, 1)
                    quantity_delta = round5(per_good_money / price)
                    # Defensive: check nested dicts
                    old_val = ws.get(k)
                    if not (isinstance(k, str) and isinstance(old_val, (int, float))):
                        continue
                    new_val = old_val + quantity_delta
                    ws[k] = new_val
                    for i, line in enumerate(lines):
                        if re.match(rf"\s*{re.escape(k)}\s*=\s*{old_val}", line):
                            comment = f"# price={price}, total_output={new}"
                            lines[i] = re.sub(r"(#.*)?$", f" {comment}\n", line)
                            break
                    changed = True
        # Write back if changed
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Updated {filepath}")

if __name__ == "__main__":
    main() 