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
            try:
                info = json.loads(creds_json)
            except json.JSONDecodeError:
                info = json.loads(creds_json.replace("'", '"').replace("\\n", ""))
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.error("Invalid GOOGLE_CREDS JSON: %s", e)
            raise
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
# Data Fetch Logic
# ----------------------------------------------------
def fetch_sheet_data():
    """Fetch last 2 non-empty date columns and compute growth."""
    try:
        if not SHEET_ID:
            raise ValueError("SHEET_ID not configured")

        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        metadata = sheet.spreadsheet.fetch_sheet_metadata()
        logger.info(f"🧩 Sheet last modifiedTime: {metadata.get('properties', {}).get('modifiedTime', 'unknown')}")
        logger.info(f"🧩 Header row fetched: {sheet.row_values(1)}")


        headers = sheet.row_values(1)
        rows = sheet.get_all_values()[1:]

        # Dynamically detect all columns with at least one numeric value
        valid_col_indices = []
        for idx in range(2, len(headers)):  # skip category and revenue
            col = [r[idx] for r in rows if idx < len(r)]
            numeric_count = sum(1 for v in col if parse_number(v) > 0)
            if numeric_count > 0:
                valid_col_indices.append(idx)

        if len(valid_col_indices) == 0:
            logger.warning("No valid daily columns found")
            return []

        last_col = valid_col_indices[-1]
        prev_col = valid_col_indices[-2] if len(valid_col_indices) > 1 else None

        logger.info(f"Last column detected: {headers[last_col]}, Previous: {headers[prev_col] if prev_col else 'N/A'}")

        data = []
        for row in rows:
            category = row[0] if len(row) > 0 else "Unknown"
            latest = parse_number(row[last_col]) if len(row) > last_col else 0
            previous = parse_number(row[prev_col]) if prev_col and len(row) > prev_col else 0
            growth = ((latest - previous) / previous * 100) if previous else None

            data.append({
                "category": category,
                "latest": latest,
                "previous": previous,
                "growth": round(growth, 2) if growth is not None else None,
                "date": headers[last_col]
            })

        return data

    except Exception as e:
        logger.exception("Error fetching Google Sheet data")
        return []


def parse_number(value):
    """Safely parse any numeric value from sheet."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        value = str(value).replace(",", "").replace("₹", "").strip()
        return float(value) if value and value != "nan" else 0.0
    except Exception:
        return 0.0


# ----------------------------------------------------
# Routes
# ----------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    if not data:
        data = [
            {"category": "Electronics", "latest": 120000, "previous": 100000, "growth": 20.0},
            {"category": "Books", "latest": 45000, "previous": 48000, "growth": -6.25},
            {"category": "Fashion", "latest": 82000, "previous": 79000, "growth": 3.8}
        ]
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

