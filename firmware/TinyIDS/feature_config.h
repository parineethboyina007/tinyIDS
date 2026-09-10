#ifndef FEATURE_CONFIG_H
#define FEATURE_CONFIG_H

#include <Arduino.h>

#define NUM_FEATURES 10

// Strict feature ordering - identical between Python, C++, and exported models
enum FeatureIndex : uint8_t {
    FEAT_TRANSACTION_RATE     = 0, // ops/s (application socket operations per second)
    FEAT_BYTE_RATE            = 1, // B/s (application payload throughput per second)
    FEAT_FREE_HEAP            = 2, // bytes (unallocated SRAM at window close)
    FEAT_HEAP_DELTA           = 3, // bytes (end - start; negative indicates allocation)
    FEAT_LOOP_AVG_MS          = 4, // ms (mean loop pass execution time)
    FEAT_LOOP_MAX_MS          = 5, // ms (worst-case blocking loop duration)
    FEAT_LOOP_JITTER_MS       = 6, // ms (streaming standard deviation of loop time)
    FEAT_WIFI_RSSI            = 7, // dBm (-30 to -95 dBm; -127 sentinel if disconnected)
    FEAT_AVG_INTER_ARRIVAL_MS = 8, // ms (mean elapsed time between socket actions)
    FEAT_SOCKET_ERRORS        = 9  // count (failed connections or write timeouts)
};

inline const char* getFeatureName(uint8_t idx) {
    switch (idx) {
        case FEAT_TRANSACTION_RATE:     return "transaction_rate";
        case FEAT_BYTE_RATE:            return "byte_rate";
        case FEAT_FREE_HEAP:            return "free_heap";
        case FEAT_HEAP_DELTA:           return "heap_delta";
        case FEAT_LOOP_AVG_MS:          return "loop_avg_ms";
        case FEAT_LOOP_MAX_MS:          return "loop_max_ms";
        case FEAT_LOOP_JITTER_MS:       return "loop_jitter_ms";
        case FEAT_WIFI_RSSI:            return "wifi_rssi";
        case FEAT_AVG_INTER_ARRIVAL_MS: return "avg_inter_arrival_ms";
        case FEAT_SOCKET_ERRORS:        return "socket_errors";
        default:                        return "unknown";
    }
}

#endif // FEATURE_CONFIG_H
