"""
Smart Task Automator - Day 1 (Final Tested Version)
---------------------------------------------------
Processes sales_data.xlsx, fixes type issues, and calculates
total revenue grouped by category using 'order_value_eur'.
"""

import pandas as pd
import json
from datetime import datetime
import re

# Load Excel
df = pd.read_excel("sales_data.xlsx")

# Normalize headers
df.columns = df.columns.str.strip().str.lower()

# Define key columns manually for this dataset
price_col = "order_value_eur"     # confirmed existing column
group_col = "category"            # group by category
quantity_col = "units"            # if not in file, will default to 1

# If units/quantity column doesn’t exist → create it
if quantity_col not in df.columns:
    df["units"] = 1.0

# Clean numeric price column (remove text or symbols)
def clean_numeric(series):
    return (
        series.astype(str)
        .str.replace(r"[^0-9.\-]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )

df["units"] = clean_numeric(df["units"])
df[price_col] = clean_numeric(df[price_col])

# Calculate revenue
df["revenue"] = df["units"] * df[price_col]

# Group and summarize
summary = df.groupby(group_col, dropna=False)["revenue"].sum().reset_index()

# Prepare JSON structure
output = {
    "timestamp": datetime.now().isoformat(),
    "summary": summary.to_dict(orient="records")
}

# Save processed summary
with open("processed_data.json", "w") as f:
    json.dump(output, f, indent=4)

print("✅ Data processed successfully.")
print(f"Detected columns → Quantity: {quantity_col}, Price: {price_col}, Group: {group_col}")
print("💾 Output saved as processed_data.json")

print("\nSummary:")
print(summary)
