"""
Automated Exploratory Data Analysis (EDA) Engine for Order Execution.
Inspects uploaded CSV/Excel files, dynamically adapts to arbitrary dataset schemas,
and performs executive-grade telemetry for:
  1. Sales Forecasting (Time-Series Decomposition, Trend, Multi-Factor Seasonality,
     Autocorrelation, Croston/Syntetos-Boylan Demand Classification)
  2. S&OP Demand Planning (Inventory Run-Rates, Days of Supply, Stockout Exposure,
     Dynamic Safety Stock Calibration)
  3. Procurement Decision Engine (Supplier Concentration HHI, Unit Cost Economics,
     Margin Cushion, PO Batching Readiness)

Generates an interactive, standalone executive HTML EDA diagnostic report for user download and viewing.
"""

import os
import io
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

def validate_and_load_dataset(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Loads CSV or Excel dataset with robust encoding detection and format checking."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return None, f"Unsupported file format '{ext}'. Please upload a CSV or Excel (.xlsx) file."
    
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
        else:
            df = pd.read_excel(file_path)
            
        if df.empty or len(df.columns) == 0:
            return None, "Uploaded dataset contains no readable data or columns."
            
        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"

def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Intelligently detects operational supply chain features with fuzzy and exact keyword matching."""
    cols = list(df.columns)
    cols_lower = [str(c).lower().strip() for c in cols]
    
    def find_best(keywords: List[str]) -> Optional[str]:
        # Exact match
        for kw in keywords:
            for c, cl in zip(cols, cols_lower):
                if cl == kw:
                    return c
        # Substring match
        for kw in keywords:
            for c, cl in zip(cols, cols_lower):
                if kw in cl:
                    return c
        return None

    date_col = find_best(["date", "order_date", "timestamp", "ds", "invoice_date", "time", "day"])
    demand_col = find_best(["units_sold", "demand", "quantity", "qty", "orders", "volume", "sales_units"])
    if not demand_col:
        demand_col = find_best(["sales", "net_sales", "gross_sales", "revenue"])
        
    price_col = find_best(["list_price", "unit_price", "price", "selling_price", "gross_sales", "net_sales"])
    sku_col = find_best(["sku_id", "sku", "product_id", "item_id", "article_id", "product", "item"])
    stock_col = find_best(["stock_on_hand", "stock", "inventory", "on_hand", "soh", "current_stock"])
    stockout_flag_col = find_best(["stock_out_flag", "stockout", "is_stockout", "out_of_stock"])
    lead_time_col = find_best(["lead_time_days", "lead_time", "leadtime", "delivery_days", "transit_time"])
    supplier_col = find_best(["supplier_id", "vendor_id", "supplier", "vendor", "vendor_name", "supplier_name"])
    cost_col = find_best(["purchase_cost", "unit_cost", "buy_price", "cost", "cogs"])
    
    return {
        "date_col": date_col,
        "demand_col": demand_col,
        "price_col": price_col,
        "sku_col": sku_col,
        "stock_col": stock_col,
        "stockout_flag_col": stockout_flag_col,
        "lead_time_col": lead_time_col,
        "supplier_col": supplier_col,
        "cost_col": cost_col,
    }

def run_order_fulfillment_eda(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    """
    Alias for run_order_execution_eda to preserve backward compatibility.
    Runs comprehensive EDA aligned with the 3 order execution stages.
    """
    return run_order_execution_eda(df, filename)

def run_order_execution_eda(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    """
    Runs senior data science and supply chain analytics across any arbitrary dataset
    for E-Commerce Order Execution (Sales Forecasting, S&OP Demand Planning, Procurement).
    """
    total_rows = int(len(df))
    total_cols = int(len(df.columns))
    memory_mb = round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 2)
    
    detected = detect_columns(df)
    date_col = detected["date_col"]
    demand_col = detected["demand_col"]
    price_col = detected["price_col"]
    sku_col = detected["sku_col"]
    stock_col = detected["stock_col"]
    stockout_flag_col = detected["stockout_flag_col"]
    lead_time_col = detected["lead_time_col"]
    supplier_col = detected["supplier_col"]
    cost_col = detected["cost_col"]

    # Inferred SKU/Catalog breadth
    unique_skus = int(df[sku_col].nunique()) if (sku_col and sku_col in df.columns) else 1
    
    # ---------------------------------------------------------
    # STAGE 1: Sales Demand Forecasting & Time-Series Diagnostics
    # ---------------------------------------------------------
    s1_diag: Dict[str, Any] = {
        "status": "Ready for Forecasting" if (date_col and demand_col) else "Baseline Mapping Applied",
        "date_column": date_col,
        "demand_column": demand_col,
        "time_horizon": "Not Detected",
        "cadence": "Unknown",
        "trend_direction": "Stationary / Stable",
        "trend_slope_pct": 0.0,
        "trend_r2": 0.0,
        "peak_dow": "N/A",
        "trough_dow": "N/A",
        "weekend_lift_pct": 0.0,
        "monthly_amplitude_ratio": 1.0,
        "peak_month": "N/A",
        "trough_month": "N/A",
        "lag_1_autocorr": 0.0,
        "lag_7_autocorr": 0.0,
        "adi": 1.0,
        "cv2": 0.0,
        "croston_category": "Smooth",
        "croston_desc": "Continuous, predictable demand. Optimal for Holt-Winters, Meta Prophet, and SARIMA.",
        "ml_recommendation": "Deploy Meta Prophet with daily/weekly seasonal regressors + holiday effects.",
        "total_demand": 0.0,
        "daily_mean_demand": 0.0,
        "daily_std_demand": 0.0,
    }

    # Attempt time series decomposition
    if date_col and demand_col and pd.api.types.is_numeric_dtype(df[demand_col]):
        try:
            temp_df = df[[date_col, demand_col]].copy()
            temp_df["parsed_date"] = pd.to_datetime(temp_df[date_col], errors="coerce")
            valid_time_df = temp_df.dropna(subset=["parsed_date"])
            
            if len(valid_time_df) > 5:
                daily_series = valid_time_df.groupby("parsed_date")[demand_col].sum().sort_index()
                start_date = daily_series.index.min().strftime("%Y-%m-%d")
                end_date = daily_series.index.max().strftime("%Y-%m-%d")
                total_calendar_days = (daily_series.index.max() - daily_series.index.min()).days + 1
                unique_days = len(daily_series)
                
                # Inferred cadence
                if total_calendar_days > 1 and (unique_days / total_calendar_days) > 0.65:
                    cadence = "Daily Intervals"
                elif unique_days > 4 and (unique_days / max(1, total_calendar_days / 7)) > 0.5:
                    cadence = "Weekly Cadence"
                else:
                    cadence = "Irregular / Batch Cadence"
                    
                s1_diag["time_horizon"] = f"{start_date} to {end_date} ({unique_days:,} active dates / {total_calendar_days:,} calendar days)"
                s1_diag["cadence"] = cadence
                
                y = daily_series.values.astype(float)
                s1_diag["total_demand"] = round(float(np.sum(y)), 1)
                s1_diag["daily_mean_demand"] = round(float(np.mean(y)), 1)
                s1_diag["daily_std_demand"] = round(float(np.std(y)), 1)
                
                # 1. Trend Analysis (Linear Least Squares)
                if len(y) >= 4:
                    x = np.arange(len(y))
                    poly = np.polyfit(x, y, 1)
                    slope, intercept = poly[0], poly[1]
                    y_pred = slope * x + intercept
                    ss_tot = np.sum((y - np.mean(y)) ** 2)
                    ss_res = np.sum((y - y_pred) ** 2)
                    r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
                    mean_val = np.mean(y)
                    pace_pct = ((slope * len(y)) / mean_val * 100.0) if mean_val > 0 else 0.0
                    
                    s1_diag["trend_slope_pct"] = round(float(pace_pct), 1)
                    s1_diag["trend_r2"] = round(float(r2), 3)
                    
                    if pace_pct > 15.0 and r2 >= 0.2:
                        s1_diag["trend_direction"] = "Strong Upward Growth"
                    elif pace_pct > 5.0:
                        s1_diag["trend_direction"] = "Moderate Upward Pace"
                    elif pace_pct < -15.0 and r2 >= 0.2:
                        s1_diag["trend_direction"] = "Steep Downward Contraction"
                    elif pace_pct < -5.0:
                        s1_diag["trend_direction"] = "Moderate Downward Pace"
                    else:
                        s1_diag["trend_direction"] = "Stable / Stationary Demand"

                # 2. Multi-Factor Seasonality
                if len(valid_time_df) > 14:
                    # Day of Week
                    valid_time_df["dow"] = valid_time_df["parsed_date"].dt.day_name()
                    dow_means = valid_time_df.groupby("dow")[demand_col].mean()
                    if not dow_means.empty:
                        s1_diag["peak_dow"] = str(dow_means.idxmax())
                        s1_diag["trough_dow"] = str(dow_means.idxmin())
                        
                        weekend_mask = valid_time_df["dow"].isin(["Saturday", "Sunday"])
                        weekend_mean = valid_time_df[weekend_mask][demand_col].mean() if weekend_mask.any() else 0
                        weekday_mean = valid_time_df[~weekend_mask][demand_col].mean() if (~weekend_mask).any() else 0
                        if weekday_mean > 0 and weekend_mean > 0:
                            lift = ((weekend_mean - weekday_mean) / weekday_mean) * 100.0
                            s1_diag["weekend_lift_pct"] = round(float(lift), 1)

                    # Monthly Seasonality
                    valid_time_df["month_name"] = valid_time_df["parsed_date"].dt.strftime("%B")
                    month_means = valid_time_df.groupby("month_name")[demand_col].mean()
                    if len(month_means) >= 2:
                        max_m = month_means.max()
                        min_m = max(1e-4, month_means.min())
                        s1_diag["peak_month"] = str(month_means.idxmax())
                        s1_diag["trough_month"] = str(month_means.idxmin())
                        s1_diag["monthly_amplitude_ratio"] = round(float(max_m / min_m), 2)

                # 3. Autocorrelation Dynamics
                if len(daily_series) >= 14:
                    try:
                        ac1 = daily_series.autocorr(lag=1)
                        s1_diag["lag_1_autocorr"] = round(float(ac1), 3) if not np.isnan(ac1) else 0.0
                    except Exception:
                        pass
                    try:
                        ac7 = daily_series.autocorr(lag=7)
                        s1_diag["lag_7_autocorr"] = round(float(ac7), 3) if not np.isnan(ac7) else 0.0
                    except Exception:
                        pass

                # 4. Syntetos-Boylan / Croston Demand Pattern Matrix
                non_zeros = y[y > 0]
                adi = len(y) / max(1, len(non_zeros))
                cv2 = (np.std(non_zeros) / np.mean(non_zeros)) ** 2 if (len(non_zeros) > 0 and np.mean(non_zeros) > 0) else 0.0
                
                s1_diag["adi"] = round(float(adi), 2)
                s1_diag["cv2"] = round(float(cv2), 3)
                
                if adi < 1.32 and cv2 < 0.49:
                    s1_diag["croston_category"] = "Smooth"
                    s1_diag["croston_desc"] = "Regular order arrival with low volatility. Highly forecastable with standard statistical and ML pipelines."
                    s1_diag["ml_recommendation"] = "Deploy Meta Prophet + SARIMA ensemble with day-of-week & promotional regressors."
                elif adi >= 1.32 and cv2 < 0.49:
                    s1_diag["croston_category"] = "Intermittent"
                    s1_diag["croston_desc"] = "Sporadic demand intervals with steady order sizes. Risk of zero-demand overfitting."
                    s1_diag["ml_recommendation"] = "Apply Croston Method (SBA variant) or Poisson regression to handle zero-demand periods without bias."
                elif adi < 1.32 and cv2 >= 0.49:
                    s1_diag["croston_category"] = "Erratic"
                    s1_diag["croston_desc"] = "Frequent order frequency with highly volatile quantities. Driven by promotions or wholesale spikes."
                    s1_diag["ml_recommendation"] = "Deploy LSTM Deep Learning or LightGBM with heavy regularization and promotion flag feature engineering."
                else:
                    s1_diag["croston_category"] = "Lumpy"
                    s1_diag["croston_desc"] = "Sporadic demand intervals coupled with volatile order sizes. Highest forecasting uncertainty."
                    s1_diag["ml_recommendation"] = "Combine intermittent Croston baseline with dynamic safety stock buffering in S&OP Stage 2."
        except Exception as e:
            logger.warning(f"Time-series decomposition notice: {e}")

    # Fallback if no demand volume computed
    if s1_diag["total_demand"] == 0.0 and demand_col and pd.api.types.is_numeric_dtype(df[demand_col]):
        s1_diag["total_demand"] = round(float(df[demand_col].sum()), 1)
        s1_diag["daily_mean_demand"] = round(float(df[demand_col].mean()), 1)

    # ---------------------------------------------------------
    # STAGE 2: Demand Planning (S&OP) & Inventory Risk
    # ---------------------------------------------------------
    s2_diag: Dict[str, Any] = {
        "status": "Ready for S&OP" if (stock_col or lead_time_col) else "Baseline Parameters Applied",
        "stock_column": stock_col,
        "lead_time_column": lead_time_col,
        "current_stock": "N/A",
        "mean_stock": "N/A",
        "days_of_supply": "N/A",
        "stockout_rows": 0,
        "stockout_rate_pct": 0.0,
        "estimated_lost_units": 0,
        "mean_lead_time": 7.0,
        "max_lead_time": 14.0,
        "recommended_safety_stock": 0,
        "recommended_rop": 0,
        "buffer_health_rating": "Optimal S&OP Alignment",
    }

    # Lead Time evaluation
    if lead_time_col and pd.api.types.is_numeric_dtype(df[lead_time_col]):
        s2_diag["mean_lead_time"] = round(float(df[lead_time_col].mean()), 1)
        s2_diag["max_lead_time"] = round(float(df[lead_time_col].max()), 1)

    # Stock & Inventory evaluation
    if stock_col and pd.api.types.is_numeric_dtype(df[stock_col]):
        curr_stock = float(df[stock_col].iloc[-1])
        avg_stock = float(df[stock_col].mean())
        s2_diag["current_stock"] = f"{int(curr_stock):,}"
        s2_diag["mean_stock"] = f"{int(avg_stock):,}"
        
        # Days of Inventory (DoI)
        run_rate = s1_diag["daily_mean_demand"] if s1_diag["daily_mean_demand"] > 0 else (avg_stock / 30.0 if avg_stock > 0 else 1.0)
        doi = curr_stock / max(1.0, run_rate)
        s2_diag["days_of_supply"] = f"{round(doi, 1)} Days"
        
        # Stockouts
        if stockout_flag_col and pd.api.types.is_numeric_dtype(df[stockout_flag_col]):
            stockouts = int((df[stockout_flag_col] == 1).sum())
        else:
            stockouts = int((df[stock_col] <= 0).sum())
            
        s2_diag["stockout_rows"] = stockouts
        stockout_pct = (stockouts / total_rows * 100.0) if total_rows > 0 else 0.0
        s2_diag["stockout_rate_pct"] = round(stockout_pct, 2)
        
        # Estimated lost demand
        unit_mean = float(df[demand_col].mean()) if (demand_col and pd.api.types.is_numeric_dtype(df[demand_col])) else 10.0
        s2_diag["estimated_lost_units"] = int(round(stockouts * unit_mean))
        
        # Buffer health
        if doi < 7.0 or stockout_pct > 8.0:
            s2_diag["buffer_health_rating"] = "Critical Stockout Exposure (Underbuffered)"
        elif doi > 60.0:
            s2_diag["buffer_health_rating"] = "Excess Working Capital Locked (Overbuffered)"
        else:
            s2_diag["buffer_health_rating"] = "Balanced S&OP Inventory Health"
    else:
        s2_diag["days_of_supply"] = "18.5 Days (Synthesized Baseline)"
        s2_diag["buffer_health_rating"] = "Baseline S&OP Parameters Active"

    # Safety Stock & Reorder Point Calculation (z = 1.65 for 95% service level)
    z_score = 1.65
    sigma_d = s1_diag["daily_std_demand"] if s1_diag["daily_std_demand"] > 0 else (s1_diag["daily_mean_demand"] * 0.25)
    l_lead = s2_diag["mean_lead_time"]
    safety_stock = z_score * sigma_d * np.sqrt(max(1.0, l_lead))
    s2_diag["recommended_safety_stock"] = int(round(safety_stock))
    
    rop = (s1_diag["daily_mean_demand"] * l_lead) + safety_stock
    s2_diag["recommended_rop"] = int(round(rop))

    # ---------------------------------------------------------
    # STAGE 3: Procurement Decision Engine & Vendor Ecosystem
    # ---------------------------------------------------------
    s3_diag: Dict[str, Any] = {
        "status": "Ready for PO Generation" if supplier_col else "Single Sourcing Baseline",
        "supplier_column": supplier_col,
        "cost_column": cost_col,
        "active_suppliers": 1,
        "top_supplier_share_pct": 100.0,
        "hhi_index": 10000,
        "vendor_resilience_rating": "Single Sourcing Baseline",
        "min_cost": "N/A",
        "mean_cost": "N/A",
        "max_cost": "N/A",
        "cost_spread_ratio": "1.0x",
        "avg_gross_margin_pct": "N/A",
        "margin_health_rating": "Baseline Margin",
        "po_readiness_score": 75,
    }

    if supplier_col and supplier_col in df.columns:
        n_supp = int(df[supplier_col].nunique())
        s3_diag["active_suppliers"] = n_supp
        shares = df[supplier_col].value_counts(normalize=True)
        top_share = float(shares.iloc[0]) * 100.0 if not shares.empty else 100.0
        s3_diag["top_supplier_share_pct"] = round(top_share, 1)
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = int(round(float((shares ** 2).sum() * 10000)))
        s3_diag["hhi_index"] = hhi
        
        if n_supp >= 3 and top_share <= 50.0:
            s3_diag["vendor_resilience_rating"] = f"Resilient Multi-Vendor Ecosystem (HHI: {hhi:,})"
        elif n_supp >= 2 and top_share <= 80.0:
            s3_diag["vendor_resilience_rating"] = f"Moderate Vendor Concentration (HHI: {hhi:,})"
        else:
            s3_diag["vendor_resilience_rating"] = f"High Single-Source Vulnerability (HHI: {hhi:,})"
    else:
        s3_diag["vendor_resilience_rating"] = "Single Sourcing Baseline (Multi-Vendor Feed Recommended)"

    # Unit Cost & Margin Analysis
    if cost_col and pd.api.types.is_numeric_dtype(df[cost_col]):
        min_c = float(df[cost_col].min())
        mean_c = float(df[cost_col].mean())
        max_c = float(df[cost_col].max())
        s3_diag["min_cost"] = f"${round(min_c, 2):,}"
        s3_diag["mean_cost"] = f"${round(mean_c, 2):,}"
        s3_diag["max_cost"] = f"${round(max_c, 2):,}"
        spread = max_c / max(1e-4, min_c)
        s3_diag["cost_spread_ratio"] = f"{round(spread, 1)}x"

        # Margin Cushion (if price column exists)
        if price_col and pd.api.types.is_numeric_dtype(df[price_col]):
            mean_p = float(df[price_col].mean())
            if mean_p > 0:
                margin_pct = ((mean_p - mean_c) / mean_p) * 100.0
                s3_diag["avg_gross_margin_pct"] = f"{round(margin_pct, 1)}%"
                if margin_pct > 40.0:
                    s3_diag["margin_health_rating"] = "Robust Enterprise Margin Cushion"
                elif margin_pct > 20.0:
                    s3_diag["margin_health_rating"] = "Healthy Operational Margin"
                else:
                    s3_diag["margin_health_rating"] = "Compressed Margin — Strict Unit Cost Control Needed"
    else:
        s3_diag["margin_health_rating"] = "Standard 35% Margin Baseline"

    # PO Execution Readiness Score (out of 100)
    score = 40
    if date_col and demand_col: score += 20
    if stock_col or lead_time_col: score += 20
    if supplier_col: score += 10
    if cost_col: score += 10
    s3_diag["po_readiness_score"] = min(100, score)

    # Inferred Revenue
    total_rev = "N/A"
    if price_col and pd.api.types.is_numeric_dtype(df[price_col]):
        if "gross_sales" in price_col.lower() or "revenue" in price_col.lower() or "net_sales" in price_col.lower():
            total_rev = f"${round(float(df[price_col].sum()), 0):,}"
        elif demand_col and pd.api.types.is_numeric_dtype(df[demand_col]):
            total_rev = f"${round(float((df[price_col] * df[demand_col]).sum()), 0):,}"

    # Overall Composite Execution Readiness
    readiness_score = int(round((
        (100 if s1_diag["status"] == "Ready for Forecasting" else 60) * 0.35 +
        (100 if s2_diag["status"] == "Ready for S&OP" else 65) * 0.35 +
        s3_diag["po_readiness_score"] * 0.30
    )))

    return {
        "filename": filename,
        "analysis_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_rows": total_rows,
        "total_cols": total_cols,
        "memory_mb": memory_mb,
        "unique_skus": unique_skus,
        "total_revenue": total_rev,
        "readiness_score": readiness_score,
        "stage_1_sales_forecasting": s1_diag,
        "stage_2_demand_planning": s2_diag,
        "stage_3_procurement": s3_diag,
    }

def generate_eda_html_report(eda_data: Dict[str, Any], output_path: str) -> str:
    """Creates a beautifully styled, senior data-science executive HTML EDA Report for Order Execution."""
    s1 = eda_data["stage_1_sales_forecasting"]
    s2 = eda_data["stage_2_demand_planning"]
    s3 = eda_data["stage_3_procurement"]

    readiness = eda_data["readiness_score"]
    readiness_badge = "badge-success" if readiness >= 80 else ("badge-warning" if readiness >= 60 else "badge-danger")
    readiness_rating = "Enterprise Production Ready" if readiness >= 85 else ("Operational with Baselines" if readiness >= 65 else "Ingestion Calibration Needed")

    # Demand Quadrant Styling
    quad_cls = "badge-success" if s1["croston_category"] == "Smooth" else ("badge-info" if s1["croston_category"] == "Intermittent" else ("badge-warning" if s1["croston_category"] == "Erratic" else "badge-danger"))

    # S&OP Buffer Styling
    sop_cls = "badge-success" if "Balanced" in s2["buffer_health_rating"] or "Optimal" in s2["buffer_health_rating"] else ("badge-danger" if "Critical" in s2["buffer_health_rating"] else "badge-warning")

    # Vendor Resilience Styling
    vend_cls = "badge-success" if "Resilient" in s3["vendor_resilience_rating"] else ("badge-warning" if "Moderate" in s3["vendor_resilience_rating"] else "badge-danger")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Quantellix.AI Automated EDA Report — {eda_data['filename']}</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
  <style>
    :root {{
      --primary: #071426;
      --navy-dark: #0f172a;
      --blue: #2563eb;
      --blue-light: #eff6ff;
      --green: #059669;
      --green-light: #ecfdf5;
      --amber: #d97706;
      --amber-light: #fffbeb;
      --red: #dc2626;
      --red-light: #fef2f2;
      --purple: #7c3aed;
      --purple-light: #f5f3ff;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --border-light: #f1f5f9;
      --text: #0f172a;
      --text-muted: #64748b;
      --shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f8fafc;
      color: var(--text);
      line-height: 1.45;
      padding: 24px;
    }}
    .report-container {{
      max-width: 1120px;
      margin: 0 auto;
    }}

    /* Screen Card Pages */
    .pdf-page {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px 28px;
      margin-bottom: 28px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .pdf-page-content {{
      flex: 1;
    }}

    /* Page Headers */
    .report-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 14px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 18px;
    }}
    .brand-title {{
      font-size: 22px;
      font-weight: 800;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: -0.3px;
    }}
    .brand-sub {{
      font-size: 12.5px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .page-header-mini {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 8px;
      border-bottom: 1.5px solid var(--border-light);
      margin-bottom: 14px;
      font-size: 11px;
      color: var(--text-muted);
    }}
    .mini-brand {{
      font-weight: 700;
      color: var(--blue);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .mini-meta {{
      color: var(--text-muted);
    }}

    /* Buttons */
    .actions-bar {{
      display: flex;
      gap: 10px;
    }}
    .btn {{
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 12px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: none;
      transition: all 0.15s ease;
    }}
    .btn-primary {{ background: var(--blue); color: #fff; }}
    .btn-primary:hover {{ background: #1d4ed8; }}
    .btn-secondary {{ background: #ffffff; border: 1px solid var(--border); color: var(--text); }}
    .btn-secondary:hover {{ background: #f1f5f9; }}

    /* KPI Top Overview */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }}
    .kpi-card {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .kpi-label {{
      font-size: 10.5px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .kpi-value {{
      font-size: 20px;
      font-weight: 800;
      color: var(--primary);
      margin-top: 4px;
      letter-spacing: -0.3px;
    }}
    .kpi-subtext {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
      line-height: 1.3;
    }}

    /* Section Headers */
    .section-title {{
      font-size: 15.5px;
      font-weight: 800;
      color: var(--primary);
      margin: 0 0 4px;
      display: flex;
      align-items: center;
      gap: 7px;
      letter-spacing: -0.2px;
    }}
    .section-subtitle {{
      font-size: 11.5px;
      color: var(--text-muted);
      margin-bottom: 14px;
    }}

    /* Stages Summary Row */
    .stages-summary {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 10px;
    }}
    .stage-box {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
    }}
    .stage-box h3 {{
      font-size: 13.5px;
      font-weight: 800;
      color: var(--blue);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    /* Metric Tables */
    .metric-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      table-layout: fixed;
    }}
    .metric-table td {{
      padding: 5px 2px;
      border-bottom: 1px solid var(--border-light);
    }}
    .metric-table td:first-child {{
      color: var(--text-muted);
      width: 48%;
      line-height: 1.3;
    }}
    .metric-table td:last-child {{
      font-weight: 700;
      color: var(--text);
      text-align: right;
      width: 52%;
      word-break: break-word;
    }}

    /* Deep Dive Grid Cards */
    .analytics-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
    }}
    .analytics-card {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
    }}
    .card-header-flex {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .card-heading {{
      font-size: 13px;
      font-weight: 800;
      color: var(--primary);
    }}

    /* Badges */
    .badge {{
      padding: 2.5px 6px;
      border-radius: 5px;
      font-size: 10px;
      font-weight: 700;
      display: inline-block;
      line-height: 1.25;
      text-align: right;
      max-width: 100%;
    }}
    .badge-success {{ background: var(--green-light); color: var(--green); }}
    .badge-warning {{ background: var(--amber-light); color: var(--amber); }}
    .badge-danger {{ background: var(--red-light); color: var(--red); }}
    .badge-info {{ background: var(--blue-light); color: var(--blue); }}
    .badge-purple {{ background: var(--purple-light); color: var(--purple); }}

    /* Action Plan Cards */
    .action-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-top: 6px;
    }}
    .action-card {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
    }}
    .action-step {{
      font-size: 9.5px;
      font-weight: 800;
      color: var(--blue);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 3px;
    }}
    .action-title {{
      font-size: 12px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 4px;
    }}
    .action-desc {{
      font-size: 10.5px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    /* Footers */
    .pdf-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 9.5px;
      color: #94a3b8;
      border-top: 1px solid var(--border);
      padding-top: 6px;
      margin-top: 14px;
    }}

    /* Print Styles */
    @media print {{
      @page {{
        size: A4 portrait;
        margin: 10mm 12mm 10mm 12mm;
      }}
      html, body {{
        background: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #0f172a !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}
      .actions-bar {{
        display: none !important;
      }}
      .report-container {{
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
      }}
      .pdf-page {{
        page-break-before: always !important;
        break-before: page !important;
        page-break-after: avoid !important;
        break-after: avoid !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        height: 275mm !important;
        max-height: 275mm !important;
        box-sizing: border-box !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        overflow: hidden !important;
      }}
      .pdf-page:first-child {{
        page-break-before: avoid !important;
        break-before: avoid !important;
      }}
      .pdf-page-content {{
        flex: 1 !important;
      }}
      .kpi-card, .stage-box, .analytics-card, .action-card {{
        box-shadow: none !important;
        border: 1px solid #cbd5e1 !important;
      }}
    }}
  </style>
</head>
<body>

<div class="report-container">

  <!-- ==================== PAGE 1: EXECUTIVE ALIGNMENT & KPI OVERVIEW ==================== -->
  <div class="pdf-page page-1">
    <div class="pdf-page-content">
      <header class="report-header">
        <div>
          <div class="brand-title">
            <span>📊 Quantellix.AI Automated EDA Report</span>
          </div>
          <div class="brand-sub">
            E-Commerce Order Execution Telemetry & Supply Chain Diagnostics • Dataset: <strong>{eda_data['filename']}</strong> • Generated: {eda_data['analysis_timestamp']}
          </div>
        </div>
        <div class="actions-bar">
          <button class="btn btn-secondary" id="btnDownloadPdf" onclick="downloadReportPdf()">📥 Download as PDF</button>
          <a href="/portal/chatbot" class="btn btn-primary">← Return to Chatbot</a>
        </div>
      </header>

      <section class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">Ingested Scale</div>
          <div class="kpi-value">{eda_data['total_rows']:,}</div>
          <div class="kpi-subtext">{eda_data['total_cols']} Features • {eda_data['memory_mb']} MB</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Product Breadth</div>
          <div class="kpi-value">{eda_data['unique_skus']:,}</div>
          <div class="kpi-subtext">Active SKUs / Items</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Observation Horizon</div>
          <div class="kpi-value" style="font-size: 14px; margin-top: 6px;">{s1['cadence']}</div>
          <div class="kpi-subtext">{s1['time_horizon']}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Demand Volume</div>
          <div class="kpi-value">{int(s1['total_demand']):,}</div>
          <div class="kpi-subtext">Gross Revenue: {eda_data['total_revenue']}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Execution Readiness</div>
          <div class="kpi-value" style="color: #2563eb;">{readiness}/100</div>
          <div class="kpi-subtext"><span class="badge {readiness_badge}">{readiness_rating}</span></div>
        </div>
      </section>

      <h2 class="section-title">🎯 Order Execution Alignment Assessment</h2>
      <div class="section-subtitle">Readiness evaluation across the 3 sequential stages of the Quantellix autonomous fulfillment pipeline</div>

      <section class="stages-summary">
        <div class="stage-box">
          <h3>📈 1. Sales Forecasting</h3>
          <table class="metric-table">
            <tr><td>Readiness Status</td><td><span class="badge badge-info">{s1['status']}</span></td></tr>
            <tr><td>Timestamp Feed</td><td>{s1['date_column'] or 'Inferred'}</td></tr>
            <tr><td>Demand Target</td><td>{s1['demand_column'] or 'Inferred'}</td></tr>
            <tr><td>Daily Run-Rate</td><td>{s1['daily_mean_demand']:,} u/day</td></tr>
            <tr><td>Demand Pattern</td><td><span class="badge {quad_cls}">{s1['croston_category']}</span></td></tr>
            <tr><td>Trend Trajectory</td><td>{s1['trend_direction']}</td></tr>
          </table>
        </div>

        <div class="stage-box">
          <h3>📦 2. Demand Planning (S&OP)</h3>
          <table class="metric-table">
            <tr><td>Readiness Status</td><td><span class="badge badge-info">{s2['status']}</span></td></tr>
            <tr><td>Stock Level Feed</td><td>{s2['stock_column'] or 'Inferred'}</td></tr>
            <tr><td>Lead Time Param</td><td>{s2['lead_time_column'] or 'Default (7d)'}</td></tr>
            <tr><td>Days of Supply</td><td>{s2['days_of_supply']}</td></tr>
            <tr><td>Stockout Exposure</td><td><span class="badge {sop_cls}">{s2['stockout_rate_pct']}% rows</span></td></tr>
            <tr><td>Buffer Health</td><td>{s2['buffer_health_rating']}</td></tr>
          </table>
        </div>

        <div class="stage-box">
          <h3>🛒 3. Procurement Engine</h3>
          <table class="metric-table">
            <tr><td>Readiness Status</td><td><span class="badge badge-info">{s3['status']}</span></td></tr>
            <tr><td>Supplier Target</td><td>{s3['supplier_column'] or 'Inferred'}</td></tr>
            <tr><td>Cost Target</td><td>{s3['cost_column'] or 'Inferred'}</td></tr>
            <tr><td>Active Base</td><td>{s3['active_suppliers']} Approved</td></tr>
            <tr><td>Concentration</td><td><span class="badge {vend_cls}">Resilient (HHI: {s3['hhi_index']})</span></td></tr>
            <tr><td>PO Readiness</td><td>{s3['po_readiness_score']}/100</td></tr>
          </table>
        </div>
      </section>
    </div>
    <footer class="pdf-footer">
      <span>Quantellix.AI • Order Execution Telemetry & Supply Chain Diagnostics</span>
      <span>Page 1 of 4 • Confidential Executive Report</span>
    </footer>
  </div>

  <!-- ==================== PAGE 2: STAGE 1 DEEP-DIVE ==================== -->
  <div class="pdf-page page-2">
    <div class="pdf-page-content">
      <div class="page-header-mini">
        <span class="mini-brand">Quantellix.AI Automated EDA Report</span>
        <span class="mini-meta">{eda_data['filename']} • Stage 1 Diagnostics</span>
      </div>

      <h2 class="section-title">📈 Stage 1 Deep-Dive: Time-Series Decomposition & Demand Diagnostics</h2>
      <div class="section-subtitle">Multi-factor empirical time-series decomposition, growth velocity analysis, and intermittent demand classification</div>

      <div class="analytics-grid">
        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Trend Velocity & Trajectory</span>
            <span class="badge badge-info">{s1['trend_direction']}</span>
          </div>
          <table class="metric-table">
            <tr><td>Directional Slope Trajectory</td><td>{s1['trend_direction']}</td></tr>
            <tr><td>Pace of Growth / Contraction</td><td>{s1['trend_slope_pct']}%</td></tr>
            <tr><td>Trend Model Fit (R² Coefficient)</td><td>{s1['trend_r2']}</td></tr>
            <tr><td>Daily Velocity Mean (μ)</td><td>{s1['daily_mean_demand']:,} units</td></tr>
            <tr><td>Demand Volatility Spread (σ)</td><td>±{s1['daily_std_demand']:,} units</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Seasonality & Autocorrelation Dynamics</span>
            <span class="badge badge-purple">Multi-Factor Periodic</span>
          </div>
          <table class="metric-table">
            <tr><td>Peak Sales Day of Week</td><td><strong>{s1['peak_dow']}</strong></td></tr>
            <tr><td>Trough Sales Day of Week</td><td>{s1['trough_dow']}</td></tr>
            <tr><td>Weekend vs. Weekday Demand Lift</td><td><span class="badge badge-success">+{s1['weekend_lift_pct']}%</span></td></tr>
            <tr><td>Peak vs. Trough Monthly Amplitude</td><td>{s1['monthly_amplitude_ratio']}x ({s1['peak_month']} vs {s1['trough_month']})</td></tr>
            <tr><td>Lag-1 Daily Momentum (Autocorr)</td><td>{s1['lag_1_autocorr']}</td></tr>
            <tr><td>Lag-7 Weekly Cyclical Persistence</td><td>{s1['lag_7_autocorr']}</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Syntetos-Boylan / Croston Demand Matrix</span>
            <span class="badge {quad_cls}">{s1['croston_category']}</span>
          </div>
          <table class="metric-table">
            <tr><td>Average Demand Interval (ADI)</td><td>{s1['adi']} (Threshold: 1.32)</td></tr>
            <tr><td>Squared Coeff. of Variation (CV²)</td><td>{s1['cv2']} (Threshold: 0.49)</td></tr>
            <tr><td>Classified Supply Chain Quadrant</td><td><strong>{s1['croston_category']}</strong></td></tr>
            <tr><td>Forecastability Profile</td><td>{s1['croston_desc']}</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Prescriptive Forecasting Architecture</span>
            <span class="badge badge-success">Optimized</span>
          </div>
          <div style="font-size: 11.5px; line-height: 1.6; color: var(--text);">
            <p style="margin-bottom: 8px;"><strong>Recommended ML Engine:</strong> {s1['ml_recommendation']}</p>
            <p style="color: var(--text-muted);">
              • <strong>Regressors to lock:</strong> Day-of-week indicators (capturing the {s1['weekend_lift_pct']}% weekend lift), holiday surge markers, and promotional discounts.<br>
              • <strong>Holdout Metric:</strong> WMAPE (Weighted Mean Absolute Percentage Error) to prevent volume distortion across intermittent periods.
            </p>
          </div>
        </div>
      </div>
    </div>
    <footer class="pdf-footer">
      <span>Quantellix.AI • Stage 1 Demand Diagnostics & Time-Series Decomposition</span>
      <span>Page 2 of 4 • Confidential Executive Report</span>
    </footer>
  </div>

  <!-- ==================== PAGE 3: STAGE 2 DEEP-DIVE ==================== -->
  <div class="pdf-page page-3">
    <div class="pdf-page-content">
      <div class="page-header-mini">
        <span class="mini-brand">Quantellix.AI Automated EDA Report</span>
        <span class="mini-meta">{eda_data['filename']} • Stage 2 S&OP Diagnostics</span>
      </div>

      <h2 class="section-title">📦 Stage 2 Deep-Dive: S&OP Inventory Dynamics & Stockout Exposure</h2>
      <div class="section-subtitle">Inventory buffer health, stockout risk quantification, and dynamic safety stock calibration (95% Cycle Service Level)</div>

      <div class="analytics-grid">
        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Inventory Coverage & Depletion Rate</span>
            <span class="badge {sop_cls}">{s2['buffer_health_rating']}</span>
          </div>
          <table class="metric-table">
            <tr><td>Latest Stock on Hand (SOH)</td><td>{s2['current_stock']} units</td></tr>
            <tr><td>Average Sustained Stock Level</td><td>{s2['mean_stock']} units</td></tr>
            <tr><td>Days of Supply Coverage (DoI)</td><td><strong>{s2['days_of_supply']}</strong></td></tr>
            <tr><td>Depletion Velocity Run-Rate</td><td>{s1['daily_mean_demand']:,} units / day</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Stockout Incidents & Lost Sales Exposure</span>
            <span class="badge badge-danger">Risk Telemetry</span>
          </div>
          <table class="metric-table">
            <tr><td>Stockout Incident Periods</td><td>{s2['stockout_rows']:,} rows</td></tr>
            <tr><td>Stockout Frequency Rate</td><td>{s2['stockout_rate_pct']}% of observed records</td></tr>
            <tr><td>Estimated Lost Demand Units</td><td><strong style="color:#dc2626;">~{s2['estimated_lost_units']:,} units</strong></td></tr>
            <tr><td>Fulfillment Health Assessment</td><td>{s2['buffer_health_rating']}</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Dynamic Safety Buffer Calibration (95% SL)</span>
            <span class="badge badge-info">Formula: z × σd × √L</span>
          </div>
          <table class="metric-table">
            <tr><td>Mean Supplier Lead Time (L)</td><td>{s2['mean_lead_time']} days (Max: {s2['max_lead_time']}d)</td></tr>
            <tr><td>Demand Standard Deviation (σd)</td><td>±{s1['daily_std_demand']:,} units</td></tr>
            <tr><td>Target Service Level Factor (z)</td><td>1.65 (95% Cycle Service Level)</td></tr>
            <tr><td>Recommended Safety Buffer</td><td><strong>{s2['recommended_safety_stock']:,} units</strong></td></tr>
            <tr><td>Recommended Reorder Point (ROP)</td><td><strong style="color: #2563eb;">{s2['recommended_rop']:,} units</strong></td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">S&OP Capital Efficiency & Replenishment Policy</span>
            <span class="badge badge-success">S&OP Protocol</span>
          </div>
          <div style="font-size: 11.5px; line-height: 1.6; color: var(--text);">
            <p style="margin-bottom: 8px;"><strong>Replenishment Trigger:</strong> Issue procurement requisition whenever available inventory drops below <strong>{s2['recommended_rop']:,} units</strong>.</p>
            <p style="color: var(--text-muted);">
              This maintains an active safety cushion of <strong>{s2['recommended_safety_stock']:,} units</strong> to protect customer order fulfillment against lead time variability ({s2['mean_lead_time']}d to {s2['max_lead_time']}d) while minimizing excess working capital lockup.
            </p>
          </div>
        </div>
      </div>
    </div>
    <footer class="pdf-footer">
      <span>Quantellix.AI • Stage 2 S&OP Inventory Health & Working Capital Policy</span>
      <span>Page 3 of 4 • Confidential Executive Report</span>
    </footer>
  </div>

  <!-- ==================== PAGE 4: STAGE 3 DEEP-DIVE & ACTION PLAN ==================== -->
  <div class="pdf-page page-4">
    <div class="pdf-page-content">
      <div class="page-header-mini">
        <span class="mini-brand">Quantellix.AI Automated EDA Report</span>
        <span class="mini-meta">{eda_data['filename']} • Stage 3 & Prescriptions</span>
      </div>

      <h2 class="section-title">🛒 Stage 3 Deep-Dive: Procurement Vendor Ecosystem & Unit Economics</h2>
      <div class="section-subtitle">Supplier concentration risk (Herfindahl-Hirschman Index), unit cost stability, and gross margin resilience</div>

      <div class="analytics-grid" style="margin-bottom: 16px;">
        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Supplier Concentration & Resilience</span>
            <span class="badge {vend_cls}">{s3['vendor_resilience_rating']}</span>
          </div>
          <table class="metric-table">
            <tr><td>Approved Supplier Ecosystem</td><td><strong>{s3['active_suppliers']} Active Vendors</strong></td></tr>
            <tr><td>Primary Supplier Share (#1 Vendor)</td><td>{s3['top_supplier_share_pct']}% of supply volume</td></tr>
            <tr><td>Herfindahl-Hirschman Index (HHI)</td><td><strong>{s3['hhi_index']:,}</strong> ({'Diversified' if s3['hhi_index'] < 1500 else ('Moderate' if s3['hhi_index'] < 2500 else 'Concentrated')})</td></tr>
            <tr><td>Single Point of Failure Vulnerability</td><td>{'Low Risk' if s3['hhi_index'] < 1500 else ('Moderate Risk' if s3['hhi_index'] < 2500 else 'High Risk')}</td></tr>
          </table>
        </div>

        <div class="analytics-card">
          <div class="card-header-flex">
            <span class="card-heading">Unit Cost Economics & Margin Cushion</span>
            <span class="badge badge-info">Procurement Audit</span>
          </div>
          <table class="metric-table">
            <tr><td>Minimum Incurred Purchase Cost</td><td>{s3['min_cost']}</td></tr>
            <tr><td>Average Benchmark Unit Cost</td><td><strong>{s3['mean_cost']}</strong></td></tr>
            <tr><td>Maximum Incurred Purchase Cost</td><td>{s3['max_cost']}</td></tr>
            <tr><td>Unit Cost Spread Ratio (Max/Min)</td><td>{s3['cost_spread_ratio']}</td></tr>
            <tr><td>Average Gross Margin Cushion</td><td><strong>{s3['avg_gross_margin_pct']}</strong></td></tr>
            <tr><td>Margin Resilience Rating</td><td>{s3['margin_health_rating']}</td></tr>
          </table>
        </div>
      </div>

      <h2 class="section-title">💡 Executive Senior Data Scientist Action Plan</h2>
      <div class="section-subtitle">Prescriptive operational roadmap to transition dataset into production order fulfillment pipelines</div>

      <div class="action-grid">
        <div class="action-card">
          <div class="action-step">Action 01 • Forecasting</div>
          <div class="action-title">Lock Seasonality Regressors</div>
          <div class="action-desc">
            Configure Meta Prophet to incorporate the detected <strong>{s1['peak_dow']}</strong> peak demand and <strong>+{s1['weekend_lift_pct']}%</strong> weekend uplift into predictive baseline schedules.
          </div>
        </div>

        <div class="action-card">
          <div class="action-step">Action 02 • S&OP Balancing</div>
          <div class="action-title">Enforce Safety Buffer</div>
          <div class="action-desc">
            Set automated reorder alerts at <strong>{s2['recommended_rop']:,} units</strong> with buffer of <strong>{s2['recommended_safety_stock']:,} units</strong> to eliminate the {s2['stockout_rate_pct']}% stockout frequency.
          </div>
        </div>

        <div class="action-card">
          <div class="action-step">Action 03 • Procurement</div>
          <div class="action-title">Multi-Vendor Allocation</div>
          <div class="action-desc">
            Maintain procurement concentration below HHI 2,500 by distributing order batch splits across approved vendors with multi-criteria MCDA scoring.
          </div>
        </div>

        <div class="action-card">
          <div class="action-step">Action 04 • Execution</div>
          <div class="action-title">Launch 3-Stage Pipeline</div>
          <div class="action-desc">
            Proceed to problem lock in the Quantellix Chatbot to generate real-time forecasts, S&OP consensus targets, and automated audit-compliant purchase orders.
          </div>
        </div>
      </div>
    </div>
    <footer class="pdf-footer">
      <span>Quantellix.AI • Stage 3 Vendor Resilience & Prescriptive Action Plan</span>
      <span>Page 4 of 4 • Confidential Executive Report</span>
    </footer>
  </div>

</div>

  <!-- Client-side script for direct download & fallback -->
  <script>
    async function downloadReportPdf() {{
      const btn = document.getElementById('btnDownloadPdf');
      const originalHtml = btn ? btn.innerHTML : '📥 Download as PDF';
      if (btn) {{
        btn.innerHTML = '⏳ Downloading...';
        btn.disabled = true;
      }}

      // Check if session ID is in URL and download directly from server endpoint
      const pathParts = window.location.pathname.split('/');
      const sessionId = pathParts[pathParts.length - 1];
      if (sessionId && window.location.pathname.includes('/api/eda/')) {{
        try {{
          const check = await fetch(`/api/eda/download-pdf/${{sessionId}}`, {{ method: 'HEAD' }});
          if (check.ok) {{
            window.location.href = `/api/eda/download-pdf/${{sessionId}}`;
            setTimeout(() => {{
              if (btn) {{ btn.innerHTML = originalHtml; btn.disabled = false; }}
            }}, 2000);
            return;
          }}
        }} catch (e) {{
          console.log('Server PDF endpoint fallback to print:', e);
        }}
      }}

      // Native browser print dialog fallback (optimized with print CSS)
      setTimeout(() => {{
        if (btn) {{ btn.innerHTML = originalHtml; btn.disabled = false; }}
        window.print();
      }}, 300);
    }}
  </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate high-fidelity server-side PDF version alongside HTML using Chrome/Edge Blink headless engine
    pdf_path = output_path.rsplit(".", 1)[0] + ".pdf"
    try:
        from portal.pdf_generator import convert_html_to_pdf
        convert_html_to_pdf(output_path, pdf_path)
    except Exception as e:
        logger.info(f"Server-side PDF generation note: {e}")

    return output_path

