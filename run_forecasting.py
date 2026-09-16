"""
Main Execution Script for Prophet Demand Forecasting Pipeline.
Executes data loading, model training, holdout evaluation, 90-day future forecasting,
and artifact generation.
"""

import os
import json
import pandas as pd
import numpy as np

from src.data_loader import load_raw_data, prepare_prophet_df, split_train_test
from src.prophet_pipeline import (
    create_baseline_prophet, 
    create_enhanced_prophet, 
    train_and_predict, 
    generate_future_forecast
)
from src.evaluator import evaluate_forecast
from src.visualizer import plot_actual_vs_forecast, plot_components, plot_future_forecast

def main():
    print("================================================================================")
    print("      PROPHET DEMAND FORECASTING PIPELINE (FORECAST-BASED PLANNING FLOW)       ")
    print("================================================================================")
    
    csv_path = "fmcg_sales_3years_1M_rows.csv"
    artifacts_dir = "artifacts"
    plots_dir = os.path.join(artifacts_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Load Data
    print("\n[1/5] Loading FMCG Sales dataset...")
    raw_df = load_raw_data(csv_path)
    print(f"Loaded {len(raw_df):,} records from {csv_path}")
    
    # 2. Select SKU & Aggregate
    sku_target = "SKU0001"
    print(f"\n[2/5] Preparing Daily Demand Time Series for target: {sku_target} (BrandA Soda)...")
    daily_df = prepare_prophet_df(raw_df, sku_id=sku_target)
    print(f"Daily dataset prepared: {len(daily_df)} days from {daily_df['ds'].min().strftime('%Y-%m-%d')} to {daily_df['ds'].max().strftime('%Y-%m-%d')}")
    print(f"Total demand across period: {daily_df['y'].sum():,} units (Avg: {daily_df['y'].mean():.1f} units/day)")
    
    # 3. Train/Test Holdout Split
    test_start = "2023-07-01"
    train_df, test_df = split_train_test(daily_df, test_start_date=test_start)
    print(f"\n[3/5] Splitting Data into Train & Holdout Test Sets:")
    print(f"  - Train Set: {len(train_df)} days ({train_df['ds'].min().strftime('%Y-%m-%d')} to {train_df['ds'].max().strftime('%Y-%m-%d')})")
    print(f"  - Test Set:  {len(test_df)} days ({test_df['ds'].min().strftime('%Y-%m-%d')} to {test_df['ds'].max().strftime('%Y-%m-%d')})")
    
    # 4. Train Models & Evaluate Holdout
    print("\n[4/5] Training Prophet Models & Evaluating Holdout Accuracy...")
    
    # A) Baseline Prophet
    print("\n --- Model A: Baseline Prophet (Trend + Seasonality) ---")
    base_model = create_baseline_prophet()
    base_model, base_test_forecast = train_and_predict(base_model, train_df, test_df)
    base_metrics = evaluate_forecast(test_df['y'], base_test_forecast['yhat'])
    for metric, val in base_metrics.items():
        print(f"   * {metric}: {val}")
        
    # B) Enhanced Prophet (with Regressors)
    print("\n --- Model B: Enhanced Prophet (+ Promo & Holiday Regressors) ---")
    enh_model = create_enhanced_prophet()
    enh_model, enh_test_forecast = train_and_predict(enh_model, train_df, test_df)
    enh_metrics = evaluate_forecast(test_df['y'], enh_test_forecast['yhat'])
    for metric, val in enh_metrics.items():
        print(f"   * {metric}: {val}")
        
    # 5. Future 90-Day Forecast Generation
    print("\n[5/5] Generating 90-Day Future Demand Forecast into 2024...")
    full_model = create_enhanced_prophet()
    full_model, future_forecast = generate_future_forecast(full_model, daily_df, future_days=90)
    
    future_only = future_forecast[future_forecast['ds'] > daily_df['ds'].max()]
    print(f"Future Forecast Period: {future_only['ds'].min().strftime('%Y-%m-%d')} to {future_only['ds'].max().strftime('%Y-%m-%d')}")
    print(f"Projected Total 90-Day Demand: {int(future_only['yhat'].sum()):,} units (Avg: {future_only['yhat'].mean():.1f} units/day)")
    print(f"95% Uncertainty Bound: [{int(future_only['yhat_lower'].sum()):,} to {int(future_only['yhat_upper'].sum()):,} units]")
    
    # 6. Generate Plots
    print("\nGenerating Visualization Plots...")
    plot_actual_vs_forecast(
        test_df, 
        enh_test_forecast, 
        title=f"Prophet Holdout Evaluation for {sku_target} (July-Dec 2023)",
        save_path=os.path.join(plots_dir, "actual_vs_forecast.png")
    )
    
    plot_components(
        full_model, 
        future_forecast, 
        save_path=os.path.join(plots_dir, "components_decomposition.png")
    )
    
    plot_future_forecast(
        daily_df, 
        future_forecast, 
        future_days=90, 
        save_path=os.path.join(plots_dir, "future_90day_forecast.png")
    )
    
    # 7. Save Outputs
    # Save forecast dataframe
    output_cols = ['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend', 'weekly', 'yearly']
    if 'promo_flag' in future_forecast.columns:
        output_cols.append('promo_flag')
    
    forecast_export = future_forecast[output_cols].copy()
    # Merge actual y where available
    forecast_export = forecast_export.merge(daily_df[['ds', 'y']], on='ds', how='left')
    forecast_csv_path = os.path.join(artifacts_dir, "prophet_forecast_results.csv")
    forecast_export.to_csv(forecast_csv_path, index=False)
    print(f"\nSaved structured forecast results: {forecast_csv_path}")
    
    # Save metrics JSON
    metrics_summary = {
        "sku_target": sku_target,
        "eval_period": f"{test_df['ds'].min().strftime('%Y-%m-%d')} to {test_df['ds'].max().strftime('%Y-%m-%d')}",
        "baseline_prophet": base_metrics,
        "enhanced_prophet": enh_metrics,
        "future_90day_summary": {
            "start_date": future_only['ds'].min().strftime('%Y-%m-%d'),
            "end_date": future_only['ds'].max().strftime('%Y-%m-%d'),
            "projected_total_units": int(future_only['yhat'].sum()),
            "projected_daily_avg": round(float(future_only['yhat'].mean()), 2),
            "lower_bound_95": int(future_only['yhat_lower'].sum()),
            "upper_bound_95": int(future_only['yhat_upper'].sum())
        }
    }
    
    metrics_json_path = os.path.join(artifacts_dir, "forecast_metrics.json")
    with open(metrics_json_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Saved metrics summary: {metrics_json_path}")
    
    print("\n================================================================================")
    print("                     PIPELINE EXECUTED SUCCESSFULLY!                           ")
    print("================================================================================")

if __name__ == "__main__":
    main()
