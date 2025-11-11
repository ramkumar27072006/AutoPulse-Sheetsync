import os
import json
import logging
from flask import Flask, jsonify, render_template
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------
# Logging setup
# ----------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopulse")

# ----------------------------------------------------
# Google Sheets Access
# ----------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def load_credentials():
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        try:
            # Handle both escaped and raw JSON formats
            try:
                info = json.loads(creds_json)
            except json.JSONDecodeError:
                info = json.loads(creds_json.replace("'", '"').replace("\\n", ""))
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.error("Invalid GOOGLE_CREDS JSON: %s", e)
            raise
    # Fallback to local file if running locally
    path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(path):
        return Credentials.from_service_account_file(path, scopes=SCOPES)
    raise ValueError("Missing Google credentials (GOOGLE_CREDS not set or file missing)")


def get_gspread_client():
    return gspread.authorize(load_credentials())


# ----------------------------------------------------
# Flask Setup
# ----------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()

# ----------------------------------------------------
# Utility
# ----------------------------------------------------
def parse_number(value):
    """Safely parse numeric value from Google Sheet cell."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        value = str(value).replace(",", "").replace("₹", "").strip()
        return float(value) if value and value != "nan" else 0.0
    except Exception:
        return 0.0


# ----------------------------------------------------
# Core Data Logic
# ----------------------------------------------------
def fetch_sheet_data():
    """Read Google Sheet (dates as columns) and compute per-category daily growth."""
    try:
        if not SHEET_ID:
            raise ValueError("SHEET_ID not configured")

        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        headers = sheet.row_values(1)
        rows = sheet.get_all_values()[1:]

        # Identify last 2 date columns dynamically
        date_cols = headers[2:]  # Skip category & revenue columns
        if len(date_cols) < 2:
            logger.warning("Not enough date columns to compute daily change.")
            return []

        last_col = len(headers) - 1
        prev_col = len(headers) - 2

        logger.info(f"✅ Using columns: {headers[prev_col]} → {headers[last_col]}")

        data = []
        for row in rows:
            if len(row) < 3:
                continue

            category = row[0]
            latest = parse_number(row[last_col]) if len(row) > last_col else 0
            previous = parse_number(row[prev_col]) if len(row) > prev_col else 0
            growth = ((latest - previous) / previous * 100) if previous else 0

            data.append({
                "category": category,
                "latest": latest,
                "previous": previous,
                "growth": round(growth, 2),
                "date": headers[last_col]
            })

        logger.info(f"✅ Loaded {len(data)} rows from Google Sheets.")
        return data

    except Exception as e:
        logger.exception("Error fetching Google Sheet data")
        return []


# ----------------------------------------------------
# Flask Routes
# ----------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    logger.info(f"📊 Sending {len(data)} live records to frontend.")
    return jsonify(data)


# ----------------------------------------------------
# Entry Point
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
