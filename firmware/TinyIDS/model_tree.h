#ifndef MODEL_TREE_H
#define MODEL_TREE_H

#include <Arduino.h>
#include "feature_config.h"

// ============================================================
// Auto-generated from sklearn DecisionTreeClassifier
// Exported: 2026-09-09 11:05:07
// Tree depth: 2, Leaves: 4
// Training data: ESP32 telemetry from dataset/esp32/raw/
// Features: transaction_rate, byte_rate, free_heap, heap_delta, loop_avg_ms, loop_max_ms, loop_jitter_ms, wifi_rssi, avg_inter_arrival_ms, socket_errors
// ============================================================

inline bool evaluateExportedTree(const float* x, float& confidence, const char*& indicator) {
    if (x[5] <= -0.197679f) { // loop_max_ms
        if (x[5] <= -0.839098f) { // loop_max_ms
            confidence = 1.0000f;
            indicator = "ANOMALY_LOOP_MAX_MS";
            return true; // class=ANOMALY, conf=1.0000
        } else {
            confidence = 1.0000f;
            indicator = "NORMAL_BASELINE";
            return false; // class=NORMAL, conf=1.0000
        }
    } else {
        if (x[6] <= 1.565818f) { // loop_jitter_ms
            confidence = 1.0000f;
            indicator = "ANOMALY_LOOP_JITTER_MS";
            return true; // class=ANOMALY, conf=1.0000
        } else {
            confidence = 0.7500f;
            indicator = "ANOMALY_LOOP_JITTER_MS";
            return true; // class=ANOMALY, conf=0.7500
        }
    }
}

#endif // MODEL_TREE_H
