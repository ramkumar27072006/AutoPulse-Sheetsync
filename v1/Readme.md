# AutoPulse-Sheetsync

## Overview

**AutoPulse-Sheetsync** is an end-to-end automated workflow that synchronizes business data from a local source to Google Sheets and visualizes it through a live Flask dashboard deployed on Render.
It is designed to perform data cleaning, cloud synchronization, and dashboard visualization with minimal manual intervention.

---

## Project Structure

```
v1/
└── Task Automater/
    ├── day1_local_automation.py      # Local data preprocessing and JSON generation
    ├── day2_gsheet_upload.py         # Automated Google Sheets update via gspread API
    ├── day3_dashboard.py             # Flask-based analytics dashboard (Render deployment)
    ├── templates/
    │   └── index.html                # Interactive dashboard UI
    ├── processed_data.json           # Processed dataset for visualization
    ├── sales_data.xlsx               # Source dataset
    ├── requirements.txt              # Python dependencies
    └── Readme.md
```

---

## Workflow Summary

### Day 1 – Local Data Automation

The script `day1_local_automation.py` performs the following:

* Reads and validates `sales_data.xlsx`
* Automatically detects key columns (e.g., quantity, price, category)
* Cleans and aggregates the data
* Exports a structured file `processed_data.json` for downstream tasks

Run:

```bash
python day1_local_automation.py
```

---

### Day 2 – Google Sheets Upload

`day2_gsheet_upload.py` handles synchronization between local processed data and Google Sheets.

Functions:

* Authenticates using Google Service Account credentials
* Uploads or updates records to a specified Google Sheet
* Maintains data consistency by appending or overwriting relevant sections

Run:

```bash
python day2_gsheet_upload.py
```

If hosted on Render, sensitive credentials are securely stored as **environment variables** (`GOOGLE_CREDS`).

---

### Day 3 – Flask Dashboard Deployment

`day3_dashboard.py` serves a live analytical dashboard using Flask, featuring an advanced HTML UI (`index.html` under `templates/`).

Core functionalities:

* Fetches and visualizes processed data from Google Sheets
* Displays category-wise revenue and trend insights
* Automatically updates based on synced sheet values

Run locally:

```bash
python day3_dashboard.py
```

Deploy on Render by setting:

* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `gunicorn day3_dashboard:app`
* **Environment Variable:**
  `GOOGLE_CREDS` → Paste your service account JSON as a single-line string

---

## Daily Data Automation (Google Sheets Integration)

To ensure daily updates to your dataset columns, a **Google Apps Script** automation is used.

### Apps Script Setup

1. Open your Google Sheet → **Extensions → Apps Script**
2. Paste the following code:

   ```javascript
   function autoUpdateSheet() {
     const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     const lastCol = sheet.getLastColumn();
     const now = new Date();
     const newHeader = Utilities.formatDate(now, "Asia/Kolkata", "MMM dd, yyyy HH:mm");
     sheet.getRange(1, lastCol + 1).setValue(newHeader);
     const dataRange = sheet.getRange(2, lastCol + 1, sheet.getLastRow() - 1);
     const randomValues = Array(sheet.getLastRow() - 1).fill([Math.floor(Math.random() * 5000)]);
     dataRange.setValues(randomValues);
   }
   ```
3. Save and authorize the script.
4. Create a **time-driven trigger**:

   * Function: `autoUpdateSheet`
   * Event Source: `Time-driven`
   * Type: `Day timer`
   * Time: `8 AM to 9 AM`

This script automatically appends a new column daily with updated simulated or imported data, ensuring the Render dashboard reflects continuous growth.

---

## Deployment Environment

| Component          | Platform         | Purpose                        |
| ------------------ | ---------------- | ------------------------------ |
| **Local (Python)** | Desktop / Server | Data preprocessing             |
| **Google Sheets**  | Cloud            | Data storage & synchronization |
| **Flask App**      | Render           | Live analytics dashboard       |
| **Apps Script**    | Google Cloud     | Time-based automation trigger  |

---

## Environment Variables

| Variable       | Description                                              |
| -------------- | -------------------------------------------------------- |
| `GOOGLE_CREDS` | Service account credentials JSON (as single-line string) |
| `SHEET_ID`     | Target Google Sheet ID (optional, can be embedded)       |

---

## Technical Stack

* **Python 3.10+**
* **Flask 3.0.3**
* **Google API (gspread, google-auth)**
* **Gunicorn (for Render)**
* **HTML5 / CSS3 / JavaScript**
* **Google Apps Script (Trigger automation)**

---

## Future Enhancements

* Integration with BigQuery for large-scale data storage
* Predictive analytics using scikit-learn
* Dynamic dashboards using Plotly or Dash
* Secure OAuth 2.0 authentication for multi-user dashboards

---

## License

This project is distributed under the **MIT License**.
Use and modify freely with appropriate attribution.

