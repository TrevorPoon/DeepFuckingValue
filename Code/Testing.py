import pandas as pd

# Path to the CSV file
csv_path = "/Users/trevorpoon/Desktop/Coding Projects/DeepFuckingValue/Raw Data/Finviz/Screener_Most_Shorted_Stocks_2024-02-10.csv"

# Read the CSV file
df = pd.read_csv(csv_path)

# Remove blank lines from column headers
df.columns = df.columns.str.strip()

# Save the DataFrame back to the CSV file
df.to_csv(csv_path, index=False)