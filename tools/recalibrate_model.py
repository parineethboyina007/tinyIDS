#!/usr/bin/env python3
"""
TinyIDS V3 — Hardware Recalibration Pipeline
============================================
1. Drives the ESP32 through NORMAL and ANOMALY scenarios via Serial CLI
2. Collects CSV telemetry from each scenario
3. Fits a real Z-score scaler on the normal baseline
4. Derives tree thresholds from the normal/anomaly separation
5. Rewrites:
   - model/preprocessing/scaler_params.json
   - firmware/TinyIDS/preprocessing_params.h
   - firmware/TinyIDS/model_tree.h

Usage:
    python3 tools/recalibrate_model.py --port /dev/cu.usbmodemE8F60ABF87A02
"""

import os
import sys
import time
import json
import argparse
import numpy as np

try:
    import serial
except ImportError:
    print("[ERROR] pyserial not installed. Run: pip3 install pyserial")
    sys.exit(1)

# ─── Feature columns extracted from CSV ──────────────────────────────────────
FEAT_COLS = [
    "transaction_rate",
    "byte_rate",
    "free_heap",
    "heap_delta",
    "loop_avg_ms",
    "loop_max_ms",
    "loop_jitter_ms",
    "wifi_rssi",
    "avg_inter_arrival_ms",
    "socket_errors",
]

CSV_HEADER = "timestamp_ms,window_id,scenario,label,free_heap,min_free_heap,heap_delta,max_alloc_heap,loop_avg_ms,loop_max_ms,loop_jitter_ms,wifi_rssi,tx_count,rx_count,tx_bytes,rx_bytes,transaction_rate,byte_rate,avg_inter_arrival_ms,transaction_count,reconnect_count,socket_errors,socket_duration_ms"

COL_IDX = {col: i for i, col in enumerate(CSV_HEADER.split(","))}

# ─── Scenarios to run ────────────────────────────────────────────────────────
# (command, label, duration_s, windows_expected)
SCENARIOS = [
    ("IDLE",      0,  25),   # Normal
    ("PERIODIC",  0,  30),   # Normal
    ("VARIABLE",  0,  30),   # Normal
    ("HIGH_RATE", 1,  25),   # Anomaly
    ("COMPUTE",   1,  25),   # Anomaly
    ("COMBINED",  1,  25),   # Anomaly
    ("IDLE",      0,  20),   # Normal (post-anomaly settle)
]


def read_windows(ser, duration_s, label):
    """Read CSV rows from serial for `duration_s` seconds. Returns list of feature dicts."""
    rows = []
    start = time.time()
    header_seen = False
    while time.time() - start < duration_s:
        try:
            raw = ser.readline().decode("utf-8", errors="replace").strip()
        except Exception:
            continue
        if not raw:
            continue
        if "timestamp_ms" in raw and "window_id" in raw:
            header_seen = True
            continue
        parts = raw.split(",")
        if len(parts) == len(COL_IDX):
            try:
                row = {col: float(parts[COL_IDX[col]]) for col in FEAT_COLS}
                row["__label__"] = label
                elapsed = time.time() - start
                print(f"  [{elapsed:5.1f}s] loop_avg={row['loop_avg_ms']:.3f} "
                      f"loop_max={row['loop_max_ms']:.3f} "
                      f"tx_rate={row['transaction_rate']:.2f} "
                      f"heap={row['free_heap']:.0f} L={label}", flush=True)
                rows.append(row)
            except (ValueError, KeyError):
                pass
    return rows


def send_cmd(ser, cmd, delay=0.5):
    ser.write((cmd + "\n").encode())
    time.sleep(delay)
    # Drain any immediate response
    ser.reset_input_buffer()


def compute_scaler(normal_rows):
    """Fit Z-score scaler on NORMAL rows only."""
    X = np.array([[r[f] for f in FEAT_COLS] for r in normal_rows], dtype=np.float64)
    mean = X.mean(axis=0)
    std  = X.std(axis=0, ddof=1)
    # Avoid division by zero
    std[std < 1e-9] = 1.0
    return mean.tolist(), std.tolist()


def normalize(rows, mean, std):
    mean_arr = np.array(mean)
    std_arr  = np.array(std)
    for r in rows:
        x = np.array([r[f] for f in FEAT_COLS])
        r["__z__"] = ((x - mean_arr) / std_arr).tolist()
    return rows


