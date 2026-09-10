#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// Attempt to load private credentials if available; otherwise use offline mode
#if __has_include("config_private.h")
#include "config_private.h"
#define HAS_WIFI_CONFIG 1
#else
#define HAS_WIFI_CONFIG 0
#define WIFI_SSID_DEFAULT     "NOT_CONFIGURED"
#define WIFI_PASSWORD_DEFAULT ""
#define TEST_SERVER_HOST      "127.0.0.1"
#define TEST_SERVER_PORT      80
#define SOFTAP_SSID_DEFAULT     "TinyIDS-ESP32"
#define SOFTAP_PASSWORD_DEFAULT "tinyids123"
#endif

// ==============================================================================
// Operating Modes
// MODE_DASHBOARD : Live visual security monitoring terminal (Default)
// MODE_CSV       : Pure machine-readable CSV stream for automated dataset collection
// ==============================================================================
#define MODE_DASHBOARD        0
#define MODE_CSV              1

// Default boot mode: DASHBOARD for instant interactive verification
#define DEFAULT_OPERATING_MODE MODE_DASHBOARD

// System & Operational Constants
#define FIRMWARE_VERSION      "3.0.0"
#define SERIAL_BAUD_RATE      115200     // USB Serial communication baud rate
#define WINDOW_DURATION_MS    5000       // Aggregation window length: 5000 ms
#define USB_CDC_WAIT_MS       3000       // Bounded wait for USB host terminal at boot
#define DEFAULT_SCENARIO_WINDOWS 12      // 12 windows * 5s = 60s per scenario

// Safety Thresholds (Hard Microcontroller Guards)
#define MIN_SAFE_FREE_HEAP    40960      // 40 KB: Abort memory stress if heap is lower
#define MAX_COMPUTE_CHUNK_MS  25         // Max continuous CPU loop block to feed WDT
#define MAX_CONNS_PER_WINDOW  60         // Cap socket attempts per 5-second window
#define MAX_STRESS_ALLOC_BYTES 49152     // 48 KB: Hard ceiling on temporary allocations

// Sentinel for disconnected Wi-Fi RSSI (NOT zero, which is a valid signal level)
#define WIFI_RSSI_DISCONNECTED -127

enum ScenarioID : uint8_t {
    SCENARIO_NORMAL_IDLE = 0,
    SCENARIO_NORMAL_PERIODIC = 1,
    SCENARIO_NORMAL_VARIABLE = 2,
    SCENARIO_ANOMALY_HIGH_RATE = 3,
    SCENARIO_ANOMALY_BURST = 4,
    SCENARIO_ANOMALY_CONNECTION_STRESS = 5,
    SCENARIO_ANOMALY_COMPUTE = 6,
    SCENARIO_ANOMALY_MEMORY = 7,
    SCENARIO_ANOMALY_COMBINED = 8,
    SCENARIO_COUNT = 9
};

enum SecurityLabel : uint8_t {
    LABEL_NORMAL = 0,
    LABEL_ANOMALY = 1,
    LABEL_TRANSITION = 255  // Transition window: mixed behavior, MUST discard from ML
};

inline const char* getScenarioName(uint8_t id) {
    switch (id) {
        case SCENARIO_NORMAL_IDLE:               return "NORMAL_IDLE";
        case SCENARIO_NORMAL_PERIODIC:           return "NORMAL_PERIODIC";
        case SCENARIO_NORMAL_VARIABLE:           return "NORMAL_VARIABLE";
        case SCENARIO_ANOMALY_HIGH_RATE:         return "ANOMALY_HIGH_RATE";
        case SCENARIO_ANOMALY_BURST:             return "ANOMALY_BURST";
        case SCENARIO_ANOMALY_CONNECTION_STRESS: return "ANOMALY_CONNECTION_STRESS";
        case SCENARIO_ANOMALY_COMPUTE:           return "ANOMALY_COMPUTE";
        case SCENARIO_ANOMALY_MEMORY:            return "ANOMALY_MEMORY";
        case SCENARIO_ANOMALY_COMBINED:          return "ANOMALY_COMBINED";
        default:                                 return "UNKNOWN";
    }
}

#endif // CONFIG_H
