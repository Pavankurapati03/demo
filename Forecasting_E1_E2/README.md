# Forecasting E1 & E2 Dashboards

This standalone package contains the complete frontend dashboards for:
- **E1**: Forecast Sales Demand (`sales_quantity`)
- **E2**: Minimize Forecast Variance (`forecast_variance` / `forecast_bias_units`)

---

## How to Run:

### Method 1: One-Click Start (Windows)
Double-click **`run.bat`**. It will automatically install dependencies and launch the server.

### Method 2: Manual Command Line
1. Open terminal inside this folder:
   ```bash
   pip install -r requirements.txt
   python server.py
   ```
2. Open your browser and go to:
   👉 **`http://127.0.0.1:5000`**

---

## Folder Structure:
```text
Forecasting_E1_E2/
│
├── server.py               # Standalone FastAPI server
├── requirements.txt        # Lightweight dependencies (FastAPI, uvicorn, jinja2)
├── run.bat                 # 1-click startup script
├── README.md               # Instructions
│
├── templates/
│   └── sales_forecasting.html  # Contains both E1 and E2 dashboards
│
└── static/                 # Stylesheets, icons, and graphics
    ├── css/styles.css
    ├── images/
    └── js/
```