def derive_thresholds(normal_rows, anomaly_rows):
    """
    Two-sided threshold derivation. For each feature, detect anomalies that
    deviate EITHER too high or too low from the normal operating envelope.

    Example: HIGH_RATE has very FAST loops (z=-2.32, below normal),
             COMPUTE has very SLOW loops (z=+4.47, above normal).
    A single directional threshold cannot catch both — we need two bounds.

    Returns dict: {feat_index: list of (threshold, direction, feat, normal_edge, anomaly_edge)}
                  where direction is '>' (too high) or '<' (too low).
    """
    normal_z  = np.array([r["__z__"] for r in normal_rows])
    anomaly_z = np.array([r["__z__"] for r in anomaly_rows])

    thresholds = {}

    for i, feat in enumerate(FEAT_COLS):
        n_val = normal_z[:, i]
        a_val = anomaly_z[:, i]

        n_p99 = np.percentile(n_val, 99)
        n_p01 = np.percentile(n_val, 1)

        rules_for_feat = []

        # ── Upper side: any anomaly values strictly above normal p99? ──
        a_high = a_val[a_val > n_p99]
        if len(a_high) > 0:
            a_high_p01 = np.percentile(a_high, 1)  # lowest of the high anomalies
            mid = (n_p99 + a_high_p01) / 2.0
            rules_for_feat.append((round(float(mid), 4), ">", feat, n_p99, a_high_p01))

        # ── Lower side: any anomaly values strictly below normal p01? ──
        a_low = a_val[a_val < n_p01]
        if len(a_low) > 0:
            a_low_p99 = np.percentile(a_low, 99)   # highest of the low anomalies
            mid = (n_p01 + a_low_p99) / 2.0
            rules_for_feat.append((round(float(mid), 4), "<", feat, a_low_p99, n_p01))

        thresholds[i] = rules_for_feat if rules_for_feat else None

    return thresholds


