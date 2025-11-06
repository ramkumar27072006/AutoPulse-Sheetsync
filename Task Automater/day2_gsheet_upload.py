"""
Smart Task Automator - Day 2 (Google Sheets Upload)
--------------------------------------------------
Reads processed_data.json and uploads it to your Google Sheet automatically.
"""

import gspread
import json
from google.oauth2.service_account import Credentials

# --- Google Sheets setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(CREDS)

# --- Open your Google Sheet ---
SPREADSHEET_ID = "1GLKQllVmysW4ARvx7RWs2KDQOmsnNMwJWaqebFsMqs4"  # e.g. 1AbCdEFghIJKlmnopQRstuVWXYZ1234567890
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # use the first worksheet

# --- Read processed JSON file ---
with open("processed_data.json", "r") as f:
    data = json.load(f)

summary = data["summary"]

# --- Clear existing data and write new ---
sheet.clear()

# Write header
headers = list(summary[0].keys())
sheet.append_row(headers)

# Write each row
for row in summary:
    sheet.append_row(list(row.values()))

print("✅ Google Sheet updated successfully!")
