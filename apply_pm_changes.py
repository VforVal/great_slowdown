import pandas as pd
import os
import re
import pyradox
from pm_analysis.loader import load_goods_prices

PM_CHANGES_CSV = "pm_changes.csv"
PROD_METHODS_DIR = "common/production_methods/"
GOODS_FILE = "common/goods/00_goods.txt"

def round5(x):
    return int(round(x / 5.0) * 5)

def get_good_from_key(key: str) -> str:
    m = re.match(r"goods_(?:input|output)_(.+)_add", key)
    return m.group(1) if m else key

def tree_to_dict(node):
    if hasattr(node, 'items'):
        return {str(k): tree_to_dict(v) for k, v in node.items()}
    elif isinstance(node, list):
        return [tree_to_dict(i) for i in node]
    else:
        return node

def main():
    df = pd.read_csv(PM_CHANGES_CSV)
    df = df[df["updated_input_cost"].notna() | df["updated_revenue"].notna() | df["updated_employment"].notna()]
    goods_prices = load_goods_prices(GOODS_FILE)
    
    file_to_pms = {}
    for _, row in df.iterrows():
        fname = os.path.join(PROD_METHODS_DIR, str(row["filename"]))
        if fname not in file_to_pms:
            file_to_pms[fname] = []
        file_to_pms[fname].append(row.to_dict())

    for filepath, pm_rows in file_to_pms.items():
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue
        
        tree = pyradox.parse(content)
        tree_dict = tree_to_dict(tree)
        lines = content.splitlines(True)
        file_changed = False

        for row in pm_rows:
            pm_name = str(row["production_method_name"])
            print(f"Processing PM: {pm_name} in {filepath}")
            
            if not isinstance(tree_dict, dict):
                print(f"  Root of {filepath} is not a dictionary. Skipping.")
                break 

            pm_node = tree_dict.get(pm_name)
            
            if pm_node is None:
                print(f"  PM {pm_name} not found in file.")
                continue

            if not isinstance(pm_node, dict):
                print(f"  PM node for {pm_name} is not a dictionary. Skipping.")
                continue

            pm_start_line, pm_end_line = -1, -1
            brace_level, in_pm = 0, False
            pm_def_pattern = re.compile(r'^\s*' + re.escape(pm_name) + r'\s*=\s*\{')
            for i, line in enumerate(lines):
                if not in_pm and pm_def_pattern.search(line):
                    pm_start_line = i
                    in_pm = True
                if in_pm:
                    brace_level += line.count('{') - line.count('}')
                    if brace_level == 0:
                        pm_end_line = i
                        break
            
            if pm_start_line == -1 or pm_end_line == -1:
                print(f"  Could not find start/end of PM block for {pm_name}. Skipping.")
                continue
            
            try:
                workforce_scaled = pm_node.get("building_modifiers", {}).get("workforce_scaled", {})
                if not isinstance(workforce_scaled, dict): workforce_scaled = {}
                input_keys = {k: v for k, v in workforce_scaled.items() if k.startswith("goods_input_")}
                output_keys = {k: v for k, v in workforce_scaled.items() if k.startswith("goods_output_")}
                # --- Employment update logic ---
                level_scaled = pm_node.get("building_modifiers", {}).get("level_scaled", {})
                if not isinstance(level_scaled, dict):
                    level_scaled = {}
                employment_keys = {k: v for k, v in level_scaled.items() if k.startswith("building_employment_")}
            except Exception as e:
                print(f"  Error accessing workforce_scaled/level_scaled for {pm_name}: {e}")
                continue

            edits = {}
            pm_changed = False
            input_cost = float(row.get("input_cost", 0)) if pd.notna(row.get("input_cost")) else 0
            output_revenue = float(row.get("output_revenue", 0)) if pd.notna(row.get("output_revenue")) else 0
            updated_input_cost = float(row.get("updated_input_cost")) if pd.notna(row.get("updated_input_cost")) else input_cost
            updated_output_revenue = float(row.get("updated_revenue")) if pd.notna(row.get("updated_revenue")) else output_revenue

            if pd.notna(row.get("updated_input_cost")) and input_keys:
                delta = updated_input_cost - input_cost
                per_good_money = delta / len(input_keys) if input_keys else 0
                for key, old_val in input_keys.items():
                    good = get_good_from_key(key)
                    price = goods_prices.get(good, 1)
                    if price == 0: continue
                    quantity_delta = round5(per_good_money / price)
                    new_val = int(old_val) + quantity_delta
                    edits[key] = (old_val, new_val, price)
                    pm_changed = True

            if pd.notna(row.get("updated_revenue")) and output_keys:
                delta = updated_output_revenue - output_revenue
                per_good_money = delta / len(output_keys) if output_keys else 0
                for key, old_val in output_keys.items():
                    good = get_good_from_key(key)
                    price = goods_prices.get(good, 1)
                    if price == 0: continue
                    quantity_delta = round5(per_good_money / price)
                    new_val = int(old_val) + quantity_delta
                    edits[key] = (old_val, new_val, price)
                    pm_changed = True

            # --- Employment update logic ---
            updated_employment = row.get("updated_employment")
            if pd.notna(updated_employment) and updated_employment != 0 and employment_keys:
                original_total_employment = sum(employment_keys.values())
                new_total_employment = int(updated_employment)

                if new_total_employment == original_total_employment:
                    continue

                if original_total_employment == 0:
                    if employment_keys:
                        delta = new_total_employment
                        n_keys = len(employment_keys)
                        base_delta = delta // n_keys
                        remainder = delta % n_keys
                        for idx, (key, old_val) in enumerate(employment_keys.items()):
                            add = base_delta + (1 if idx < remainder else 0)
                            new_val = int(old_val) + add
                            edits[key] = (old_val, new_val, None)
                            pm_changed = True
                else:
                    new_values_float = {key: (val / original_total_employment) * new_total_employment for key, val in employment_keys.items()}
                    new_values_floor = {key: int(val) for key, val in new_values_float.items()}
                    remainders = {key: val - new_values_floor[key] for key, val in new_values_float.items()}
                    
                    current_total = sum(new_values_floor.values())
                    shortfall = new_total_employment - current_total
                    
                    keys_sorted_by_remainder = sorted(remainders, key=lambda k: remainders[k], reverse=True)
                    
                    final_new_values = new_values_floor.copy()
                    for i in range(shortfall):
                        key_to_increment = keys_sorted_by_remainder[i]
                        final_new_values[key_to_increment] += 1

                    for key, old_val in employment_keys.items():
                        new_val = final_new_values[key]
                        if int(old_val) != new_val:
                            edits[key] = (old_val, new_val, None)
                            pm_changed = True

            if not pm_changed:
                continue
            file_changed = True

            for i in range(pm_start_line, pm_end_line + 1):
                for key, (old_val, new_val, price) in list(edits.items()):
                    pattern = re.compile(r'(\s*' + re.escape(key) + r'\s*=\s*)' + str(old_val) + r'(\b.*)')
                    match = pattern.search(lines[i])
                    if match:
                        if price is not None:
                            total_good_cost = new_val * price
                            comment = f" # Price: {price}, Total: {total_good_cost}"
                        else:
                            comment = " # Employment update"
                        new_line = f"{match.group(1)}{new_val}{match.group(2).rstrip()}{comment}\n"
                        print(f"  - Changing line {i+1}: {lines[i].strip()} -> {new_line.strip()}")
                        lines[i] = new_line
                        del edits[key] # a key can only be edited once
                        break
            
            profit = updated_output_revenue - updated_input_cost
            profit_comment = f"\t# Profit = {updated_output_revenue:.2f} (rev) - {updated_input_cost:.2f} (cost) = {profit:.2f}\n"
            
            closing_brace_line_index = -1
            for i in range(pm_end_line, pm_start_line - 1, -1):
                if '}' in lines[i]:
                    closing_brace_line_index = i
                    break
            
            if closing_brace_line_index != -1:
                indent_match = re.match(r'(\s*)\}', lines[closing_brace_line_index])
                indent = indent_match.group(1) if indent_match else ''
                lines.insert(closing_brace_line_index, f"{indent}{profit_comment}")
                print(f"  - Adding profit comment before line {closing_brace_line_index + 1}")

        if file_changed:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.writelines(lines)
            print(f"Updated {filepath}\n")
        else:
            print(f"No changes made to {filepath}\n")

if __name__ == "__main__":
    main() 