def write_scaler_json(mean, std, out_path):
    obj = {
        "features": FEAT_COLS,
        "mean": [round(v, 10) for v in mean],
        "scale": [round(v, 10) for v in std],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[SCALER] Written to {out_path}")


def write_preprocessing_h(mean, std, out_path):
    lines = [
        "#ifndef PREPROCESSING_PARAMS_H",
        "#define PREPROCESSING_PARAMS_H",
        "",
        "// Auto-generated from hardware recalibration — DO NOT EDIT MANUALLY",
        "// Source: tools/recalibrate_model.py",
        f"// Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"#define NUM_FEATURES {len(FEAT_COLS)}",
        "",
        "// Feature names (for documentation)",
        "// " + ", ".join(FEAT_COLS),
        "",
        "static const float SCALER_MEAN[NUM_FEATURES] = {",
    ]
    lines.append("    " + ", ".join(f"{v:.10f}f" for v in mean))
    lines.append("};")
    lines.append("")
    lines.append("static const float SCALER_SCALE[NUM_FEATURES] = {")
    lines.append("    " + ", ".join(f"{v:.10f}f" for v in std))
    lines.append("};")
    lines.append("")
    lines.append("inline void normalizeFeatures(float* x) {")
    lines.append("    for (int i = 0; i < NUM_FEATURES; i++) {")
    lines.append("        x[i] = (x[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];")
    lines.append("    }")
    lines.append("}")
    lines.append("")
    lines.append("#endif // PREPROCESSING_PARAMS_H")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[PREPROC] Written to {out_path}")


def write_model_tree_h(thresholds, out_path):
    """
    Generate model_tree.h with rules derived from real hardware data.
    Uses the top-N separable features, ordered by separability.
    """
    feat_index_map = {
        "transaction_rate":    "FEAT_TRANSACTION_RATE",
        "byte_rate":           "FEAT_BYTE_RATE",
        "free_heap":           "FEAT_FREE_HEAP",
        "heap_delta":          "FEAT_HEAP_DELTA",
        "loop_avg_ms":         "FEAT_LOOP_AVG_MS",
        "loop_max_ms":         "FEAT_LOOP_MAX_MS",
        "loop_jitter_ms":      "FEAT_LOOP_JITTER_MS",
        "wifi_rssi":           "FEAT_WIFI_RSSI",
        "avg_inter_arrival_ms":"FEAT_AVG_INTER_ARRIVAL_MS",
        "socket_errors":       "FEAT_SOCKET_ERRORS",
    }

    indicator_map = {
        "transaction_rate":    "HIGH_TRANSACTION_RATE",
        "byte_rate":           "HIGH_BYTE_RATE",
        "free_heap":           "HEAP_MEMORY_PRESSURE",
        "heap_delta":          "HEAP_MEMORY_PRESSURE",
        "loop_avg_ms":         "CPU_LOOP_BLOCKING",
        "loop_max_ms":         "CPU_LOOP_BLOCKING",
        "loop_jitter_ms":      "HIGH_LOOP_JITTER",
        "wifi_rssi":           "WIFI_SIGNAL_DROP",
        "avg_inter_arrival_ms":"BURST_INTER_ARRIVAL",
        "socket_errors":       "SOCKET_ERROR_BURST",
    }

    confidence_map = {
        "transaction_rate":    0.98,
        "loop_max_ms":         0.96,
        "loop_avg_ms":         0.96,
        "loop_jitter_ms":      0.92,
        "heap_delta":          0.94,
        "free_heap":           0.94,
        "socket_errors":       0.90,
        "byte_rate":           0.88,
        "avg_inter_arrival_ms":0.88,
        "wifi_rssi":           0.85,
    }

    # Build rules only for features with clean separation
    # thresholds[i] is now a list of (thresh, direction, feat, normal_edge, anomaly_edge) or None
    rules = []
    for i, feat in enumerate(FEAT_COLS):
        feat_rules = thresholds.get(i)
        if feat_rules:
            for (thresh, direction, fname, normal_edge, anomaly_edge) in feat_rules:
                # Derive indicator from direction
                base_indicator = indicator_map[feat]
                if direction == ">":
                    indicator = base_indicator + "_HIGH" if direction == ">" and \
                        any(r.get("direction") == "<" for r in rules if r["feat"] == feat) \
                        else base_indicator
                else:
                    indicator = base_indicator + "_LOW"
                rules.append({
                    "feat": feat,
                    "index": feat_index_map[feat],
                    "threshold": thresh,
                    "direction": direction,
                    "indicator": indicator,
                    "confidence": confidence_map.get(feat, 0.90),
                    "normal_edge": normal_edge,
                    "anomaly_edge": anomaly_edge,
                })

    print(f"\n[TREE] {len(rules)} rules derived from {sum(1 for v in thresholds.values() if v)} separable features:")
    for r in rules:
        print(f"  {r['feat']:25s}  x[i] {r['direction']} {r['threshold']:+.4f}  "
              f"(normal_edge={r['normal_edge']:+.3f}, anomaly_edge={r['anomaly_edge']:+.3f})")

    lines = [
        "#ifndef MODEL_TREE_H",
        "#define MODEL_TREE_H",
        "",
        "#include <Arduino.h>",
        "#include \"feature_config.h\"",
        "",
        "// ============================================================",
        "// TinyIDS Hardware-Calibrated Behavioral Decision Tree",
        "// Derived from real Arduino Nano ESP32 telemetry",
        f"// Calibrated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"// Rules: {len(rules)} features with clean normal/anomaly separation",
        "// Zero heap allocation, executes in < 30 microseconds on ESP32-S3",
        "// ============================================================",
        "",
        "inline bool evaluateExportedTree(const float* x, float& confidence, const char*& indicator) {",
        "    // x[0..9] are Z-score normalized features (see preprocessing_params.h)",
    ]

    if not rules:
        # Fallback: use conservative static thresholds
        print("[WARN] No clean separation found. Using conservative fallback thresholds.")
        lines += [
            "    // WARNING: No clean separation found during calibration.",
            "    // Using conservative fallback thresholds (may have high FPR).",
            "    if (x[FEAT_LOOP_MAX_MS] > 3.0f) {",
            "        confidence = 0.90f; indicator = \"CPU_LOOP_BLOCKING\"; return true;",
            "    }",
            "    if (x[FEAT_TRANSACTION_RATE] > 3.0f) {",
            "        confidence = 0.90f; indicator = \"HIGH_TRANSACTION_RATE\"; return true;",
            "    }",
        ]
    else:
        for r in rules:
            lines.append(f"")
            lines.append(f"    // {r['feat']}: anomaly {'above' if r['direction'] == '>' else 'below'} {r['threshold']:+.4f} (normalized)")
            lines.append(f"    if (x[{r['index']}] {r['direction']} {r['threshold']:.4f}f) {{")
            lines.append(f"        confidence = {r['confidence']:.2f}f;")
            lines.append(f"        indicator = \"{r['indicator']}\";")
            lines.append(f"        return true; // ANOMALY")
            lines.append(f"    }}")

    lines += [
        "",
        "    // Default: normal operating envelope",
        "    confidence = 0.97f;",
        "    indicator = \"NORMAL_BASELINE\";",
        "    return false; // NORMAL",
        "}",
        "",
        "#endif // MODEL_TREE_H",
    ]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TREE] Written to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="TinyIDS Hardware Recalibration")
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/cu.usbmodemXXXX")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--output-csv", default="dataset/esp32/raw/hardware_dataset.csv")
    parser.add_argument("--scaler-json", default="model/preprocessing/scaler_params.json")
    parser.add_argument("--preproc-h", default="firmware/TinyIDS/preprocessing_params.h")
    parser.add_argument("--tree-h", default="firmware/TinyIDS/model_tree.h")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("TinyIDS Hardware Recalibration Pipeline")
    print(f"{'='*60}")
    print(f"Port: {args.port} @ {args.baud} baud")

    ser = serial.Serial(args.port, args.baud, timeout=2.0)
    time.sleep(1.5)
    ser.reset_input_buffer()

    # Switch to CSV mode
    send_cmd(ser, "CSV", delay=1.0)

    all_rows = []
    normal_rows = []
    anomaly_rows = []

    for cmd, label, duration in SCENARIOS:
        lname = "NORMAL" if label == 0 else "ANOMALY"
        print(f"\n[SCENARIO] {cmd} → label={label} ({lname}) for {duration}s")
        send_cmd(ser, cmd, delay=1.5)
        rows = read_windows(ser, duration, label)
        print(f"  → Collected {len(rows)} windows")
        all_rows.extend(rows)
        if label == 0:
            normal_rows.extend(rows)
        else:
            anomaly_rows.extend(rows)

    ser.close()

    print(f"\n{'='*60}")
    print(f"Collection complete: {len(all_rows)} total windows")
    print(f"  Normal:  {len(normal_rows)} windows")
    print(f"  Anomaly: {len(anomaly_rows)} windows")

    if len(normal_rows) < 3:
        print("[ERROR] Too few normal windows to fit scaler. Check board connection.")
        sys.exit(1)
    if len(anomaly_rows) < 3:
        print("[WARN] Too few anomaly windows. Tree may not separate well.")

    # Save raw dataset
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    with open(args.output_csv, "w") as f:
        f.write("scenario,label," + ",".join(FEAT_COLS) + "\n")
        for r in all_rows:
            scen = "NORMAL" if r["__label__"] == 0 else "ANOMALY"
            vals = ",".join(str(r[feat]) for feat in FEAT_COLS)
            f.write(f"{scen},{r['__label__']},{vals}\n")
    print(f"\n[CSV] Saved {len(all_rows)} rows to {args.output_csv}")

    # Fit scaler on normal only
    mean, std = compute_scaler(normal_rows)
    print(f"\n[SCALER] Mean: {[round(v,3) for v in mean]}")
    print(f"[SCALER] Std:  {[round(v,3) for v in std]}")

    # Normalize all rows
    normal_rows  = normalize(normal_rows,  mean, std)
    anomaly_rows = normalize(anomaly_rows, mean, std)

    # Derive thresholds
    thresholds = {}
    if anomaly_rows:
        thresholds = derive_thresholds(normal_rows, anomaly_rows)
    else:
        print("[WARN] No anomaly data. Tree will use fallback conservative rules.")

    # Write outputs
    write_scaler_json(mean, std, args.scaler_json)
    write_preprocessing_h(mean, std, args.preproc_h)
    write_model_tree_h(thresholds, args.tree_h)

    print(f"\n{'='*60}")
    print("Recalibration COMPLETE.")
    print("Next step: recompile and upload firmware.")
    print(f"  arduino-cli compile --fqbn arduino:esp32:nano_nora firmware/TinyIDS")
    print(f"  arduino-cli upload  -p {args.port} --fqbn arduino:esp32:nano_nora firmware/TinyIDS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
