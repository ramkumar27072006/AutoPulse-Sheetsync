import os
import json
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

def update_data():
    """Uploads real data from sales_data.xlsx to Google Sheets, replacing all old junk."""
    creds_json = os.getenv("GOOGLE_CREDS")
    spreadsheet_id = os.getenv("SHEET_ID") or os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME", "Sheet1")

    if not creds_json:
        raise ValueError("Missing GOOGLE_CREDS environment variable")
    if not spreadsheet_id:
        raise ValueError("Missing SHEET_ID/SPREADSHEET_ID environment variable")

    # Authenticate with service account
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

    # Load your real Excel file
    excel_path = os.path.join(os.path.dirname(__file__), "sales_data.xlsx")
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"❌ sales_data.xlsx not found at {excel_path}")

    df = pd.read_excel(excel_path)
    df.fillna(0, inplace=True)

    # Add a timestamp column to mark last sync (optional)
    df["last_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Clear entire sheet before writing new data
    sheet.clear()

    # Convert DataFrame to list of lists and upload
    records = [df.columns.tolist()] + df.values.tolist()
    sheet.update(records)

    print(f"✅ Synced {len(df)} rows from {os.path.basename(excel_path)} to Google Sheet [{sheet_name}]")

if __name__ == "__main__":
    update_data()
