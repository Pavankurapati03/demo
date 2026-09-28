@echo off
title Forecasting E1 & E2 Dashboards
echo ========================================================
echo   Starting Forecasting E1 & E2 Dashboards...
echo ========================================================
echo.
pip install -r requirements.txt
python server.py
pause
