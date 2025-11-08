# day3_dashboard.py (restored stable version)
import os
import json
import gspread
from flask import Flask, jsonify, render_template
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

# Google Sheets setup
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")

if not (SHEET_ID and GOOGLE_CREDS):
    raise ValueError("Missing Google credentials or Sheet ID environment variables")

creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS))
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    try:
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        print(f"⚠️ Google Sheets fetch failed: {e}")
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
