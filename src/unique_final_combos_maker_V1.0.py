import json
import os
import re
import plotly.graph_objects as go

rarities = ['Mil-Spec', 'Restricted', 'Classified', 'Covert']

def process_string(s):
    return re.sub(r'[\d()]+', '', s.replace('_', ' ')).strip()

def extract_tradeup_details(filename):
    base_string = filename[len("Best_Tradeup_"):-len(".json")]

    collections_part, extra_part = base_string.split("+", 1)
    base_collection_part, modifier_collection_part = collections_part.split("_(", 1)[0], extra_part.split(")_", 1)[0]
    
    base_collection_quantity = int(re.findall(r'\((\d+)\)', collections_part)[0])
    modifier_collection_quantity = int(re.findall(r'\((\d+)\)', extra_part)[0])

    base_collection = re.sub(r'_\(\d+\)', '', base_collection_part).replace('_', ' ')
    modifier_collection = re.sub(r'_\(\d+\)', '', modifier_collection_part).replace('_', ' ')
    modifier_collection = process_string(modifier_collection)
    items = re.findall(r'_([a-zA-Z-]+)_', filename)
    input_rarity = re.findall(r'_([a-zA-Z-]+)_', filename)[-1]
    if input_rarity not in rarities:
        print(input_rarity)
        print(filename)
        print(items)
        print('errror')
    max_tradeup_float = float(re.findall(r'_([\d.]+)_', filename)[0])
    tradeup_breakeven_price = float(re.findall(r'_([\d.]+)\.json', filename)[-1])

    return {
        "base_collection": base_collection,
        "base_collection_quantity": base_collection_quantity,
        "modifier_collection": modifier_collection,
        "modifier_collection_quantity": modifier_collection_quantity,
        "input_rarity": input_rarity,
        "max_tradeup_float": max_tradeup_float,
        "tradeup_breakeven_price": tradeup_breakeven_price
    }

def collect_combinations_from_jsons(input_dir):
    all_combinations = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            with open(os.path.join(input_dir, filename), 'r') as file:
                data = json.load(file)
                for combo in data:
                    combo['tradeup_details'] = extract_tradeup_details(filename)
                all_combinations.extend(data)
    return all_combinations

def sort_combinations_by_profitability(combinations):
    return sorted(combinations, key=lambda x: x['profitability'], reverse=True)

def get_unique_combinations(combinations):
    used_items = set()
    unique_tradeups_final = []

    for combo in combinations:
        combo_items = [tuple(item) for item in combo['combination']]
        
        # Check if any item in this combo has been used before or if there are duplicates within the combo
        if any(item in used_items for item in combo_items) or len(set(combo_items)) != len(combo_items):
            continue
        
        # If we reach here, all items in this combo are unique
        unique_tradeups_final.append(combo)
        
        # Add all items from this combo to the used_items set
        used_items.update(combo_items)

    return unique_tradeups_final

def save_unique_combinations(unique_combinations, output_file):
    with open(output_file, 'w') as file:
        json.dump(unique_combinations, file, indent=2)

def calculate_stats_and_plot(filename):
    with open(filename, 'r') as file:
        combinations = json.load(file)

    num_combinations = len(combinations)
    total_inputs_price = 0
    total_profit = 0
    
    profits = []
    expenses = []

    for combo in combinations:
        avg_price = combo['avg_price']
        profitability = combo['profitability']
        num_inputs = len(combo['combination'])
        
        # Calculate the total input price for this combination
        combo_total_inputs_price = avg_price * num_inputs
        
        # Update total inputs price
        total_inputs_price += combo_total_inputs_price
        
        # Calculate total profit
        combo_profit = profitability * combo_total_inputs_price - combo_total_inputs_price
        total_profit += combo_profit
        
        # Track individual profits and expenses
        expenses.append(total_inputs_price)
        profits.append(total_profit)
    
    # Calculate overall profitability
    overall_profitability = (total_inputs_price + total_profit) / total_inputs_price
    
    # Print statistics
    print(f"Number of combinations: {num_combinations}")
    print(f"Total inputs price: {total_inputs_price:.2f}")
    print(f"Total profit: {total_profit:.2f}")
    print(f"Overall profitability: {overall_profitability:.2f}")

    # Plot the graph using Plotly
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=expenses,
        y=profits,
        mode='lines',  # Only plot connected lines, no markers
        line=dict(color='blue', width=2),
        name='Profit vs Money Spent'
    ))

    fig.update_layout(
        title='Profit vs Money Spent for Tradeups',
        xaxis_title='Money Spent',
        yaxis_title='Profit',
        xaxis=dict(type='linear'),
        yaxis=dict(type='linear'),
        template='plotly_white',
        autosize=True,
    )
    
    fig.show()

def main():
    input_dir = 'tradeup_combos'
    output_file = 'unique_tradeups_final.json'
    
    # Collect combinations from all JSON files
    all_combinations = collect_combinations_from_jsons(input_dir)
    
    # Sort combinations by profitability
    sorted_combinations = sort_combinations_by_profitability(all_combinations)
    
    # Get unique combinations
    unique_combinations = get_unique_combinations(sorted_combinations)
    
    # Save unique combinations to a file
    save_unique_combinations(unique_combinations, output_file)
    
    # Calculate stats and plot
    calculate_stats_and_plot(output_file)
    
    print(f"Unique tradeups saved to {output_file}")

if __name__ == '__main__':
    main()
