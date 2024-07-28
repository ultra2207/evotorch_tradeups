import orjson
from tqdm import tqdm

def get_wear(float_value):
    if float_value < 0.07:
        return "Factory New"
    elif float_value < 0.15:
        return "Minimal Wear"
    elif float_value < 0.38:
        return "Field-Tested"
    elif float_value < 0.45:
        return "Well-Worn"
    else:
        return "Battle-Scarred"

def format_data(input_file, output_file, sample_output_file):
    with open(input_file, 'rb') as f:
        data = orjson.loads(f.read())

    formatted_data = {}
    sample_formatted_data = {}

    for idx, (key, value) in enumerate(tqdm(data.items(), desc="Processing items")):
        tradeup_info = value[0]
        items_info = value[1]

        formatted_items = []

        for case, items in items_info.items():
            for item in items:
                wear = get_wear(item['floatvalue'])
                formatted_item = [
                    f"{item['name']} ({wear})",
                    "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20placeholder",
                    case,
                    str(item['price']),
                    str(item['floatvalue']),
                    "placeholder",
                    "placeholder"
                ]
                formatted_items.append(formatted_item)

        # Constructing the new key
        new_key = f"Best Tradeup: {key}_{tradeup_info['tradeup_price']:.2f}"
        formatted_data[new_key] = formatted_items
        
        # Adding to sample data (first 5 complete key-value pairs)
        if idx < 5:
            sample_formatted_data[new_key] = formatted_items

    print("Saving main output file...")
    with open(output_file, 'wb') as f:
        f.write(orjson.dumps(formatted_data, option=orjson.OPT_INDENT_2))

    print("Saving sample output file...")
    with open(sample_output_file, 'wb') as f:
        f.write(orjson.dumps(sample_formatted_data, option=orjson.OPT_INDENT_2))

    print("Processing complete.")

# Usage
format_data('processed_items.json', 'formatted_processed_items.json', 'formatted_processed_items_sample.json')