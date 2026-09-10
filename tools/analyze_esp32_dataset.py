#!/usr/bin/env python3
"""
TinyIDS V3 — ESP32 Dataset Analysis & Feature Validation Tool
Inspects collected ESP32 telemetry, checks data quality, computes statistics,
and generates feature distribution plots.
"""

import os
import sys
import glob
import json
import numpy as np
import pandas as pd

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def analyze_dataset(data_dir="dataset/esp32/raw", out_dir="reports/figures/esp32_feature_distributions"):
    os.makedirs(out_dir, exist_ok=True)
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        print(f"[WARN] No CSV files found in {data_dir}. Run data collection first.")
        return None

    print(f"[INFO] Found {len(csv_files)} CSV files in {data_dir}. Merging for analysis...")
    dfs = []
    for f in sorted(csv_files):
        try:
            d = pd.read_csv(f)
            # Filter out transition windows (label == 255)
            d = d[d['label'] != 255]
            dfs.append(d)
        except Exception as e:
            print(f"[WARN] Could not read {f}: {e}")

    if not dfs:
        print("[ERROR] No valid data could be read.")
        return None

    df = pd.concat(dfs, ignore_index=True)
    print(f"[INFO] Total valid windows loaded: {len(df):,}")
    print(f"Scenarios present: {df['scenario'].value_counts().to_dict()}")
    print(f"Class distribution: {df['label'].value_counts().to_dict()}")

    numeric_cols = [
        'free_heap', 'min_free_heap', 'heap_delta', 'max_alloc_heap',
        'loop_avg_ms', 'loop_max_ms', 'loop_jitter_ms', 'wifi_rssi',
        'transaction_rate', 'byte_rate', 'avg_inter_arrival_ms',
        'transaction_count', 'reconnect_count', 'socket_errors', 'socket_duration_ms'
    ]

    stats_list = []
    for col in numeric_cols:
        if col in df.columns:
            s = df[col]
            norm_s = df[df['label'] == 0][col]
            anom_s = df[df['label'] == 1][col]
            stats_list.append({
                "feature": col,
                "overall_mean": round(float(s.mean()), 4),
                "overall_std": round(float(s.std()), 4),
                "overall_min": round(float(s.min()), 4),
                "overall_max": round(float(s.max()), 4),
                "normal_mean": round(float(norm_s.mean()), 4) if len(norm_s) > 0 else 0.0,
                "anomaly_mean": round(float(anom_s.mean()), 4) if len(anom_s) > 0 else 0.0,
                "null_count": int(s.isnull().sum()),
                "inf_count": int(np.isinf(s).sum())
            })

    stats_df = pd.DataFrame(stats_list)
    stats_csv = "reports/phase2_feature_validation.csv"
    stats_df.to_csv(stats_csv, index=False)
    print(f"[INFO] Saved feature validation stats to {stats_csv}")

    # Generate Feature Distribution Plots
    print("[INFO] Generating distribution plots...")
    plot_features = ['transaction_rate', 'byte_rate', 'free_heap', 'loop_avg_ms', 'loop_max_ms', 'loop_jitter_ms']
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()

    for i, feat in enumerate(plot_features):
        ax = axes[i]
        if feat in df.columns:
            norm_vals = df[df['label'] == 0][feat].dropna()
            anom_vals = df[df['label'] == 1][feat].dropna()
            ax.hist(norm_vals, bins=25, alpha=0.6, color='blue', label='Normal (0)', density=True)
            if len(anom_vals) > 0:
                ax.hist(anom_vals, bins=25, alpha=0.6, color='red', label='Anomaly (1)', density=True)
            ax.set_title(f"Distribution: {feat}", fontsize=11)
            ax.set_xlabel(feat)
            ax.set_ylabel("Density")
            ax.legend(loc='upper right')
            ax.grid(True, linestyle='--', alpha=0.5)

    plt.suptitle("ESP32 On-Device Telemetry Feature Distributions (Normal vs Anomaly)", fontsize=14, y=0.98)
    plt.tight_layout()
    fig_path = os.path.join(out_dir, "esp32_distributions.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"[INFO] Saved distribution figure to {fig_path}")

    # Correlation Matrix
    corr_cols = [c for c in numeric_cols if c in df.columns]
    corr_matrix = df[corr_cols].corr()
    corr_csv = "reports/esp32_feature_correlation.csv"
    corr_matrix.to_csv(corr_csv)
    print(f"[INFO] Saved correlation matrix to {corr_csv}")

    return stats_df

if __name__ == "__main__":
    analyze_dataset()
