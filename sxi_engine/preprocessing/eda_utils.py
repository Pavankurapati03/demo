import os
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from sxi_engine.preprocessing.csv_extractor import safe_read_file
except ImportError:
    try:
        from .csv_extractor import safe_read_file
    except ImportError:
        try:
            from pipeline.metadata_extractors.csv_extractor import safe_read_file
        except ImportError:
            def safe_read_file(path: str) -> Optional[pd.DataFrame]:
                try:
                    if str(path).endswith(".xlsx") or str(path).endswith(".xls"):
                        return pd.read_excel(path)
                    return pd.read_csv(path)
                except Exception:
                    return None

sns.set_style("whitegrid")
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "figure.titlesize": 18,
})


def generate_eda_dashboard(dataset_path: str, output_path: str) -> Optional[Dict[str, Any]]:
    df = safe_read_file(dataset_path)
    if df is None or df.empty:
        return None

    file_name = os.path.basename(dataset_path)
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()
    findings = _build_findings(df, num_cols, cat_cols)

    _render_dashboard(
        df=df,
        file_name=file_name,
        num_cols=num_cols,
        cat_cols=cat_cols,
        findings=findings,
        output_path=output_path,
    )

    chart_files = _render_individual_charts(
        df=df,
        num_cols=num_cols,
        cat_cols=cat_cols,
        output_path=output_path,
    )

    return {
        "dataset_name": file_name,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "findings": findings,
        "charts": chart_files,
    }


def _build_findings(df: pd.DataFrame, num_cols: List[str], cat_cols: List[str]) -> List[str]:
    findings: List[str] = []

    if num_cols:
        skew_direction = "right" if float(df[num_cols[0]].dropna().skew() or 0) > 0 else "left"
        findings.append(f"{num_cols[0]} shows a {skew_direction}-skewed distribution")

    if cat_cols:
        top_category = df[cat_cols[0]].dropna()
        if not top_category.empty:
            findings.append(f"'{top_category.value_counts().idxmax()}' is the most frequent category")

    if len(num_cols) >= 2:
        findings.append(f"Scatter plot compares {num_cols[0]} and {num_cols[1]}")

        corr = df[num_cols].corr(numeric_only=True)
        strongest_pair = _top_correlation_pair(corr)
        if strongest_pair is not None:
            left, right, value = strongest_pair
            findings.append(f"Strongest correlation: {left} and {right} ({value:.2f})")

    findings.append(f"Rows x columns: {df.shape[0]} x {df.shape[1]}")
    findings.append(f"Missing cells: {int(df.isna().sum().sum())}")

    return findings[:6]


def _top_correlation_pair(corr: pd.DataFrame) -> Optional[tuple[str, str, float]]:
    if corr.empty or corr.shape[1] < 2:
        return None

    corr_abs = corr.abs().copy()
    np.fill_diagonal(corr_abs.values, np.nan)
    top_corr = corr_abs.stack().sort_values(ascending=False)
    if top_corr.empty:
        return None

    left, right = top_corr.index[0]
    return str(left), str(right), float(top_corr.iloc[0])


