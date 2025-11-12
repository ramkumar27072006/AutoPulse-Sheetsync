import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template, request
import gspread
from google.oauth2.service_account import Credentials

# Optional Excel support
try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopulse")

# ---------- Google scopes ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ---------- Config from env ----------
SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()
MASTER_XLSX_PATH = os.getenv("MASTER_XLSX_PATH", "sales_data.xlsx").strip()

# ---------- Credential loader ----------
def load_credentials():
    creds_json = os.getenv("GOOGLE_CREDS")
    if not creds_json:
        local = os.path.join(os.path.dirname(__file__), "service_account.json")
        if os.path.exists(local):
            return Credentials.from_service_account_file(local, scopes=SCOPES)
        raise ValueError("Missing GOOGLE_CREDS or local service_account.json")

    try:
        info = json.loads(creds_json.replace("\\n", "\n"))
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    except Exception:
        logger.exception("Failed to parse GOOGLE_CREDS")
        raise

def get_gspread_client():
    creds = load_credentials()
    return gspread.authorize(creds)

# ---------- Helpers ----------
def parse_number(value):
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip().replace(",", "").replace("₹", "").replace("Rs", "").strip()
        return float(s) if s else 0.0
    except Exception:
        return 0.0

# ---------- Fetch data from Google Sheets ----------
def fetch_sheet_data():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet(SHEET_NAME)

        values = ws.get_all_values()
        if len(values) < 2:
            logger.warning("Sheet has no data rows")
            return []

        header = values[0]
        rows = values[1:]

        # Detect last two numeric columns (latest and previous)
        last_col = len(header) - 1
        prev_col = last_col - 1 if last_col > 2 else None

        data = []
        for row in rows:
            if not row or len(row) <= last_col:
                continue
            category = row[0].strip() if len(row) > 0 else "Unknown"
            latest = parse_number(row[last_col])
            previous = parse_number(row[prev_col]) if prev_col is not None else 0
            growth = round(((latest - previous) / previous) * 100, 2) if previous else None
            data.append({
                "category": category,
                "latest": latest,
                "previous": previous,
                "growth": growth,
                "date": header[last_col]
            })
        logger.info(f"Fetched {len(data)} rows from Google Sheet")
        return data
    except Exception as e:
        logger.exception("Error fetching Google Sheet data")
        return []

# ---------- Sync from local Excel to Google Sheet ----------
def sync_from_master():
    if not OPENPYXL_AVAILABLE:
        return {"ok": False, "error": "openpyxl not installed"}
    if not os.path.exists(MASTER_XLSX_PATH):
        return {"ok": False, "error": f"Master file not found: {MASTER_XLSX_PATH}"}

    try:
        wb = load_workbook(MASTER_XLSX_PATH, data_only=True)
        ws_master = wb.active
        master_data = [list(row) for row in ws_master.iter_rows(values_only=True)]
        if len(master_data) < 2:
            return {"ok": False, "error": "Master file too small"}

        master_header = master_data[0]
        latest_col = len(master_header) - 1
        latest_label = master_header[latest_col] or datetime.now().strftime("%b %d, %Y %H:%M")
        master_map = {str(r[0]).strip(): parse_number(r[latest_col]) for r in master_data[1:] if r[0]}

        gc = get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet(SHEET_NAME)

        # Add a new header column
        existing_header = ws.row_values(1)
        next_col = len(existing_header) + 1
        ws.update_cell(1, next_col, latest_label)

        # Update category-wise values
        sheet_rows = ws.get_all_values()[1:]
        for i, row in enumerate(sheet_rows, start=2):
            cat = row[0].strip() if row and row[0] else "Unknown"
            val = master_map.get(cat)
            if val is not None:
                ws.update_cell(i, next_col, val)

        logger.info(f"Appended column {latest_label} to Sheet successfully.")
        return {"ok": True, "written_column": next_col, "header": latest_label}
    except Exception:
        logger.exception("Sync from master failed")
        return {"ok": False, "error": "Sync failed - check logs"}

# ---------- Flask App ----------
app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    if not data:
        return jsonify({
            "data": [],
            "updated_at": datetime.utcnow().isoformat(),
            "error": "No data or sheet access issue"
        })
    return jsonify({"data": data, "updated_at": datetime.utcnow().isoformat()})

@app.route("/api/sync", methods=["POST"])
def api_sync():
    result = sync_from_master()
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
