import json
import torch
import numpy as np
import os
import orjson
from tqdm import tqdm
import torch.multiprocessing as mp
import gc

def sanitize_filename(filename):
    return filename.replace(':', '').replace('/', '_').replace('\\', '_').replace(' ', '_')

# Load and parse the JSON data
with open('filtered_tradeup_expanded_items.json', 'r') as file:
    data = json.load(file)

# Extract constraints and organize items within each constraint
constraints = {}

for key, items in data.items():
    parts = key.split('_')
    case_info = parts[0].replace('Best Tradeup: ', '').split(' + ')
    max_float = float(parts[2])
    max_price = float(parts[3])
    
    case_counts = {}
    for case in case_info:
        case_name, count = case.rsplit(' ', 1)
        count = int(count.strip('()'))
        case_counts[case_name.strip()] = count
    
    constraints[key] = {
        'case_counts': case_counts,
        'max_float': max_float,
        'max_price': max_price,
        'items': items
    }

def generate_combinations(constraint, num_attempts=80, profitability_threshold=1, max_count=100):
    device = torch.device("cuda")
    
    case_counts = constraint['case_counts']
    max_float = constraint['max_float']
    max_price = constraint['max_price']
    items = constraint['items']
    
    case_names = list(case_counts.keys())
    case_items = {case: [item for item in items if item[2] == case] for case in case_names}
    case_items_array = {case: torch.tensor([[float(item[3]), float(item[4])] for item in items], device=device) for case, items in case_items.items()}
    case_sizes = torch.tensor([len(case_items[case]) for case in case_names], device=device)
    
    num_combinations = 1000000
    num_items_per_combo = sum(case_counts.values())
    
    final_combinations = []
    used_indices = torch.zeros(sum(case_sizes), dtype=torch.bool, device=device)
    
    max_price_tensor = torch.tensor(max_price, dtype=torch.float32, device=device)
    
    attempt_count = 0
    attempt_number = 0
    while attempt_count < num_attempts and attempt_number < max_count:
        random_indices = torch.randint(0, case_sizes.max(), (num_combinations, num_items_per_combo), dtype=torch.int64, device=device)
        
        masks = []
        offset = 0
        for i, case in enumerate(case_names):
            mask = (random_indices[:, offset:offset+case_counts[case]] < case_sizes[i]).all(dim=1)
            masks.append(mask)
            offset += case_counts[case]
        
        valid_mask = torch.stack(masks).all(dim=0)
        valid_indices = torch.nonzero(valid_mask, as_tuple=True)[0]
        
        valid_random_indices = random_indices[valid_indices]
        
        prices_tensor = torch.zeros((len(valid_random_indices), num_items_per_combo), dtype=torch.float32, device=device)
        floats_tensor = torch.zeros((len(valid_random_indices), num_items_per_combo), dtype=torch.float32, device=device)

        offset = 0
        for case in case_names:
            case_indices = valid_random_indices[:, offset:offset+case_counts[case]]
            prices_tensor[:, offset:offset+case_counts[case]] = case_items_array[case][case_indices, 0]
            floats_tensor[:, offset:offset+case_counts[case]] = case_items_array[case][case_indices, 1]
            offset += case_counts[case]
        
        mean_prices = torch.mean(prices_tensor, dim=1)
        mean_floats = torch.mean(floats_tensor, dim=1)
        
        valid_mask = (mean_floats <= max_float)
        valid_indices = torch.nonzero(valid_mask, as_tuple=True)[0]
        
        valid_combinations = valid_random_indices[valid_indices]
        valid_mean_prices = mean_prices[valid_indices]
        valid_mean_floats = mean_floats[valid_indices]

        if len(valid_combinations) == 0:
            attempt_count += 1
            continue

        profitability_tensor = max_price_tensor / valid_mean_prices

        profitability_mask = profitability_tensor >= profitability_threshold
        profitable_combinations = valid_combinations[profitability_mask]
        profitable_mean_prices = valid_mean_prices[profitability_mask]
        profitable_mean_floats = valid_mean_floats[profitability_mask]
        profitable_tensor = profitability_tensor[profitability_mask]

        if len(profitable_combinations) == 0:
            attempt_count += 1
            continue

        # Add uniqueness check here
        unique_mask = torch.tensor([
        len(torch.unique(combo)) == num_items_per_combo 
        for combo in profitable_combinations
        ], device=device)

        profitable_combinations = profitable_combinations[unique_mask]
        profitable_mean_prices = profitable_mean_prices[unique_mask]
        profitable_mean_floats = profitable_mean_floats[unique_mask]
        profitable_tensor = profitable_tensor[unique_mask]

        if len(profitable_combinations) == 0:
            attempt_count += 1
            continue

        sorted_indices = torch.argsort(profitable_mean_prices)
        
        found_new_combination = False
        
        for idx in sorted_indices:
            combo = profitable_combinations[idx]
            avg_price = profitable_mean_prices[idx]
            avg_float = profitable_mean_floats[idx]
            profitability = profitable_tensor[idx]

            if not used_indices[combo].any().item():
                final_combinations.append({
                    'combination': combo.cpu().numpy(),
                    'avg_price': avg_price.item(),
                    'avg_float': avg_float.item(),
                    'profitability': profitability.item()
                })
                used_indices[combo] = True
                found_new_combination = True

        if attempt_number == max_count-1:           
            print(f'max count of {max_count} reached. Breaking...')
            
        if found_new_combination:
            attempt_count = 0
        else:
            attempt_count += 1

        attempt_number += 1

    del case_sizes, random_indices, valid_indices, valid_random_indices, prices_tensor, floats_tensor, mean_prices, mean_floats, valid_combinations, valid_mean_prices, valid_mean_floats, masks
    torch.cuda.empty_cache()

    return final_combinations, case_items


def process_constraint(item):
    key, constraint = item
    combo_data, case_items = generate_combinations(constraint)
    
    if combo_data:
        cpu_final_combinations = []
        for combo in combo_data:
            cpu_combo = []
            offset = 0
            for case, count in constraint['case_counts'].items():
                case_item_list = case_items[case]
                for i in range(count):
                    index = combo['combination'][offset + i]
                    cpu_combo.append(case_item_list[index])
                offset += count
            
            cpu_final_combinations.append({
                'combination': cpu_combo,
                'avg_price': combo['avg_price'],
                'avg_float': combo['avg_float'],
                'profitability': combo['profitability']
            })
        
        sanitized_key = sanitize_filename(key)
        output_file = os.path.join(output_dir, f"{sanitized_key}.json")
        with open(output_file, 'wb') as f:
            f.write(orjson.dumps(cpu_final_combinations, option=orjson.OPT_INDENT_2))

    del combo_data
    torch.cuda.empty_cache()

output_dir = 'tradeup_combos'
os.makedirs(output_dir, exist_ok=True)

def main():
    constraint_items = list(constraints.items())
    
    num_processes = mp.cpu_count() - 6
    with mp.Pool(processes=num_processes) as pool:
        list(tqdm(pool.imap(process_constraint, constraint_items), total=len(constraint_items), desc="Processing constraints"))

    print("Processing complete. Results saved in the 'tradeup_combos' directory.")
    gc.collect()

if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    main()