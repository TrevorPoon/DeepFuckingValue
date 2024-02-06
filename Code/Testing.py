import os
import pandas as pd

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Go to the "Processed Data" folder
processed_data_dir = os.path.join(parent_dir, "Processed Data", "Finviz")

os.chdir(processed_data_dir)

csv_files = [file for file in os.listdir() if file.startswith("CB_") and file.endswith(".csv")]

# Sort the CSV files by name to get the latest one
csv_files.sort(reverse=False)

if csv_files:
    # Get the latest CSV file
    latest_csv = csv_files[0]

    # Read the CSV file as a pandas DataFrame
    df = pd.read_csv(latest_csv)

    print(df)

    df.loc[df['EPS past 5Y'] > 0, 'Fundamental Score'] += 1
    df.loc[df['Sales past 5Y'] > 0, 'Fundamental Score'] += 1
    df.loc[df['Debt/Eq'] < 1, 'Fundamental Score'] += 1
    df.loc[df['Profit M'] > 0.1, 'Fundamental Score'] += 1
    df.loc[df['Quick R'] > 1, 'Fundamental Score'] += 1
    df.loc[df['P/B'] < 1, 'Fundamental Score'] += 1
    df.loc[df['Insider Trans'] >= 0, 'Fundamental Score'] += 1

    # Print the DataFrame
    print(df)