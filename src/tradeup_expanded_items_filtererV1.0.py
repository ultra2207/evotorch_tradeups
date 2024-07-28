import json
import csv
import re


correct = 0
wrong = 0
fail=0
# Load the JSON file
with open('tradeup_expanded_items.json', 'r') as f:
    tradeup_data = json.load(f)

# Load the CSV file
skins_data = {}
with open('skins.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        item_name = row['Weapon_Skin'].replace(' | ', '  ').strip()
        rarity = row['Rarity']
        skins_data[item_name] = rarity

# Function to extract rarity from the key
def extract_rarity(key):
    parts = key.split('_')
    if len(parts) >= 3:
        return parts[-3]  # Get the third-to-last element
    return None

# Function to process item names
def process_item_name(filename):

    filename = filename.replace('_data.json', '')
    filename = re.sub(r'\(.*?\)', '', filename).strip()
    filename.replace('  ',' | ')
    return filename

# Filter items based on rarity
filtered_data = {}
for key, items in tradeup_data.items():
    rarity_from_key = extract_rarity(key)
    if rarity_from_key:
        filtered_items = []
        for item in items:
            filename = item[0]
            item_name = process_item_name(filename)
            correct_rarity = skins_data.get(item_name)
            if correct_rarity == rarity_from_key:
                filtered_items.append(item)
                correct += 1
            else:
                wrong += 1
        if filtered_items:
            filtered_data[key] = filtered_items

        else:
            fail+=1

    else:
        fail+=1

# Write the filtered data back to a JSON file
with open('filtered_tradeup_expanded_items.json', 'w') as f:
    json.dump(filtered_data, f, indent=4)

print("Filtered data has been written to 'filtered_tradeup_expanded_items.json'")
print(f"correct: {correct}")
print(f"wrong: {wrong}")
print(f"fail: {fail}")