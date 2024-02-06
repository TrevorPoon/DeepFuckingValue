import os

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

    print(latest_csv)