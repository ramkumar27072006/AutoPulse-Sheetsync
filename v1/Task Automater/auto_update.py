import os
import json
import gspread
import pandas as pd
import gdown
from datetime import datetime
from google.oauth2.service_account import Credentials

# ----------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------
# 👇 Replace with your actual Google Drive file ID
DRIVE_FILE_ID = "1VmbHlPBcFdi9TdwPlvbSJm9FWY16Xvpm"  # <- from your shared link

def download_excel_from_drive():
    """Download the Excel dataset from Google Drive."""
    url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
    local_path = "/tmp/sales_data.xlsx"
    gdown.download(url, local_path, quiet=False)
    print(f"✅ Downloaded sales_data.xlsx from Drive → {local_path}")
    return local_path


# ----------------------------------------------------
# 2. GOOGLE SHEETS CONNECTION
# ----------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    creds_json = os.getenv("GOOGLE_CREDS")
    if not creds_json:
        raise ValueError("Missing GOOGLE_CREDS environment variable")

    try:
        info = json.loads(creds_json)
    except json.JSONDecodeError:
        info = json.loads(creds_json.replace("'", '"').replace("\\n", ""))

    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


# ----------------------------------------------------
# 3. MAIN UPDATE FUNCTION
# ----------------------------------------------------
def update_data():
    spreadsheet_id = os.getenv("SHEET_ID") or os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME", "Sheet1")
    if not spreadsheet_id:
        raise ValueError("Missing SHEET_ID/SPREADSHEET_ID environment variable")

    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # --- Download and read the latest Excel file ---
    excel_path = download_excel_from_drive()
    df = pd.read_excel(excel_path)
    df.fillna(0, inplace=True)

    # --- Read existing Google Sheet data ---
    existing = sheet.get_all_values()
    headers = existing[0] if existing else []
    rows = existing[1:] if len(existing) > 1 else []

    # --- Create new timestamped column ---
    new_col = datetime.now().strftime("%b %d, %Y %H:%M")
    if new_col in headers:
        print(f"⚠️ Already updated at {new_col}. Skipping duplicate update.")
        return

    # --- Append new data matching by category ---
    if headers:
        categories = [r[0] for r in rows]
        for _, r in df.iterrows():
            cat, val = r["category"], float(r["revenue"])
            if cat in categories:
                rows[categories.index(cat)].append(val)
            else:
                new_row = [cat] + ["" for _ in range(len(headers) - 1)] + [val]
                rows.append(new_row)
        headers.append(new_col)
        final_data = [headers] + rows
    else:
        df[new_col] = df["revenue"]
        final_data = [df.columns.tolist()] + df.values.tolist()

    # --- Write to Google Sheet ---
    sheet.clear()
    sheet.update(final_data)
    print(f"✅ Appended new column '{new_col}' from Drive Excel dataset")

# ----------------------------------------------------
# 4. ENTRY POINT
# ----------------------------------------------------
if __name__ == "__main__":
    update_data()
