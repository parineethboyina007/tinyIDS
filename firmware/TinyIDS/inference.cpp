#include "inference.h"

InferenceEngine TinyML;

InferenceEngine::InferenceEngine() {
    history_idx = 0;
    history_count = 0;
    for (int i = 0; i < 3; i++) history[i] = 0;
}

void InferenceEngine::begin() {
    history_idx = 0;
    history_count = 0;
    for (int i = 0; i < 3; i++) history[i] = 0;
}

void InferenceEngine::extractFeatureVector(const TelemetryWindow& win, float* out_raw) {
    out_raw[FEAT_TRANSACTION_RATE]     = win.transaction_rate;
    out_raw[FEAT_BYTE_RATE]            = win.byte_rate;
    out_raw[FEAT_FREE_HEAP]            = (float)win.free_heap;
    out_raw[FEAT_HEAP_DELTA]           = (float)win.heap_delta;
    out_raw[FEAT_LOOP_AVG_MS]          = win.loop_avg_ms;
    out_raw[FEAT_LOOP_MAX_MS]          = win.loop_max_ms;
    out_raw[FEAT_LOOP_JITTER_MS]       = win.loop_jitter_ms;
    out_raw[FEAT_WIFI_RSSI]            = (float)win.wifi_rssi;
    out_raw[FEAT_AVG_INTER_ARRIVAL_MS] = win.avg_inter_arrival_ms;
    out_raw[FEAT_SOCKET_ERRORS]        = (float)win.socket_errors;
}

uint8_t InferenceEngine::calculateRiskScore(bool isAnomaly, float conf, const TelemetryWindow& win) {
    if (!isAnomaly) {
        float base = 5.0f;
        if (win.transaction_rate > 3.0f) base += 8.0f;
        if (win.loop_max_ms > 8.0f) base += 5.0f;
        return (uint8_t)constrain((int)base, 0, 29);
    }
    
    float score = 60.0f + (conf * 25.0f);
    if (win.transaction_rate >= 10.0f) score += 8.0f;
    if (win.loop_max_ms >= 20.0f) score += 7.0f;
    if (win.heap_delta <= -16384) score += 8.0f;
    return (uint8_t)constrain((int)score, 60, 100);
}

const char* InferenceEngine::getSeverityString(uint8_t score) {
    if (score < 30) return "LOW";
    if (score < 60) return "MEDIUM";
    if (score < 80) return "HIGH";
    return "CRITICAL";
}

InferenceResult InferenceEngine::predict(const TelemetryWindow& win) {
    uint32_t t0_us = micros();
    
    float raw_features[NUM_FEATURES];
    float norm_features[NUM_FEATURES];
    
    extractFeatureVector(win, raw_features);
    normalizeFeatures(raw_features, norm_features);
    
    float conf = 0.0f;
    const char* reason = "NORMAL_BASELINE";
    bool is_anomaly = evaluateExportedTree(norm_features, conf, reason);
    
    InferenceResult res;
    res.prediction = is_anomaly ? 1 : 0;
    res.confidence = conf;
    res.primary_reason = reason;
    res.risk_score = calculateRiskScore(is_anomaly, conf, win);
    res.severity = getSeverityString(res.risk_score);
    
    // Temporal smoothing: 3-window ring buffer (2-of-3 majority consensus)
    history[history_idx] = res.prediction;
    history_idx = (history_idx + 1) % 3;
    if (history_count < 3) history_count++;
    
    uint8_t votes = 0;
    for (int i = 0; i < history_count; i++) {
        if (history[i] == 1) votes++;
    }
    res.smoothed_prediction = (votes >= 2) ? 1 : 0;
    res.inference_time_us = micros() - t0_us;
    
    return res;
}
