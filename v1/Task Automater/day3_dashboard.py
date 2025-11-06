"""
Tasklytics - Day 3.5
---------------------------------
Adds AI-style insight generation with dynamic summaries
based on live Google Sheets or local data.
"""

from flask import Flask, render_template, jsonify
import gspread, json, time
from google.oauth2.service_account import Credentials
import statistics
import os

app = Flask(__name__)

# --- Config ---
SPREADSHEET_ID = "1GLKQllVmysW4ARvx7RWs2KDQOmsnNMwJWaqebFsMqs4"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds_json = os.getenv("GOOGLE_CREDS")
CREDS = Credentials.from_service_account_info(json.loads(creds_json))
client = gspread.authorize(CREDS)

def fetch_data():
    """Fetches data from Google Sheets"""
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        rows = sheet.get_all_records()
        last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
        return {"data": rows, "updated": last_updated}
    except Exception as e:
        print("⚠️ Google Sheets fetch failed:", e)
        return {"data": [], "updated": "Error"}

def generate_insight(rows):
    """Generates human-readable insights."""
    if not rows:
        return "No data available for insight generation."

    # Extract data
    categories = [r["category"] for r in rows]
    revenues = [float(r["revenue"]) for r in rows]

    total = sum(revenues)
    top_index = revenues.index(max(revenues))
    top_cat, top_rev = categories[top_index], revenues[top_index]
    mean_rev = statistics.mean(revenues)

    contribution = (top_rev / total) * 100 if total else 0
    insight = (
        f"📊 Category '{top_cat}' leads with ₹{top_rev:,.0f}, "
        f"contributing {contribution:.1f}% of total revenue ₹{total:,.0f}. "
        f"Average category revenue is ₹{mean_rev:,.0f}. "
    )

    if contribution > 60:
        insight += "⚡ Outstanding dominance in this category!"
    elif contribution < 20:
        insight += "📉 More balanced distribution across categories."
    else:
        insight += "📈 Healthy distribution with moderate concentration."

    return insight

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    result = fetch_data()
    insight = generate_insight(result["data"])
    result["insight"] = insight
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")


