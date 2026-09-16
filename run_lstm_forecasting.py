"""
Main Execution Script for PyTorch LSTM Demand Forecasting.
Trains LSTM on historical daily sales and evaluates accuracy on holdout test set.
"""

import os
import json
import pandas as pd
import numpy as np

from src.data_loader import load_raw_data, prepare_prophet_df, split_train_test
from src.lstm_pipeline import (
    prepare_lstm_data, 
    train_lstm_model, 
    predict_lstm, 
    forecast_future_lstm
)
from src.evaluator import evaluate_forecast
from src.visualizer import plot_actual_vs_forecast, plot_future_forecast

def main():
    print("================================================================================")
    print("        PYTORCH LSTM DEMAND FORECASTING PIPELINE (DEEP LEARNING)               ")
    print("================================================================================")
    
    csv_path = "fmcg_sales_3years_1M_rows.csv"
    artifacts_dir = "artifacts"
    plots_dir = os.path.join(artifacts_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Load Data
    print("\n[1/5] Loading dataset & preparing SKU0001 daily series...")
    raw_df = load_raw_data(csv_path)
    daily_df = prepare_prophet_df(raw_df, sku_id="SKU0001")
    
    # 2. Split Data
    test_start = "2023-07-01"
    train_df, test_df = split_train_test(daily_df, test_start_date=test_start)
    print(f"Train Set: {len(train_df)} days | Test Set: {len(test_df)} days")
    
    # 3. Prepare LSTM Data Sequences
    print("\n[2/5] Scaling features & creating 30-day sliding window sequences...")
    feature_cols = ['y', 'promo_flag', 'discount_pct', 'is_holiday']
    scaler, train_loader, test_loader, test_scaled = prepare_lstm_data(
        train_df, test_df, feature_cols=feature_cols, window_size=30
    )
    
    # 4. Train LSTM Model
    print("\n[3/5] Training 2-Layer PyTorch LSTM Model (120 Epochs)...")
    lstm_model = train_lstm_model(train_loader, input_size=len(feature_cols), epochs=120, lr=0.003)
    
    # 5. Predict & Evaluate Holdout Set
    print("\n[4/5] Evaluating LSTM Model on 184-Day Unseen Holdout Test Set...")
    lstm_preds = predict_lstm(lstm_model, test_loader, scaler)
    
    # Ensure prediction length matches test_df
    if len(lstm_preds) > len(test_df):
        lstm_preds = lstm_preds[:len(test_df)]
        
    lstm_metrics = evaluate_forecast(test_df['y'], lstm_preds)
    print("\n --- LSTM Holdout Evaluation Metrics ---")
    for metric, val in lstm_metrics.items():
        print(f"   * {metric}: {val}")
        
    # 6. Future 90-Day Forecast
    print("\n[5/5] Generating 90-Day Future Forecast into 2024...")
    future_df = forecast_future_lstm(
        lstm_model, daily_df, scaler, feature_cols=feature_cols, window_size=30, future_days=90
    )
    print(f"Projected 90-Day Demand: {int(future_df['yhat'].sum()):,} units (Avg: {future_df['yhat'].mean():.1f} units/day)")
    
    # Save LSTM Forecast CSV
    test_df_copy = test_df.copy()
    test_df_copy['yhat'] = lstm_preds
    test_df_copy['yhat_lower'] = lstm_preds * 0.85
    test_df_copy['yhat_upper'] = lstm_preds * 1.15
    
    full_lstm_export = pd.concat([
        test_df_copy[['ds', 'y', 'yhat', 'yhat_lower', 'yhat_upper']],
        future_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    ], ignore_index=True)
    
    lstm_csv_path = os.path.join(artifacts_dir, "lstm_forecast_results.csv")
    full_lstm_export.to_csv(lstm_csv_path, index=False)
    print(f"Saved LSTM forecast results: {lstm_csv_path}")
    
    # Save Plot
    plot_actual_vs_forecast(
        test_df_copy, 
        test_df_copy, 
        title="PyTorch LSTM Holdout Evaluation for SKU0001 (July-Dec 2023)",
        save_path=os.path.join(plots_dir, "lstm_actual_vs_forecast.png")
    )
    
    print("\n================================================================================")
    print("                     LSTM PIPELINE COMPLETED!                                  ")
    print("================================================================================")

if __name__ == "__main__":
    main()
