from pathlib import Path, Path as path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "Data"/ "Raw"
datapath = path("data/raw")
files =["batteries.csv",
        "city_daily_context.csv",
        "fleet_partners.csv",
        "riders.csv",
        "station_hourly_status.csv",
        "stations.csv",
        "support_tickets.csv",
        "swap_events.csv"]
data = {}

for filename in files:
    input_path = DATA_DIR / filename
    if filename == "city_daily_context.csv" and not input_path.exists():
        input_path = BASE_DIR / "Data" / "Cleaned_data" / "city_daily_context_cleaned.csv"
        print(f"Raw city context file not found; using existing cleaned file: {input_path}")

    df = pd.read_csv(input_path)

    data[filename.replace(".csv", "")] = df

    print(f"\nDataset: {filename}")
    print("Shape:", df.shape)
    print("Duplicates:", df.duplicated().sum())
    print("Missing values:\n", df.isnull().sum())
    print("columns:\n", df.columns)

    