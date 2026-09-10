#!/usr/bin/env python3
"""
TinyIDS — Train a REAL sklearn DecisionTreeClassifier on ESP32 telemetry
and export it as C++ code for embedded inference.

Outputs:
  - model/preprocessing/scaler_params.json
  - model/final_model/decision_tree.pkl
  - model/final_model/metrics.json
  - firmware/TinyIDS/model_tree.h
  - firmware/TinyIDS/preprocessing_params.h
"""

import os
import sys
import json
import pickle
import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

SEED = 42
np.random.seed(SEED)

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FEATURE_COLS = [
    'transaction_rate', 'byte_rate', 'free_heap', 'heap_delta',
    'loop_avg_ms', 'loop_max_ms', 'loop_jitter_ms', 'wifi_rssi',
    'avg_inter_arrival_ms', 'socket_errors'
]

# Feature index to human-readable indicator name mapping
FEATURE_INDICATOR = {
    0: "TRANSACTION_RATE",
    1: "BYTE_RATE",
    2: "FREE_HEAP",
    3: "HEAP_DELTA",
    4: "LOOP_AVG_MS",
    5: "LOOP_MAX_MS",
    6: "LOOP_JITTER_MS",
    7: "WIFI_RSSI",
    8: "AVG_INTER_ARRIVAL_MS",
    9: "SOCKET_ERRORS"
}


def load_data():
    """Load real hardware CSV files from dataset/esp32/raw/ (excludes synthetic calibration_dataset.csv)."""
    raw_dir = os.path.join(WORKSPACE, "dataset", "esp32", "raw")
    files = [
        os.path.join(raw_dir, f) for f in os.listdir(raw_dir)
        if f.endswith(".csv") and f != "calibration_dataset.csv"
    ]
    if not files:
        print("[ERROR] No real hardware CSV files found in dataset/esp32/raw/")
        sys.exit(1)

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    # Exclude transition windows (label == 255)
    df = df[df['label'].isin([0, 1])].reset_index(drop=True)

    # Verify all feature columns exist
    for col in FEATURE_COLS:
        if col not in df.columns:
            print(f"[ERROR] Missing feature column: {col}")
            sys.exit(1)

    print(f"[INFO] Loaded {len(df)} REAL HARDWARE samples from {len(files)} files: {', '.join([os.path.basename(f) for f in files])}")
    print(f"       Normal: {(df['label']==0).sum()}, Anomaly: {(df['label']==1).sum()}")
    return df


def train_model(df):
    """Train DecisionTreeClassifier with StandardScaler preprocessing."""
    X = df[FEATURE_COLS].values.astype(np.float64)
    y = df['label'].values.astype(int)

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=SEED, stratify=y
    )

    print(f"[INFO] Train: {len(X_train)} samples, Test: {len(X_test)} samples")

    # Fit StandardScaler on training data only
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Train Decision Tree
    dt = DecisionTreeClassifier(max_depth=6, min_samples_leaf=3, random_state=SEED)
    dt.fit(X_train_s, y_train)

    # Evaluate
    preds = dt.predict(X_test_s)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    cm = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = [int(x) for x in cm.ravel()]
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    metrics = {
        "accuracy": round(acc, 6),
        "precision": round(prec, 6),
        "recall": round(rec, 6),
        "f1": round(f1, 6),
        "fpr": round(fpr, 6),
        "fnr": round(fnr, 6),
        "tree_depth": int(dt.get_depth()),
        "tree_leaves": int(dt.get_n_leaves()),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    }

    print(f"\n=== Decision Tree Evaluation ===")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  FPR:       {fpr:.4f}")
    print(f"  FNR:       {fnr:.4f}")
    print(f"  Depth:     {dt.get_depth()}")
    print(f"  Leaves:    {dt.get_n_leaves()}")
    print(f"  Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")

    return dt, scaler, metrics


