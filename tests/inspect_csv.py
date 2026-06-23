# debug_diseases.py
import pandas as pd
import csv

file_path = "backend/data/raw/Diseases.csv"

# Method 1: Count unique diseases
df = pd.read_csv(file_path)
unique_diseases = df['diseases'].nunique()
print(f"Unique diseases: {unique_diseases}")
print(f"Total rows: {len(df)}")

# Method 2: Check disease name column
print(f"\nFirst 10 disease names:")
print(df['diseases'].head(10).tolist())

# Method 3: Check for empty values
empty_diseases = df['diseases'].isna().sum()
print(f"\nEmpty disease names: {empty_diseases}")

# Method 4: Check unique disease names
unique_names = df['diseases'].unique()
print(f"\nFirst 20 unique disease names:")
print(unique_names[:20].tolist())

# Method 5: Count rows with symptoms
symptom_cols = df.columns[1:]
print(f"\nSymptom columns: {len(symptom_cols)}")

# Count rows that have at least one symptom
has_symptom = 0
for _, row in df.iterrows():
    if (row.iloc[1:] == 1).any():
        has_symptom += 1
print(f"Rows with at least one symptom: {has_symptom}")