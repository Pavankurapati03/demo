"""
Adaptive 3-Model Demand Forecasting Benchmarking Suite.
Trains Meta Prophet, Auto-SARIMAX, and Enhanced Residual LSTM on identical
train/holdout splits, evaluates all models, and outputs:
  - Side-by-side metrics table in console
  - artifacts/three_model_comparison_metrics.json
  - artifacts/plots/three_models_holdout_comparison.png
All three models adapt automatically to any e-commerce time series dataset.
"""

import os
import json
import warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

from src.data_loader import load_raw_data, prepare_prophet_df, split_train_test
from src.prophet_pipeline import build_prophet_model, train_and_predict
from src.lstm_pipeline import (
    prepare_lstm_data, train_lstm_model, predict_lstm,
    get_feature_cols, add_calendar_features
)
from src.sarima_pipeline import run_sarimax_pipeline
from src.evaluator import evaluate_forecast

plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)


def print_metrics_table(metrics_dict: dict):
    """Print a formatted side-by-side metrics table."""
    metrics = ["MAE", "RMSE", "MAPE_percent", "WMAPE_percent", "Bias", "R2_Score"]
    labels  = {"MAE": "MAE", "RMSE": "RMSE", "MAPE_percent": "MAPE (%)",
               "WMAPE_percent": "WMAPE (%)", "Bias": "Bias", "R2_Score": "R² Score"}
    models  = list(metrics_dict.keys())

    # Header
    header = f"{'Metric':<14}" + "".join(f"{m:>16}" for m in models)
    print("\n" + "=" * (14 + 16 * len(models)))
    print(header)
    print("-" * (14 + 16 * len(models)))

    for key in metrics:
        row = f"{labels[key]:<14}"
        for m in models:
            val = metrics_dict[m].get(key, float("nan"))
            row += f"{val:>16.4f}"
        print(row)

    print("=" * (14 + 16 * len(models)) + "\n")


def build_comparison_json(m_prophet, m_sarima, m_lstm):
    """Build full comparison JSON with winner annotation per metric."""
    metrics = ["MAE", "RMSE", "MAPE_percent", "WMAPE_percent", "R2_Score"]
    winner_is_low  = {"MAE", "RMSE", "MAPE_percent", "WMAPE_percent"}   # lower is better
    winner_is_high = {"R2_Score"}                                          # higher is better

    comparison = {}
    for metric in metrics:
        vals = {
            "Prophet":    m_prophet.get(metric, float("nan")),
            "Auto-SARIMAX": m_sarima.get(metric, float("nan")),
            "LSTM":       m_lstm.get(metric, float("nan")),
        }
        if metric in winner_is_low:
            best_key = min(vals, key=lambda k: vals[k])
        else:
            best_key = max(vals, key=lambda k: vals[k])

        comparison[metric] = {**vals, "winner": best_key}

    return comparison


