from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "dataset" / "medicinal_plants.csv"

if not CSV_PATH.is_file():
    raise SystemExit(
        f"Dataset not found: {CSV_PATH}\n"
        "Place medicinal_plants.csv inside the project's dataset folder."
    )

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
print("\nHERB-AI DATASET COMPLETENESS REPORT")
print("=" * 60)
print(f"File: {CSV_PATH}")
print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
for column in df.columns:
    valid = df[column].notna() & df[column].astype(str).str.strip().ne("")
    available = int(valid.sum())
    missing = len(df) - available
    completion = (available / len(df) * 100) if len(df) else 0
    print(f"\n{column}: {available} available, {missing} missing ({completion:.2f}%)")

sample_columns = [
    "common_name", "scientific_name", "botanical_family",
    "traditional_uses", "hindi_name", "sanskrit_name",
    "plant_parts_used", "known_compounds"
]
available_columns = [c for c in sample_columns if c in df.columns]
if available_columns:
    print("\nSAMPLE PLANT RECORDS")
    print("=" * 60)
    print(df[available_columns].head(10).to_string(index=False))
