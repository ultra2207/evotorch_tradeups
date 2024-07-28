import polars as pl
import re
from tqdm import tqdm
import json
from operator import itemgetter
import concurrent.futures

STEAM_TAX_THRESHOLD = 1.15

def probability_float_function(item_name, start_float, end_float, target_float):
    types = {
        'Factory New': [0, 0.07],
        'Minimal Wear': [0.07, 0.15],
        'Field-Tested': [0.15, 0.38],
        'Well-Worn': [0.38, 0.45],
        'Battle-Scarred': [0.45, 1]
    }

    # Determine item_type based on target_float
    item_type = None
    for key, value in types.items():
        if value[0] <= target_float < value[1]:
            item_type = key
            break

    prob_dict = {
        'r1': [[0, 0.07], 0.03],
        'r2': [[0.08, 0.15], 0.24],
        'r3': [[0.16, 0.38], 0.33],
        'r4': [[0.39, 0.45], 0.24],
        'r5': [[0.46, 1], 0.16]
    }

    squish_factor = 1 - ((start_float - 0) + (1 - end_float))

    # Adjust the probability ranges by multiplying the float ranges by the squish_factor
    adjusted_prob_dict = {}
    for key, value in prob_dict.items():
        adjusted_prob_dict[key] = [[start_float + v * squish_factor for v in value[0]], value[1]]

    # Determine the minimum float value based on the item type and adjusted number line
    min_type_value = types[item_type][0]
    min_float = None
    max_type_value = types[item_type][1]
    number_line = sorted([item for sublist in [value[0] for value in adjusted_prob_dict.values()] for item in sublist])

    for i in range(0, len(number_line), 2):
        if number_line[i] <= min_type_value < number_line[i + 1]:
            min_float = min_type_value
            break
        elif number_line[i] > min_type_value:
            min_float = number_line[i]
            break

    if min_float is None:
        min_float = types[item_type][0]

    # Find the max_float where the area from min_float to target_float is equal to the area from target_float to max_float
    def calculate_area(start, end):
        area = 0
        for key, value in adjusted_prob_dict.items():
            r_start, r_end = value[0]
            if r_start < end and r_end > start:
                overlap_start = max(r_start, start)
                overlap_end = min(r_end, end)
                if overlap_start < overlap_end:
                    area += (overlap_end - overlap_start) * value[1]
        return area

    target_area = calculate_area(min_float, target_float)

    # Binary search for max_float
    def binary_search_max_float(target_area, target_float):
        low = target_float
        high = types[item_type][1]
        max_float = target_float

        while high - low > 1e-14:
            mid = (low + high) / 2
            area_mid = calculate_area(target_float, mid)
            if area_mid < target_area:
                low = mid
            else:
                high = mid
            max_float = mid

        return max_float

    max_float = binary_search_max_float(target_area, target_float)

    # Calculate the areas for probability calculation
    area_target = calculate_area(min_float, target_float)
    area_full = calculate_area(min_float, max_type_value)

    # Calculate the probability as a percentage
    probability_percentage = (area_target * 2 / area_full) * 100 if area_full != 0 else 0

    return min_float, max_float, probability_percentage

# Optimized helper functions
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

def find_best_item(input_prices):
    def calculate_cost(input_price, probability_percentage):
        probability_percentage = min(probability_percentage, 100)
        probability_value = probability_percentage / 100
        return float('inf') if probability_percentage == 0 else \
                input_price * ((1 / probability_value) - (((1 / probability_value) - 1) * (1/STEAM_TAX_THRESHOLD))) #input_price

                
    costs = [calculate_cost(item[4], item[5]) for item in input_prices]
    for item, cost in zip(input_prices, costs):
        item.append(cost)

    sorted_by_price = sorted(input_prices, key=lambda x: x[4])
    sorted_by_cost = sorted(input_prices, key=lambda x: x[-1])
    
    return sorted_by_cost[1] if sorted_by_cost[0] == sorted_by_price[0] else sorted_by_cost[0]

