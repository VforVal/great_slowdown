import os
import pyradox

# Configuration: map file paths to employment multipliers
FILE_MULTIPLIERS = {
    'production_methods/01_industry.txt': 0.5,
    'production_methods/02_agro.txt': 0.75,
    'production_methods/03_mines.txt': 0.75,
    'production_methods/04_plantations.txt': 0.75,
    'production_methods/05_military.txt': 0.5,
    'production_methods/06_urban_center.txt': 0.5,
    'production_methods/07_government.txt': 0.8,
    'production_methods/08_monuments.txt': 0.75,
    'production_methods/09_misc_resource.txt': 0.75,
    'production_methods/10_canals.txt': 0.75,
    'production_methods/11_private_infrastructure.txt': 0.75,
    'production_methods/12_subsistence.txt': 0.75,
    'production_methods/13_construction.txt': 0.5,
}

def is_employment_key(key):
    return key.startswith('building_employment_') and key.endswith('_add')

def round10(x):
    return int(round(x / 10.0) * 10)

def process_level_scaled_block(block, multiplier):
    edits = 0
    for key in block:
        if is_employment_key(key):
            try:
                orig = float(block[key])
                new = round10(orig * multiplier)
                if int(new) != int(orig):
                    block[key] = int(new)
                    edits += 1
            except Exception:
                pass  # Ignore non-numeric values
    return edits

def traverse_and_edit(node, multiplier):
    edits = 0
    # pyradox Tree supports .items(), but is not a dict or list
    if hasattr(node, 'items'):
        for k, v in node.items():
            if k == 'level_scaled' and hasattr(v, 'items'):
                edits += process_level_scaled_block(v, multiplier)
            else:
                edits += traverse_and_edit(v, multiplier)
    elif isinstance(node, list):
        for item in node:
            edits += traverse_and_edit(item, multiplier)
    return edits

def process_file(filepath, multiplier):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = pyradox.parse(f.read())
    edits = traverse_and_edit(tree, multiplier)
    print(f"{filepath}: {edits} employment edits made.")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(tree))

if __name__ == '__main__':
    for rel_path, multiplier in FILE_MULTIPLIERS.items():
        if not os.path.exists(rel_path):
            print(f"File not found: {rel_path}")
            continue
        print(f"Processing {rel_path} with multiplier {multiplier}")
        process_file(rel_path, multiplier)
    print("Done.") 