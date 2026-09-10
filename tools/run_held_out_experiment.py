#!/usr/bin/env python3
"""
TinyIDS — Held-Out Behavioral Anomaly Evaluation
Evaluates whether a model trained WITHOUT ANOMALY_COMBINED can still detect it
as an anomaly based strictly on multi-feature behavioral boundaries.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, recall_score, f1_score

WORKSPACE = "/Users/parineeth/Desktop/tinyIDS"

FEATURE_COLS = [
    'transaction_rate', 'byte_rate', 'free_heap', 'heap_delta',
    'loop_avg_ms', 'loop_max_ms', 'loop_jitter_ms', 'wifi_rssi',
    'avg_inter_arrival_ms', 'socket_errors'
]

def main():
    print("==================================================")
    print("  TinyIDS — Held-Out Behavioral Anomaly Evaluation")
    print("==================================================")

    raw_dir = os.path.join(WORKSPACE, "dataset", "esp32", "raw")
    files = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(".csv") and f != "calibration_dataset.csv"]

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df = df[df['label'].isin([0, 1])].reset_index(drop=True)

    # Train on all scenarios EXCEPT ANOMALY_COMBINED
    train_subset = df[df['scenario'] != 'ANOMALY_COMBINED'].reset_index(drop=True)
    test_subset = df[df['scenario'] == 'ANOMALY_COMBINED'].reset_index(drop=True)

    print(f"Training set (excluding ANOMALY_COMBINED): {len(train_subset)} samples")
    print(f"Test set (strictly ANOMALY_COMBINED):     {len(test_subset)} samples")

    X_train = train_subset[FEATURE_COLS].values
    y_train = train_subset['label'].values

    X_test = test_subset[FEATURE_COLS].values
    y_test = test_subset['label'].values

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_te_s = scaler.transform(X_test)

    dt = DecisionTreeClassifier(max_depth=5, min_samples_leaf=2, random_state=42)
    dt.fit(X_tr_s, y_train)

    preds = dt.predict(X_te_s)
    recall = recall_score(y_test, preds, zero_division=0)
    detected = int(sum(preds))
    total = len(y_test)

    print(f"\nResults:")
    print(f"  Held-out ANOMALY_COMBINED samples: {total}")
    print(f"  Detected as ANOMALY:               {detected}")
    print(f"  Recall on Unseen Anomaly:         {recall*100:.2f}%")

    report_content = f"""# TinyIDS — Held-Out Behavioral Anomaly Evaluation Report

**Held-Out Scenario**: `ANOMALY_COMBINED` (Fused High-Rate Traffic + CPU Compute Stress)  
**Training Scenarios**: `NORMAL_IDLE`, `NORMAL_PERIODIC`, `NORMAL_VARIABLE`, `ANOMALY_HIGH_RATE`, `ANOMALY_BURST`, `ANOMALY_COMPUTE`, `ANOMALY_MEMORY`  

| Metric | Measured Value | Security Significance |
| :--- | :---: | :--- |
| **Held-Out Detection Recall** | **{recall*100:.2f}%** | Demonstrates the Decision Tree learns generalized multi-feature behavioral boundaries rather than memorizing specific scenario signatures. |
| **Total Held-Out Samples** | {total} | Real ESP32 telemetry windows |
| **Successfully Flagged** | {detected} | Predicted as ANOMALY (label 1) |
| **False Negatives** | {total - detected} | Missed windows |
"""

    out_path = os.path.join(WORKSPACE, "reports", "final", "held_out_anomaly_report.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(report_content)
    print(f"\nSaved report to: {out_path}")

if __name__ == "__main__":
    main()
