from bulk_editor import BulkEditor

# Original task: for each file, edit all 'building_employment_*_add' keys with the given multiplier
file_configs = [
    {
        'filepath': 'production_methods/01_industry.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.5,
    },
    {
        'filepath': 'production_methods/02_agro.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/03_mines.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/04_plantations.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/05_military.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.5,
    },
    {
        'filepath': 'production_methods/06_urban_center.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.5,
    },
    {
        'filepath': 'production_methods/07_government.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.8,
    },
    {
        'filepath': 'production_methods/08_monuments.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/09_misc_resource.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/10_canals.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/11_private_infrastructure.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/12_subsistence.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.75,
    },
    {
        'filepath': 'production_methods/13_construction.txt',
        'pattern': 'building_employment_*_add',
        'multiplier': 0.5,
    },
]

if __name__ == '__main__':
    editor = BulkEditor(file_configs)
    editor.run() 