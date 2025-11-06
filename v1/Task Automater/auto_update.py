import gspread
from google.oauth2.service_account import Credentials
import json, os
from datetime import datetime

def update_data():
    creds_json = os.getenv("GOOGLE_CREDS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")

    creds = Credentials.from_service_account_info(json.loads(creds_json))
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).sheet1

    # Read current data
    data = sheet.get_all_records()

    # Simulate new daily column or calculation
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet.update_cell(1, len(data[0]) + 1, f"Update @ {now}")

    print(f"[{now}] Data updated successfully.")

if __name__ == "__main__":
    update_data()
