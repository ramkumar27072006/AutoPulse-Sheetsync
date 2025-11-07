# day3_dashboard.py
import os
import json
import pandas as pd
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ------------------------------------------------------------
# 1️⃣  Google Sheets setup
# ------------------------------------------------------------
SHEET_ID = os.getenv("SHEET_ID")                 # from Render → Environment Variables
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")         # full JSON string (service account)

if not (SHEET_ID and GOOGLE_CREDS):
    raise RuntimeError("Missing SHEET_ID or GOOGLE_CREDS environment variables.")

creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS))
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# ------------------------------------------------------------
# 2️⃣  Data update logic
# ------------------------------------------------------------
def update_google_sheet():
    """Reads sales_data.xlsx and appends one column daily."""
    try:
        data_path = os.path.join(os.path.dirname(__file__), "sales_data.xlsx")
        df = pd.read_excel(data_path)

        # Expecting columns like ['category', 'revenue_day1', 'revenue_day2', ...]
        # Determine how many columns already exist in Sheet
        existing = sheet.get_all_records()
        last_col = len(existing[0]) if existing else 0

        # Select next revenue column from Excel
        excel_cols = list(df.columns)
        base_cols = ["category", "revenue"]
        extra_cols = [c for c in excel_cols if c not in base_cols]

        next_index = min(len(extra_cols), last_col - 1)  # fallback
        if last_col < len(excel_cols):
            next_col = excel_cols[last_col]
        else:
            print("✅ All columns already synced.")
            return

        # Prepare column header and values
        header = f"{next_col} ({datetime.now().strftime('%b %d %H:%M')})"
        values = [[v] for v in df[next_col].tolist()]

        # Write new header
        sheet.update_cell(1, last_col + 1, header)
        # Write column values
        sheet.update(f"{chr(65 + last_col)}2:{chr(65 + last_col)}{len(values)+1}", values)

        print(f"✅ Synced column {next_col} → Google Sheet at {datetime.now()}")

    except Exception as e:
        print("❌ Update failed:", e)

# ------------------------------------------------------------
# 3️⃣  Background scheduler (8 AM IST daily)
# ------------------------------------------------------------
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(update_google_sheet, "cron", hour=8, minute=0)
scheduler.start()

# ------------------------------------------------------------
# 4️⃣  Dashboard routes
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    try:
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
