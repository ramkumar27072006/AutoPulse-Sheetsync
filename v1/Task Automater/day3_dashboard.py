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
    """Load service account credentials from GOOGLE_CREDS or local file."""
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        try:
            try:
                info = json.loads(creds_json)
            except json.JSONDecodeError:
                fixed = creds_json.replace("'", '"').replace("\\n", "")
                info = json.loads(fixed)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.exception("Failed to parse GOOGLE_CREDS JSON")
            raise ValueError("Invalid GOOGLE_CREDS JSON") from e

    local_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local_path):
        logger.info("Using local service_account.json file")
        return Credentials.from_service_account_file(local_path, scopes=SCOPES)

    raise ValueError("Missing Google credentials (GOOGLE_CREDS not set and no local file found)")


def get_gspread_client():
    creds = load_credentials()
    return gspread.authorize(creds)


# ----------------------------------------------------
# Flask App Setup
# ----------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()


# ----------------------------------------------------
# Data Fetch Logic
# ----------------------------------------------------
def fetch_sheet_data():
    """Fetch latest and previous day columns from Google Sheets."""
    if not SHEET_ID:
        logger.warning("SHEET_ID not configured")
        return []

    try:
        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

        data = sheet.get_all_values()
        if not data or len(data) < 2:
            return []

        headers = data[0]
        rows = data[1:]

        category_index = headers.index("category")
        last_col_index = len(headers) - 1
        prev_col_index = len(headers) - 2 if len(headers) > 2 else None

        last_col_name = headers[last_col_index]
        prev_col_name = headers[prev_col_index] if prev_col_index else None

        logger.info(f"Latest column: {last_col_name}, Previous column: {prev_col_name}")

        formatted_data = []
        for row in rows:
            if len(row) <= last_col_index:
                continue
            category = row[category_index] or "Unknown"
            latest_value = parse_number(row[last_col_index])
            prev_value = parse_number(row[prev_col_index]) if prev_col_index else None

            growth = None
            if prev_value and prev_value != 0:
                growth = ((latest_value - prev_value) / prev_value) * 100

            formatted_data.append({
                "category": category,
                "latest": latest_value,
                "previous": prev_value,
                "growth": round(growth, 2) if growth is not None else None,
                "date": last_col_name
            })

        return formatted_data

    except Exception as e:
        logger.exception("Error fetching sheet data")
        return []


def parse_number(value):
    """Convert formatted strings to floats safely."""
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return 0.0


# ----------------------------------------------------
# Flask Routes
# ----------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    """Return JSON with latest + growth info."""
    data = fetch_sheet_data()
    if not data:
        data = [
            {"category": "Electronics", "latest": 120000, "previous": 100000, "growth": 20.0},
            {"category": "Books", "latest": 45000, "previous": 48000, "growth": -6.25},
            {"category": "Fashion", "latest": 82000, "previous": 79000, "growth": 3.8}
        ]
    return jsonify(data)


# ----------------------------------------------------
# Main App Entry
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
