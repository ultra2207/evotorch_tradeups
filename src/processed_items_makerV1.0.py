import orjson
import pandas as pd
import re
import json
from tqdm import tqdm
import os
import requests
import sys

def get_MULTIPLIER(file_path='.temp/cached_usd.json', url='https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json'):
    # Ensure the .temp directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Try to fetch and save the latest currency data
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    except (requests.RequestException, json.JSONDecodeError):
        # If fetching fails, use the cached data
        print("Request failed or JSON decode error. Using cached data.")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            print(f"Using cached currency data from: {data['date']}")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Cached data not found or error decoding. Exiting.")
            return None
    
    # Extract and return the USD/INR rate
    try:
        usd_inr_rate = data['usd']['inr']
        return usd_inr_rate/(10*1.15*1.05)
    
    except KeyError:
        print("USD/INR rate not found in the data.")
        return None


MULTIPLIER = get_MULTIPLIER()
if MULTIPLIER is None:
    sys.exit(1)

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
    if item_name not in item_details:
        item_details[item_name] = []
    item_details[item_name].append({
        'case_name': case_name,
        'price': row['Price (INR)'],
        'floatvalue': row['floatvalue'],
        'rarity': rarity
    })

# Define a function to process one tradeup line
def process_tradeup_line(tradeup):
    case_str = tradeup['Case']
    case_details = parse_case(case_str)
    avg_float = tradeup['Average Float']
    
    avg_output_price = tradeup['Avg Output Price']
    tradeup_price = avg_output_price*MULTIPLIER
    input_rarity = tradeup['Input Rarity']
    
    # Initialize result structure
    case_items = {case: [] for case in case_details}
    
    # Fill the items for each case
    for item_name, details_list in item_details.items():
        for details in details_list:
            if details['rarity'] == input_rarity:
                for case_name in case_details:
                    if details['case_name'] == case_name:
                        case_items[case_name].append({
                            'name': item_name,
                            'price': details['price'],
                            'floatvalue': details['floatvalue'],
                            'rarity': details['rarity']
                        })

    return {
        f"{case_str}_{input_rarity}_{avg_float}": [
            {
                'cases': case_details,
                'avg_float': avg_float,
                'tradeup_price': tradeup_price,
                'input_rarity': input_rarity
            },
            case_items
        ]
    }

# Process combos_to_check.jsonl in chunks
processed_items = {}
chunk_size = 10  # Number of lines per chunk

with open('combos_to_check.jsonl', 'r') as f:
    lines = f.readlines()
    
    # Create a progress bar
    for i in tqdm(range(0, len(lines), chunk_size), desc="Processing chunks"):
        chunk_lines = lines[i:i + chunk_size]
        
        for line in chunk_lines:
            tradeup = json.loads(line)
            result = process_tradeup_line(tradeup)
            
            for key, value in result.items():
                if key in processed_items:
                    print(f"Error: Key {key} is being overwritten.")
                processed_items[key] = value

# Serialize with orjson and write to file
with open('processed_items.json', 'wb') as f:
    f.write(orjson.dumps(processed_items, option=orjson.OPT_INDENT_2))


print("Processing complete. The results have been saved to processed_items.json.")
