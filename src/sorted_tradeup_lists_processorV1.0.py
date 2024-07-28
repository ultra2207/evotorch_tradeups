import csv
import orjson
from collections import defaultdict
from tqdm import tqdm

def parse_tradeup_file(filename):
    tradeups = {}
    current_tradeup = ""
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith("Best Tradeup:"):
                current_tradeup = line.strip()
                tradeups[current_tradeup] = {"float_values": []}
            elif line.startswith("Best Individual:"):
                best_individual = eval(line.split(": ")[1])
                mid = len(best_individual) // 2
                tradeups[current_tradeup]["float_values"] = best_individual[mid:]
                tradeups[current_tradeup]["prices"] = best_individual[:mid]
            elif line.startswith("price_deviation:"):
                tradeups[current_tradeup]["price_deviation"] = float(line.split(": ")[1])
    return tradeups

def calculate_modified_price(prices, price_deviation):
    total_price = sum(prices)
    modified_price = (total_price / len(prices)) - price_deviation
    return modified_price

def process_tradeups(tradeups, csv_filename):
    result_json = defaultdict(set)
    expanded_json = defaultdict(list)

    print("Reading CSV file...")
    float_to_items = defaultdict(list)
    with open(csv_filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            float_value = float(row[4])
            float_to_items[float_value].append(row)

    print("Processing tradeups...")
    for tradeup, data in tqdm(tradeups.items()):
        modified_price = calculate_modified_price(data["prices"], data["price_deviation"])
        new_key = f"{tradeup}_{modified_price:.2f}"
        
        for float_value in data["float_values"]:
            matching_items = float_to_items.get(float_value, [])
            for item in matching_items:
                result_json[new_key].add(item[0].replace("_data.json", ""))
                expanded_json[new_key].append(item)


    return {k: list(v) for k, v in result_json.items()}, dict(expanded_json)

def save_json(data, filename):
    with open(filename, 'wb') as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

# Main execution
print("Parsing tradeup file...")
tradeups = parse_tradeup_file("sorted_tradeup_lists.txt")

print("Processing tradeups...")
result_json, expanded_json = process_tradeups(tradeups, "steam_data_processed.csv")

print("Saving results...")

save_json(expanded_json, "tradeup_expanded_items.json")

print("Done!")