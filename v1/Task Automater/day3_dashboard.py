import os
import json
import logging
from flask import Flask, jsonify, render_template
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopulse")

# Required Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]

def load_credentials():
    """Load service account credentials from GOOGLE_CREDS or local file."""
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        try:
            # Try to load directly from environment (handle escaped or raw JSON)
            try:
                info = json.loads(creds_json)
            except json.JSONDecodeError:
                fixed = creds_json.replace("'", '"').replace("\n", "")
                info = json.loads(fixed)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return creds
        except Exception as e:
            logger.exception("Failed to parse GOOGLE_CREDS JSON from environment")
            raise ValueError("Invalid GOOGLE_CREDS JSON") from e

    # Fallback if environment variable not found
    local_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local_path):
        logger.info("Using local service_account.json file")
        return Credentials.from_service_account_file(local_path, scopes=SCOPES)

    raise ValueError("Missing Google credentials (GOOGLE_CREDS not set and no local file found)")

def get_gspread_client():
    creds = load_credentials()
    return gspread.authorize(creds)

# Flask App
app = Flask(__name__, static_folder="static", template_folder="templates")

# Env variables
SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()

def fetch_sheet_data():
    """Fetch and normalize data from the Google Sheet."""
    if not SHEET_ID:
        logger.warning("SHEET_ID not configured")
        return []

    try:
        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        records = sheet.get_all_records()
        data = []
        for row in records:
            cat = row.get("category") or row.get("Category") or "Unknown"
            rev = row.get("revenue") or row.get("Revenue") or 0
            try:
                rev = float(str(rev).replace("₹", "").replace(",", "").strip())
            except Exception:
                rev = 0
            data.append({"category": cat, "revenue": rev})
        return data
    except Exception as e:
        logger.exception("Failed to fetch sheet data")
        return []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    if not data:
        # Fallback sample data to keep UI alive
        data = [
            {"category": "Electronics", "revenue": 120000},
            {"category": "Books", "revenue": 45000},
            {"category": "Fashion", "revenue": 82000}
        ]
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
