import csv
import json
from collections import defaultdict
from tqdm import tqdm

STEAM_TAX_THRESHOLD = 1.15

def read_skins_csv(filename):
    skins = defaultdict(lambda: defaultdict(list))
    cases = set()
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skins[row['Case']][row['Rarity']].append({
                'name': row['Weapon_Skin'],
                'start_float': float(row['start_float']),
                'end_float': float(row['end_float'])
            })
            cases.add(row['Case'])
    return skins, list(cases)

def read_market_data_csv(filename):
    market_data = {}
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            market_data[row['hash_name']] = {
                'sell_listings': int(row['sell_listings']),
                'sell_price': float(row['sell_price'])
            }
    return market_data

def calculate_output_float(avg_float, min_float, max_float):
    return (max_float - min_float) * avg_float + min_float

def get_wear_category(output_float):
    wears = {
        'Factory New': (0, 0.07),
        'Minimal Wear': (0.07, 0.15),
        'Field-Tested': (0.15, 0.38),
        'Well-Worn': (0.38, 0.45),
        'Battle-Scarred': (0.45, 1)
    }
    return next((wear for wear, (min_float, max_float) in wears.items() 
                 if min_float <= output_float < max_float), None)

def get_cheapest_price(weapon_skin, wear, market_data):
    for key, data in market_data.items():
        if weapon_skin in key and wear in key:
            return data['sell_price']
    return None

def generate_tradeup_combinations(original_tradeup, all_skins, all_cases, market_data):
    combinations = []
    original_case = original_tradeup['Case']
    original_rarity = original_tradeup['Input Rarity']
    input_wear = original_tradeup['Inputs Wear']
    output_rarity = original_tradeup['Output Rarity']
    average_float = original_tradeup['Average Float']
    
    other_cases = [case for case in all_cases if case != original_case]
    
    for other_case in other_cases:
        for num_other in range(1, 6):  # 1 to 5 items from other case
            num_original = 10 - num_other
            new_tradeup = original_tradeup.copy()
            new_tradeup['Case'] = f"{original_case} ({num_original}) + {other_case} ({num_other})"
            
            # Calculate input cost
            original_cost = get_cheapest_price(original_tradeup['Input Skin'], input_wear, market_data) * num_original
            other_cost = get_cheapest_price(all_skins[other_case][original_rarity][0]['name'], input_wear, market_data) * num_other
            new_tradeup['Total Input Cost'] = original_cost + other_cost
            
            # Keep the average float the same
            new_tradeup['Average Float'] = average_float
            
            # Calculate outputs
            outputs = []
            for case, count in [(original_case, num_original), (other_case, num_other)]:
                case_outputs = []
                for skin in all_skins[case][output_rarity]:
                    output_float = calculate_output_float(average_float, skin['start_float'], skin['end_float'])
                    output_wear = get_wear_category(output_float)
                    output_price = get_cheapest_price(skin['name'], output_wear, market_data)
                    case_outputs.append({'name': skin['name'], 'wear': output_wear, 'price': output_price})
                outputs.extend(case_outputs * count)
            
            # Calculate average output price
            total_price = sum(item['price'] for item in outputs)
            avg_output_price = total_price / len(outputs)
            
            new_tradeup['Avg Output Price'] = avg_output_price
            profitability_before_tax = avg_output_price / new_tradeup['Total Input Cost']
            new_tradeup['Real Profitablity'] = profitability_before_tax / STEAM_TAX_THRESHOLD
            
            # Calculate outputs_details with percentages
            output_counts = defaultdict(int)
            for item in outputs:
                output_counts[(item['name'], item['wear'])] += 1
            
            new_tradeup['outputs_details'] = {
                f"{name} ({wear})": [price, f"{count/len(outputs):.2%}"]
                for (name, wear), count in output_counts.items()
                for item in outputs if item['name'] == name and item['wear'] == wear
                for price in [item['price']]
            }
            
            combinations.append(new_tradeup)
    
    return combinations

def group_tradeups(tradeups):
    groups = defaultdict(list)
    for tradeup in tradeups:
        key = json.dumps({k: v for k, v in tradeup.items() if k != 'Average Float'})
        groups[key].append(tradeup)
    return groups

def main():
    skins, cases = read_skins_csv('skins.csv')
    market_data = read_market_data_csv('searched_market_data.csv')
    
    with open('profitable_tradeups.jsonl', 'r') as f:
        original_tradeups = [json.loads(line) for line in f]
    
    # Group tradeups
    grouped_tradeups = group_tradeups(original_tradeups)
    
    # Select best tradeup from each group (highest float)
    best_tradeups = [max(group, key=lambda x: x['Average Float']) for group in grouped_tradeups.values()]
    
    all_new_tradeups = []
    
    for tradeup in tqdm(best_tradeups, desc="Processing trade-ups"):
        new_tradeups = generate_tradeup_combinations(tradeup, skins, cases, market_data)
        all_new_tradeups.extend(new_tradeups)
    
    # Write new tradeups to a file
    with open('combos_to_check.jsonl', 'w') as f:
        for tradeup in all_new_tradeups:
            # Remove 'Theoretical Max Profitablity'
            tradeup.pop('Theoretical Max Profitablity', None)
            json.dump(tradeup, f)
            f.write('\n')

if __name__ == "__main__":
    main()