#ifndef PREPROCESSING_PARAMS_H
#define PREPROCESSING_PARAMS_H

// Auto-generated from sklearn StandardScaler
// Source: ml/training/train_and_export.py
// Generated: 2026-09-09 11:05:07

#include "feature_config.h"

// Feature names (for documentation)
// transaction_rate, byte_rate, free_heap, heap_delta, loop_avg_ms, loop_max_ms, loop_jitter_ms, wifi_rssi, avg_inter_arrival_ms, socket_errors

static const float SCALER_MEAN[NUM_FEATURES] = {
    9.5056901235f, 1738.8514814815f, 320948.6419753087f, 1.8765432099f, 11.3602037037f, 13.1073703704f, 0.1547098765f, -127.0000000000f, 1843.3949753086f, 0.0000000000f
};

static const float SCALER_SCALE[NUM_FEATURES] = {
    13.6927528535f, 2656.7602770794f, 44.7564902920f, 7.0297124540f, 12.4072986210f, 12.6991991576f, 0.4381990738f, 1.0000000000f, 2298.1423199609f, 1.0000000000f
};

inline void normalizeFeatures(const float* raw, float* out) {
    for (int i = 0; i < NUM_FEATURES; i++) {
        out[i] = (raw[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];
    }
}

#endif // PREPROCESSING_PARAMS_H
