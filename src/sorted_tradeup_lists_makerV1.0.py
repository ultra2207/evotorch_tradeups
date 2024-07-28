import re
import glob
import os

# Define the regex pattern
pattern_item = re.compile(
    r"(Best Tradeup: .*?)\n(Best Individual: \[.*?\])\nprice_deviation: (-?\d+\.\d+)\nfloat_deviation: (-?\d+\.\d+)\n------"
)

# Initialize an empty list to store the items with their profitability
items_with_profitability = []

# Function to calculate profitability
def calculate_profitability(prices, price_deviation):
    if price_deviation<=0:

        print('deviation:',price_deviation)

        profitability = ((sum(prices) / len(prices))-price_deviation) / (sum(prices) / len(prices))

        return profitability
    else:
        return 0.0

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Read all text files that start with "best" in the same directory as the script
for filepath in glob.glob(os.path.join(current_dir, "best*.txt")):
    with open(filepath, 'r') as file:
        content = file.read()

        # Find all items in the file
        matches = pattern_item.findall(content)
        for match in matches:
            best_tradeup = match[0]
            best_individual = match[1]
            price_deviation = float(match[2])
            float_deviation = float(match[3])
            
            # Extract prices and floats from best_individual
            best_individual_values = eval(best_individual.split(": ")[1])
            length = len(best_individual_values)
            
            if length % 2 != 0:
                raise ValueError("The length of Best Individual values is not even.")
            
            half_length = length // 2
            prices = best_individual_values[:half_length]
            floats = best_individual_values[half_length:]

            # Check if float_deviation <= 0
            if float_deviation <= 0: #change to 0
                # Calculate profitability
                tradeup_profitability = calculate_profitability(prices, price_deviation)

                num_unique_tradeups = len(set(floats)) // 10

                max_num_unique_tradeups = half_length // 10

                total_price = (sum(x for x in prices)) * (num_unique_tradeups / max_num_unique_tradeups)

                overall_profitability = 1 + num_unique_tradeups * (tradeup_profitability / 100 - 1)

                # Store the item with its profitability and other details
                item_details = (
                    f"{best_tradeup}\n"
                    f"{best_individual}\n"
                    f"price_deviation: {price_deviation}\n"
                    f"float_deviation: {float_deviation}\n"
                    f"Profitability: {tradeup_profitability}\n"  # using tradeup profitabilty as currently only 1 tradeup per individual
                    f"Total Price: {total_price}\n"
                    f"---------------------------------"
                )
                items_with_profitability.append((item_details, tradeup_profitability,total_price))


# Sort the items by profitability in descending order
sorted_items = sorted(items_with_profitability, key=lambda x: x[1], reverse=True)

# Save the sorted items to a new text file in the current directory
output_filepath = os.path.join(current_dir, "sorted_tradeup_lists.txt")
with open(output_filepath, 'w') as output_file:
    for item_details, _,_ in sorted_items:
        output_file.write(f"{item_details}\n\n")

    print(f"Sorted items have been saved to {output_filepath}")
