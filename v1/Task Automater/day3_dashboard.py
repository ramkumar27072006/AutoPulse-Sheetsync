import os
import json
import logging
from flask import Flask, jsonify, render_template
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# Logging setup
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopulse")

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

# -------------------------
# Credential loading
# -------------------------
def load_credentials():
    """Load Google service account credentials from Render environment or local file."""
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        try:
            info = json.loads(creds_json)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.exception("Invalid GOOGLE_CREDS JSON format")
            raise ValueError("Invalid GOOGLE_CREDS format") from e

    local_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local_path):
        return Credentials.from_service_account_file(local_path, scopes=SCOPES)

    raise ValueError("No valid Google credentials found")

def get_gspread_client():
    creds = load_credentials()
    return gspread.authorize(creds)

# -------------------------
# Flask app setup
# -------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()

# -------------------------
# Core data fetcher
# -------------------------
def fetch_sheet_data():
    """
    Dynamically fetch the latest day's data (rightmost date column)
    from the Google Sheet.
    """
    if not SHEET_ID:
        logger.warning("SHEET_ID not configured.")
        return []

    try:
        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        all_values = sheet.get_all_values()

        if len(all_values) < 2:
            logger.warning("Sheet appears empty or missing data rows.")
            return []

        header = all_values[0]
        latest_col_index = len(header) - 1
        latest_date = header[latest_col_index]

        logger.info(f"Using latest data column: {latest_date}")

        data = []
        for row in all_values[1:]:
            if len(row) > latest_col_index:
                category = row[0] or "Unknown"
                value = row[latest_col_index].strip()
                try:
                    revenue = float(str(value).replace(",", "").replace("₹", "").strip())
                except ValueError:
                    revenue = 0.0
                data.append({
                    "category": category,
                    "revenue": revenue,
                    "date": latest_date
                })

        return data

    except Exception as e:
        logger.exception("Error fetching sheet data")
        return []

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    """API endpoint returning the latest Google Sheet data."""
    data = fetch_sheet_data()
    if not data:
        # Fallback sample data
        data = [
            {"category": "Electronics", "revenue": 120000},
            {"category": "Books", "revenue": 45000},
            {"category": "Fashion", "revenue": 82000}
        ]
    return jsonify(data)

@app.after_request
def add_no_cache_headers(response):
    """Prevent browser caching so data refreshes daily."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# -------------------------
# Entrypoint
# -------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