def save_artifacts(dt, scaler, metrics):
    """Save model, scaler, and metrics to disk."""
    # Save scaler params
    os.makedirs(os.path.join(WORKSPACE, "model", "preprocessing"), exist_ok=True)
    scaler_dict = {
        "features": FEATURE_COLS,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist()
    }
    scaler_path = os.path.join(WORKSPACE, "model", "preprocessing", "scaler_params.json")
    with open(scaler_path, "w") as f:
        json.dump(scaler_dict, f, indent=2)
    print(f"[INFO] Saved {scaler_path}")

    # Save model pickle
    os.makedirs(os.path.join(WORKSPACE, "model", "final_model"), exist_ok=True)
    model_path = os.path.join(WORKSPACE, "model", "final_model", "decision_tree.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(dt, f)
    print(f"[INFO] Saved {model_path}")

    # Save metrics
    metrics_path = os.path.join(WORKSPACE, "model", "final_model", "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[INFO] Saved {metrics_path}")

    return scaler_dict


def find_dominant_feature(tree_, node, feature_names):
    """Walk back from a leaf to find the most impactful split feature."""
    # Use the parent split feature - walk up the tree
    # Since sklearn doesn't store parent links, we'll track during recursion
    pass  # Handled inline during recursion


def export_model_tree_h(dt, scaler_dict):
    """Export sklearn Decision Tree as C++ header with exact thresholds."""
    tree_ = dt.tree_
    feature_names = FEATURE_COLS
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("#ifndef MODEL_TREE_H")
    lines.append("#define MODEL_TREE_H")
    lines.append("")
    lines.append("#include <Arduino.h>")
    lines.append('#include "feature_config.h"')
    lines.append("")
    lines.append("// ============================================================")
    lines.append(f"// Auto-generated from sklearn DecisionTreeClassifier")
    lines.append(f"// Exported: {now}")
    lines.append(f"// Tree depth: {dt.get_depth()}, Leaves: {dt.get_n_leaves()}")
    lines.append(f"// Training data: ESP32 telemetry from dataset/esp32/raw/")
    lines.append(f"// Features: {', '.join(feature_names)}")
    lines.append("// ============================================================")
    lines.append("")
    lines.append("inline bool evaluateExportedTree(const float* x, float& confidence, const char*& indicator) {")

    def recurse(node, depth, last_split_feature=None):
        indent = "    " * (depth + 1)
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            feat_idx = int(tree_.feature[node])
            feat_name = feature_names[feat_idx]
            thresh = float(tree_.threshold[node])
            lines.append(f"{indent}if (x[{feat_idx}] <= {thresh:.6f}f) {{ // {feat_name}")
            recurse(tree_.children_left[node], depth + 1, feat_idx)
            lines.append(f"{indent}}} else {{")
            recurse(tree_.children_right[node], depth + 1, feat_idx)
            lines.append(f"{indent}}}")
        else:
            # Leaf node
            values = tree_.value[node][0]
            total = float(sum(values))
            n_normal = values[0]
            n_anomaly = values[1]
            pred_class = int(values.argmax())
            conf = float(values[pred_class] / total)
            is_anomaly = pred_class == 1

            if is_anomaly:
                # Use the last split feature to create a meaningful indicator
                if last_split_feature is not None:
                    indicator_str = f"ANOMALY_{FEATURE_INDICATOR.get(last_split_feature, 'UNKNOWN')}"
                else:
                    indicator_str = "ANOMALY_DETECTED"
            else:
                indicator_str = "NORMAL_BASELINE"

            lines.append(f"{indent}confidence = {conf:.4f}f;")
            lines.append(f'{indent}indicator = "{indicator_str}";')
            lines.append(f"{indent}return {'true' if is_anomaly else 'false'}; // class={'ANOMALY' if is_anomaly else 'NORMAL'}, conf={conf:.4f}")

    recurse(0, 0)
    lines.append("}")
    lines.append("")
    lines.append("#endif // MODEL_TREE_H")
    lines.append("")

    code = "\n".join(lines)
    out_path = os.path.join(WORKSPACE, "firmware", "TinyIDS", "model_tree.h")
    with open(out_path, "w") as f:
        f.write(code)
    print(f"[INFO] Exported decision tree to {out_path}")
    print(f"       Size: {len(code)} bytes")


def export_preprocessing_params_h(scaler_dict):
    """Export preprocessing_params.h with 2-arg normalizeFeatures signature."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    means = scaler_dict["mean"]
    scales = scaler_dict["scale"]
    n = len(means)

    mean_str = ", ".join(f"{v:.10f}f" for v in means)
    scale_str = ", ".join(f"{v:.10f}f" for v in scales)

    code = f"""#ifndef PREPROCESSING_PARAMS_H
#define PREPROCESSING_PARAMS_H

// Auto-generated from sklearn StandardScaler
// Source: ml/training/train_and_export.py
// Generated: {now}

#include "feature_config.h"

// Feature names (for documentation)
// {', '.join(scaler_dict['features'])}

static const float SCALER_MEAN[NUM_FEATURES] = {{
    {mean_str}
}};

static const float SCALER_SCALE[NUM_FEATURES] = {{
    {scale_str}
}};

inline void normalizeFeatures(const float* raw, float* out) {{
    for (int i = 0; i < NUM_FEATURES; i++) {{
        out[i] = (raw[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];
    }}
}}

#endif // PREPROCESSING_PARAMS_H
"""

    out_path = os.path.join(WORKSPACE, "firmware", "TinyIDS", "preprocessing_params.h")
    with open(out_path, "w") as f:
        f.write(code)
    print(f"[INFO] Exported preprocessing params to {out_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("TinyIDS — Decision Tree Training & C++ Export")
    print("=" * 60)

    df = load_data()
    dt, scaler, metrics = train_model(df)
    scaler_dict = save_artifacts(dt, scaler, metrics)
    export_model_tree_h(dt, scaler_dict)
    export_preprocessing_params_h(scaler_dict)

    print("\n[DONE] All artifacts generated successfully.")
