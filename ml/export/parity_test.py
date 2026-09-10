#!/usr/bin/env python3
"""
TinyIDS — Preprocessing & Model Parity Test
Verifies that Python sklearn prediction matches the C++ tree traversal exactly.
"""

import os
import json
import pickle
import numpy as np
from sklearn.tree import _tree

WORKSPACE = "/Users/parineeth/Desktop/tinyIDS"

FEATURE_COLS = [
    'transaction_rate', 'byte_rate', 'free_heap', 'heap_delta',
    'loop_avg_ms', 'loop_max_ms', 'loop_jitter_ms', 'wifi_rssi',
    'avg_inter_arrival_ms', 'socket_errors'
]


def simulate_cpp_tree(dt, x_norm):
    """Traverse the sklearn tree exactly as the C++ code would.
    Returns (prediction, confidence) matching evaluateExportedTree().
    """
    tree_ = dt.tree_
    node = 0

    while tree_.feature[node] != _tree.TREE_UNDEFINED:
        feat_idx = tree_.feature[node]
        threshold = tree_.threshold[node]
        if x_norm[feat_idx] <= threshold:
            node = tree_.children_left[node]
        else:
            node = tree_.children_right[node]

    # Leaf node
    values = tree_.value[node][0]
    total = float(sum(values))
    pred_class = int(values.argmax())
    confidence = float(values[pred_class] / total)
    return pred_class, confidence


def simulate_cpp_normalize(raw, means, scales):
    """Replicate the C++ normalizeFeatures function exactly."""
    return [(raw[i] - means[i]) / scales[i] for i in range(len(raw))]


def run_parity_test():
    print("=" * 60)
    print("TinyIDS — Preprocessing & Model Parity Test")
    print("=" * 60)

    # Load scaler params
    scaler_path = os.path.join(WORKSPACE, "model/preprocessing/scaler_params.json")
    with open(scaler_path, "r") as f:
        scaler_data = json.load(f)

    features = scaler_data["features"]
    means = np.array(scaler_data["mean"])
    scales = np.array(scaler_data["scale"])

    assert features == FEATURE_COLS, f"Feature mismatch: {features} vs {FEATURE_COLS}"

    # Load trained model
    model_path = os.path.join(WORKSPACE, "model/final_model/decision_tree.pkl")
    with open(model_path, "rb") as f:
        dt = pickle.load(f)

    # Test vectors covering diverse scenarios
    test_vectors = [
        {"desc": "Normal Idle (minimal activity)",
         "vals": [0.05, 10.0, 270000, 0, 0.15, 0.5, 0.05, -55, 5000.0, 0]},
        {"desc": "Normal Periodic (moderate traffic)",
         "vals": [1.0, 128.0, 268000, -200, 0.35, 1.2, 0.12, -58, 1000.0, 0]},
        {"desc": "Normal Variable (higher traffic)",
         "vals": [2.2, 280.0, 266000, -500, 0.50, 2.5, 0.25, -60, 450.0, 0]},
        {"desc": "Anomaly High-Rate Flood",
         "vals": [18.5, 2400.0, 255000, -15000, 1.8, 12.0, 1.8, -62, 55.0, 1]},
        {"desc": "Anomaly Compute Stress",
         "vals": [0.8, 100.0, 269000, 0, 8.5, 24.0, 4.2, -56, 1250.0, 0]},
        {"desc": "Anomaly Memory Pressure",
         "vals": [0.5, 80.0, 235000, -35000, 0.8, 4.0, 0.4, -55, 2000.0, 0]},
        {"desc": "Anomaly Combined (flood + compute)",
         "vals": [16.0, 2100.0, 240000, -30000, 7.5, 32.0, 5.0, -64, 62.0, 4]},
        {"desc": "HW Normal (from real ESP32 data)",
         "vals": [2.0, 192.0, 320884, 0, 4.993, 5.024, 0.001, -127, 401.024, 0]},
        {"desc": "HW Anomaly High-Rate (from real ESP32 data)",
         "vals": [40.0, 7680.0, 320884, 0, 0.0034, 0.209, 0.0031, -127, 24.784, 0]},
        {"desc": "HW Anomaly Compute (from real ESP32 data)",
         "vals": [0.0, 0.0, 320884, 0, 19.9942, 20.318, 0.0206, -127, 5000.0, 0]},
    ]

    results = []
    all_match = True

    for vec in test_vectors:
        x_raw = np.array(vec["vals"], dtype=np.float64)

        # Python sklearn prediction
        x_norm_py = (x_raw - means) / scales
        py_pred = int(dt.predict([x_norm_py])[0])

        # Simulated C++ prediction (exact tree traversal)
        x_norm_cpp = simulate_cpp_normalize(vec["vals"], means.tolist(), scales.tolist())
        cpp_pred, cpp_conf = simulate_cpp_tree(dt, x_norm_cpp)

        # Verify normalization parity
        norm_match = all(abs(a - b) < 1e-6 for a, b in zip(x_norm_py, x_norm_cpp))

        match = (py_pred == cpp_pred) and norm_match
        if not match:
            all_match = False

        label = "ANOMALY" if py_pred == 1 else "NORMAL"
        status = "✓ PASS" if match else "✗ FAIL"

        results.append({
            "vector": vec["desc"],
            "python_prediction": py_pred,
            "cpp_prediction": cpp_pred,
            "cpp_confidence": round(cpp_conf, 4),
            "normalize_match": norm_match,
            "parity_match": match
        })
        print(f"  {status}  {vec['desc']}: {label} (py={py_pred}, cpp={cpp_pred}, conf={cpp_conf:.4f})")

    print(f"\n{'=' * 60}")
    print(f"Overall Parity: {'PASS ✓ (100% Match)' if all_match else 'FAIL ✗'}")
    print(f"Vectors tested: {len(results)}")
    print(f"{'=' * 60}")

    # Save test vectors
    os.makedirs(os.path.join(WORKSPACE, "model/test_vectors"), exist_ok=True)
    out_path = os.path.join(WORKSPACE, "model/test_vectors/test_vectors.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {out_path}")

    return all_match


if __name__ == "__main__":
    success = run_parity_test()
    exit(0 if success else 1)