def _render_dashboard(
    df: pd.DataFrame,
    file_name: str,
    num_cols: List[str],
    cat_cols: List[str],
    findings: List[str],
    output_path: str,
) -> None:
    fig = plt.figure(figsize=(15, 10))
    grid = fig.add_gridspec(4, 2, height_ratios=[0.35, 2.5, 2.5, 2])

    ax_header = fig.add_subplot(grid[0, :])
    ax_header.axis("off")
    ax_header.text(0.01, 0.5, "EDA Dashboard:", fontsize=22, fontweight="bold", va="center")
    ax_header.text(0.26, 0.5, file_name, fontsize=16, va="center")

    ax1 = fig.add_subplot(grid[1, 0])
    _plot_bar(df, cat_cols, ax1)

    ax2 = fig.add_subplot(grid[1, 1])
    _plot_pie(df, cat_cols, ax2)

    ax3 = fig.add_subplot(grid[2, 0])
    _plot_histogram(df, num_cols, ax3)

    ax4 = fig.add_subplot(grid[2, 1])
    _plot_scatter(df, num_cols, ax4)

    ax5 = fig.add_subplot(grid[3, :])
    _plot_heatmap(df, num_cols, ax5)

    summary_text = "Summary of Key Findings\n" + "\n".join(f"- {finding}" for finding in findings)
    fig.text(
        0.01,
        0.01,
        summary_text,
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.5", fc="#F5F5F5", ec="#CCCCCC"),
    )

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _render_individual_charts(
    df: pd.DataFrame,
    num_cols: List[str],
    cat_cols: List[str],
    output_path: str,
) -> List[Dict[str, str]]:
    output_dir = os.path.dirname(output_path)
    output_stem = os.path.splitext(os.path.basename(output_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    chart_specs = [
        ("bar", "Key Topic Distribution", _plot_bar, (7, 5)),
        ("pie", "Data Source Types", _plot_pie, (7, 5)),
        ("histogram", f"Distribution of {num_cols[0]}" if num_cols else "Distribution", _plot_histogram, (7, 5)),
        (
            "scatter",
            f"{num_cols[0]} vs {num_cols[1]}" if len(num_cols) >= 2 else "Scatter Plot",
            _plot_scatter,
            (7, 5),
        ),
        ("heatmap", "Correlation Heatmap", _plot_heatmap, (8, 6)),
    ]

    chart_files: List[Dict[str, str]] = []

    for slug, title, plotter, figsize in chart_specs:
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("white")
        plotter(df, num_cols if plotter in {_plot_histogram, _plot_scatter, _plot_heatmap} else cat_cols, ax)
        plt.tight_layout()

        file_name = f"{output_stem}_{slug}.png"
        file_path = os.path.join(output_dir, file_name)
        fig.savefig(file_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        chart_files.append({
            "key": slug,
            "title": title,
            "file_name": file_name,
        })

    return chart_files


def _plot_bar(df: pd.DataFrame, cat_cols: List[str], ax: Any) -> None:
    if cat_cols:
        df[cat_cols[0]].fillna("Missing").value_counts().head(6).plot(
            kind="bar",
            ax=ax,
            color="#4C72B0",
        )
        ax.set_title("Key Topic Distribution")
        ax.set_xlabel("")
        ax.set_ylabel("Count")
        ax.tick_params(axis="x", rotation=20)
        return

    ax.axis("off")
    ax.text(0.5, 0.5, "No categorical column available", ha="center", va="center")


def _plot_pie(df: pd.DataFrame, cat_cols: List[str], ax: Any) -> None:
    if cat_cols:
        df[cat_cols[0]].fillna("Missing").value_counts().head(4).plot(
            kind="pie",
            autopct="%1.0f%%",
            ax=ax,
            startangle=90,
        )
        ax.set_title("Data Source Types")
        ax.set_ylabel("")
        return

    counts = pd.Series({
        "Numeric": len(df.select_dtypes(include=np.number).columns),
        "Other": max(len(df.columns) - len(df.select_dtypes(include=np.number).columns), 0),
    })
    counts = counts[counts > 0]
    counts.plot(kind="pie", autopct="%1.0f%%", ax=ax, startangle=90)
    ax.set_title("Data Source Types")
    ax.set_ylabel("")


def _plot_histogram(df: pd.DataFrame, num_cols: List[str], ax: Any) -> None:
    if num_cols:
        sns.histplot(df[num_cols[0]].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution of {num_cols[0]}")
        return

    ax.axis("off")
    ax.text(0.5, 0.5, "No numeric column available", ha="center", va="center")


def _plot_scatter(df: pd.DataFrame, num_cols: List[str], ax: Any) -> None:
    if len(num_cols) >= 2:
        sns.scatterplot(x=df[num_cols[0]], y=df[num_cols[1]], ax=ax)
        ax.set_title(f"{num_cols[0]} vs {num_cols[1]}")
        return

    ax.axis("off")
    ax.text(0.5, 0.5, "Need at least two numeric columns", ha="center", va="center")


def _plot_heatmap(df: pd.DataFrame, num_cols: List[str], ax: Any) -> None:
    if len(num_cols) >= 2:
        corr = df[num_cols].corr(numeric_only=True)
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        ax.set_title("Correlation Heatmap")
        return

    ax.axis("off")
    ax.text(0.5, 0.5, "Correlation heatmap needs at least two numeric columns", ha="center", va="center")
