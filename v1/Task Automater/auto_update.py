import os
import json
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

def update_data():
    """Syncs real Excel data (sales_data.xlsx) to Google Sheets daily/hourly."""
    # --- Load credentials and config ---
    creds_json = os.getenv("GOOGLE_CREDS")
    spreadsheet_id = os.getenv("SHEET_ID") or os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME", "Sheet1")

    if not creds_json:
        raise ValueError("Missing GOOGLE_CREDS environment variable.")
    if not spreadsheet_id:
        raise ValueError("Missing SHEET_ID/SPREADSHEET_ID environment variable.")

    # --- Authenticate ---
    try:
        info = json.loads(creds_json)
    except json.JSONDecodeError:
        info = json.loads(creds_json.replace("'", '"').replace("\\n", ""))
    creds = Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # --- Load local Excel file ---
    excel_path = os.path.join(os.path.dirname(__file__), "sales_data.xlsx")
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"sales_data.xlsx not found at {excel_path}")

    df = pd.read_excel(excel_path)
    df.fillna(0, inplace=True)

    # --- Add daily/hourly timestamp column ---
    timestamp_col = datetime.now().strftime("%b %d, %Y %H:%M")
    if timestamp_col not in df.columns:
        df[timestamp_col] = df.iloc[:, 1]  # replicate revenue or daily metric

    # --- Upload to Google Sheets ---
    records = [df.columns.tolist()] + df.values.tolist()
    sheet.clear()
    sheet.update(records)

    print(f"✅ Synced {len(df)} rows from sales_data.xlsx to Google Sheets [{sheet_name}] at {timestamp_col}")

if __name__ == "__main__":
    update_data()
