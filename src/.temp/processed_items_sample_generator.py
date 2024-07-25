import pandas as pd
import json
import re

# Load CSV files
steam_data = pd.read_csv('steam_data_processed.csv')
skins_data = pd.read_csv('skins.csv')

# Helper function to clean item names
def clean_item_name(name):
    name = name.replace('_data.json', '').strip()
    name = re.sub(r'\s*\(.*?\)', '', name).strip()
    name = name.replace('  ', ' | ')
    return name

# Helper function to extract case and number from "Case" field
def parse_case(case_str):
    case_parts = case_str.split('+')
    cases = {}
    for part in case_parts:
        match = re.search(r'(.+?)\s*\(\d+\)', part.strip())
        if match:
            case_name = match.group(1).strip()
            number = int(re.search(r'\((\d+)\)', part).group(1))
            cases[case_name] = number
    return cases

# Process skins.csv to build a mapping from Case-Weapon_Skin to Rarity
case_skin_rarity = {}
for _, row in skins_data.iterrows():
    case_name = row['Case'].strip()
    weapon_skin = row['Weapon_Skin'].strip()
    rarity = row['Rarity'].strip()
    case_skin_rarity[(case_name, weapon_skin)] = rarity

# Process steam_data_processed.csv to build a mapping from cleaned item names to their details
item_details = {}
for _, row in steam_data.iterrows():
    item_name = clean_item_name(row['Name'])
    case_name = row['Collection'].strip()
    rarity = 'Unknown'  # Default value
    for (c_name, weapon_skin), r in case_skin_rarity.items():
        if case_name == c_name and weapon_skin in item_name:
            rarity = r
            break
    item_details[item_name] = {
        'case_name': case_name,
        'price': row['Price (INR)'],
        'floatvalue': row['floatvalue'],
        'rarity': rarity
    }

# Load combos_to_check.jsonl and process each line
processed_items = {}

with open('combos_to_check.jsonl', 'r') as f:
    for line in f:
        tradeup = json.loads(line)
        case_str = tradeup['Case']
        case_details = parse_case(case_str)
        avg_float = tradeup['Average Float']
        avg_output_price = tradeup['Avg Output Price']
        tradeup_price = avg_output_price / (10 * 1.07 * 1.15)
        input_rarity = tradeup['Input Rarity']
        
        # Initialize result structure
        case_items = {case: [] for case in case_details}
        
        # Fill the items for each case
        for item_name, details in item_details.items():
            if details['rarity'] == input_rarity:
                for case_name in case_details:
                    if details['case_name'] == case_name:
                        case_items[case_name].append({
                            'name': item_name,
                            'price': details['price'],
                            'floatvalue': details['floatvalue'],
                            'rarity': details['rarity']
                        })

        processed_items[f"{case_str}_{input_rarity}_{avg_float}"] = [
            {
                'cases': case_details,
                'avg_float': avg_float,
                'tradeup_price': tradeup_price,
                'input_rarity': input_rarity
            },
            case_items
        ]

# Write to processed_items.json
with open('processed_items_sample.json', 'w') as f:
    json.dump(processed_items, f, indent=4)

print("Processing complete. The results have been saved to processed_items_sample.json.")
