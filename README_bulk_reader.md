# Bulk Reader for Victoria 3 Mod Files

A Python script for bulk reading and extracting data from Victoria 3 mod files, outputting the results as pandas DataFrames.

## Features

- **Bulk Reading**: Process entire directories of Paradox script files
- **Flexible Key Matching**: Extract specific keys or use pattern matching
- **DataFrame Output**: Get structured data ready for analysis
- **Multiple Output Formats**: Save to CSV, Excel, or work with DataFrames directly
- **Recursive Processing**: Process subdirectories automatically
- **Error Handling**: Graceful handling of parsing errors

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from bulk_reader import BulkReader

# Read all data from a directory
reader = BulkReader([{
    'filepath': 'common/production_methods',
    'recursive': True
}])

df = reader.read_to_dataframe()
print(df.head())
```

### Reading Specific Keys

```python
# Extract only specific keys
reader = BulkReader([{
    'filepath': 'common/production_methods',
    'keys': ['base_goods_output', 'base_goods_input', 'level'],
    'recursive': True
}])

df = reader.read_to_dataframe()
```

### Pattern Matching

```python
# Extract keys matching a pattern
reader = BulkReader([{
    'filepath': 'common/production_methods',
    'pattern': '*_add',  # All keys ending with '_add'
    'recursive': True
}])

df = reader.read_to_dataframe()
```

### Using Regex Patterns

```python
# Use regex patterns (prefix with 're:')
reader = BulkReader([{
    'filepath': 'common/production_methods',
    'pattern': 're:.*_output$',  # All keys ending with '_output'
    'recursive': True
}])

df = reader.read_to_dataframe()
```

### Saving to Files

```python
# Save to CSV
reader.read_to_csv("output.csv")

# Save to Excel
reader.read_to_excel("output.xlsx")
```

### Custom Extraction Functions

```python
def custom_extractor(key, value, filepath):
    if isinstance(value, (int, float)) and value > 0:
        return {
            'filepath': filepath,
            'key': key,
            'value': value,
            'category': 'positive_numeric'
        }
    return None

reader = BulkReader([{
    'filepath': 'common/production_methods',
    'extract_func': custom_extractor,
    'recursive': True
}])

df = reader.read_to_dataframe()
```

## Configuration Options

Each configuration dictionary supports the following options:

- **`filepath`** (str): Path to file or directory to process
- **`keys`** (list): List of specific keys to extract
- **`pattern`** (str): Wildcard or regex pattern for key matching
- **`extract_func`** (callable): Custom extraction function
- **`recursive`** (bool): Process subdirectories (default: False)
- **`file_pattern`** (str): File pattern to match (default: "*.txt")

## Output Format

The DataFrame contains the following columns:

- **`filepath`**: Path to the source file
- **`key`**: The extracted key name
- **`value`**: The extracted value
- **`type`**: Data type (int, float, string, etc.)

## Example Scripts

### Production Methods Analysis

```python
from bulk_reader import create_production_method_reader

# Create a reader specifically for production methods
reader = create_production_method_reader("common/production_methods")

# Get all data
df = reader.read_to_dataframe()

# Analyze the data
print(f"Total files: {df['filepath'].nunique()}")
print(f"Total keys: {df['key'].nunique()}")
print(f"Data types: {df['type'].value_counts()}")
```

### Building Analysis

```python
from bulk_reader import create_building_reader

# Create a reader for buildings
reader = create_building_reader("common/buildings")

# Get all data
df = reader.read_to_dataframe()

# Filter for specific building types
industrial_buildings = df[df['filepath'].str.contains('industry')]
```

## Running the Example

```bash
python example_reader.py
```

This will demonstrate various usage patterns and save sample data to CSV.

## Notes

- The script handles pyradox.Token types by converting keys to strings
- Files with parsing errors are skipped with a warning message
- The DataFrame is automatically sorted with filepath as the first column
- Empty results return an empty DataFrame rather than None 