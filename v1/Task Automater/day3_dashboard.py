# day3_dashboard.py
import os
import json
import logging
import base64
from datetime import datetime
from flask import Flask, jsonify, render_template, request
import gspread
from google.oauth2.service_account import Credentials

try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopulse")

# Google API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Environment config
SHEET_ID = os.getenv("SHEET_ID", "").strip()
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1").strip()
MASTER_XLSX_PATH = os.getenv("MASTER_XLSX_PATH", "sales_data.xlsx").strip()
SYNC_SECRET = os.getenv("SYNC_SECRET", "").strip()

# ------------------------------------------------------------------
# CREDENTIALS LOADER
# ------------------------------------------------------------------
def load_credentials():
    """Load Google credentials from env var or file."""
    creds_env = os.getenv("GOOGLE_CREDS")

    if creds_env:
        try:
            # Try base64 decode (most stable for Render env)
            try:
                decoded = base64.b64decode(creds_env)
                info = json.loads(decoded)
                logger.info("Loaded GOOGLE_CREDS (base64)")
                return Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception:
                pass

            # Try JSON directly
            try:
                info = json.loads(creds_env)
                logger.info("Loaded GOOGLE_CREDS (raw JSON)")
                return Credentials.from_service_account_info(info, scopes=SCOPES)
            except json.JSONDecodeError:
                # Fix escaped newlines
                fixed = creds_env.replace("\\n", "\n")
                info = json.loads(fixed)
                logger.info("Loaded GOOGLE_CREDS (newline fixed)")
                return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception:
            logger.exception("Failed to parse GOOGLE_CREDS")

    # Fallback to local file
    local = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local):
        logger.info("Loaded credentials from service_account.json")
        return Credentials.from_service_account_file(local, scopes=SCOPES)

    raise ValueError("Missing GOOGLE_CREDS")

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def get_gspread_client():
    return gspread.authorize(load_credentials())

def parse_number(v):
    try:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", "").replace("₹", "").replace("Rs", "")
        return float(s) if s else 0.0
    except Exception:
        return 0.0

def detect_last_numeric_columns(rows, header):
    ncols = len(header)
    numeric_cols = [i for i in range(2, ncols)
                    if any(parse_number(r[i]) != 0.0 for r in rows if len(r) > i)]
    if not numeric_cols:
        return (None, None)
    last = numeric_cols[-1]
    prev = numeric_cols[-2] if len(numeric_cols) > 1 else None
    return (last, prev)

# ------------------------------------------------------------------
# FETCH SHEET DATA
# ------------------------------------------------------------------
def fetch_sheet_data():
    if not SHEET_ID:
        return []
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(SHEET_NAME)
        except Exception:
            ws = sh.get_worksheet(0)

        values = ws.get_all_values()
        if not values or len(values) < 2:
            return []

        header, rows = values[0], values[1:]
        last_col, prev_col = detect_last_numeric_columns(rows, header)
        if last_col is None:
            return []

        data = []
        for r in rows:
            category = r[0].strip() if r and r[0].strip() else "Unknown"
            latest = parse_number(r[last_col]) if len(r) > last_col else 0.0
            previous = parse_number(r[prev_col]) if prev_col and len(r) > prev_col else 0.0
            growth = round((latest - previous) / previous * 100, 2) if previous else None
            data.append({
                "category": category,
                "latest": latest,
                "previous": previous,
                "growth": growth,
                "date": header[last_col]
            })
        return data
    except Exception:
        logger.exception("fetch_sheet_data failed")
        return []

# ------------------------------------------------------------------
# SYNC MASTER XLSX → SHEET
# ------------------------------------------------------------------
def sync_from_master():
    if not SHEET_ID:
        return {"ok": False, "error": "SHEET_ID not set"}
    if not OPENPYXL_AVAILABLE:
        return {"ok": False, "error": "openpyxl not installed"}
    if not os.path.exists(MASTER_XLSX_PATH):
        return {"ok": False, "error": f"{MASTER_XLSX_PATH} not found"}

    try:
        wb = load_workbook(MASTER_XLSX_PATH, data_only=True)
        ws_master = wb.active
        rows = [list(r) for r in ws_master.iter_rows(values_only=True)]
        header, data_rows = rows[0], rows[1:]
        latest_col = len(header) - 1
        master_map = {str(r[0]).strip(): parse_number(r[latest_col]) for r in data_rows if r and r[0]}

        gc = get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(SHEET_NAME)
        except Exception:
            ws = sh.get_worksheet(0)

        sheet_header = ws.row_values(1)
        next_col = len(sheet_header) + 1
        header_val = header[latest_col] or datetime.now().isoformat()
        ws.update_cell(1, next_col, header_val)

        sheet_rows = ws.get_all_values()[1:]
        for i, r in enumerate(sheet_rows, start=2):
            cat = r[0].strip() if r and r[0] else "Unknown"
            if cat in master_map:
                ws.update_cell(i, next_col, master_map[cat])

        return {"ok": True, "written_column": next_col, "header": header_val}
    except Exception:
        logger.exception("sync_from_master failed")
        return {"ok": False, "error": "sync_from_master exception"}

# ------------------------------------------------------------------
# FLASK APP
# ------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    data = fetch_sheet_data()
    if not data:
        return jsonify({"data": [], "error": "No data or sheet access issue", "updated_at": datetime.utcnow().isoformat()})
    return jsonify({"data": data, "updated_at": datetime.utcnow().isoformat()})

@app.route("/api/sync", methods=["POST"])
def api_sync():
    if SYNC_SECRET and request.headers.get("X-SYNC-SECRET", "") != SYNC_SECRET:
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    result = sync_from_master()
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