def main():
    print("=" * 80)
    print("    ADAPTIVE 3-MODEL DEMAND FORECASTING BENCHMARKING SUITE                     ")
    print("    Meta Prophet  |  Auto-SARIMAX  |  Enhanced Residual LSTM                   ")
    print("=" * 80)

    csv_path     = "fmcg_sales_3years_1M_rows.csv"
    artifacts_dir = "artifacts"
    plots_dir    = os.path.join(artifacts_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. LOAD & SPLIT DATA                                                 #
    # ------------------------------------------------------------------ #
    print("\n[1/4] Loading dataset and splitting train / test...")
    raw_df   = load_raw_data(csv_path)
    daily_df = prepare_prophet_df(raw_df, sku_id="SKU0001")

    test_start = "2023-07-01"
    train_df, test_df = split_train_test(daily_df, test_start_date=test_start)

    print(f"  SKU: SKU0001 (BrandA Soda)")
    print(f"  Train: {len(train_df)} days  ({train_df['ds'].min().date()} -> {train_df['ds'].max().date()})")
    print(f"  Test:  {len(test_df)} days  ({test_df['ds'].min().date()} -> {test_df['ds'].max().date()})")

    actual = test_df["y"].values

    # ------------------------------------------------------------------ #
    # 2. META PROPHET                                                      #
    # ------------------------------------------------------------------ #
    print("\n[2/4] Training Meta Prophet...")
    prophet_model, exog_cols_p = build_prophet_model(train_df)
    print(f"  Regressors detected: {exog_cols_p}")
    _, prophet_forecast = train_and_predict(prophet_model, train_df, test_df)
    prophet_preds = np.clip(prophet_forecast["yhat"].values, 0, None)
    m_prophet = evaluate_forecast(actual, prophet_preds)
    print(f"  Prophet  -> WMAPE={m_prophet['WMAPE_percent']:.2f}%  R2={m_prophet['R2_Score']:.4f}")

    # ------------------------------------------------------------------ #
    # 3. AUTO-SARIMAX                                                      #
    # ------------------------------------------------------------------ #
    print("\n[3/4] Training Auto-SARIMAX...")
    _, sarima_preds, _, _ = run_sarimax_pipeline(
        train_df, test_df, full_df=None, future_days=0
    )
    m_sarima = evaluate_forecast(actual, sarima_preds)
    print(f"  SARIMAX  -> WMAPE={m_sarima['WMAPE_percent']:.2f}%  R2={m_sarima['R2_Score']:.4f}")

    # ------------------------------------------------------------------ #
    # 4. ENHANCED RESIDUAL LSTM                                           #
    # ------------------------------------------------------------------ #
    print("\n[4/4] Training Enhanced Residual LSTM...")
    scaler, train_loader, test_loader, _, feature_cols = prepare_lstm_data(
        train_df, test_df, window_size=None   # Auto-selects optimal window
    )
    input_size = len(feature_cols)
    print(f"  LSTM input features ({input_size}): {feature_cols}")

    lstm_model = train_lstm_model(
        train_loader,
        input_size=input_size,
        hidden_size=96,
        epochs=200,
        lr=0.001
    )

    y_idx = feature_cols.index("y")
    lstm_preds = predict_lstm(lstm_model, test_loader, scaler, y_col_idx=y_idx)

    # Align lengths (sliding window removes first `window` samples)
    n_align = min(len(actual), len(lstm_preds))
    actual_aligned = actual[-n_align:]
    lstm_preds_aligned = lstm_preds[-n_align:]
    m_lstm = evaluate_forecast(actual_aligned, lstm_preds_aligned)
    print(f"  LSTM     -> WMAPE={m_lstm['WMAPE_percent']:.2f}%  R2={m_lstm['R2_Score']:.4f}")

    # ------------------------------------------------------------------ #
    # METRICS TABLE                                                        #
    # ------------------------------------------------------------------ #
    all_metrics = {
        "Meta Prophet":    m_prophet,
        "Auto-SARIMAX": m_sarima,
        "Enhanced LSTM":   m_lstm
    }
    print_metrics_table(all_metrics)

    # ------------------------------------------------------------------ #
    # SAVE JSON                                                            #
    # ------------------------------------------------------------------ #
    comparison_block = build_comparison_json(m_prophet, m_sarima, m_lstm)
    output_json = {
        "meta_prophet":   m_prophet,
        "auto_sarimax":   m_sarima,
        "enhanced_lstm":  m_lstm,
        "comparison":     comparison_block
    }
    json_path = os.path.join(artifacts_dir, "three_model_comparison_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    print(f"Saved 3-model metrics JSON: {json_path}")

    # ------------------------------------------------------------------ #
    # OVERLAY COMPARISON PLOT                                              #
    # ------------------------------------------------------------------ #
    test_dates    = pd.to_datetime(test_df["ds"].values)
    n_sarima      = len(sarima_preds)
    n_lstm        = len(lstm_preds_aligned)
    n_prophet     = len(prophet_preds)

    # All models use actual as reference; align to minimum overlap
    n_common = min(len(test_dates), n_sarima, n_prophet)

    # For LSTM, it's already aligned to n_align from end of test_df
    lstm_dates  = test_dates[-n_lstm:]

    fig, axes = plt.subplots(2, 1, figsize=(16, 12), dpi=150)

    # ---- Top panel: Actual vs all 3 models ----
    ax = axes[0]
    ax.plot(test_dates[:n_common], actual[:n_common],
            color="#1a202c", linewidth=2.0, label="Actual Demand", zorder=5)
    ax.plot(test_dates[:n_common], prophet_preds[:n_common],
            color="#3182ce", linewidth=1.6, linestyle="--",
            label=f"Prophet  (WMAPE={m_prophet['WMAPE_percent']:.1f}%, R²={m_prophet['R2_Score']:.3f})",
            alpha=0.85)
    ax.plot(test_dates[:n_sarima], sarima_preds[:n_sarima],
            color="#38a169", linewidth=1.6, linestyle="-.",
            label=f"SARIMAX (WMAPE={m_sarima['WMAPE_percent']:.1f}%, R²={m_sarima['R2_Score']:.3f})",
            alpha=0.85)
    ax.plot(lstm_dates, lstm_preds_aligned,
            color="#e53e3e", linewidth=1.6, linestyle=":",
            label=f"LSTM     (WMAPE={m_lstm['WMAPE_percent']:.1f}%, R²={m_lstm['R2_Score']:.3f})",
            alpha=0.85)

    ax.set_title("3-Model Demand Forecast vs Actual (Holdout Test Period — SKU0001)",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Units Sold", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.tick_params(axis="x", rotation=30)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)

    # ---- Bottom panel: Metric bar chart ----
    ax2 = axes[1]
    metric_names = ["MAE", "RMSE", "WMAPE (%)"]
    prophet_vals = [m_prophet["MAE"], m_prophet["RMSE"], m_prophet["WMAPE_percent"]]
    sarima_vals  = [m_sarima["MAE"],  m_sarima["RMSE"],  m_sarima["WMAPE_percent"]]
    lstm_vals    = [m_lstm["MAE"],    m_lstm["RMSE"],    m_lstm["WMAPE_percent"]]

    x = np.arange(len(metric_names))
    w = 0.26
    bars1 = ax2.bar(x - w, prophet_vals, w, label="Prophet",    color="#3182ce", edgecolor="white")
    bars2 = ax2.bar(x,     sarima_vals,  w, label="Auto-SARIMAX", color="#38a169", edgecolor="white")
    bars3 = ax2.bar(x + w, lstm_vals,   w, label="LSTM",        color="#e53e3e", edgecolor="white")

    for bar in list(bars1) + list(bars2) + list(bars3):
        h = bar.get_height()
        ax2.annotate(f"{h:.1f}",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points",
                     ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax2.set_title("Error Metric Comparison Across 3 Models (Lower is Better)",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(metric_names, fontsize=11)
    ax2.set_ylabel("Error Value", fontsize=11)
    ax2.legend(fontsize=10)

    # Annotate R2 scores on the bottom panel
    r2_text = (f"R² Scores —  Prophet: {m_prophet['R2_Score']:.3f}  |  "
               f"SARIMAX: {m_sarima['R2_Score']:.3f}  |  "
               f"LSTM: {m_lstm['R2_Score']:.3f}")
    fig.text(0.5, 0.01, r2_text, ha="center", fontsize=10,
             color="#4a5568", style="italic")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plot_path = os.path.join(plots_dir, "three_models_holdout_comparison.png")
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    print(f"Saved 3-model comparison plot: {plot_path}")

    print("\n" + "=" * 80)
    print("  3-MODEL BENCHMARKING COMPLETE!                                                ")
    print("=" * 80)


if __name__ == "__main__":
    main()
