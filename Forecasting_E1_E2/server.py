"""
Standalone Server for E1 & E2 Sales Forecasting Dashboards
- E1: Forecast Sales Demand
- E2: Minimize Forecast Variance
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Forecasting E1 & E2 Dashboards", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
@app.get("/portal/marketplace/sales_forecasting", response_class=HTMLResponse)
@app.get("/sales_forecasting", response_class=HTMLResponse)
async def sales_forecasting_page(request: Request):
    return templates.TemplateResponse(request=request, name="sales_forecasting.html")

if __name__ == "__main__":
    import uvicorn
    print("\n========================================================")
    print("  Forecasting E1 & E2 Dashboard Server Started!")
    print("  Open in Browser: http://127.0.0.1:5000")
    print("========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=5000)
