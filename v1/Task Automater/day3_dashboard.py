import os
import json
import logging
from flask import Flask, jsonify, render_template
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------
# Logging setup
# --------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("autopulse")

# --------------------------------------
# Google API scopes
# --------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

# --------------------------------------
# Load credentials
# --------------------------------------
def load_credentials():
    """Load Google credentials from Render secret or local JSON."""
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        try:
            info = json.loads(creds_json)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.exception("Invalid GOOGLE_CREDS format")
            raise ValueError("Invalid GOOGLE_CREDS format") from e

    local_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local_path):
        logger.info("Using local service_account.json file")
        return Credentials.from_service_account_file(local_path, scopes=SCOPES)

    raise ValueError("Missing Google service account credentials")

def get_gspread_client():
    creds = load_credentials()
    return gspread.authorize(creds)

# --------------------------------------
# Flask app setup
# --------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()

# --------------------------------------
# Fetch data dynamically
# --------------------------------------
def fetch_sheet_data():
    """Fetch latest day's data from the rightmost column of the Google Sheet."""
    if not SHEET_ID:
        logger.warning("SHEET_ID not configured")
        return []

    try:
        gc = get_gspread_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        all_values = sheet.get_all_values()

        if len(all_values) < 2:
            logger.warning("Empty or invalid sheet.")
            return []

        headers = [str(h).strip() for h in all_values[0] if h]
        latest_col = len(headers) - 1
        latest_date = headers[latest_col]

        logger.info(f"📊 Fetching latest column: {latest_date} (index {latest_col})")

        dataset = []
        for row in all_values[1:]:
            if len(row) > latest_col:
                category = str(row[0]).strip() or "Unknown"
                val = row[latest_col].strip()
                try:
                    revenue = float(str(val).replace(",", "").replace("₹", "").strip())
                except Exception:
                    revenue = 0.0
                dataset.append({
                    "category": category,
                    "revenue": revenue,
                    "date": latest_date
                })

        return dataset

    except Exception as e:
        logger.exception("Error fetching Google Sheet data")
        return []

# --------------------------------------
# Routes
# --------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    if not data:
        # fallback demo
        data = [
            {"category": "Electronics", "revenue": 120000},
            {"category": "Books", "revenue": 45000},
            {"category": "Fashion", "revenue": 82000}
        ]
    return jsonify(data)

@app.after_request
def disable_cache(response):
    """Force fresh data on each reload."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# --------------------------------------
# Entrypoint
# --------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting AutoPulse Sheetsync on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
