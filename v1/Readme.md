
# AutoPulse-Sheetsync

AutoPulse-Sheetsync is a full-stack automation dashboard that seamlessly connects data pipelines, automates processing workflows, syncs with Google Sheets, and visualizes live business metrics through an interactive Flask web interface.

---

## Overview

AutoPulse-Sheetsync demonstrates how **automation**, **APIs**, and **data visualization** unite in real-world workflows.  
It mirrors enterprise automation systems used by analytics teams — transforming manual tasks (like data entry or reporting) into efficient automated pipelines.

- **Day 1:** Automate local data extraction & processing  
- **Day 2:** Upload data to Google Sheets automatically  
- **Day 3:** Display live visual dashboards using Flask + Chart.js  
- **Day 3.5:** Add AI-style insight summaries and auto-refresh functionality  

---

## Tech Stack

| Layer | Tools & Technologies |
|-------|----------------------|
| Backend Automation | Python, Pandas |
| Data Storage / Sync | Google Sheets API, GSpread |
| Frontend Dashboard | Flask, HTML5, Chart.js |
| Design & Aesthetics | CSS3 (Glassmorphism + Neon UI), Google Fonts |
| Deployment (Optional) | Render / GitHub Pages |
| Data Format | JSON / Google Sheets |

---

## Features

- Automates data extraction and transformation from Excel files  
- Syncs processed results with Google Sheets in real time  
- Displays live data visualization dashboard (auto-refreshing)  
- Includes optional AI-style summary card (insight generator)  
- Simple configuration — no external database needed  
- Ready for deployment on Render, Vercel, or local setups  

---

## Project Structure

```

AutoPulse-Sheetsync/
│
├── sales_data.xlsx               # Sample dataset
├── processed_data.json           # Output file (Day 1)
├── credentials.json              # Google API key (keep private)
│
├── day1_local_automation.py      # Automates local data processing
├── day2_gsheet_upload.py         # Uploads data to Google Sheets
├── day3_dashboard.py             # Flask dashboard (main app)
│
├── templates/
│   └── index.html                # Dashboard frontend (Chart.js)
│
├── requirements.txt              # Required dependencies
└── README.md                     # This file

```

---

## Quick Start

### 1. Clone the Repository
```

git clone [https://github.com/ramkumar27072006/AutoPulse-Sheetsync.git](https://github.com/ramkumar27072006/AutoPulse-Sheetsync.git)
cd AutoPulse-Sheetsync

```

### 2. Install Requirements
```

pip install -r requirements.txt

```

### 3. Prepare Google API Credentials
- Visit [Google Cloud Console](https://console.cloud.google.com/)  
- Enable **Google Sheets API**  
- Create a **Service Account**  
- Download the credentials as `credentials.json`  
- Share your Google Sheet with the email in that credentials file (Editor access)  

### 4. Run Automation (Day 1)
```

python day1_local_automation.py

```
Processes `sales_data.xlsx` and generates `processed_data.json`.

### 5. Sync Data to Google Sheets (Day 2)
```

python day2_gsheet_upload.py

```

### 6. Launch Dashboard (Day 3)
```

python day3_dashboard.py

```
Then open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Behind the Scenes

| Stage | Description |
|--------|-------------|
| Automation Logic | Python scripts clean and transform raw Excel data, then save to structured JSON. |
| Sync Engine | Google Sheets API authenticates via OAuth and updates data cells. |
| Web Dashboard | Flask serves real-time data visualization using Chart.js. |
| Auto Refresh | Frontend fetches data every 5 minutes to update charts dynamically. |

---

## Example Output

```

{
"timestamp": "2025-11-06T20:40:13.530Z",
"summary": [
{"category": "Accessories", "revenue": 45200.0},
{"category": "Appliances", "revenue": 98500.0},
{"category": "Smartphones", "revenue": 74500.0}
]
}

```

---

## UI Design Highlights

- Futuristic Glassmorphism design — transparent, blurred cards for a modern analytics feel  
- Neon Orbitron typography — cyber-inspired glowing headers  
- Live animated charts — smooth transitions powered by Chart.js  
- AI insight panel (optional) — generates summaries like:  
  “Revenue peaked in the Smartphones category this week, contributing 43% of total income.”

---

## Sample Google Sheet Layout

| category | revenue |
|-----------|---------|
| Accessories | 45200 |
| Appliances  | 98500 |
| Smartphones | 74500 |

---

## requirements.txt

```

flask==3.0.2
gspread==6.1.2
google-auth==2.33.0
pandas==2.2.2
chart.js==4.x

```

---

## Optional Deployment on Render

1. Push the project to GitHub  
2. Create a new **Web Service** on [Render](https://render.com)  
3. Environment: Python 3  
4. Start Command:
```

python day3_dashboard.py

```
5. Get your live link, e.g.  
[https://autopulse-sheetsync.onrender.com](https://autopulse-sheetsync.onrender.com)

---

## Future Scope

- Add Telegram or Slack notification bots  
- Integrate AI-powered trend analysis (OpenAI / Gemini APIs)  
- Use SQLite or MongoDB backend for larger datasets  
- Add user authentication for multi-dashboard environments  
- Deploy via Streamlit Cloud for instant data exploration  

---

## Key Learnings

- Working with REST APIs and OAuth in Python  
- Managing automation pipelines with Google Sheets  
- Flask + Chart.js integration for real-time dashboards  
- Designing modern UIs with HTML/CSS (Glassmorphism)  
- Building deployable, end-to-end automation systems  

---

## Author

**R. Ramkumar**  
B.Tech Artificial Intelligence & Data Science  
Passionate about Full Stack Automation & AI Systems  

**Connect:**  
- [LinkedIn](http://linkedin.com/in/ramkumar-r-a16a79335)  
- [GitHub](https://github.com/ramkumar27072006)  
- [Email](mailto:ramkumarashvanth09@gmail.com)

---

**If you like this project**, give it a ⭐ on GitHub and help more developers discover AutoPulse-Sheetsync!

```

git clone [https://github.com/ramkumar27072006/AutoPulse-Sheetsync.git](https://github.com/ramkumar27072006/AutoPulse-Sheetsync.git)

```

> “Automate tasks. Visualize intelligence. Build the future.”
```
