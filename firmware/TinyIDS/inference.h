#ifndef INFERENCE_H
#define INFERENCE_H

#include <Arduino.h>
#include "telemetry.h"
#include "feature_config.h"
#include "preprocessing_params.h"
#include "model_tree.h"

struct InferenceResult {
    uint8_t     prediction;          // 0 = NORMAL, 1 = ANOMALY
    float       confidence;          // 0.0 to 1.0
    uint8_t     risk_score;          // 0 to 100
    const char* severity;            // "LOW", "MEDIUM", "HIGH", "CRITICAL"
    const char* primary_reason;      // Dominant behavioral indicator
    uint8_t     smoothed_prediction; // 0 or 1 based on 2-of-3 window consensus
    uint32_t    inference_time_us;   // Exact measured execution latency in microseconds
};

class InferenceEngine {
public:
    InferenceEngine();
    void begin();
    InferenceResult predict(const TelemetryWindow& win);

private:
    uint8_t history[3];
    uint8_t history_idx;
    uint8_t history_count;
    
    void extractFeatureVector(const TelemetryWindow& win, float* out_raw);
    uint8_t calculateRiskScore(bool isAnomaly, float conf, const TelemetryWindow& win);
    const char* getSeverityString(uint8_t score);
};

extern InferenceEngine TinyML;

#endif // INFERENCE_H
