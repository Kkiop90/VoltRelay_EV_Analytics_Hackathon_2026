from pathlib import Path
import pandas as pd
import numpy as np

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset directory
DATA_DIR = BASE_DIR / "Data"/ "Raw"

# Check dataset folder
print("Dataset folder:", DATA_DIR)
print("Folder exists:", DATA_DIR.exists())

# List available files
for file in DATA_DIR.iterdir():
    print(file.name)