def process_case(case, skins_df, market_data_df):
    rarities = ['Mil-Spec', 'Restricted', 'Classified', 'Covert']
    profitable_tradeups = []

    for rarity_index in range(len(rarities) - 1):
        input_rarity = rarities[rarity_index]
        output_rarity = rarities[rarity_index + 1]
        
        input_skins = skins_df.filter((pl.col('Case') == case) & (pl.col('Rarity') == input_rarity))
        output_skins = skins_df.filter((pl.col('Case') == case) & (pl.col('Rarity') == output_rarity))

        for avg_float in [i / 10000 for i in range(1, 10001)]:
            output_floats = {row['Weapon_Skin']: calculate_output_float(avg_float, row['start_float'], row['end_float']) 
                             for row in output_skins.iter_rows(named=True)}
            
            outputs_details = {}
            total_output_price = 0
            valid_outputs = 0

            for weapon_name, output_float in output_floats.items():
                wear_category = get_wear_category(output_float)
                if wear_category:
                    market_row = market_data_df.filter(
                        pl.col('hash_name').str.starts_with(weapon_name) & 
                        pl.col('hash_name').str.contains(re.escape(f"({wear_category})"))
                    )
                    if not market_row.is_empty():
                        output_price = market_row['sell_price'].item()
                        total_output_price += output_price
                        outputs_details[weapon_name] = [wear_category, output_price]
                        valid_outputs += 1
            
            if valid_outputs > 0:
                avg_output_price = total_output_price / valid_outputs

                input_prices = []
                for row in input_skins.iter_rows(named=True):
                    input_skin_name = row['Weapon_Skin']
                    wear_category = get_wear_category(avg_float)
                    if wear_category:
                        market_row = market_data_df.filter(
                            pl.col('hash_name').str.starts_with(row["Weapon_Skin"]) & 
                            pl.col('hash_name').str.contains(re.escape(f"({wear_category})"))
                        )

                        if not market_row.is_empty():
                            input_price = market_row['sell_price'].item()
                            _, _, probability_percentage = probability_float_function(
                                input_skin_name, row['start_float'], row['end_float'], avg_float)
                            input_prices.append([row['Case'], input_skin_name, row['Rarity'], 
                                                 avg_float, input_price, probability_percentage])

                if input_prices:
                    best_item = find_best_item(input_prices)
                    input_price = best_item[4]

                    total_input_cost = 10 * best_item[-1] * 0.98
                    profitability = avg_output_price / total_input_cost

                    total_input_price = 10 * input_price * 0.98

                    if total_input_price > total_input_cost:
                        print(f"ratio: = {total_input_price / total_input_cost}, probability = {best_item[5]}")

                    theoretical_max_profitability = avg_output_price / total_input_price
                    inputs_wear_category = get_wear_category(best_item[3])
                    if profitability >= STEAM_TAX_THRESHOLD:
                        profitable_tradeups.append({
                            'Case': best_item[0],
                            'Input Skin': best_item[1],
                            'Input Rarity': best_item[2],
                            'Inputs Wear': inputs_wear_category,
                            'Output Rarity': output_rarity,
                            'Average Float': best_item[3],
                            'Avg Output Price': avg_output_price,
                            'Total Input Cost': total_input_cost,
                            'Real Profitablity': profitability / STEAM_TAX_THRESHOLD,
                            'Theoretical Max Profitablity': theoretical_max_profitability / STEAM_TAX_THRESHOLD,
                            'outputs_details': outputs_details
                        })

    return profitable_tradeups

def main():
    # Read the CSV files
    skins_df = pl.read_csv('skins.csv')
    market_data_df = pl.read_csv('searched_market_data.csv')

    cases = skins_df['Case'].unique().to_list()

    # Process cases in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_case, case, skins_df, market_data_df) for case in cases]
        all_profitable_tradeups = []
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(cases), desc="Processing Cases"):
            all_profitable_tradeups.extend(future.result())

    # Sort the tradeups
    sorted_tradeups = sorted(all_profitable_tradeups, key=itemgetter('Real Profitablity'), reverse=True)

    # Save to JSONL file
    def custom_json_dump(obj, file):
        json_str = json.dumps(obj, ensure_ascii=False)
        file.write(json_str + '\n')

    with open('profitable_tradeups.jsonl', 'w', encoding='utf-8') as jsonl_file:
        for tradeup in sorted_tradeups:
            custom_json_dump(tradeup, jsonl_file)

    print("Data has been saved to profitable_tradeups.jsonl")

if __name__ == "__main__":
    main()